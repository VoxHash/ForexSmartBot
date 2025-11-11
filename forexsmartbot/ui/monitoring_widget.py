"""
Monitoring Widget for main window integration.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from typing import Optional


class StrategyMonitorWidget(QWidget):
    """Widget displaying strategy monitoring in the main window."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        title = QLabel("Strategy Monitor")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Status table
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(3)
        self.status_table.setHorizontalHeaderLabels(["Strategy", "Status", "Performance"])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        self.status_table.setRowCount(0)
        layout.addWidget(self.status_table)
    
    def setup_timer(self):
        """Setup update timer."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def update_status(self):
        """Update strategy status."""
        try:
            from ..monitoring.strategy_monitor import StrategyMonitor
            
            # Try to get shared monitor from parent window, otherwise create new
            monitor = None
            if self.parent():
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'strategy_monitor'):
                        monitor = parent.strategy_monitor
                        break
                    parent = parent.parent()
            
            if not monitor:
                monitor = StrategyMonitor()
            
            statuses = monitor.get_strategy_statuses()
            
            if not statuses:
                # No strategies registered yet
                self.status_table.setRowCount(1)
                self.status_table.setItem(0, 0, QTableWidgetItem("No strategies"))
                self.status_table.setItem(0, 1, QTableWidgetItem("Not monitored"))
                self.status_table.setItem(0, 2, QTableWidgetItem("N/A"))
                return
            
            self.status_table.setRowCount(len(statuses))
            
            for i, (strategy, status) in enumerate(statuses.items()):
                self.status_table.setItem(i, 0, QTableWidgetItem(strategy))
                self.status_table.setItem(i, 1, QTableWidgetItem(status.get('status', 'Unknown')))
                performance = status.get('performance', 0)
                self.status_table.setItem(i, 2, QTableWidgetItem(f"{performance:.2f}"))
        except Exception as e:
            self.status_table.setRowCount(1)
            self.status_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.status_table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.status_table.setItem(0, 2, QTableWidgetItem(""))

