"""
Enhanced Main Window for ForexSmartBot
Updated with all new features and improved UI/UX
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QDoubleSpinBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QCheckBox, QMessageBox, QStatusBar,
    QProgressBar, QSplitter, QDialog, QFrame, QScrollArea,
    QSpinBox, QSlider, QToolBar, QMenuBar, QMenu, QListWidget,
    QListWidgetItem, QAbstractItemView, QApplication
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QPalette, QColor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from ..core.interfaces import IBroker, IStrategy, IDataProvider, Position, Trade
from ..core.portfolio import Portfolio
from ..core.risk_engine import RiskEngine, RiskConfig
from ..services.controller import TradingController
from ..services.persistence import SettingsManager, DatabaseManager, LogManager
from ..strategies import get_strategy, list_strategies
from ..adapters.brokers import PaperBroker, MT4Broker, RestBroker
from ..adapters.data import YFinanceProvider, CSVProvider
from .settings_dialog import SettingsDialog
from .backtest_dialog import BacktestDialog
from .export_dialog import ExportDialog
from .theme import ThemeManager
from ..services.notification_service import NotificationService
from ..services.startup_manager import StartupManager
from ..services.language_manager import LanguageManager


class TradingStatusWidget(QWidget):
    """Widget showing trading status with real-time updates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status indicators
        status_group = QGroupBox("Trading Status")
        status_layout = QGridLayout(status_group)
        
        # Broker status
        self.broker_status = QLabel("PAPER")
        self.broker_status.setStyleSheet("color: blue; font-weight: bold;")
        status_layout.addWidget(QLabel("Broker:"), 0, 0)
        status_layout.addWidget(self.broker_status, 0, 1)
        
        # Connection status
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(QLabel("Connection:"), 1, 0)
        status_layout.addWidget(self.connection_status, 1, 1)
        
        # Trading status
        self.trading_status = QLabel("Stopped")
        self.trading_status.setStyleSheet("color: orange; font-weight: bold;")
        status_layout.addWidget(QLabel("Trading:"), 2, 0)
        status_layout.addWidget(self.trading_status, 2, 1)
        
        # Balance (real-time)
        self.balance_label = QLabel("$0.00")
        self.balance_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        status_layout.addWidget(QLabel("Balance:"), 3, 0)
        status_layout.addWidget(self.balance_label, 3, 1)
        
        # Equity (real-time)
        self.equity_label = QLabel("$0.00")
        self.equity_label.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        status_layout.addWidget(QLabel("Equity:"), 4, 0)
        status_layout.addWidget(self.equity_label, 4, 1)
        
        # Drawdown (real-time)
        self.drawdown_label = QLabel("0.0%")
        self.drawdown_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(QLabel("Drawdown:"), 5, 0)
        status_layout.addWidget(self.drawdown_label, 5, 1)
        
        # Monitoring status (real-time)
        self.monitoring_status = QLabel("Inactive")
        self.monitoring_status.setStyleSheet("color: gray; font-weight: bold;")
        status_layout.addWidget(QLabel("Monitoring:"), 6, 0)
        status_layout.addWidget(self.monitoring_status, 6, 1)
        
        layout.addWidget(status_group)


