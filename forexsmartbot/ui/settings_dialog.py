"""Settings dialog for ForexSmartBot."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QComboBox, QCheckBox, QPushButton, QGroupBox,
                             QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
from typing import Dict, Any


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs."""
    
    def __init__(self, settings_manager, language_manager=None, parent=None, on_settings_saved=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.language_manager = language_manager
        self.on_settings_saved = on_settings_saved  # Callback function
        self.setWindowTitle(self.tr("settings", "Settings"))
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_settings()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General tab
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, self.tr("general", "General"))
        
        # Broker tab
        broker_tab = self.create_broker_tab()
        tab_widget.addTab(broker_tab, self.tr("broker", "Broker"))
        
        # Risk tab
        risk_tab = self.create_risk_tab()
        tab_widget.addTab(risk_tab, self.tr("risk", "Risk"))
        
        # Data Providers tab
        data_providers_tab = self.create_data_providers_tab()
        tab_widget.addTab(data_providers_tab, self.tr("data_providers", "Data Providers"))
        
        # UI tab
        ui_tab = self.create_ui_tab()
        tab_widget.addTab(ui_tab, self.tr("ui", "UI"))
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton(self.tr("save", "Save"))
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton(self.tr("cancel", "Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton(self.tr("reset_to_defaults", "Reset to Defaults"))
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
        
        # Portfolio mode
        self.portfolio_mode_checkbox = QCheckBox(self.tr('enable_portfolio_mode', 'Enable Portfolio Mode'))
        layout.addRow(f"{self.tr('portfolio_mode', 'Portfolio Mode')}:", self.portfolio_mode_checkbox)
        
        # Confirm live trades
        self.confirm_live_trades_checkbox = QCheckBox(self.tr('require_confirmation_live_trades', 'Require confirmation for live trades'))
        layout.addRow(f"{self.tr('live_trade_confirmation', 'Live Trade Confirmation')}:", self.confirm_live_trades_checkbox)
        
        return widget
        
    def create_broker_tab(self) -> QWidget:
        """Create broker settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Broker mode
        self.broker_mode_combo = QComboBox()
        self.broker_mode_combo.addItems(['PAPER', 'MT4', 'REST API'])
        layout.addRow(f"{self.tr('broker_mode', 'Broker Mode')}:", self.broker_mode_combo)
        
        # MT4 settings group
        mt4_group = QGroupBox(self.tr('mt4_settings', 'MT4 Settings'))
        mt4_layout = QFormLayout(mt4_group)
        
        self.mt4_host_edit = QLineEdit()
        self.mt4_host_edit.setPlaceholderText("127.0.0.1")
        mt4_layout.addRow(f"{self.tr('host', 'Host')}:", self.mt4_host_edit)
        
        self.mt4_port_spin = QSpinBox()
        self.mt4_port_spin.setRange(1, 65535)
        self.mt4_port_spin.setValue(5555)
        mt4_layout.addRow(f"{self.tr('port', 'Port')}:", self.mt4_port_spin)
        
        layout.addWidget(mt4_group)
        
        # REST API settings group
        rest_group = QGroupBox(self.tr('rest_api_settings', 'REST API Settings'))
        rest_layout = QFormLayout(rest_group)
        
        self.rest_api_key_edit = QLineEdit()
        self.rest_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        rest_layout.addRow(f"{self.tr('api_key', 'API Key')}:", self.rest_api_key_edit)
        
        self.rest_api_secret_edit = QLineEdit()
        self.rest_api_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        rest_layout.addRow(f"{self.tr('api_secret', 'API Secret')}:", self.rest_api_secret_edit)
        
        self.rest_base_url_edit = QLineEdit()
        self.rest_base_url_edit.setPlaceholderText("https://api.example.com")
        rest_layout.addRow(f"{self.tr('base_url', 'Base URL')}:", self.rest_base_url_edit)
        
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
        layout.addRow(f"{self.tr('base_risk', 'Base Risk')} %:", self.risk_pct_spin)
        
        # Max risk percentage
        self.max_risk_pct_spin = QDoubleSpinBox()
        self.max_risk_pct_spin.setRange(0.001, 0.2)
        self.max_risk_pct_spin.setDecimals(3)
        self.max_risk_pct_spin.setSingleStep(0.005)
        self.max_risk_pct_spin.setValue(0.05)
        layout.addRow(f"{self.tr('max_risk', 'Max Risk')} %:", self.max_risk_pct_spin)
        
        # Daily risk cap
        self.daily_risk_cap_spin = QDoubleSpinBox()
        self.daily_risk_cap_spin.setRange(0.001, 0.2)
        self.daily_risk_cap_spin.setDecimals(3)
        self.daily_risk_cap_spin.setSingleStep(0.005)
        self.daily_risk_cap_spin.setValue(0.05)
        layout.addRow(f"{self.tr('daily_risk_cap', 'Daily Risk Cap')} %:", self.daily_risk_cap_spin)
        
        # Broker spread configuration
        self.broker_spread_spin = QDoubleSpinBox()
        self.broker_spread_spin.setRange(0.0, 50.0)
        self.broker_spread_spin.setDecimals(1)
        self.broker_spread_spin.setSingleStep(0.1)
        self.broker_spread_spin.setValue(2.0)
        self.broker_spread_spin.setSuffix(" pips")
        layout.addRow(f"{self.tr('broker_spread', 'Broker Spread')}:", self.broker_spread_spin)
        
        # Max drawdown
        self.max_drawdown_spin = QDoubleSpinBox()
        self.max_drawdown_spin.setRange(0.01, 0.5)
        self.max_drawdown_spin.setDecimals(3)
        self.max_drawdown_spin.setSingleStep(0.01)
        self.max_drawdown_spin.setValue(0.25)
        layout.addRow(f"{self.tr('max_drawdown', 'Max Drawdown')} %:", self.max_drawdown_spin)
        
        # Trade amount limits
        self.min_trade_amount_spin = QDoubleSpinBox()
        self.min_trade_amount_spin.setRange(1, 1000)
        self.min_trade_amount_spin.setDecimals(2)
        self.min_trade_amount_spin.setValue(10)
        layout.addRow(f"{self.tr('min_trade_amount', 'Min Trade Amount')}:", self.min_trade_amount_spin)
        
        self.max_trade_amount_spin = QDoubleSpinBox()
        self.max_trade_amount_spin.setRange(10, 10000)
        self.max_trade_amount_spin.setDecimals(2)
        self.max_trade_amount_spin.setValue(100)
        layout.addRow(f"{self.tr('max_trade_amount', 'Max Trade Amount')}:", self.max_trade_amount_spin)
        
        # Max trades per day
        self.max_trades_per_day_spin = QSpinBox()
        self.max_trades_per_day_spin.setRange(1, 1000)
        self.max_trades_per_day_spin.setValue(50)
        layout.addRow(f"{self.tr('max_trades_per_day', 'Max Trades Per Day')}:", self.max_trades_per_day_spin)
        
        return widget
        
    def create_data_providers_tab(self) -> QWidget:
        """Create data providers settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Data interval selection
        data_interval_group = QGroupBox(self.tr('data_settings', 'Data Settings'))
        data_interval_layout = QFormLayout(data_interval_group)
        
        self.data_interval_combo = QComboBox()
        self.data_interval_combo.addItems(['1m', '5m', '15m', '1h', '4h', '1d'])
        data_interval_layout.addRow(f"{self.tr('data_interval', 'Data Interval')}:", self.data_interval_combo)
        
        layout.addWidget(data_interval_group)
        
        # Yahoo Finance group
        
        
        # MT4 Data Provider group
        mt4_data_group = QGroupBox(self.tr('mt4_data_settings', 'MT4 Data Provider'))
        mt4_data_layout = QFormLayout(mt4_data_group)
        
        self.mt4_data_enabled_checkbox = QCheckBox(self.tr('enable_mt4_data', 'Use MT4 as Data Provider'))
        mt4_data_layout.addRow(f"{self.tr('status', 'Status')}:", self.mt4_data_enabled_checkbox)
        
        mt4_data_info = QLabel(self.tr('mt4_data_info', 'Use MT4\'s data feed for real-time and historical data. Requires MT4 connection.'))
        mt4_data_info.setWordWrap(True)
        mt4_data_info.setStyleSheet("color: #888; font-size: 11px;")
        mt4_data_layout.addRow(mt4_data_info)
        
        layout.addWidget(mt4_data_group)
        
        # Test connection button
        test_button = QPushButton(self.tr('test_connections', 'Test Data Provider Connections'))
        test_button.clicked.connect(self.test_data_providers)
        layout.addWidget(test_button)
        
        return widget
        
    def create_ui_tab(self) -> QWidget:
        """Create UI settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['auto', 'light', 'dark', 'dracula'])
        layout.addRow(f"{self.tr('theme', 'Theme')}:", self.theme_combo)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_mapping = {
            "English": "en",
            "Français": "fr", 
            "Español": "es",
            "中文": "zh",
            "日本語": "ja",
            "Deutsch": "de",
            "Русский": "ru",
            "Eesti": "et",
            "Português": "pt",
            "한국어": "ko",
            "Català": "ca",
            "Euskera": "eu",
            "Galego": "gl"
        }
        self.language_combo.addItems(list(self.language_mapping.keys()))
        layout.addRow(f"{self.tr('language', 'Language')}:", self.language_combo)
        
        # Startup options
        self.startup_checkbox = QCheckBox(self.tr('run_on_startup', 'Run ForexSmartBot on system startup'))
        layout.addRow(f"{self.tr('startup', 'Startup')}:", self.startup_checkbox)
        
        # Window settings
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        self.window_width_spin.setValue(1400)
        layout.addRow(f"{self.tr('window_width', 'Window Width')}:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1200)
        self.window_height_spin.setValue(900)
        layout.addRow(f"{self.tr('window_height', 'Window Height')}:", self.window_height_spin)
        
        # Display settings
        self.show_toolbar_checkbox = QCheckBox(self.tr('show_toolbar', 'Show Toolbar'))
        self.show_toolbar_checkbox.setChecked(True)
        layout.addRow(f"{self.tr('show_toolbar', 'Show Toolbar')}:", self.show_toolbar_checkbox)
        
        self.show_statusbar_checkbox = QCheckBox(self.tr('show_statusbar', 'Show Status Bar'))
        self.show_statusbar_checkbox.setChecked(True)
        layout.addRow(f"{self.tr('show_statusbar', 'Show Status Bar')}:", self.show_statusbar_checkbox)
        
        # Notification settings
        notification_group = QGroupBox(self.tr('notifications', 'Notifications'))
        notification_layout = QFormLayout(notification_group)
        
        # Telegram settings
        self.telegram_notifications_checkbox = QCheckBox(self.tr('enable_telegram_notifications', 'Enable Telegram Notifications'))
        notification_layout.addRow(f"{self.tr('telegram', 'Telegram')}:", self.telegram_notifications_checkbox)
        
        self.telegram_bot_token_edit = QLineEdit()
        self.telegram_bot_token_edit.setPlaceholderText(self.tr('bot_token', 'Bot Token'))
        self.telegram_bot_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        notification_layout.addRow(f"{self.tr('bot_token', 'Bot Token')}:", self.telegram_bot_token_edit)
        
        self.telegram_channel_id_edit = QLineEdit()
        self.telegram_channel_id_edit.setPlaceholderText(self.tr('channel_id_placeholder', 'Channel ID (e.g., @channelname or -1001234567890)'))
        notification_layout.addRow(f"{self.tr('channel_id', 'Channel ID')}:", self.telegram_channel_id_edit)
        
        # Discord settings
        self.discord_notifications_checkbox = QCheckBox(self.tr('enable_discord_notifications', 'Enable Discord Notifications'))
        notification_layout.addRow(f"{self.tr('discord', 'Discord')}:", self.discord_notifications_checkbox)
        
        self.discord_webhook_url_edit = QLineEdit()
        self.discord_webhook_url_edit.setPlaceholderText(self.tr('webhook_url', 'Webhook URL'))
        notification_layout.addRow(f"{self.tr('webhook_url', 'Webhook URL')}:", self.discord_webhook_url_edit)
        
        layout.addRow(notification_group)
        
        return widget
        
    def load_settings(self):
        """Load settings from settings manager."""
        if not self.settings_manager:
            return
            
        # General settings
        self.portfolio_mode_checkbox.setChecked(self.settings_manager.get('portfolio_mode', False))
        self.confirm_live_trades_checkbox.setChecked(self.settings_manager.get('confirm_live_trades', True))
        
        # Data Provider settings
        self.data_interval_combo.setCurrentText(self.settings_manager.get('data_interval', '1h'))
        
        # Broker settings
        self.broker_mode_combo.setCurrentText(self.settings_manager.get('broker_mode', 'PAPER'))
        self.mt4_host_edit.setText(self.settings_manager.get('mt4_host', '127.0.0.1'))
        self.mt4_port_spin.setValue(self.settings_manager.get('mt4_port', 5555))
        
        # REST API settings
        self.rest_api_key_edit.setText(self.settings_manager.get('rest_api_key', ''))
        self.rest_api_secret_edit.setText(self.settings_manager.get('rest_api_secret', ''))
        self.rest_base_url_edit.setText(self.settings_manager.get('rest_base_url', 'https://api.example.com'))
        
        # Risk settings
        self.risk_pct_spin.setValue(self.settings_manager.get('base_risk_pct', 0.02))
        self.max_risk_pct_spin.setValue(self.settings_manager.get('max_risk_pct', 0.05))
        self.daily_risk_cap_spin.setValue(self.settings_manager.get('daily_risk_cap', 0.05))
        self.broker_spread_spin.setValue(self.settings_manager.get('broker_spread', 2.0))
        self.max_drawdown_spin.setValue(self.settings_manager.get('max_drawdown_pct', 0.25))
        self.min_trade_amount_spin.setValue(self.settings_manager.get('trade_amount_min', 10.0))
        self.max_trade_amount_spin.setValue(self.settings_manager.get('trade_amount_max', 100.0))
        self.max_trades_per_day_spin.setValue(self.settings_manager.get('max_trades_per_day', 50))
        
        # Data Provider settings
        self.mt4_data_enabled_checkbox.setChecked(self.settings_manager.get('mt4_data_enabled', True))
        
        # UI settings
        self.theme_combo.setCurrentText(self.settings_manager.get('theme', 'auto'))
        self.window_width_spin.setValue(self.settings_manager.get('window_width', 1400))
        self.window_height_spin.setValue(self.settings_manager.get('window_height', 900))
        self.show_toolbar_checkbox.setChecked(self.settings_manager.get('show_toolbar', True))
        self.show_statusbar_checkbox.setChecked(self.settings_manager.get('show_statusbar', True))
        
        # Language settings
        current_lang = self.settings_manager.get('language', 'en')
        for display_name, lang_code in self.language_mapping.items():
            if lang_code == current_lang:
                self.language_combo.setCurrentText(display_name)
                break
        
        # Startup settings
        self.startup_checkbox.setChecked(self.settings_manager.get('startup_enabled', False))
        
        # Notification settings
        self.telegram_bot_token_edit.setText(self.settings_manager.get('telegram_bot_token', ''))
        self.telegram_channel_id_edit.setText(self.settings_manager.get('telegram_channel_id', ''))
        self.telegram_notifications_checkbox.setChecked(self.settings_manager.get('telegram_notifications', False))
        self.discord_webhook_url_edit.setText(self.settings_manager.get('discord_webhook_url', ''))
        self.discord_notifications_checkbox.setChecked(self.settings_manager.get('discord_notifications', False))
        
    def save_settings(self):
        """Save settings to settings manager."""
        if not self.settings_manager:
            return
            
        try:
            # Validate broker settings before saving
            broker_mode = self.broker_mode_combo.currentText()
            if broker_mode == 'MT4':
                if not self.mt4_host_edit.text().strip() or self.mt4_port_spin.value() == 0:
                    QMessageBox.warning(self, "Broker Configuration", 
                                      "You need to configure the MT4 settings before save")
                    return
            elif broker_mode == 'REST API':
                if not self.rest_api_key_edit.text().strip() or not self.rest_api_secret_edit.text().strip() or not self.rest_base_url_edit.text().strip():
                    QMessageBox.warning(self, "Broker Configuration", 
                                      "You need to configure the REST API settings before save")
                    return
            
            # General settings
            self.settings_manager.set('portfolio_mode', self.portfolio_mode_checkbox.isChecked())
            self.settings_manager.set('confirm_live_trades', self.confirm_live_trades_checkbox.isChecked())
            
            # Broker settings
            self.settings_manager.set('broker_mode', broker_mode)
            self.settings_manager.set('mt4_host', self.mt4_host_edit.text())
            self.settings_manager.set('mt4_port', self.mt4_port_spin.value())
            
            # REST API settings
            self.settings_manager.set('rest_api_key', self.rest_api_key_edit.text())
            self.settings_manager.set('rest_api_secret', self.rest_api_secret_edit.text())
            self.settings_manager.set('rest_base_url', self.rest_base_url_edit.text())
            
            # Risk settings
            self.settings_manager.set('base_risk_pct', self.risk_pct_spin.value())
            self.settings_manager.set('max_risk_pct', self.max_risk_pct_spin.value())
            self.settings_manager.set('daily_risk_cap', self.daily_risk_cap_spin.value())
            self.settings_manager.set('broker_spread', self.broker_spread_spin.value())
            self.settings_manager.set('max_drawdown_pct', self.max_drawdown_spin.value())
            self.settings_manager.set('trade_amount_min', self.min_trade_amount_spin.value())
            self.settings_manager.set('trade_amount_max', self.max_trade_amount_spin.value())
            self.settings_manager.set('max_trades_per_day', self.max_trades_per_day_spin.value())
            
            # Data Provider settings
            self.settings_manager.set('data_interval', self.data_interval_combo.currentText())
            self.settings_manager.set('mt4_data_enabled', self.mt4_data_enabled_checkbox.isChecked())
            
            # UI settings
            self.settings_manager.set('theme', self.theme_combo.currentText())
            self.settings_manager.set('window_width', self.window_width_spin.value())
            self.settings_manager.set('window_height', self.window_height_spin.value())
            self.settings_manager.set('show_toolbar', self.show_toolbar_checkbox.isChecked())
            self.settings_manager.set('show_statusbar', self.show_statusbar_checkbox.isChecked())
            
            # Language settings
            selected_lang = self.language_combo.currentText()
            lang_code = self.language_mapping.get(selected_lang, 'en')
            self.settings_manager.set('language', lang_code)
            
            # Startup settings
            self.settings_manager.set('startup_enabled', self.startup_checkbox.isChecked())
            
            # Notification settings
            self.settings_manager.set('telegram_bot_token', self.telegram_bot_token_edit.text())
            self.settings_manager.set('telegram_channel_id', self.telegram_channel_id_edit.text())
            self.settings_manager.set('telegram_notifications', self.telegram_notifications_checkbox.isChecked())
            self.settings_manager.set('discord_webhook_url', self.discord_webhook_url_edit.text())
            self.settings_manager.set('discord_notifications', self.discord_notifications_checkbox.isChecked())
            
            # Save to file
            if self.settings_manager.save():
                QMessageBox.information(self, "Settings", "Settings saved successfully!")
                
                # Call callback if provided
                if self.on_settings_saved:
                    self.on_settings_saved()
                
                self.accept()
            else:
                QMessageBox.warning(self, "Settings", "Failed to save settings!")
                
        except Exception as e:
            QMessageBox.critical(self, "Settings", f"Error saving settings: {str(e)}")
    
    def test_data_providers(self):
        """Test data provider connections."""
        try:
            from ..adapters.data import MT4Provider
            
            results = []
            
            
            # Test Alpha Vantage
            if self.av_enabled_checkbox.isChecked():
                api_key = self.av_api_key_edit.text().strip()
                if api_key:
                    try:
                        av_provider = AlphaVantageProvider(api_key)
                        price = av_provider.get_latest_price("EURUSD")
                        if price:
                            results.append("✅ Alpha Vantage: Connected successfully")
                        else:
                            results.append("❌ Alpha Vantage: No data available")
                    except Exception as e:
                        results.append(f"❌ Alpha Vantage: {str(e)}")
                else:
                    results.append("❌ Alpha Vantage: API key required")
            
            # Test OANDA
            if self.oanda_enabled_checkbox.isChecked():
                api_key = self.oanda_api_key_edit.text().strip()
                account_id = self.oanda_account_id_edit.text().strip()
                if api_key and account_id:
                    try:
                        oanda_provider = OANDAProvider(api_key, account_id)
                        price = oanda_provider.get_latest_price("EURUSD")
                        if price:
                            results.append("✅ OANDA: Connected successfully")
                        else:
                            results.append("❌ OANDA: No data available")
                    except Exception as e:
                        results.append(f"❌ OANDA: {str(e)}")
                else:
                    results.append("❌ OANDA: API key and Account ID required")
            
            # Test MT4 Data Provider
            if self.mt4_data_enabled_checkbox.isChecked():
                try:
                    mt4_host = self.mt4_host_edit.text().strip() or "127.0.0.1"
                    mt4_port = self.mt4_port_spin.value()
                    mt4_provider = MT4Provider(mt4_host, mt4_port)
                    
                    # Test if MT4 is available (without actually connecting)
                    if mt4_provider.is_available():
                        results.append("✅ MT4 Data Provider: Available (MT4 connection required)")
                    else:
                        results.append("❌ MT4 Data Provider: Not available (MT4 not running or wrong host/port)")
                        
                except Exception as e:
                    results.append(f"❌ MT4 Data Provider: {str(e)}")
            
            # Show results
            if results:
                message = "Data Provider Test Results:\n\n" + "\n".join(results)
                QMessageBox.information(self, "Connection Test", message)
            else:
                QMessageBox.warning(self, "Connection Test", "No data providers enabled for testing.")
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Test", f"Error testing connections: {str(e)}")
            
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
