from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QTextEdit,
    QPushButton,
    QInputDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from datetime import datetime

from src.db_manager import DatabaseManager, Context


class ContextManagerDialog(QDialog):
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()
        self.load_contexts()

    def setup_ui(self) -> None:
        self.setWindowTitle("Context Manager")
        self.setMinimumSize(600, 400)

        layout = QHBoxLayout(self)

        # Left side - context list
        left_layout = QVBoxLayout()
        self.context_list = QListWidget()
        self.context_list.currentItemChanged.connect(self.on_context_selected)
        left_layout.addWidget(self.context_list)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        self.add_button.clicked.connect(self.add_context)
        self.delete_button.clicked.connect(self.delete_context)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        left_layout.addLayout(button_layout)

        layout.addLayout(left_layout)

        # Right side - context editor
        right_layout = QVBoxLayout()
        self.context_editor = QTextEdit()
        self.context_editor.textChanged.connect(self.on_context_edited)
        right_layout.addWidget(self.context_editor)

        save_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_context)
        self.save_button.setEnabled(False)
        save_layout.addStretch()
        save_layout.addWidget(self.save_button)
        right_layout.addLayout(save_layout)

        layout.addLayout(right_layout)

    def load_contexts(self) -> None:
        contexts = self.db.get_contexts()
        self.context_list.clear()
        for context in contexts:
            self.context_list.addItem(context.name)
            self.context_list.item(self.context_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole, context
            )

    def on_context_selected(self, current, previous) -> None:
        if current:
            context = current.data(Qt.ItemDataRole.UserRole)
            self.context_editor.setText(context.content)
        else:
            self.context_editor.clear()
        self.save_button.setEnabled(False)

    def on_context_edited(self) -> None:
        if self.context_list.currentItem():
            self.save_button.setEnabled(True)

    def add_context(self) -> None:
        name, ok = QInputDialog.getText(self, "New Context", "Enter context name:")
        if ok and name:
            context = Context(
                id=None,
                name=name,
                content="",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            context_id = self.db.add_context(context)
            context.id = context_id
            item = self.context_list.addItem(name)
            item.setData(Qt.ItemDataRole.UserRole, context)

    def delete_context(self) -> None:
        current = self.context_list.currentItem()
        if not current:
            return

        context = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete context '{context.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_context(context.id)
            self.context_list.takeItem(self.context_list.row(current))
            self.context_editor.clear()

    def save_context(self) -> None:
        current = self.context_list.currentItem()
        if not current:
            return
        context = current.data(Qt.ItemDataRole.UserRole)
        context.content = self.context_editor.toPlainText()
        context.updated_at = datetime.now()
        self.db.update_context(context)
        self.save_button.setEnabled(False)