from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox,
)
from PyQt6.QtCore import Qt
from db_manager import DatabaseManager, ChatMessage
from datetime import datetime


class SearchDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWindowTitle("Search Chat History")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Search controls
        search_layout = QHBoxLayout()

        self.search_type = QComboBox()
        self.search_type.addItems(["All", "User Messages", "Assistant Responses"])
        search_layout.addWidget(self.search_type)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search terms...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(
            ["Time", "Context", "User Message", "Assistant Response"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)

        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def perform_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return

        search_type = self.search_type.currentText()
        messages = self.db.search_messages(query, search_type)

        self.results_table.setRowCount(0)
        for msg in messages:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            time_item = QTableWidgetItem(msg.timestamp.strftime("%Y-%m-%d %H:%M"))
            context_item = QTableWidgetItem(
                msg.context_name if hasattr(msg, "context_name") else ""
            )
            user_msg_item = QTableWidgetItem(msg.user_message)
            assistant_msg_item = QTableWidgetItem(msg.assistant_message)

            self.results_table.setItem(row, 0, time_item)
            self.results_table.setItem(row, 1, context_item)
            self.results_table.setItem(row, 2, user_msg_item)
            self.results_table.setItem(row, 3, assistant_msg_item)

        self.status_label.setText(f"Found {len(messages)} results")