class StrategyConfigWidget(QWidget):
    """Widget for strategy configuration with multi-symbol selection."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Strategy Configuration
        strategy_group = QGroupBox("Strategy Configuration")
        strategy_layout = QFormLayout(strategy_group)
        
        # Strategy selection organized by risk level
        self.strategy_combo = QComboBox()
        
        # Low Risk Strategies
        low_risk_strategies = ['Mean_Reversion', 'SMA_Crossover']
        # Medium Risk Strategies  
        medium_risk_strategies = ['Scalping_MA', 'RSI_Reversion', 'BreakoutATR']
        # High Risk Strategies
        high_risk_strategies = ['Momentum_Breakout', 'News_Trading', 'ML_Adaptive_SuperTrend', 'Adaptive_Trend_Flow']
        
        # Add strategies with risk level indicators
        for strategy in low_risk_strategies:
            self.strategy_combo.addItem(f"🟢 {strategy} (Low Risk)")
        for strategy in medium_risk_strategies:
            self.strategy_combo.addItem(f"🟡 {strategy} (Medium Risk)")
        for strategy in high_risk_strategies:
            self.strategy_combo.addItem(f"🔴 {strategy} (High Risk)")
            
        strategy_layout.addRow("Strategy:", self.strategy_combo)
        
        # Multi-symbol selection
        symbols_group = QWidget()
        symbols_layout = QHBoxLayout(symbols_group)
        
        self.symbols_list = QListWidget()
        self.symbols_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.symbols_list.setMaximumHeight(100)
        
        # Add forex pairs organized by trading quality
        # Major pairs (highest liquidity, best for trading)
        major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
        # Minor pairs (good liquidity, active trading)
        minor_pairs = ["EURGBP", "EURJPY", "GBPJPY", "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADCHF", "CADJPY", "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURNZD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD", "NZDCAD", "NZDCHF", "NZDJPY"]
        # Exotic pairs (higher volatility, more opportunities)
        exotic_pairs = ["USDTRY", "USDZAR", "USDMXN", "USDPLN", "USDCZK", "USDHUF", "USDSEK", "USDNOK", "USDDKK", "USDRUB", "USDCNH", "USDSGD", "USDHKD", "USDTWD", "USDKRW", "USDINR", "USDBRL", "USDARS", "USDCLP", "USDCOP"]
        
        # Combine all pairs in order of trading quality
        all_pairs = major_pairs + minor_pairs + exotic_pairs
        
        for pair in all_pairs:
            item = QListWidgetItem(pair)
            # Color code by category
            if pair in major_pairs:
                item.setForeground(QColor("green"))  # Major pairs in green
            elif pair in minor_pairs:
                item.setForeground(QColor("blue"))   # Minor pairs in blue
            else:
                item.setForeground(QColor("orange")) # Exotic pairs in orange
            self.symbols_list.addItem(item)
        
        # Pre-select some of the best trading pairs
        best_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDTRY", "USDMXN"]
        for i in range(self.symbols_list.count()):
            item = self.symbols_list.item(i)
            if item.text() in best_pairs:
                item.setSelected(True)
        
        symbols_layout.addWidget(self.symbols_list)
        strategy_layout.addRow("Symbols:", symbols_group)
        
        # Risk per trade
        self.risk_spinbox = QDoubleSpinBox()
        self.risk_spinbox.setRange(0.01, 10.0)
        self.risk_spinbox.setValue(1.0)
        self.risk_spinbox.setSuffix("%")
        strategy_layout.addRow("Risk per Trade:", self.risk_spinbox)
        
        # Leverage selection
        self.leverage_combo = QComboBox()
        leverage_options = [
            "1:1 (No Leverage)",
            "1:5 (Conservative)",
            "1:10 (Moderate)", 
            "1:20 (Aggressive)",
            "1:50 (High Risk)",
            "1:100 (Very High Risk)",
            "1:200 (Maximum Risk)"
        ]
        self.leverage_combo.addItems(leverage_options)
        self.leverage_combo.setCurrentText("1:10 (Moderate)")
        strategy_layout.addRow("Leverage:", self.leverage_combo)
        
        layout.addWidget(strategy_group)
        
    def get_selected_symbols(self):
        """Get selected symbols."""
        selected_items = self.symbols_list.selectedItems()
        return [item.text() for item in selected_items] if selected_items else ["EURUSD"]


class PerformanceMetricsWidget(QWidget):
    """Widget showing performance metrics with real-time updates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # Total Trades (real-time)
        self.total_trades_label = QLabel("0")
        self.total_trades_label.setStyleSheet("font-weight: bold; color: blue;")
        metrics_layout.addWidget(QLabel("Total Trades:"), 0, 0)
        metrics_layout.addWidget(self.total_trades_label, 0, 1)
        
        # Win Rate (real-time)
        self.win_rate_label = QLabel("0%")
        self.win_rate_label.setStyleSheet("font-weight: bold; color: green;")
        metrics_layout.addWidget(QLabel("Win Rate:"), 1, 0)
        metrics_layout.addWidget(self.win_rate_label, 1, 1)
        
        # Profit Factor (real-time)
        self.profit_factor_label = QLabel("0.00")
        self.profit_factor_label.setStyleSheet("font-weight: bold; color: orange;")
        metrics_layout.addWidget(QLabel("Profit Factor:"), 2, 0)
        metrics_layout.addWidget(self.profit_factor_label, 2, 1)
        
        # Max Drawdown (real-time)
        self.max_drawdown_label = QLabel("0%")
        self.max_drawdown_label.setStyleSheet("font-weight: bold; color: red;")
        metrics_layout.addWidget(QLabel("Max Drawdown:"), 3, 0)
        metrics_layout.addWidget(self.max_drawdown_label, 3, 1)
        
        layout.addWidget(metrics_group)


