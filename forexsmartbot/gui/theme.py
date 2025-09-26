from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
import darkdetect

def apply_theme(app: QApplication, force: str | None = None):
    mode = force or ('dark' if darkdetect.isDark() else 'light')
    pal = QPalette()
    if mode == 'dark':
        pal.setColor(QPalette.ColorRole.Window, QColor(30,30,30))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(220,220,220))
        pal.setColor(QPalette.ColorRole.Base, QColor(25,25,25))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(53,53,53))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(220,220,220))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(220,220,220))
        pal.setColor(QPalette.ColorRole.Text, QColor(220,220,220))
        pal.setColor(QPalette.ColorRole.Button, QColor(53,53,53))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(220,220,220))
        pal.setColor(QPalette.ColorRole.BrightText, QColor(255,0,0))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(42,130,218))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(0,0,0))
    else:
        # default palette is fine for light, but we define a gentle scheme
        pal.setColor(QPalette.ColorRole.Window, QColor(250,250,250))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(20,20,20))
        pal.setColor(QPalette.ColorRole.Base, QColor(255,255,255))
        pal.setColor(QPalette.ColorRole.Text, QColor(20,20,20))
        pal.setColor(QPalette.ColorRole.Button, QColor(245,245,245))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(20,20,20))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(30,144,255))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255,255,255))
    app.setPalette(pal)
    return mode
