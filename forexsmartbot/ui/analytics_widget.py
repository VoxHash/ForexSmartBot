"""
Analytics Widget for main window integration.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from typing import Optional


class PortfolioAnalyticsWidget(QWidget):
    """Widget displaying portfolio analytics in the main window."""
    
    def __init__(self, portfolio, parent=None):
        super().__init__(parent)
        self.portfolio = portfolio
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        title = QLabel("Portfolio Analytics")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setRowCount(0)
        layout.addWidget(self.metrics_table)
        
        self.update_metrics()
    
    def update_metrics(self):
        """Update portfolio metrics."""
        try:
            from ..analytics.portfolio_analytics import PortfolioAnalytics
            
            analytics = PortfolioAnalytics()
            metrics = analytics.calculate_metrics(self.portfolio)
            
            if not metrics:
                # No metrics available
                self.metrics_table.setRowCount(1)
                self.metrics_table.setItem(0, 0, QTableWidgetItem("No data"))
                self.metrics_table.setItem(0, 1, QTableWidgetItem("No trades available"))
                return
            
            self.metrics_table.setRowCount(len(metrics))
            
            for i, (key, value) in enumerate(metrics.items()):
                self.metrics_table.setItem(i, 0, QTableWidgetItem(str(key).replace('_', ' ').title()))
                if isinstance(value, float):
                    if abs(value) > 1000:
                        self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.2f}"))
                    elif abs(value) > 1:
                        self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
                    else:
                        self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.6f}"))
                else:
                    self.metrics_table.setItem(i, 1, QTableWidgetItem(str(value)))
        except Exception as e:
            self.metrics_table.setRowCount(1)
            self.metrics_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.metrics_table.setItem(0, 1, QTableWidgetItem(str(e)))

