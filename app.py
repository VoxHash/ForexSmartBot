import os
import sys
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication
from forexsmartbot.ui.main_window import MainWindow

def main():
    """Main entry point for ForexSmartBot."""
    load_dotenv()
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("ForexSmartBot")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("VoxHash")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
