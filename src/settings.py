from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QComboBox,
    QSpinBox,
)
from config import AppConfig, ConfigManager


class SettingsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()
        self.load_settings()

    def setup_ui(self) -> None:
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Form layout for settings
        form_layout = QFormLayout()

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"])
        form_layout.addRow("Model:", self.model_combo)

        # Window dimensions
        self.width_input = QSpinBox()
        self.width_input.setRange(400, 1920)
        self.width_input.setSingleStep(50)
        form_layout.addRow("Window Width:", self.width_input)

        self.height_input = QSpinBox()
        self.height_input.setRange(300, 1080)
        self.height_input.setSingleStep(50)
        form_layout.addRow("Window Height:", self.height_input)

        # History limit
        self.history_limit = QSpinBox()
        self.history_limit.setRange(10, 1000)
        self.history_limit.setSingleStep(10)
        form_layout.addRow("Max History Items:", self.history_limit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def load_settings(self) -> None:
        config = self.config_manager.config
        self.model_combo.setCurrentText(config.model_name)
        self.width_input.setValue(config.window_width)
        self.height_input.setValue(config.window_height)
        self.history_limit.setValue(config.max_history_items)

    def save_settings(self) -> None:
        current_config = self.config_manager.config
        new_config = AppConfig(
            openai_api_key=current_config.openai_api_key,
            model_name=self.model_combo.currentText(),
            window_width=self.width_input.value(),
            window_height=self.height_input.value(),
            max_history_items=self.history_limit.value(),
            database_path=current_config.database_path,
            default_context=current_config.default_context,
        )
        self.config_manager.save_config(new_config)
        self.accept()
