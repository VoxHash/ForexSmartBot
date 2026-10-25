"""Application entry point (console script: forexsmartbot)."""

import logging
import os
import sys

from dotenv import load_dotenv
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from forexsmartbot import __version__
from forexsmartbot.ui.enhanced_main_window import EnhancedMainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("forexsmartbot.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def _icon_path() -> str:
    """Resolve app icon from install/repo layouts without assuming CWD."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "assets", "icons", "forexsmartbot_256.png"),
        os.path.join(os.getcwd(), "assets", "icons", "forexsmartbot_256.png"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def main():
    """Main entry point for ForexSmartBot."""
    try:
        load_dotenv()
        logger.info("Starting ForexSmartBot application...")

        app = QApplication(sys.argv)
        app.setApplicationName("ForexSmartBot")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("VoxHash")

        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        except AttributeError:
            pass

        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass

        icon_path = _icon_path()
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        window = EnhancedMainWindow()
        window.show()

        logger.info("Application started successfully")
        sys.exit(app.exec())

    except Exception as e:
        logger.error("Failed to start application: %s", e)

        try:
            if "app" in locals():
                QMessageBox.critical(
                    None,
                    "Application Error",
                    f"Failed to start ForexSmartBot:\n\n{str(e)}",
                )
        except Exception as display_error:
            print(f"Critical error: {e}")
            print(f"Failed to display error dialog: {display_error}")

        sys.exit(1)


if __name__ == "__main__":
    main()