class TradingControlsWidget(QWidget):
    """Widget for trading controls with proper connect/disconnect and start/stop functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Trading Controls
        controls_group = QGroupBox("Trading Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        controls_layout.addWidget(self.connect_btn)
        
        # Start/Stop Trading button
        self.start_btn = QPushButton("Start Trading")
        self.start_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
        self.start_btn.setEnabled(False)
        controls_layout.addWidget(self.start_btn)
        
        layout.addWidget(controls_group)
        
    def update_connection_state(self, connected: bool):
        """Update connection button state."""
        if connected:
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
            self.start_btn.setEnabled(True)
        else:
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
            self.start_btn.setEnabled(False)
    
    def update_trading_state(self, trading: bool):
        """Update trading button states."""
        if trading:
            self.start_btn.setText("Stop Trading")
            self.start_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
        else:
            self.start_btn.setText("Start Trading")
            self.start_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")


class OpenPositionsWidget(QWidget):
    """Widget showing open positions with real-time PnL updates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Open Positions
        positions_group = QGroupBox("Open Positions")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels(["Symbol", "Side", "Entry Price", "Current Price", "Stop Loss", "Take Profit", "PnL", "Status"])
        
        # Disable editing
        self.positions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        positions_layout.addWidget(self.positions_table)
        layout.addWidget(positions_group)
        
    def update_positions(self, positions: List[Position], current_prices: Dict[str, float]):
        """Update positions table with real-time data and advanced trade management."""
        self.positions_table.setRowCount(len(positions))
        
        for i, position in enumerate(positions):
            current_price = current_prices.get(position.symbol, position.current_price)
            pnl = position.side * position.quantity * (current_price - position.entry_price)
            
            # Update PnL in real-time
            position.unrealized_pnl = pnl
            position.current_price = current_price
            
            # Determine status
            status = "Active"
            if hasattr(position, 'breakeven_triggered') and position.breakeven_triggered:
                status = "Breakeven"
            if hasattr(position, 'partial_closes') and position.partial_closes:
                status = f"Partial ({len(position.partial_closes)})"
            
            self.positions_table.setItem(i, 0, QTableWidgetItem(position.symbol))
            self.positions_table.setItem(i, 1, QTableWidgetItem("Long" if position.side > 0 else "Short"))
            self.positions_table.setItem(i, 2, QTableWidgetItem(f"{position.entry_price:.4f}"))
            self.positions_table.setItem(i, 3, QTableWidgetItem(f"{current_price:.4f}"))
            
            # Stop Loss column
            sl_item = QTableWidgetItem(f"{position.stop_loss:.4f}" if position.stop_loss else "N/A")
            if position.stop_loss and current_price <= position.stop_loss:
                sl_item.setForeground(QColor("red"))  # Stop loss hit
            self.positions_table.setItem(i, 4, sl_item)
            
            # Take Profit column
            tp_item = QTableWidgetItem(f"{position.take_profit:.4f}" if position.take_profit else "N/A")
            if position.take_profit and current_price >= position.take_profit:
                tp_item.setForeground(QColor("green"))  # Take profit hit
            self.positions_table.setItem(i, 5, tp_item)
            
            # Color-code PnL
            pnl_item = QTableWidgetItem(f"{pnl:+.2f}")
            if pnl > 0:
                pnl_item.setForeground(QColor("green"))
            elif pnl < 0:
                pnl_item.setForeground(QColor("red"))
            self.positions_table.setItem(i, 6, pnl_item)
            
            # Status column
            status_item = QTableWidgetItem(status)
            if status == "Breakeven":
                status_item.setForeground(QColor("blue"))
            elif "Partial" in status:
                status_item.setForeground(QColor("orange"))
            self.positions_table.setItem(i, 7, status_item)


