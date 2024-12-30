from dataclasses import dataclass
from typing import Optional
import os
import json
from pathlib import Path


@dataclass
class AppConfig:
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    database_path: str = "chat_history.db"
    max_history_items: int = 100
    default_context: str = ""
    window_width: int = 800
    window_height: int = 600


class ConfigManager:
    def __init__(self):
        self.config_file = Path.home() / ".toolbar_chat" / "config.json"
        self.config: Optional[AppConfig] = None
        self._load_config()

    def _load_config(self) -> None:
        if not self.config_file.exists():
            self._create_default_config()

        try:
            with open(self.config_file, "r") as f:
                config_data = json.load(f)
                self.config = AppConfig(**config_data)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")

    def _create_default_config(self) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        default_config = AppConfig(openai_api_key=os.environ.get("OPENAI_API_KEY", ""))
        self.save_config(default_config)

    def save_config(self, config: AppConfig) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(vars(config), f, indent=4)
        self.config = config
