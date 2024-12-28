import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from .ui.toolbar_app import ToolbarApp
from .config import ConfigManager


def setup_logging() -> None:
    log_dir = Path.home() / ".toolbar_chat" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting application...")

    try:
        # Create application
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName("AI Chat Toolbar")

        # Set application icon
        icon_path = Path(__file__).parent / "resources" / "icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        # Initialize toolbar
        toolbar = ToolbarApp()

        # Start event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