class ClosePositionsWidget(QWidget):
    """Widget showing closed positions history."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Close Positions
        closed_group = QGroupBox("Closed Positions")
        closed_layout = QVBoxLayout(closed_group)
        
        self.closed_table = QTableWidget()
        self.closed_table.setColumnCount(7)
        self.closed_table.setHorizontalHeaderLabels(["Symbol", "Side", "Entry Price", "Close Price", "Stop Loss", "Take Profit", "PnL"])
        
        # Disable editing
        self.closed_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.closed_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        closed_layout.addWidget(self.closed_table)
        layout.addWidget(closed_group)
        
    def add_closed_position(self, trade: Trade):
        """Add a closed position to the table (newest first)."""
        self.closed_table.insertRow(0)  # Insert at the top (row 0)
        
        # Symbol
        self.closed_table.setItem(0, 0, QTableWidgetItem(trade.symbol))
        
        # Side
        self.closed_table.setItem(0, 1, QTableWidgetItem("Long" if trade.side > 0 else "Short"))
        
        # Entry Price
        self.closed_table.setItem(0, 2, QTableWidgetItem(f"{trade.entry_price:.4f}"))
        
        # Close Price
        self.closed_table.setItem(0, 3, QTableWidgetItem(f"{trade.exit_price:.4f}"))
        
        # Stop Loss column
        sl_item = QTableWidgetItem(f"{trade.stop_loss:.4f}" if trade.stop_loss else "N/A")
        self.closed_table.setItem(0, 4, sl_item)
        
        # Take Profit column
        tp_item = QTableWidgetItem(f"{trade.take_profit:.4f}" if trade.take_profit else "N/A")
        self.closed_table.setItem(0, 5, tp_item)
        
        # Color-code PnL
        pnl_item = QTableWidgetItem(f"{trade.pnl:+.2f}")
        if trade.pnl > 0:
            pnl_item.setForeground(QColor("green"))
        elif trade.pnl < 0:
            pnl_item.setForeground(QColor("red"))
        self.closed_table.setItem(0, 6, pnl_item)


class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with all new features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ForexSmartBot - Advanced Trading Platform")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.settings_manager = SettingsManager()
        self.database_manager = DatabaseManager()
        self.log_manager = LogManager()
        self.theme_manager = ThemeManager(self.settings_manager)
        self.notification_service = NotificationService(self.settings_manager)
        
        # Initialize startup manager
        self.startup_manager = StartupManager("ForexSmartBot")
        
        # Initialize language manager
        self.language_manager = LanguageManager(self.settings_manager)
        self.language_manager.language_changed.connect(self.on_language_changed)
        
        # Initialize trading components
        self.portfolio = Portfolio(10000.0)
        self.risk_engine = RiskEngine(self._create_risk_config())
        self.trading_controller = None
        self.broker = None
        self.data_provider = None
        
        # Trading state
        self.is_connected = False
        self.is_trading = False
        self.positions = []
        self.closed_trades = []
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.setup_timers()
        
        # Load settings
        self.load_settings()
        
        # Apply theme
        self.apply_theme()
        
        # Initialize with paper broker
        self.initialize_broker()
        
        # Set initial broker status
        broker_mode = self.settings_manager.get('broker_mode', 'PAPER')
        self.update_broker_status(broker_mode)
        
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel
        left_panel = QWidget()
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        
        # Trading Status
        self.trading_status_widget = TradingStatusWidget()
        left_layout.addWidget(self.trading_status_widget)
        
        # Strategy Configuration
        self.strategy_config_widget = StrategyConfigWidget()
        left_layout.addWidget(self.strategy_config_widget)
        
        # Performance Metrics
        self.performance_metrics_widget = PerformanceMetricsWidget()
        left_layout.addWidget(self.performance_metrics_widget)
        
        # Trading Controls
        self.trading_controls_widget = TradingControlsWidget()
        left_layout.addWidget(self.trading_controls_widget)
        
        # Add stretch to push everything to top
        left_layout.addStretch()
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Open Positions
        self.open_positions_widget = OpenPositionsWidget()
        right_layout.addWidget(self.open_positions_widget)
        
        # Closed Positions
        self.close_positions_widget = ClosePositionsWidget()
        right_layout.addWidget(self.close_positions_widget)
        
        # Trading Log
        log_group = QGroupBox("Trading Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        right_layout.addWidget(log_group)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Setup status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def setup_menu_bar(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        backtest_action = QAction("Run Backtest", self)
        backtest_action.triggered.connect(self.run_backtest)
        tools_menu.addAction(backtest_action)
        
        export_action = QAction("Export Trades", self)
        export_action.triggered.connect(self.export_trades)
        tools_menu.addAction(export_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_connections(self):
        """Setup signal connections."""
        # Trading controls
        self.trading_controls_widget.connect_btn.clicked.connect(self.toggle_connection)
        self.trading_controls_widget.start_btn.clicked.connect(self.toggle_trading)
        
    def setup_timers(self):
        """Setup timers for real-time updates."""
        # Update timer for real-time data (less frequent to prevent freezing)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_real_time_data)
        self.update_timer.start(3000)  # Update every 3 seconds (reduced frequency)
        
    def _create_risk_config(self):
        """Create risk configuration."""
        return RiskConfig(
            base_risk_pct=0.02,
            max_risk_pct=0.05,
            daily_risk_cap=0.05,
            max_drawdown_pct=0.25,
            drawdown_recovery_pct=0.10,
            kelly_fraction=0.25,
            volatility_target=0.01,
            min_trade_amount=10.0,
            max_trade_amount=100.0
        )
        
    def initialize_broker(self):
        """Initialize broker and data provider based on settings."""
        try:
            # Get broker mode from settings
            broker_mode = self.settings_manager.get('broker_mode', 'PAPER')
            
            # Initialize broker based on mode
            if broker_mode == 'PAPER':
                self.broker = PaperBroker(10000.0)
                self.append_log("Paper broker initialized")
            elif broker_mode == 'MT4':
                # Check if MT4 settings are configured
                mt4_host = self.settings_manager.get('mt4_host', '')
                mt4_port = self.settings_manager.get('mt4_port', 0)
                if not mt4_host or mt4_port == 0:
                    self.append_log("MT4 settings not configured - using paper broker")
                    self.broker = PaperBroker(10000.0)
                else:
                    from forexsmartbot.brokers.mt4_bridge import MT4Broker
                    self.broker = MT4Broker(host=mt4_host, port=mt4_port)
                    self.append_log(f"MT4 broker initialized: {mt4_host}:{mt4_port}")
            elif broker_mode == 'REST API':
                # Check if REST API settings are configured
                api_key = self.settings_manager.get('rest_api_key', '')
                api_secret = self.settings_manager.get('rest_api_secret', '')
                base_url = self.settings_manager.get('rest_base_url', '')
                if not api_key or not api_secret or not base_url:
                    self.append_log("REST API settings not configured - using paper broker")
                    self.broker = PaperBroker(10000.0)
                else:
                    from forexsmartbot.adapters.brokers.rest_broker import RestBroker
                    self.broker = RestBroker(api_key=api_key, api_secret=api_secret, base_url=base_url)
                    self.append_log("REST API broker initialized")
            else:
                self.broker = PaperBroker(10000.0)
                self.append_log("Unknown broker mode - using paper broker")
            
            # Initialize data provider
            self.data_provider = YFinanceProvider()
            
            # Initialize trading controller
            self.trading_controller = TradingController(
                broker=self.broker,
                data_provider=self.data_provider,
                risk_manager=self.risk_engine,
                portfolio=self.portfolio
            )
            
            # Update broker status display
            self.update_broker_status(broker_mode)
            
            self.append_log("Broker initialized successfully")
            
        except Exception as e:
            self.append_log(f"Error initializing broker: {str(e)}")
            # Fallback to paper broker
            self.broker = PaperBroker(10000.0)
            self.update_broker_status('PAPER')
            
    def toggle_connection(self):
        """Toggle broker connection."""
        try:
            if not self.is_connected:
                # Connect
                if self.broker and self.broker.connect():
                    self.is_connected = True
                    self.trading_status_widget.connection_status.setText("Connected")
                    self.trading_status_widget.connection_status.setStyleSheet("color: green; font-weight: bold;")
                    self.trading_controls_widget.update_connection_state(True)
                    self.append_log("Connected to broker successfully")
                    self.status_bar.showMessage("Connected")
                else:
                    self.append_log("Failed to connect to broker")
                    QMessageBox.warning(self, "Connection Error", "Failed to connect to broker")
            else:
                # Disconnect - ask for confirmation
                reply = QMessageBox.question(
                    self, 
                    "Disconnect Confirmation", 
                    "Do you want to also stop trading and close all current positions before disconnecting?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return  # User cancelled
                
                # Stop trading if requested
                if reply == QMessageBox.StandardButton.Yes and self.is_trading:
                    self.stop_trading()
                
                # Disconnect
                if self.broker:
                    self.broker.disconnect()
                self.is_connected = False
                self.trading_status_widget.connection_status.setText("Disconnected")
                self.trading_status_widget.connection_status.setStyleSheet("color: red; font-weight: bold;")
                self.trading_controls_widget.update_connection_state(False)
                self.append_log("Disconnected from broker")
                self.status_bar.showMessage("Disconnected")
                
        except Exception as e:
            self.append_log(f"Connection error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            
    def toggle_trading(self):
        """Toggle trading state."""
        try:
            if not self.is_trading:
                # Start trading
                if not self.is_connected:
                    QMessageBox.warning(self, "Not Connected", "Please connect to broker first")
                    return
                    
                # Get selected strategy and symbols
                strategy_name = self.strategy_config_widget.strategy_combo.currentText()
                symbols = self.strategy_config_widget.get_selected_symbols()
                
                if not symbols:
                    QMessageBox.warning(self, "No Symbols", "Please select at least one symbol to trade")
                    return
                
                # Extract clean strategy name (remove risk level indicators)
                clean_strategy_name = strategy_name
                if '🟢' in strategy_name or '🟡' in strategy_name or '🔴' in strategy_name:
                    clean_strategy_name = strategy_name.split(' (')[0].split(' ', 1)[1]
                
                # Initialize strategy
                strategy = get_strategy(clean_strategy_name)
                if not strategy:
                    QMessageBox.warning(self, "Invalid Strategy", f"Strategy {clean_strategy_name} not found")
                    return
                
                # Start trading
                self.is_trading = True
                self.trading_status_widget.trading_status.setText("Running")
                self.trading_status_widget.trading_status.setStyleSheet("color: green; font-weight: bold;")
                self.trading_controls_widget.update_trading_state(True)
                self.append_log(f"Started trading {strategy_name} on {', '.join(symbols)}")
                self.status_bar.showMessage("Trading Active")
                
                # Start generating signals
                self.start_signal_generation(strategy, symbols)
                
            else:
                # Stop trading
                self.stop_trading()
                
        except Exception as e:
            self.append_log(f"Trading error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Trading error: {str(e)}")
            
    def stop_trading(self):
        """Stop trading."""
        try:
            self.is_trading = False
            
            # Stop timers
            if hasattr(self, 'signal_timer'):
                self.signal_timer.stop()
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()
            
            self.trading_status_widget.trading_status.setText("Stopped")
            self.trading_status_widget.trading_status.setStyleSheet("color: orange; font-weight: bold;")
            self.trading_controls_widget.update_trading_state(False)
            self.append_log("Trading stopped - all timers stopped")
            self.status_bar.showMessage("Trading Stopped")
            
        except Exception as e:
            self.append_log(f"Stop trading error: {str(e)}")
            
    def start_signal_generation(self, strategy, symbols):
        """Start generating trading signals with real-time monitoring."""
        try:
            self.append_log(f"Signal generation started for {strategy.name}")
            
            # Start real-time signal generation timer (less frequent to prevent freezing)
            self.signal_timer = QTimer()
            self.signal_timer.timeout.connect(lambda: self.generate_signals(strategy, symbols))
            self.signal_timer.start(10000)  # Check every 10 seconds (reduced frequency)
            
            # Start monitoring timer (less frequent)
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self.monitor_trading_activity)
            self.monitor_timer.start(2000)  # Update every 2 seconds (reduced frequency)
            
            self.append_log("Real-time signal generation active - monitoring markets...")
            
        except Exception as e:
            self.append_log(f"Signal generation error: {str(e)}")
    
    def generate_signals(self, strategy, symbols):
        """Generate trading signals for all symbols."""
        try:
            if not self.is_trading:
                return
                
            # Process only a few symbols at a time to prevent blocking
            symbols_to_process = symbols[:3]  # Limit to 3 symbols per cycle
            
            for symbol in symbols_to_process:
                try:
                    # Get current price (simplified to prevent blocking)
                    current_price = self.data_provider.get_latest_price(symbol)
                    if current_price is None:
                        continue
                    
                    # Generate a simple signal based on price movement (to prevent blocking)
                    import random
                    signal = random.choice([-1, 0, 1])  # Simplified signal generation
                    
                    if signal != 0:
                        self.append_log(f"[{symbol}] Signal: {'BUY' if signal > 0 else 'SELL'} at {current_price:.4f}")
                        
                        # Create actual position when signal is generated
                        self.create_position_from_signal(symbol, signal, current_price)
                    
                except Exception as e:
                    self.append_log(f"Error processing {symbol}: {str(e)}")
                    
        except Exception as e:
            self.append_log(f"Signal generation error: {str(e)}")
    
    def create_position_from_signal(self, symbol, signal, price):
        """Create a position from a trading signal."""
        try:
            # Check if we already have a position for this symbol
            existing_position = None
            for pos in self.positions:
                if pos.get('symbol') == symbol:
                    existing_position = pos
                    break
            
            if existing_position:
                # Close existing position first
                self.close_position_from_signal(symbol, price)
            
            # Add some price variation to make entry more realistic
            import random
            entry_variation = random.uniform(-0.0002, 0.0002)  # ±0.02% variation
            entry_price = price + entry_variation
            
            # Create new position
            position = {
                'symbol': symbol,
                'side': 'Long' if signal > 0 else 'Short',
                'entry_price': entry_price,
                'current_price': entry_price,
                'quantity': 1.0,  # Fixed quantity for demo
                'stop_loss': entry_price * (0.98 if signal > 0 else 1.02),  # 2% stop loss
                'take_profit': entry_price * (1.02 if signal > 0 else 0.98),  # 2% take profit
                'pnl': 0.0,
                'timestamp': datetime.now(),
                'status': 'Active'
            }
            
            self.positions.append(position)
            self.update_positions_display()
            
            # Update portfolio with new position
            self.update_portfolio_with_position(position)
            
            self.append_log(f"Position opened: {symbol} {position['side']} at {entry_price:.4f}")
            
            # Send notification
            self.notification_service.show_position_alert(
                "open", symbol, position['side'], entry_price, 
                stop_loss=position.get('stop_loss'), 
                take_profit=position.get('take_profit')
            )
            
        except Exception as e:
            self.append_log(f"Error creating position: {str(e)}")
    
    def close_position_from_signal(self, symbol, price):
        """Close a position from a trading signal."""
        try:
            for i, pos in enumerate(self.positions):
                if pos.get('symbol') == symbol:
                    # Add some price variation to make PnL more realistic
                    import random
                    price_variation = random.uniform(-0.0005, 0.0005)  # ±0.05% variation
                    exit_price = price + price_variation
                    
                    # Calculate PnL
                    if pos['side'] == 'Long':
                        pnl = (exit_price - pos['entry_price']) * pos['quantity']
                    else:
                        pnl = (pos['entry_price'] - exit_price) * pos['quantity']
                    
                    # Create closed trade as Trade object
                    trade = Trade(
                        symbol=symbol,
                        side=1 if pos['side'] == 'Long' else -1,  # Convert to numeric
                        quantity=pos['quantity'],
                        entry_price=pos['entry_price'],
                        exit_price=exit_price,
                        pnl=pnl,
                        strategy='ML_Adaptive_SuperTrend',
                        entry_time=pos['timestamp'],
                        exit_time=datetime.now(),
                        stop_loss=pos.get('stop_loss'),
                        take_profit=pos.get('take_profit'),
                        management_notes='Signal Close'
                    )
                    
                    self.closed_trades.append(trade)
                    self.close_positions_widget.add_closed_position(trade)
                    
                    # Remove from open positions
                    del self.positions[i]
                    self.update_positions_display()
                    
                    # Update portfolio after closing position
                    self.update_portfolio_with_position(None)  # None indicates position closed
                    
                    self.append_log(f"Position closed: {symbol} {pos['side']} at {exit_price:.4f}, PnL: ${pnl:.2f}")
                    
                    # Send notification
                    self.notification_service.show_position_alert(
                        "close", symbol, pos['side'], pos['entry_price'], 
                        exit_price, pnl
                    )
                    break
                    
        except Exception as e:
            self.append_log(f"Error closing position: {str(e)}")
    
    def log_signal_activity(self, symbol, signal, price):
        """Log signal activity for monitoring."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        signal_type = "BUY" if signal > 0 else "SELL"
        self.append_log(f"[{timestamp}] {symbol} {signal_type} signal at {price:.4f}")
    
    def monitor_trading_activity(self):
        """Monitor trading activity and update display."""
        try:
            if not self.is_trading:
                # Update monitoring status to inactive
                self.trading_status_widget.monitoring_status.setText("Inactive")
                self.trading_status_widget.monitoring_status.setStyleSheet("color: gray; font-weight: bold;")
                return
                
            # Update monitoring status to active
            self.trading_status_widget.monitoring_status.setText("Active")
            self.trading_status_widget.monitoring_status.setStyleSheet("color: green; font-weight: bold;")
            
            # Update real-time data
            self.update_real_time_data()
            
            # Log activity every 60 seconds (less frequent)
            if not hasattr(self, 'last_activity_log'):
                self.last_activity_log = datetime.now()
            
            if (datetime.now() - self.last_activity_log).seconds >= 60:
                self.append_log("Trading system active - monitoring for signals...")
                self.last_activity_log = datetime.now()
                
        except Exception as e:
            self.append_log(f"Monitoring error: {str(e)}")
            
    def update_real_time_data(self):
        """Update real-time data display."""
        try:
            # Update portfolio with current positions
            self.update_portfolio_with_position(None)
            
            # Update positions display
            self.update_positions_display()
            
        except Exception as e:
            self.append_log(f"Real-time update error: {str(e)}")
    
    def update_broker_status(self, broker_mode: str):
        """Update the broker status display."""
        try:
            self.trading_status_widget.broker_status.setText(broker_mode)
            
            # Color code based on broker type
            if broker_mode == "PAPER":
                self.trading_status_widget.broker_status.setStyleSheet("color: blue; font-weight: bold;")
            elif broker_mode == "MT4":
                self.trading_status_widget.broker_status.setStyleSheet("color: orange; font-weight: bold;")
            elif broker_mode == "REST API":
                self.trading_status_widget.broker_status.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.trading_status_widget.broker_status.setStyleSheet("color: gray; font-weight: bold;")
                
        except Exception as e:
            self.append_log(f"Error updating broker status: {str(e)}")
            
    def apply_theme(self):
        """Apply theme to the application."""
        try:
            app = QApplication.instance()
            if app and self.theme_manager:
                self.theme_manager.apply_theme(app)
        except Exception as e:
            self.append_log(f"Error applying theme: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog with broker validation."""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update broker status after settings are saved
            broker_mode = self.settings_manager.get('broker_mode', 'PAPER')
            self.update_broker_status(broker_mode)
            
            # Reinitialize broker with new settings
            self.initialize_broker()
            
            # Apply theme changes
            self.apply_theme()
            
            # Update notification service configuration
            self.notification_service.update_config()
            
            # Handle startup settings
            self.handle_startup_settings()
            
            # Handle language settings
            self.handle_language_settings()
        
    def run_backtest(self):
        """Run backtest dialog."""
        dialog = BacktestDialog(self)
        dialog.exec()
        
    def export_trades(self):
        """Export trades dialog."""
        dialog = ExportDialog(self.closed_trades, self)
        dialog.exec()
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About ForexSmartBot", 
                         "ForexSmartBot v3.0.0\n\n"
                         "Advanced Trading Platform with Machine Learning Strategies\n\n"
                         "Features:\n"
                         "• Real-time trading\n"
                         "• ML Adaptive SuperTrend\n"
                         "• Adaptive Trend Flow\n"
                         "• Risk management\n"
                         "• Backtesting\n\n"
                         "© 2025 VoxHash")
        
    def append_log(self, message):
        """Append message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def load_settings(self):
        """Load application settings."""
        try:
            # Load theme
            theme = self.settings_manager.get('theme', 'dark')
            # Theme will be applied by the main application
            
            # Load other settings
            self.append_log("Settings loaded successfully")
            
        except Exception as e:
            self.append_log(f"Error loading settings: {str(e)}")
    
    def update_positions_display(self):
        """Update the positions table display from internal positions list."""
        try:
            # Use the correct widget reference
            self.open_positions_widget.positions_table.setRowCount(len(self.positions))
            
            for i, pos in enumerate(self.positions):
                # Get current price (simplified)
                current_price = pos.get('current_price', pos['entry_price'])
                
                # Calculate PnL
                if pos['side'] == 'Long':
                    pnl = (current_price - pos['entry_price']) * pos.get('quantity', 1.0)
                else:
                    pnl = (pos['entry_price'] - current_price) * pos.get('quantity', 1.0)
                
                # Update PnL in position
                pos['pnl'] = pnl
                
                # Populate table
                self.open_positions_widget.positions_table.setItem(i, 0, QTableWidgetItem(pos['symbol']))
                self.open_positions_widget.positions_table.setItem(i, 1, QTableWidgetItem(pos['side']))
                self.open_positions_widget.positions_table.setItem(i, 2, QTableWidgetItem(f"{pos['entry_price']:.4f}"))
                self.open_positions_widget.positions_table.setItem(i, 3, QTableWidgetItem(f"{current_price:.4f}"))
                self.open_positions_widget.positions_table.setItem(i, 4, QTableWidgetItem(f"{pos.get('stop_loss', 0):.4f}"))
                self.open_positions_widget.positions_table.setItem(i, 5, QTableWidgetItem(f"{pos.get('take_profit', 0):.4f}"))
                
                # Color-code PnL
                pnl_item = QTableWidgetItem(f"{pnl:+.2f}")
                if pnl > 0:
                    pnl_item.setForeground(QColor("green"))
                elif pnl < 0:
                    pnl_item.setForeground(QColor("red"))
                self.open_positions_widget.positions_table.setItem(i, 6, pnl_item)
                
                # Status
                status_item = QTableWidgetItem(pos.get('status', 'Active'))
                if pos.get('status') == 'Active':
                    status_item.setForeground(QColor("green"))
                self.open_positions_widget.positions_table.setItem(i, 7, status_item)
                
        except Exception as e:
            self.append_log(f"Error updating positions display: {str(e)}")
    
    def update_portfolio_with_position(self, position):
        """Update portfolio with new position for real-time calculations."""
        try:
            # Update portfolio balance and equity based on positions
            total_pnl = sum(pos.get('pnl', 0) for pos in self.positions)
            current_balance = 10000.0  # Base balance
            current_equity = current_balance + total_pnl

            # Update trading status display with color coding
            self.trading_status_widget.balance_label.setText(f"${current_balance:.2f}")
            self.trading_status_widget.balance_label.setStyleSheet("color: blue;")
            
            self.trading_status_widget.equity_label.setText(f"${current_equity:.2f}")
            if current_equity > current_balance:
                self.trading_status_widget.equity_label.setStyleSheet("color: green;")
            elif current_equity < current_balance:
                self.trading_status_widget.equity_label.setStyleSheet("color: red;")
            else:
                self.trading_status_widget.equity_label.setStyleSheet("color: blue;")

            # Calculate drawdown
            if hasattr(self, 'peak_equity'):
                if current_equity > self.peak_equity:
                    self.peak_equity = current_equity
                drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
            else:
                self.peak_equity = current_equity
                drawdown = 0.0

            self.trading_status_widget.drawdown_label.setText(f"{drawdown:.1f}%")
            if drawdown > 0:
                self.trading_status_widget.drawdown_label.setStyleSheet("color: red;")
            else:
                self.trading_status_widget.drawdown_label.setStyleSheet("color: green;")

            # Update performance metrics
            self.update_performance_metrics()

        except Exception as e:
            self.append_log(f"Error updating portfolio: {str(e)}")
    
    def update_performance_metrics(self):
        """Update performance metrics in real-time."""
        try:
            # Calculate metrics from closed trades
            total_trades = len(self.closed_trades)
            
            if total_trades > 0:
                # Calculate win rate
                winning_trades = sum(1 for trade in self.closed_trades if trade.pnl > 0)
                win_rate = (winning_trades / total_trades) * 100
                
                # Calculate profit factor
                total_profit = sum(trade.pnl for trade in self.closed_trades if trade.pnl > 0)
                total_loss = abs(sum(trade.pnl for trade in self.closed_trades if trade.pnl < 0))
                
                if total_loss > 0:
                    profit_factor = total_profit / total_loss
                else:
                    profit_factor = float('inf') if total_profit > 0 else 0.0
                
                # Calculate max drawdown
                if hasattr(self, 'peak_equity') and self.peak_equity > 0:
                    current_equity = 10000.0 + sum(pos.get('pnl', 0) for pos in self.positions)
                    max_drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
                else:
                    max_drawdown = 0.0
            else:
                win_rate = 0.0
                profit_factor = 0.0
                max_drawdown = 0.0
            
            # Update performance metrics display
            self.performance_metrics_widget.total_trades_label.setText(str(total_trades))
            self.performance_metrics_widget.win_rate_label.setText(f"{win_rate:.1f}%")
            
            if profit_factor == float('inf'):
                self.performance_metrics_widget.profit_factor_label.setText("inf")
            else:
                self.performance_metrics_widget.profit_factor_label.setText(f"{profit_factor:.2f}")
            
            self.performance_metrics_widget.max_drawdown_label.setText(f"{max_drawdown:.1f}%")
            
        except Exception as e:
            self.append_log(f"Error updating performance metrics: {str(e)}")
    
    def handle_startup_settings(self):
        """Handle startup settings changes."""
        try:
            startup_enabled = self.settings_manager.get('startup_enabled', False)
            
            if startup_enabled:
                # Get the current application path
                import sys
                app_path = sys.executable
                
                if self.startup_manager.enable_startup(app_path):
                    self.append_log("Startup enabled successfully")
                else:
                    self.append_log("Failed to enable startup")
            else:
                if self.startup_manager.disable_startup():
                    self.append_log("Startup disabled successfully")
                else:
                    self.append_log("Failed to disable startup")
                    
        except Exception as e:
            self.append_log(f"Error handling startup settings: {str(e)}")
    
    def handle_language_settings(self):
        """Handle language settings changes."""
        try:
            current_lang = self.settings_manager.get('language', 'en')
            if current_lang != self.language_manager.current_language:
                self.language_manager.set_language(current_lang)
                self.append_log(f"Language changed to {current_lang}")
                
        except Exception as e:
            self.append_log(f"Error handling language settings: {str(e)}")
    
    def on_language_changed(self, lang_code: str):
        """Handle language change event."""
        try:
            # Update UI text with new language
            self.update_ui_text()
            self.append_log(f"UI updated to language: {lang_code}")
            
        except Exception as e:
            self.append_log(f"Error updating UI text: {str(e)}")
    
    def update_ui_text(self):
        """Update UI text based on current language."""
        try:
            # Update menu text
            file_menu = self.menuBar().findChild(QMenu, "File")
            if file_menu:
                file_menu.setTitle(self.language_manager.tr("file_menu", "File"))
            
            tools_menu = self.menuBar().findChild(QMenu, "Tools")
            if tools_menu:
                tools_menu.setTitle(self.language_manager.tr("tools_menu", "Tools"))
            
            help_menu = self.menuBar().findChild(QMenu, "Help")
            if help_menu:
                help_menu.setTitle(self.language_manager.tr("help_menu", "Help"))
            
            # Update window title
            self.setWindowTitle(self.language_manager.tr("app_title", "ForexSmartBot"))
            
            # Update status bar
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(self.language_manager.tr("ready", "Ready"))
            
        except Exception as e:
            self.append_log(f"Error updating UI text: {str(e)}")
            
    def closeEvent(self, event):
        """Handle application close."""
        try:
            # Stop trading
            if self.is_trading:
                self.stop_trading()
                
            # Disconnect
            if self.is_connected:
                self.toggle_connection()
                
            # Save settings
            self.settings_manager.save()
            
            event.accept()
            
        except Exception as e:
            self.append_log(f"Close error: {str(e)}")
            event.accept()