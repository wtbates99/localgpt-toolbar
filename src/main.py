#!/usr/bin/env python3
"""Main entry point for the AI Chat Toolbar application."""

import sys
import asyncio
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qasync import QEventLoop

from toolbar_app import ToolbarApp


def main() -> None:
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("AI Chat Toolbar")

    # Create event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Set application icon
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Initialize toolbar
    toolbar = ToolbarApp()

    # Start event loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
