import os
import sys
import logging
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from forexsmartbot.ui.enhanced_main_window import EnhancedMainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('forexsmartbot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for ForexSmartBot."""
    try:
        load_dotenv()
        logger.info("Starting ForexSmartBot application...")
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("ForexSmartBot")
        app.setApplicationVersion("3.0.0")
        app.setOrganizationName("VoxHash")
        
        # Set application properties (PyQt6 compatibility)
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        except AttributeError:
            pass  # Not available in this PyQt6 version
            
        try:
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            pass  # Not available in this PyQt6 version
        
        # Set application icon if available
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'forexsmartbot_256.png')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Create and show main window
        window = EnhancedMainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        
        # Show error message if QApplication is available
        try:
            if 'app' in locals():
                QMessageBox.critical(None, "Application Error", 
                                   f"Failed to start ForexSmartBot:\n\n{str(e)}")
        except:
            print(f"Critical error: {e}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
