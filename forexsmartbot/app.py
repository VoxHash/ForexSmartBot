"""Application entry point (console script: forexsmartbot)."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from forexsmartbot.assets import resolve_app_icon
from forexsmartbot.desktop_identity import APP_NAME, configure_qt_identity
from forexsmartbot.ui.enhanced_main_window import EnhancedMainWindow

_LOG_DIR = Path.home() / ".forexsmartbot"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "forexsmartbot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(_LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for ForexSmartBot."""
    try:
        load_dotenv()
        logger.info("Starting ForexSmartBot application...")

        # Before QApplication: unique Wayland app_id / WM_CLASS (not python3).
        configure_qt_identity()

        app = QApplication(sys.argv)

        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        except AttributeError:
            pass

        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass

        icon_path = resolve_app_icon()
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
                    f"Failed to start {APP_NAME}:\n\n{str(e)}",
                )
        except Exception as display_error:
            print(f"Critical error: {e}")
            print(f"Failed to display error dialog: {display_error}")

        sys.exit(1)


if __name__ == "__main__":
    main()
