import sys
import asyncio
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qasync import QEventLoop

from toolbar import ToolbarApp


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("AI Chat Toolbar")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    toolbar = ToolbarApp()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
