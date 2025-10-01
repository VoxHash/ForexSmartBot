"""Enhanced main window for ForexSmartBot."""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QDoubleSpinBox, QSpinBox, QTextEdit, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QGroupBox, QFormLayout, QCheckBox, QMessageBox,
                             QStatusBar, QProgressBar, QSplitter, QDialog)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFont
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

from ..core.interfaces import IBroker, IStrategy, IDataProvider
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig
from ..services.controller import TradingController
from ..services.persistence import SettingsManager, DatabaseManager, LogManager
from ..strategies import get_strategy, list_strategies
from ..adapters.brokers import PaperBroker, MT4Broker, RestBroker
from ..adapters.data import YFinanceProvider, CSVProvider
from .settings_dialog import SettingsDialog
from .charts import ChartWidget
from .theme import ThemeManager


class MainWindow(QMainWindow):
    """Enhanced main window with portfolio mode and advanced features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ForexSmartBot - Professional Trading System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize services
        self.settings_manager = SettingsManager()
        self.db_manager = DatabaseManager()
        self.log_manager = LogManager()
        self.logger = self.log_manager.get_logger(__name__)
        
        # Initialize components
        self.portfolio = Portfolio(self.settings_manager.get('initial_balance', 10000.0))
        self.risk_config = self._create_risk_config()
        self.risk_engine = RiskEngine(self.risk_config)
        
        # Initialize brokers and data providers
        self.broker = None
        self.data_provider = None
        self.controller = None
        
        # UI state
        self.is_running = False
        self.selected_symbols = []
        self.strategies = {}
        
        # Initialize UI
        self.setup_ui()
        self.setup_theme()
        self.setup_connections()
        self.load_settings()
        
        # Initialize timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(5000)  # Update every 5 seconds
        
        # Load initial chart data
        self.load_chart_data()
        
    def setup_ui(self):
        """Setup the main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Top controls
        self.create_controls_panel(main_layout)
        
        # Status bar
        self.create_status_bar()
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - controls and log
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - charts and positions
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 1000])
        
    def create_controls_panel(self, parent_layout):
        """Create the top controls panel."""
        controls_group = QGroupBox("Trading Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        # Broker selection
        controls_layout.addWidget(QLabel("Broker:"))
        self.broker_combo = QComboBox()
        self.broker_combo.addItems(["PAPER", "MT4", "REST"])
        controls_layout.addWidget(self.broker_combo)
        
        # Strategy selection
        controls_layout.addWidget(QLabel("Strategy:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(list_strategies())
        controls_layout.addWidget(self.strategy_combo)
        
        # Symbols selection
        controls_layout.addWidget(QLabel("Symbols:"))
        self.symbols_edit = QLineEdit()
        self.symbols_edit.setPlaceholderText("EURUSD,USDJPY,GBPUSD")
        controls_layout.addWidget(self.symbols_edit)
        
        # Risk percentage
        controls_layout.addWidget(QLabel("Risk %:"))
        self.risk_pct_spin = QDoubleSpinBox()
        self.risk_pct_spin.setRange(0.001, 0.1)
        self.risk_pct_spin.setDecimals(3)
        self.risk_pct_spin.setSingleStep(0.005)
        self.risk_pct_spin.setValue(0.02)
        controls_layout.addWidget(self.risk_pct_spin)
        
        # Theme selector
        controls_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Auto", "Light", "Dark"])
        controls_layout.addWidget(self.theme_combo)
        
        # Buttons
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect)
        controls_layout.addWidget(self.connect_button)
        
        self.start_button = QPushButton("Start Bot")
        self.start_button.clicked.connect(self.on_start)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Bot")
        self.stop_button.clicked.connect(self.on_stop)
        controls_layout.addWidget(self.stop_button)
        
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings)
        controls_layout.addWidget(self.settings_button)
        
        self.export_button = QPushButton("Export Trades")
        self.export_button.clicked.connect(self.export_trades)
        controls_layout.addWidget(self.export_button)
        
        parent_layout.addWidget(controls_group)
        
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status labels
        self.status_label = QLabel("Status: Idle")
        self.balance_label = QLabel("Balance: $0.00")
        self.equity_label = QLabel("Equity: $0.00")
        self.drawdown_label = QLabel("DD: 0.0%")
        
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addWidget(self.balance_label)
        self.status_bar.addWidget(self.equity_label)
        self.status_bar.addWidget(self.drawdown_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def create_left_panel(self):
        """Create the left panel with log and metrics."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Log tab widget
        self.log_tabs = QTabWidget()
        layout.addWidget(self.log_tabs)
        
        # Log tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        self.log_tabs.addTab(log_widget, "Log")
        
        # Metrics tab
        metrics_widget = self.create_metrics_tab()
        self.log_tabs.addTab(metrics_widget, "Metrics")
        
        # Open positions tab
        positions_widget = self.create_positions_tab()
        self.log_tabs.addTab(positions_widget, "Positions")
        
        return widget
        
    def create_right_panel(self):
        """Create the right panel with charts."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Chart widget
        self.chart_widget = ChartWidget()
        layout.addWidget(self.chart_widget)
        
        return widget
        
    def create_metrics_tab(self):
        """Create the metrics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.metrics_table)
        
        return widget
        
    def create_positions_tab(self):
        """Create the positions tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(7)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Side", "Quantity", "Entry Price", "Current Price", "PnL", "Strategy"
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.positions_table)
        
        return widget
        
    def setup_theme(self):
        """Setup theme management."""
        self.theme_manager = ThemeManager(self.settings_manager)
        self.theme_manager.apply_theme(self.app)
        
    def setup_connections(self):
        """Setup signal connections."""
        # Theme change
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        
        # Strategy change
        self.strategy_combo.currentTextChanged.connect(self.on_strategy_changed)
        
        # Symbol change for chart
        self.symbols_edit.textChanged.connect(self.on_symbols_changed)
        
    def load_settings(self):
        """Load settings from settings manager."""
        # Load theme
        theme = self.settings_manager.get('theme', 'auto')
        theme_map = {'auto': 0, 'light': 1, 'dark': 2}
        self.theme_combo.setCurrentIndex(theme_map.get(theme, 0))
        
        # Load broker
        broker = self.settings_manager.get('broker_mode', 'PAPER')
        self.broker_combo.setCurrentText(broker)
        
        # Load strategy
        strategy = self.settings_manager.get('strategy', 'SMA_Crossover')
        self.strategy_combo.setCurrentText(strategy)
        
        # Load symbols
        symbols = self.settings_manager.get('selected_symbols', ['EURUSD'])
        self.symbols_edit.setText(','.join(symbols))
        
        # Load risk settings
        self.risk_pct_spin.setValue(self.settings_manager.get('risk_pct', 0.02))
        
    def _create_risk_config(self) -> RiskConfig:
        """Create risk configuration from settings."""
        return RiskConfig(
            base_risk_pct=self.settings_manager.get('risk_pct', 0.02),
            max_risk_pct=self.settings_manager.get('max_risk_pct', 0.05),
            daily_risk_cap=self.settings_manager.get('daily_risk_cap', 0.05),
            max_drawdown_pct=self.settings_manager.get('max_drawdown_pct', 0.25),
            min_trade_amount=self.settings_manager.get('trade_amount_min', 10.0),
            max_trade_amount=self.settings_manager.get('trade_amount_max', 100.0)
        )
        
    def on_connect(self):
        """Handle broker connection."""
        broker_type = self.broker_combo.currentText()
        
        try:
            if broker_type == "PAPER":
                self.broker = PaperBroker(self.settings_manager.get('initial_balance', 10000.0))
            elif broker_type == "MT4":
                host = self.settings_manager.get('mt4_host', '127.0.0.1')
                port = self.settings_manager.get('mt4_port', 5555)
                self.broker = MT4Broker(host, port)
            elif broker_type == "REST":
                api_key = self.settings_manager.get('rest_api_key', '')
                api_secret = self.settings_manager.get('rest_api_secret', '')
                base_url = self.settings_manager.get('rest_base_url', 'https://api.example.com')
                self.broker = RestBroker(api_key, api_secret, base_url)
                
            if self.broker.connect():
                self.append_log(f"Connected to {broker_type} broker")
                self.status_label.setText(f"Status: Connected to {broker_type}")
            else:
                self.append_log(f"Failed to connect to {broker_type} broker")
                self.status_label.setText("Status: Connection Failed")
                
        except Exception as e:
            self.append_log(f"Connection error: {str(e)}")
            self.status_label.setText("Status: Error")
            
    def on_start(self):
        """Start the trading bot."""
        if not self.broker or not self.broker.is_connected():
            QMessageBox.warning(self, "Start Bot", "Please connect to a broker first")
            return
            
        # Parse symbols
        symbols_text = self.symbols_edit.text().strip()
        if not symbols_text:
            QMessageBox.warning(self, "Start Bot", "Please enter at least one symbol")
            return
            
        self.selected_symbols = [s.strip().upper() for s in symbols_text.split(',') if s.strip()]
        
        # Initialize data provider
        data_provider_type = self.settings_manager.get('data_provider', 'yfinance')
        if data_provider_type == 'yfinance':
            self.data_provider = YFinanceProvider()
        elif data_provider_type == 'csv':
            self.data_provider = CSVProvider()
            
        # Initialize controller
        self.controller = TradingController(
            self.broker, self.data_provider, self.risk_engine, self.portfolio
        )
        
        # Connect controller signals
        self.controller.signal_trade_executed.connect(self.on_trade_executed)
        self.controller.signal_position_updated.connect(self.on_position_updated)
        self.controller.signal_equity_updated.connect(self.on_equity_updated)
        self.controller.signal_error_occurred.connect(self.on_error_occurred)
        self.controller.signal_log_message.connect(self.append_log)
        
        # Add strategies for each symbol
        strategy_name = self.strategy_combo.currentText()
        for symbol in self.selected_symbols:
            strategy = get_strategy(strategy_name)
            self.controller.add_strategy(symbol, strategy)
            
        # Start trading
        if self.controller.start_trading():
            self.is_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Status: Running")
            self.append_log("Trading bot started")
        else:
            QMessageBox.critical(self, "Start Bot", "Failed to start trading bot")
            
    def on_stop(self):
        """Stop the trading bot."""
        if self.controller:
            self.controller.stop_trading()
            
        self.is_running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.append_log("Trading bot stopped")
        
    def on_theme_changed(self, index):
        """Handle theme change."""
        theme_map = {0: 'auto', 1: 'light', 2: 'dark'}
        theme = theme_map[index]
        self.theme_manager.set_theme(theme)
        self.theme_manager.apply_theme(self.app)
        
    def on_strategy_changed(self, strategy_name):
        """Handle strategy change."""
        # Update strategy parameters if needed
        pass
        
    def on_symbols_changed(self):
        """Handle symbol change for chart update."""
        try:
            symbols_text = self.symbols_edit.text().strip()
            if symbols_text and len(symbols_text) >= 3:  # Only process complete symbols
                # Get the first symbol for chart display
                first_symbol = symbols_text.split(',')[0].strip().upper()
                # Only update if it's a valid forex pair (6 characters)
                if len(first_symbol) == 6:
                    self.update_chart_data(first_symbol)
        except Exception as e:
            self.append_log(f"Error updating chart for symbol: {str(e)}")
        
    def on_trade_executed(self, trade_data):
        """Handle trade execution signal."""
        self.append_log(f"Trade executed: {trade_data}")
        self.update_positions_table()
        self.update_metrics_table()
        
    def on_position_updated(self, position_data):
        """Handle position update signal."""
        self.update_positions_table()
        
    def on_equity_updated(self, equity):
        """Handle equity update signal."""
        self.equity_label.setText(f"Equity: ${equity:.2f}")
        
    def on_error_occurred(self, error_message):
        """Handle error signal."""
        self.append_log(f"ERROR: {error_message}")
        self.status_label.setText("Status: Error")
        
    def append_log(self, message):
        """Append message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.moveCursor(self.log_text.textCursor().MoveOperation.End)
        
    def update_display(self):
        """Update the display with current data."""
        if not self.is_running or not self.broker:
            return
            
        try:
            # Update balance and equity
            balance = self.broker.get_balance()
            equity = self.broker.get_equity()
            
            self.balance_label.setText(f"Balance: ${balance:.2f}")
            self.equity_label.setText(f"Equity: ${equity:.2f}")
            
            # Update drawdown
            if hasattr(self.portfolio, 'get_current_drawdown'):
                drawdown = self.portfolio.get_current_drawdown()
                self.drawdown_label.setText(f"DD: {drawdown:.1f}%")
                
            # Update tables
            self.update_positions_table()
            self.update_metrics_table()
            
        except Exception as e:
            self.append_log(f"Display update error: {str(e)}")
            
    def update_positions_table(self):
        """Update the positions table."""
        if not self.broker:
            return
            
        positions = self.broker.get_positions()
        
        self.positions_table.setRowCount(len(positions))
        
        for row, (symbol, position) in enumerate(positions.items()):
            self.positions_table.setItem(row, 0, QTableWidgetItem(symbol))
            self.positions_table.setItem(row, 1, QTableWidgetItem("LONG" if position.side > 0 else "SHORT"))
            self.positions_table.setItem(row, 2, QTableWidgetItem(f"{position.quantity:.6f}"))
            self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position.entry_price:.5f}"))
            self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position.current_price:.5f}"))
            self.positions_table.setItem(row, 5, QTableWidgetItem(f"{position.unrealized_pnl:.2f}"))
            self.positions_table.setItem(row, 6, QTableWidgetItem("Unknown"))
            
    def update_metrics_table(self):
        """Update the metrics table."""
        if not self.portfolio:
            return
            
        metrics = self.portfolio.calculate_metrics()
        
        metrics_data = [
            ("Total Balance", f"${metrics.total_balance:.2f}"),
            ("Total Equity", f"${metrics.total_equity:.2f}"),
            ("Unrealized PnL", f"${metrics.unrealized_pnl:.2f}"),
            ("Realized PnL", f"${metrics.realized_pnl:.2f}"),
            ("Max Drawdown", f"{metrics.max_drawdown:.2f}%"),
            ("Current Drawdown", f"{metrics.current_drawdown:.2f}%"),
            ("Win Rate", f"{metrics.win_rate:.2f}%"),
            ("Profit Factor", f"{metrics.profit_factor:.2f}"),
            ("Total Trades", str(metrics.total_trades)),
            ("Winning Trades", str(metrics.winning_trades)),
            ("Losing Trades", str(metrics.losing_trades)),
            ("Avg Win", f"${metrics.avg_win:.2f}"),
            ("Avg Loss", f"${metrics.avg_loss:.2f}"),
        ]
        
        self.metrics_table.setRowCount(len(metrics_data))
        
        for row, (metric, value) in enumerate(metrics_data):
            self.metrics_table.setItem(row, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(value))
            
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_settings()
            # Recreate risk config with new settings
            self.risk_config = self._create_risk_config()
            self.risk_engine = RiskEngine(self.risk_config)
            
    def export_trades(self):
        """Export trades to CSV."""
        try:
            trades = self.db_manager.get_trades()
            if not trades:
                QMessageBox.information(self, "Export Trades", "No trades to export")
                return
                
            # Create CSV content
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            if trades:
                writer.writerow(trades[0].keys())
                for trade in trades:
                    writer.writerow(trade.values())
                    
            # Save to file
            from PyQt6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Trades", "trades.csv", "CSV Files (*.csv)"
            )
            
            if filename:
                with open(filename, 'w', newline='') as f:
                    f.write(output.getvalue())
                QMessageBox.information(self, "Export Trades", f"Trades exported to {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Trades", f"Error exporting trades: {str(e)}")
            
    def load_chart_data(self):
        """Load initial chart data for display."""
        try:
            # Create data provider
            data_provider = YFinanceProvider()
            
            if data_provider.is_available():
                # Get data for EURUSD
                from datetime import timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                df = data_provider.get_data('EURUSD=X', start_date, end_date, '1h')
                
                if not df.empty:
                    # Add to chart widget
                    self.chart_widget.set_data('EURUSD', df)
                    self.append_log(f"Chart data loaded: {df.shape[0]} rows for EURUSD")
                else:
                    # Create sample data if no real data
                    self.create_sample_chart_data()
            else:
                # Create sample data if no internet
                self.create_sample_chart_data()
                
        except Exception as e:
            self.append_log(f"Error loading chart data: {str(e)}")
            self.create_sample_chart_data()
    
    def create_sample_chart_data(self):
        """Create sample chart data for demonstration."""
        try:
            import pandas as pd
            import numpy as np
            
            # Generate sample data
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='1h')
            np.random.seed(42)
            base_price = 1.1800
            price_changes = np.random.randn(len(dates)) * 0.001
            prices = base_price + np.cumsum(price_changes)
            
            sample_data = pd.DataFrame({
                'Open': prices,
                'High': prices + np.random.rand(len(dates)) * 0.0005,
                'Low': prices - np.random.rand(len(dates)) * 0.0005,
                'Close': prices + np.random.randn(len(dates)) * 0.0001,
                'Volume': np.random.randint(1000, 10000, len(dates))
            }, index=dates)
            
            # Add SMA indicators
            sample_data['SMA_fast'] = sample_data['Close'].rolling(window=10).mean()
            sample_data['SMA_slow'] = sample_data['Close'].rolling(window=20).mean()
            sample_data['ATR'] = sample_data['High'].rolling(window=14).max() - sample_data['Low'].rolling(window=14).min()
            
            # Add to chart widget
            self.chart_widget.set_data('EURUSD', sample_data)
            self.append_log(f"Sample chart data created: {sample_data.shape[0]} rows for EURUSD")
            
        except Exception as e:
            self.append_log(f"Error creating sample data: {str(e)}")
    
    def update_chart_data(self, symbol: str):
        """Update chart data for a specific symbol."""
        try:
            if self.data_provider and self.data_provider.is_available():
                from datetime import timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                # Convert symbol format for Yahoo Finance
                yahoo_symbol = f"{symbol}=X" if not symbol.endswith('=X') else symbol
                
                df = self.data_provider.get_data(yahoo_symbol, start_date, end_date, '1h')
                
                if not df.empty:
                    self.chart_widget.set_data(symbol, df)
                    self.append_log(f"Chart data updated: {df.shape[0]} rows for {symbol}")
                else:
                    self.append_log(f"No data available for {symbol}")
            else:
                self.append_log("Data provider not available")
                
        except Exception as e:
            self.append_log(f"Error updating chart data: {str(e)}")

    @property
    def app(self):
        """Get the QApplication instance."""
        from PyQt6.QtWidgets import QApplication
        return QApplication.instance()
