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
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor, QKeySequence, QShortcut
import asyncio
import asyncio.events
from typing import Optional
from datetime import datetime
import markdown2

from openai_client import OpenAIWrapper
from db_manager import DatabaseManager, ChatMessage
from config import AppConfig


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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Context selector
        context_layout = QHBoxLayout()
        context_layout.setContentsMargins(0, 0, 0, 8)
        self.context_combo = QComboBox()
        self.context_combo.setMinimumWidth(200)
        self.context_combo.setStyleSheet(
            """
            QComboBox {
                padding: 5px;
                border: 1px solid;
                border-radius: 4px;
            }
        """
        )
        context_layout.addWidget(QLabel("Context:"))
        context_layout.addWidget(self.context_combo)
        context_layout.addStretch()
        layout.addLayout(context_layout)

        # Split view for search results and chat
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid;
                border-radius: 4px;
                padding: 8px;
            }
        """
        )
        splitter.addWidget(self.chat_history)
        layout.addWidget(splitter)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 8, 0, 8)
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid;
                border-radius: 4px;
                padding: 8px;
            }
        """
        )
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(
            """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid;
                border-radius: 4px;
            }
            QPushButton:hover {
                border-width: 2px;
            }
        """
        )
        self.send_button.clicked.connect(self.handle_send_message)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid;
                border-radius: 4px;
                text-align: center;
            }
        """
        )
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
            current_context = self.context_combo.currentData()
            response = await self.api_client.send_message(
                [{"role": "user", "content": message}],
                context=current_context.content if current_context else "",
            )

            thread_id = None
            if not hasattr(self, "current_thread_id"):
                self.current_thread_id = datetime.now().timestamp()
            thread_id = self.current_thread_id

            self.db.add_message(
                ChatMessage(
                    id=None,
                    user_message=message,
                    assistant_message=response.choices[0].message.content,
                    context_id=current_context.id if current_context else "",
                    timestamp=datetime.now(),
                    thread_id=thread_id,
                )
            )

            if current_context:
                self.append_message("Context", current_context.content)
            self.append_message("You", message)
            self.append_message("Assistant", response.choices[0].message.content)

        finally:
            self.progress_bar.setVisible(False)

    def append_message(self, sender: str, content: str) -> None:
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Convert markdown to HTML for Assistant messages
        if sender == "Assistant":
            content = markdown2.markdown(
                content,
                extras=[
                    "fenced-code-blocks",
                    "tables",
                    "break-on-newline",
                    "code-friendly",
                ],
            )

        # Add styling to different message types
        if sender == "You":
            cursor.insertHtml(
                f'<div style="margin: 12px 0; padding: 8px; border: 1px solid; border-radius: 4px;">'
                f"<b>{sender}:</b><br>{content}<br><br></div>"
            )
        elif sender == "Assistant":
            cursor.insertHtml(
                f'<div style="margin: 12px 0; padding: 8px; border: 1px solid; border-radius: 4px;">'
                f"<b>{sender}:</b><br>{content}</div>"
                f'<div style="margin: 12px 0;">{"".join(["-" for _ in range(10)])}<br><br></div>'
            )
        elif sender == "Context":
            cursor.insertHtml(
                f'<div style="margin: 12px 0; padding: 8px; border: 1px solid; border-radius: 4px; border-style: dashed;">'
                f"<i>{sender}:</i><br>{content}<br><br></div>"
            )

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
