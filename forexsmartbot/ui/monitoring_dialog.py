"""
Monitoring Dialog
Provides UI for monitoring tools.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QGroupBox
)
from PyQt6.QtCore import QTimer
from typing import Optional


class MonitoringDialog(QDialog):
    """Dialog for monitoring tools."""
    
    def __init__(self, monitor_type: str, parent=None, language_manager=None, **kwargs):
        super().__init__(parent)
        self.monitor_type = monitor_type
        self.language_manager = language_manager
        self.kwargs = kwargs
        self.setWindowTitle(f"Monitoring: {monitor_type.replace('_', ' ').title()}")
        self.setModal(False)  # Allow multiple windows
        self.resize(900, 700)
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        if self.monitor_type == 'strategy':
            self.setup_strategy_monitor(layout)
        elif self.monitor_type == 'performance':
            self.setup_performance_tracker(layout)
        elif self.monitor_type == 'health':
            self.setup_health_check(layout)
        else:
            layout.addWidget(QLabel(f"Monitoring: {self.monitor_type}"))
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def setup_strategy_monitor(self, layout):
        """Setup strategy monitor UI."""
        from ..monitoring.strategy_monitor import StrategyMonitor
        
        title = QLabel("Strategy Monitor")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        self.monitor = StrategyMonitor()
        
        # Status table
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels(["Strategy", "Status", "Signals", "Errors"])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.status_table)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_strategy_status)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial update
        self.update_strategy_status()
    
    def update_strategy_status(self):
        """Update strategy status table."""
        try:
            statuses = self.monitor.get_strategy_statuses()
            
            if not statuses:
                self.status_table.setRowCount(1)
                self.status_table.setItem(0, 0, QTableWidgetItem("No strategies"))
                self.status_table.setItem(0, 1, QTableWidgetItem("Not monitored"))
                self.status_table.setItem(0, 2, QTableWidgetItem("N/A"))
                self.status_table.setItem(0, 3, QTableWidgetItem("N/A"))
                return
            
            self.status_table.setRowCount(len(statuses))
            
            for i, (strategy, status) in enumerate(statuses.items()):
                self.status_table.setItem(i, 0, QTableWidgetItem(strategy))
                self.status_table.setItem(i, 1, QTableWidgetItem(status.get('status', 'Unknown')))
                self.status_table.setItem(i, 2, QTableWidgetItem(str(status.get('signal_count', 0))))
                self.status_table.setItem(i, 3, QTableWidgetItem(str(status.get('error_count', 0))))
        except Exception as e:
            self.status_table.setRowCount(1)
            self.status_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.status_table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.status_table.setItem(0, 2, QTableWidgetItem(""))
            self.status_table.setItem(0, 3, QTableWidgetItem(""))
    
    def setup_performance_tracker(self, layout):
        """Setup performance tracker UI."""
        from ..monitoring.performance_tracker import PerformanceTracker
        
        title = QLabel("Performance Tracker")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        self.tracker = PerformanceTracker()
        
        # Metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.metrics_table)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_performance_metrics)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial update
        self.update_performance_metrics()
    
    def update_performance_metrics(self):
        """Update performance metrics table."""
        try:
            # Get summary from tracker
            summary = self.tracker.get_summary()
            
            if not summary:
                self.metrics_table.setRowCount(1)
                self.metrics_table.setItem(0, 0, QTableWidgetItem("No data"))
                self.metrics_table.setItem(0, 1, QTableWidgetItem("No trades recorded"))
                return
            
            self.metrics_table.setRowCount(len(summary))
            
            for i, (key, value) in enumerate(summary.items()):
                self.metrics_table.setItem(i, 0, QTableWidgetItem(str(key).replace('_', ' ').title()))
                if isinstance(value, float):
                    self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{value:.4f}"))
                else:
                    self.metrics_table.setItem(i, 1, QTableWidgetItem(str(value)))
        except Exception as e:
            self.metrics_table.setRowCount(1)
            self.metrics_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.metrics_table.setItem(0, 1, QTableWidgetItem(str(e)))
    
    def setup_health_check(self, layout):
        """Setup health check UI."""
        from ..monitoring.health_check import HealthChecker
        from ..monitoring.strategy_monitor import StrategyMonitor
        
        title = QLabel("Health Check")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Create monitor and checker
        monitor = StrategyMonitor()
        self.checker = HealthChecker(monitor)
        
        # Results table
        self.health_table = QTableWidget()
        self.health_table.setColumnCount(3)
        self.health_table.setHorizontalHeaderLabels(["Strategy", "Status", "Details"])
        self.health_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.health_table)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_health_status)
        self.update_timer.start(10000)  # Update every 10 seconds
        
        # Initial update
        self.update_health_status()
    
    def update_health_status(self):
        """Update health check results."""
        try:
            results = self.checker.check_all()
            
            if not results:
                self.health_table.setRowCount(1)
                self.health_table.setItem(0, 0, QTableWidgetItem("No strategies"))
                self.health_table.setItem(0, 1, QTableWidgetItem("Not monitored"))
                self.health_table.setItem(0, 2, QTableWidgetItem("Register strategies to monitor"))
                return
            
            self.health_table.setRowCount(len(results))
            
            for i, (strategy, health_data) in enumerate(results.items()):
                self.health_table.setItem(i, 0, QTableWidgetItem(strategy))
                self.health_table.setItem(i, 1, QTableWidgetItem(health_data.get('status', 'unknown')))
                
                # Format checks as details
                checks = health_data.get('checks', [])
                if checks:
                    details = "; ".join([f"{c.get('name', '')}: {c.get('status', '')}" for c in checks[:3]])
                else:
                    details = health_data.get('message', 'No checks performed')
                
                self.health_table.setItem(i, 2, QTableWidgetItem(details))
        except Exception as e:
            self.health_table.setRowCount(1)
            self.health_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.health_table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.health_table.setItem(0, 2, QTableWidgetItem(""))

