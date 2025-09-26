"""Theme management with persistence."""

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
import darkdetect
from typing import Optional


class ThemeManager:
    """Manages application theming with persistence."""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.current_theme = "auto"
        
    def apply_theme(self, app: QApplication, force: Optional[str] = None) -> str:
        """Apply theme to application."""
        if force is not None:
            theme = force
        elif self.settings_manager:
            theme = self.settings_manager.get('theme', 'auto')
        else:
            theme = 'auto'
            
        self.current_theme = theme
        
        # Determine actual theme
        if theme == 'auto':
            actual_theme = 'dark' if darkdetect.isDark() else 'light'
        else:
            actual_theme = theme
            
        # Apply theme
        pal = QPalette()
        
        if actual_theme == 'dark':
            self._apply_dark_theme(pal)
        elif actual_theme == 'dracula':
            self._apply_dracula_theme(pal)
        else:
            self._apply_light_theme(pal)
            
        app.setPalette(pal)
        return actual_theme
        
    def _apply_dark_theme(self, pal: QPalette) -> None:
        """Apply dark theme colors."""
        pal.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        pal.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 220, 220))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
        pal.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        pal.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        pal.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        
    def _apply_light_theme(self, pal: QPalette) -> None:
        """Apply light theme colors."""
        pal.setColor(QPalette.ColorRole.Window, QColor(250, 250, 250))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(20, 20, 20))
        pal.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.Text, QColor(20, 20, 20))
        pal.setColor(QPalette.ColorRole.Button, QColor(245, 245, 245))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(20, 20, 20))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(30, 144, 255))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
    def _apply_dracula_theme(self, pal: QPalette) -> None:
        """Apply Dracula theme colors."""
        # Dracula color scheme
        background = QColor(40, 42, 54)      # Dracula background
        foreground = QColor(248, 248, 242)   # Dracula foreground
        selection = QColor(68, 71, 90)       # Dracula selection
        comment = QColor(98, 114, 164)       # Dracula comment
        cyan = QColor(139, 233, 253)         # Dracula cyan
        green = QColor(80, 250, 123)         # Dracula green
        orange = QColor(255, 184, 108)       # Dracula orange
        pink = QColor(255, 121, 198)         # Dracula pink
        purple = QColor(189, 147, 249)       # Dracula purple
        red = QColor(255, 85, 85)            # Dracula red
        yellow = QColor(241, 250, 140)       # Dracula yellow
        
        pal.setColor(QPalette.ColorRole.Window, background)
        pal.setColor(QPalette.ColorRole.WindowText, foreground)
        pal.setColor(QPalette.ColorRole.Base, QColor(30, 32, 44))
        pal.setColor(QPalette.ColorRole.AlternateBase, selection)
        pal.setColor(QPalette.ColorRole.ToolTipBase, background)
        pal.setColor(QPalette.ColorRole.ToolTipText, foreground)
        pal.setColor(QPalette.ColorRole.Text, foreground)
        pal.setColor(QPalette.ColorRole.Button, background)
        pal.setColor(QPalette.ColorRole.ButtonText, foreground)
        pal.setColor(QPalette.ColorRole.BrightText, red)
        pal.setColor(QPalette.ColorRole.Link, cyan)
        pal.setColor(QPalette.ColorRole.LinkVisited, purple)
        
    def set_theme(self, theme: str) -> None:
        """Set theme and save to settings."""
        self.current_theme = theme
        if self.settings_manager:
            self.settings_manager.set('theme', theme)
            self.settings_manager.save()
            
    def get_available_themes(self) -> list:
        """Get list of available themes."""
        return ['auto', 'light', 'dark', 'dracula']
