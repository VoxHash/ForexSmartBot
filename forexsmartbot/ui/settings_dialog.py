"""Settings dialog for ForexSmartBot."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QComboBox, QCheckBox, QPushButton, QGroupBox,
                             QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
from typing import Dict, Any


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs."""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General tab
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "General")
        
        # Broker tab
        broker_tab = self.create_broker_tab()
        tab_widget.addTab(broker_tab, "Broker")
        
        # Risk tab
        risk_tab = self.create_risk_tab()
        tab_widget.addTab(risk_tab, "Risk")
        
        # UI tab
        ui_tab = self.create_ui_tab()
        tab_widget.addTab(ui_tab, "UI")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Strategy selection
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['SMA_Crossover', 'BreakoutATR', 'RSI_Reversion'])
        layout.addRow("Default Strategy:", self.strategy_combo)
        
        # Data provider
        self.data_provider_combo = QComboBox()
        self.data_provider_combo.addItems(['yfinance', 'csv'])
        layout.addRow("Data Provider:", self.data_provider_combo)
        
        # Data interval
        self.data_interval_combo = QComboBox()
        self.data_interval_combo.addItems(['1m', '5m', '15m', '1h', '4h', '1d'])
        layout.addRow("Data Interval:", self.data_interval_combo)
        
        # Portfolio mode
        self.portfolio_mode_checkbox = QCheckBox("Enable Portfolio Mode")
        layout.addRow("Portfolio Mode:", self.portfolio_mode_checkbox)
        
        # Confirm live trades
        self.confirm_live_trades_checkbox = QCheckBox("Require confirmation for live trades")
        layout.addRow("Live Trade Confirmation:", self.confirm_live_trades_checkbox)
        
        return widget
        
    def create_broker_tab(self) -> QWidget:
        """Create broker settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Broker mode
        self.broker_mode_combo = QComboBox()
        self.broker_mode_combo.addItems(['PAPER', 'MT4', 'REST'])
        layout.addRow("Broker Mode:", self.broker_mode_combo)
        
        # MT4 settings group
        mt4_group = QGroupBox("MT4 Settings")
        mt4_layout = QFormLayout(mt4_group)
        
        self.mt4_host_edit = QLineEdit()
        self.mt4_host_edit.setPlaceholderText("127.0.0.1")
        mt4_layout.addRow("Host:", self.mt4_host_edit)
        
        self.mt4_port_spin = QSpinBox()
        self.mt4_port_spin.setRange(1, 65535)
        self.mt4_port_spin.setValue(5555)
        mt4_layout.addRow("Port:", self.mt4_port_spin)
        
        layout.addWidget(mt4_group)
        
        # REST API settings group
        rest_group = QGroupBox("REST API Settings")
        rest_layout = QFormLayout(rest_group)
        
        self.rest_api_key_edit = QLineEdit()
        self.rest_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        rest_layout.addRow("API Key:", self.rest_api_key_edit)
        
        self.rest_api_secret_edit = QLineEdit()
        self.rest_api_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        rest_layout.addRow("API Secret:", self.rest_api_secret_edit)
        
        self.rest_base_url_edit = QLineEdit()
        self.rest_base_url_edit.setPlaceholderText("https://api.example.com")
        rest_layout.addRow("Base URL:", self.rest_base_url_edit)
        
        layout.addWidget(rest_group)
        
        return widget
        
    def create_risk_tab(self) -> QWidget:
        """Create risk management settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Base risk percentage
        self.risk_pct_spin = QDoubleSpinBox()
        self.risk_pct_spin.setRange(0.001, 0.1)
        self.risk_pct_spin.setDecimals(3)
        self.risk_pct_spin.setSingleStep(0.005)
        self.risk_pct_spin.setValue(0.02)
        layout.addRow("Base Risk %:", self.risk_pct_spin)
        
        # Max risk percentage
        self.max_risk_pct_spin = QDoubleSpinBox()
        self.max_risk_pct_spin.setRange(0.001, 0.2)
        self.max_risk_pct_spin.setDecimals(3)
        self.max_risk_pct_spin.setSingleStep(0.005)
        self.max_risk_pct_spin.setValue(0.05)
        layout.addRow("Max Risk %:", self.max_risk_pct_spin)
        
        # Daily risk cap
        self.daily_risk_cap_spin = QDoubleSpinBox()
        self.daily_risk_cap_spin.setRange(0.001, 0.2)
        self.daily_risk_cap_spin.setDecimals(3)
        self.daily_risk_cap_spin.setSingleStep(0.005)
        self.daily_risk_cap_spin.setValue(0.05)
        layout.addRow("Daily Risk Cap %:", self.daily_risk_cap_spin)
        
        # Max drawdown
        self.max_drawdown_spin = QDoubleSpinBox()
        self.max_drawdown_spin.setRange(0.01, 0.5)
        self.max_drawdown_spin.setDecimals(3)
        self.max_drawdown_spin.setSingleStep(0.01)
        self.max_drawdown_spin.setValue(0.25)
        layout.addRow("Max Drawdown %:", self.max_drawdown_spin)
        
        # Trade amount limits
        self.min_trade_amount_spin = QDoubleSpinBox()
        self.min_trade_amount_spin.setRange(1, 1000)
        self.min_trade_amount_spin.setDecimals(2)
        self.min_trade_amount_spin.setValue(10)
        layout.addRow("Min Trade Amount:", self.min_trade_amount_spin)
        
        self.max_trade_amount_spin = QDoubleSpinBox()
        self.max_trade_amount_spin.setRange(10, 10000)
        self.max_trade_amount_spin.setDecimals(2)
        self.max_trade_amount_spin.setValue(100)
        layout.addRow("Max Trade Amount:", self.max_trade_amount_spin)
        
        return widget
        
    def create_ui_tab(self) -> QWidget:
        """Create UI settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['auto', 'light', 'dark'])
        layout.addRow("Theme:", self.theme_combo)
        
        # Default symbols
        self.default_symbols_edit = QLineEdit()
        self.default_symbols_edit.setPlaceholderText("EURUSD,USDJPY,GBPUSD")
        layout.addRow("Default Symbols:", self.default_symbols_edit)
        
        # Selected symbols
        self.selected_symbols_edit = QLineEdit()
        self.selected_symbols_edit.setPlaceholderText("EURUSD")
        layout.addRow("Selected Symbols:", self.selected_symbols_edit)
        
        return widget
        
    def load_settings(self):
        """Load settings from settings manager."""
        if not self.settings_manager:
            return
            
        # General settings
        self.strategy_combo.setCurrentText(self.settings_manager.get('strategy', 'SMA_Crossover'))
        self.data_provider_combo.setCurrentText(self.settings_manager.get('data_provider', 'yfinance'))
        self.data_interval_combo.setCurrentText(self.settings_manager.get('data_interval', '1h'))
        self.portfolio_mode_checkbox.setChecked(self.settings_manager.get('portfolio_mode', False))
        self.confirm_live_trades_checkbox.setChecked(self.settings_manager.get('confirm_live_trades', True))
        
        # Broker settings
        self.broker_mode_combo.setCurrentText(self.settings_manager.get('broker_mode', 'PAPER'))
        self.mt4_host_edit.setText(self.settings_manager.get('mt4_host', '127.0.0.1'))
        self.mt4_port_spin.setValue(self.settings_manager.get('mt4_port', 5555))
        
        # Risk settings
        self.risk_pct_spin.setValue(self.settings_manager.get('risk_pct', 0.02))
        self.max_risk_pct_spin.setValue(self.settings_manager.get('max_risk_pct', 0.05))
        self.daily_risk_cap_spin.setValue(self.settings_manager.get('daily_risk_cap', 0.05))
        self.max_drawdown_spin.setValue(self.settings_manager.get('max_drawdown_pct', 0.25))
        self.min_trade_amount_spin.setValue(self.settings_manager.get('trade_amount_min', 10.0))
        self.max_trade_amount_spin.setValue(self.settings_manager.get('trade_amount_max', 100.0))
        
        # UI settings
        self.theme_combo.setCurrentText(self.settings_manager.get('theme', 'auto'))
        self.default_symbols_edit.setText(','.join(self.settings_manager.get('default_symbols', ['EURUSD', 'USDJPY', 'GBPUSD'])))
        self.selected_symbols_edit.setText(','.join(self.settings_manager.get('selected_symbols', ['EURUSD'])))
        
    def save_settings(self):
        """Save settings to settings manager."""
        if not self.settings_manager:
            return
            
        try:
            # General settings
            self.settings_manager.set('strategy', self.strategy_combo.currentText())
            self.settings_manager.set('data_provider', self.data_provider_combo.currentText())
            self.settings_manager.set('data_interval', self.data_interval_combo.currentText())
            self.settings_manager.set('portfolio_mode', self.portfolio_mode_checkbox.isChecked())
            self.settings_manager.set('confirm_live_trades', self.confirm_live_trades_checkbox.isChecked())
            
            # Broker settings
            self.settings_manager.set('broker_mode', self.broker_mode_combo.currentText())
            self.settings_manager.set('mt4_host', self.mt4_host_edit.text())
            self.settings_manager.set('mt4_port', self.mt4_port_spin.value())
            
            # Risk settings
            self.settings_manager.set('risk_pct', self.risk_pct_spin.value())
            self.settings_manager.set('max_risk_pct', self.max_risk_pct_spin.value())
            self.settings_manager.set('daily_risk_cap', self.daily_risk_cap_spin.value())
            self.settings_manager.set('max_drawdown_pct', self.max_drawdown_spin.value())
            self.settings_manager.set('trade_amount_min', self.min_trade_amount_spin.value())
            self.settings_manager.set('trade_amount_max', self.max_trade_amount_spin.value())
            
            # UI settings
            self.settings_manager.set('theme', self.theme_combo.currentText())
            self.settings_manager.set('default_symbols', [s.strip() for s in self.default_symbols_edit.text().split(',') if s.strip()])
            self.settings_manager.set('selected_symbols', [s.strip() for s in self.selected_symbols_edit.text().split(',') if s.strip()])
            
            # Save to file
            if self.settings_manager.save():
                QMessageBox.information(self, "Settings", "Settings saved successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Settings", "Failed to save settings!")
                
        except Exception as e:
            QMessageBox.critical(self, "Settings", f"Error saving settings: {str(e)}")
            
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.load_settings()
