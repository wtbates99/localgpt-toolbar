from PyQt6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QDialog,
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional
from pathlib import Path

from config import ConfigManager
from chat_window import ChatWindow
from settings_dialog import SettingsDialog
from openai_client import OpenAIWrapper
from db_manager import DatabaseManager
from context_manager_dialog import ContextManagerDialog


class ToolbarApp(QObject):
    chat_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.setup_app()

    def setup_app(self) -> None:
        self.db = DatabaseManager(self.config_manager.config.database_path)
        self.api_client = OpenAIWrapper(
            self.config_manager.config.openai_api_key,
            self.config_manager.config.model_name,
        )

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.get_app_icon())
        self.setup_tray_menu()

        self.chat_window: Optional[ChatWindow] = None
        self.chat_requested.connect(self.show_chat_window)

        self.tray_icon.show()

    def get_app_icon(self) -> QIcon:
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if not icon_path.exists():
            return QIcon()
        return QIcon(str(icon_path))

    def setup_tray_menu(self) -> None:
        menu = QMenu()

        # Chat action
        chat_action = QAction("New Chat", self)
        chat_action.triggered.connect(self.chat_requested.emit)
        chat_action.setShortcut("Ctrl+Shift+C")
        menu.addAction(chat_action)

        # Search action
        search_action = QAction("Search History", self)
        search_action.triggered.connect(self.show_search_dialog)
        menu.addAction(search_action)

        # Context Manager action
        context_action = QAction("Manage Contexts", self)
        context_action.triggered.connect(self.show_context_manager)
        menu.addAction(context_action)

        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.handle_tray_activation)

    def handle_tray_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.chat_requested.emit()

    def show_chat_window(self) -> None:
        if not self.chat_window:
            self.chat_window = ChatWindow(
                self.api_client, self.db, self.config_manager.config
            )
            self.chat_window.closed.connect(self.handle_chat_window_closed)

        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()

    def handle_chat_window_closed(self) -> None:
        self.chat_window = None

    def show_settings(self) -> None:
        dialog = SettingsDialog(self.config_manager, None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload app with new settings
            self.setup_app()

    def show_context_manager(self) -> None:
        dialog = ContextManagerDialog(self.db)
        dialog.exec()
        # Refresh context in chat window if it's open
        if self.chat_window:
            self.chat_window.load_contexts()

    def show_search_dialog(self) -> None:
        from search_dialog import SearchDialog

        dialog = SearchDialog(self.db)
        dialog.exec()
