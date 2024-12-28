from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QProgressBar,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor, QKeySequence, QShortcut
import asyncio
import asyncio.events
from typing import Optional
from datetime import datetime

from src.api.openai_client import OpenAIWrapper
from src.database.db_manager import DatabaseManager, ChatMessage
from src.config import AppConfig


class ChatWindow(QMainWindow):
    closed = pyqtSignal()

    def __init__(
        self,
        api_client: OpenAIWrapper,
        db: DatabaseManager,
        config: AppConfig,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.api_client = api_client
        self.db = db
        self.config = config
        self._sending = False

        self.setup_ui()
        self.load_contexts()
        self.setup_shortcuts()

    def setup_ui(self) -> None:
        self.setWindowTitle("Chat")
        self.setGeometry(100, 100, self.config.window_width, self.config.window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Context selector
        context_layout = QHBoxLayout()
        self.context_combo = QComboBox()
        self.context_combo.setMinimumWidth(200)
        context_layout.addWidget(QLabel("Context:"))
        context_layout.addWidget(self.context_combo)
        context_layout.addStretch()
        layout.addLayout(context_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search chat history...")
        self.search_input.textChanged.connect(self.search_history)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Split view for search results and chat
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Search results
        self.search_results = QListWidget()
        self.search_results.itemClicked.connect(self.load_chat_thread)
        self.search_results.setVisible(False)
        splitter.addWidget(self.search_results)

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        splitter.addWidget(self.chat_history)
        layout.addWidget(splitter)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_send_message)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def setup_shortcuts(self) -> None:
        send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        send_shortcut.activated.connect(self.handle_send_message)

        clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_shortcut.activated.connect(self.clear_chat)

    def handle_send_message(self) -> None:
        """Handle the send message action by running the coroutine."""
        if self._sending:
            self.logger.warning("Message send in progress, please wait...")
            return

        self._sending = True
        asyncio.create_task(self._send_message_wrapper())

    @pyqtSlot()
    async def _send_message_wrapper(self) -> None:
        try:
            await self.send_message()
        finally:
            self._sending = False

    async def send_message(self) -> None:
        message = self.input_field.toPlainText().strip()
        if not message:
            return

        self.input_field.clear()
        self.progress_bar.setVisible(True)

        try:
            context = self.context_combo.currentData()
            response = await self.api_client.send_message(
                [{"role": "user", "content": message}],
                context=context.content if context else "",
            )

            # Save message to database
            self.db.add_message(
                ChatMessage(
                    id=None,
                    role="user",
                    content=message,
                    context_id=context.id if context else None,
                    timestamp=datetime.now(),
                    thread_id=None,
                )
            )

            # Update chat history
            self.append_message("You", message)
            self.append_message("Assistant", response.choices[0].message.content)

        finally:
            self.progress_bar.setVisible(False)

    def append_message(self, sender: str, content: str) -> None:
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"\n{sender}: {content}\n")
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()

    def clear_chat(self) -> None:
        self.chat_history.clear()

    def load_contexts(self) -> None:
        """Load available contexts into the context selector."""
        self.context_combo.clear()
        self.context_combo.addItem("No Context", None)

        contexts = self.db.get_contexts()
        for context in contexts:
            self.context_combo.addItem(context.name, context)

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)

    def search_history(self) -> None:
        """Search chat history for the given query."""
        query = self.search_input.text().strip().lower()
        self.search_results.clear()

        if not query:
            self.search_results.setVisible(False)
            return

        messages = self.db.search_messages(query)

        if messages:
            self.search_results.setVisible(True)
            for msg in messages:
                item = QListWidgetItem(
                    f"{msg.timestamp.strftime('%Y-%m-%d %H:%M')} - "
                    f"{msg.content[:100]}..."
                )
                item.setData(Qt.ItemDataRole.UserRole, msg)
                self.search_results.addItem(item)
        else:
            self.search_results.setVisible(False)

    def load_chat_thread(self, item: QListWidgetItem) -> None:
        """Load the chat thread containing the selected message."""
        message = item.data(Qt.ItemDataRole.UserRole)
        if not message.thread_id:
            return

        self.chat_history.clear()
        messages = self.db.get_messages(thread_id=message.thread_id)

        for msg in reversed(messages):  # Show oldest first
            sender = "You" if msg.role == "user" else "Assistant"
            self.append_message(sender, msg.content)

    def setup_event_loop(self) -> None:
        """Set up the event loop for async operations."""
        self.loop = asyncio.get_event_loop()
