"""
Cloud Dialog
Provides UI for cloud integration features.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QLineEdit, QFormLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional
import os
from dotenv import load_dotenv, set_key, find_dotenv


class CloudDialog(QDialog):
    """Dialog for cloud features."""
    
    def __init__(self, cloud_type: str, parent=None, language_manager=None):
        super().__init__(parent)
        self.cloud_type = cloud_type
        self.language_manager = language_manager
        self.setWindowTitle(f"Cloud: {cloud_type.replace('_', ' ').title()}")
        self.setModal(False)  # Allow multiple windows
        self.resize(700, 500)
        load_dotenv(override=False)
        self.setup_ui()
        self.load_settings()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        if self.cloud_type == 'sync':
            self.setup_cloud_sync(layout)
        elif self.cloud_type == 'remote_monitor':
            self.setup_remote_monitor(layout)
        elif self.cloud_type == 'api':
            self.setup_api_access(layout)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def setup_cloud_sync(self, layout):
        """Setup cloud sync UI."""
        title = QLabel("Cloud Sync")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #2196F3;")
        layout.addWidget(title)
        
        info_label = QLabel("Synchronize settings and data across devices")
        info_label.setStyleSheet("color: #888; padding-bottom: 10px;")
        layout.addWidget(info_label)
        
        config_group = QGroupBox("Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(10)
        
        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setPlaceholderText("https://api.forexsmartbot.cloud")
        self.api_endpoint_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #2b2b2b;
                color: white;
            }
        """)
        config_layout.addRow("API Endpoint:", self.api_endpoint_edit)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key")
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #2b2b2b;
                color: white;
            }
        """)
        config_layout.addRow("API Key:", self.api_key_edit)
        
        layout.addWidget(config_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Configuration")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_cloud_sync_config)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def setup_remote_monitor(self, layout):
        """Setup remote monitor UI."""
        title = QLabel("Remote Monitor")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #2196F3;")
        layout.addWidget(title)
        
        info_label = QLabel("Access your trading dashboard from any device")
        info_label.setStyleSheet("color: #888; padding-bottom: 10px;")
        layout.addWidget(info_label)
        
        monitor_host = os.getenv('REMOTE_MONITOR_HOST', '127.0.0.1')
        monitor_port = os.getenv('REMOTE_MONITOR_PORT', '8080')
        dashboard_url = f"http://{monitor_host}:{monitor_port}"
        
        url_group = QGroupBox("Dashboard Access")
        url_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        url_layout = QVBoxLayout(url_group)
        
        url_label = QLabel(f"<a href='{dashboard_url}' style='color: #2196F3; font-size: 14px;'>{dashboard_url}</a>")
        url_label.setOpenExternalLinks(True)
        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        url_layout.addWidget(url_label)
        
        status_label = QLabel("Status: Not Running")
        status_label.setStyleSheet("color: #888; padding-top: 10px;")
        self.monitor_status_label = status_label
        url_layout.addWidget(status_label)
        
        layout.addWidget(url_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        start_btn = QPushButton("Start Server")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        start_btn.clicked.connect(self.start_remote_monitor)
        button_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("Stop Server")
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        stop_btn.clicked.connect(self.stop_remote_monitor)
        button_layout.addWidget(stop_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def setup_api_access(self, layout):
        """Setup API access UI."""
        title = QLabel("API Access")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #2196F3;")
        layout.addWidget(title)
        
        info_label = QLabel("REST API and WebSocket endpoints for external integrations")
        info_label.setStyleSheet("color: #888; padding-bottom: 10px;")
        layout.addWidget(info_label)
        
        api_host = os.getenv('API_HOST', '127.0.0.1')
        api_port = os.getenv('API_PORT', '5000')
        ws_host = os.getenv('WS_HOST', '127.0.0.1')
        ws_port = os.getenv('WS_PORT', '8765')
        
        rest_url = f"http://{api_host}:{api_port}"
        ws_url = f"ws://{ws_host}:{ws_port}"
        
        api_group = QGroupBox("API Endpoints")
        api_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        api_layout = QVBoxLayout(api_group)
        
        rest_label = QLabel(f"<b>REST API:</b> <a href='{rest_url}' style='color: #2196F3;'>{rest_url}</a>")
        rest_label.setOpenExternalLinks(True)
        rest_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        api_layout.addWidget(rest_label)
        
        ws_label = QLabel(f"<b>WebSocket:</b> <span style='color: #2196F3;'>{ws_url}</span>")
        api_layout.addWidget(ws_label)
        
        status_label = QLabel("Status: Not Running")
        status_label.setStyleSheet("color: #888; padding-top: 10px;")
        self.api_status_label = status_label
        api_layout.addWidget(status_label)
        
        layout.addWidget(api_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        start_btn = QPushButton("Start API Server")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        start_btn.clicked.connect(self.start_api_server)
        button_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("Stop API Server")
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        stop_btn.clicked.connect(self.stop_api_server)
        button_layout.addWidget(stop_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load existing settings from environment."""
        if self.cloud_type == 'sync':
            self.api_endpoint_edit.setText(os.getenv('CLOUD_API_ENDPOINT', 'https://api.forexsmartbot.cloud'))
            self.api_key_edit.setText(os.getenv('CLOUD_API_KEY', ''))
    
    def save_cloud_sync_config(self):
        """Save cloud sync configuration to .env file."""
        try:
            endpoint = self.api_endpoint_edit.text().strip()
            api_key = self.api_key_edit.text().strip()
            
            if not endpoint:
                QMessageBox.warning(self, "Validation", "API Endpoint is required")
                return
            
            # Find .env file
            env_file = find_dotenv()
            if not env_file:
                env_file = '.env'
            
            # Update .env file
            set_key(env_file, 'CLOUD_API_ENDPOINT', endpoint)
            if api_key:
                set_key(env_file, 'CLOUD_API_KEY', api_key)
            
            QMessageBox.information(self, "Success", "Cloud sync configuration saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def start_remote_monitor(self):
        """Start remote monitor server."""
        try:
            from ..cloud.remote_monitor import RemoteMonitorServer
            # Note: Server would need to be started in a separate thread/process
            self.monitor_status_label.setText("Status: Starting...")
            self.monitor_status_label.setStyleSheet("color: orange;")
            QMessageBox.information(self, "Info", "Remote monitor server starting.\nCheck the console for status.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start remote monitor: {e}")
    
    def stop_remote_monitor(self):
        """Stop remote monitor server."""
        self.monitor_status_label.setText("Status: Stopped")
        self.monitor_status_label.setStyleSheet("color: #888;")
        QMessageBox.information(self, "Info", "Remote monitor server stopped.")
    
    def start_api_server(self):
        """Start API server."""
        try:
            from ..cloud.api_server import APIServer
            # Note: Server would need to be started in a separate thread/process
            self.api_status_label.setText("Status: Starting...")
            self.api_status_label.setStyleSheet("color: orange;")
            QMessageBox.information(self, "Info", "API server starting.\nCheck the console for status.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start API server: {e}")
    
    def stop_api_server(self):
        """Stop API server."""
        self.api_status_label.setText("Status: Stopped")
        self.api_status_label.setStyleSheet("color: #888;")
        QMessageBox.information(self, "Info", "API server stopped.")

