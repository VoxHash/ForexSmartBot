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
    QListWidgetItem, QAbstractItemView, QApplication, QTabWidget
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
from ..adapters.data import YFinanceProvider, CSVProvider, MultiProvider, AlphaVantageProvider, OANDAProvider
from .settings_dialog import SettingsDialog
from .backtest_dialog import BacktestDialog
from .export_dialog import ExportDialog
from .theme import ThemeManager
from ..services.notification_service import NotificationService
from ..services.startup_manager import StartupManager
from ..services.language_manager import LanguageManager


class TradingStatusWidget(QWidget):
    """Widget showing trading status with real-time updates."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status indicators
        status_group = QGroupBox(self.tr("trading_status", "Trading Status"))
        status_layout = QGridLayout(status_group)
        
        # Broker status
        self.broker_status = QLabel(self.tr("paper", "PAPER"))
        self.broker_status.setStyleSheet("color: blue; font-weight: bold;")
        status_layout.addWidget(QLabel(f"{self.tr('broker', 'Broker')}:"), 0, 0)
        status_layout.addWidget(self.broker_status, 0, 1)
        
        # Connection status
        self.connection_status = QLabel(self.tr("disconnected", "Disconnected"))
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(QLabel(f"{self.tr('connection', 'Connection')}:"), 1, 0)
        status_layout.addWidget(self.connection_status, 1, 1)
        
        # Trading status
        self.trading_status = QLabel(self.tr("stopped", "Stopped"))
        self.trading_status.setStyleSheet("color: orange; font-weight: bold;")
        status_layout.addWidget(QLabel(f"{self.tr('trading', 'Trading')}:"), 2, 0)
        status_layout.addWidget(self.trading_status, 2, 1)
        
        # Balance (real-time)
        self.balance_label = QLabel("$0.00")
        self.balance_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        status_layout.addWidget(QLabel(f"{self.tr('balance', 'Balance')}:"), 3, 0)
        status_layout.addWidget(self.balance_label, 3, 1)
        
        # Equity (real-time)
        self.equity_label = QLabel("$0.00")
        self.equity_label.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        status_layout.addWidget(QLabel(f"{self.tr('equity', 'Equity')}:"), 4, 0)
        status_layout.addWidget(self.equity_label, 4, 1)
        
        # Drawdown (real-time)
        self.drawdown_label = QLabel("0.0%")
        self.drawdown_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(QLabel(f"{self.tr('drawdown', 'Drawdown')}:"), 5, 0)
        status_layout.addWidget(self.drawdown_label, 5, 1)
        
        # Monitoring status (real-time)
        self.monitoring_status = QLabel(self.tr("inactive", "Inactive"))
        self.monitoring_status.setStyleSheet("color: gray; font-weight: bold;")
        status_layout.addWidget(QLabel(f"{self.tr('monitoring', 'Monitoring')}:"), 6, 0)
        status_layout.addWidget(self.monitoring_status, 6, 1)
        
        layout.addWidget(status_group)
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            status_group = self.findChild(QGroupBox)
            if status_group:
                status_group.setTitle(language_manager.tr("trading_status", "Trading Status"))
            
            # Update labels
            labels = self.findChildren(QLabel)
            for label in labels:
                text = label.text()
                if text == "Broker:":
                    label.setText(language_manager.tr("broker", "Broker:"))
                elif text == "Connection:":
                    label.setText(language_manager.tr("connection", "Connection:"))
                elif text == "Trading:":
                    label.setText(language_manager.tr("trading", "Trading:"))
                elif text == "Balance:":
                    label.setText(language_manager.tr("balance", "Balance:"))
                elif text == "Equity:":
                    label.setText(language_manager.tr("equity", "Equity:"))
                elif text == "Drawdown:":
                    label.setText(language_manager.tr("drawdown", "Drawdown:"))
                elif text == "Monitoring:":
                    label.setText(language_manager.tr("monitoring", "Monitoring:"))
                # Update status values
                elif text == "PAPER":
                    label.setText(language_manager.tr("paper", "PAPER"))
                elif text == "Disconnected":
                    label.setText(language_manager.tr("disconnected", "Disconnected"))
                elif text == "Stopped":
                    label.setText(language_manager.tr("stopped", "Stopped"))
                elif text == "Inactive":
                    label.setText(language_manager.tr("inactive", "Inactive"))
        except Exception as e:
            print(f"Error updating TradingStatusWidget language: {e}")


class StrategyConfigWidget(QWidget):
    """Widget for strategy configuration with multi-symbol selection."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Strategy Configuration
        strategy_group = QGroupBox(self.tr("strategy_config", "Strategy Configuration"))
        strategy_layout = QFormLayout(strategy_group)
        
        # Strategy selection - Load all strategies dynamically from module
        self.strategy_combo = QComboBox()
        
        # Get all available strategies from the strategies module
        from ..strategies import STRATEGIES, RISK_LEVELS
        
        # Organize strategies by risk level
        low_risk_strategies = RISK_LEVELS.get('Low_Risk', [])
        medium_risk_strategies = RISK_LEVELS.get('Medium_Risk', [])
        high_risk_strategies = RISK_LEVELS.get('High_Risk', [])
        
        # Get all strategies and categorize them
        all_strategies = list(STRATEGIES.keys())
        
        # Add ML strategies to appropriate risk levels
        ml_strategies = ['LSTM_Strategy', 'SVM_Strategy', 'Ensemble_ML_Strategy', 
                        'Transformer_Strategy', 'RL_Strategy', 'Multi_Timeframe']
        for ml_strategy in ml_strategies:
            if ml_strategy in all_strategies and ml_strategy not in high_risk_strategies:
                high_risk_strategies.append(ml_strategy)
        
        # Add strategies with risk level indicators
        for strategy in low_risk_strategies:
            if strategy in all_strategies:
                self.strategy_combo.addItem(f"🟢 {strategy} ({self.tr('low_risk', 'Low Risk')})")
        for strategy in medium_risk_strategies:
            if strategy in all_strategies:
                self.strategy_combo.addItem(f"🟡 {strategy} ({self.tr('medium_risk', 'Medium Risk')})")
        for strategy in high_risk_strategies:
            if strategy in all_strategies:
                self.strategy_combo.addItem(f"🔴 {strategy} ({self.tr('high_risk', 'High Risk')})")
        
        # Add any remaining strategies that weren't categorized
        for strategy in all_strategies:
            if strategy not in low_risk_strategies + medium_risk_strategies + high_risk_strategies:
                self.strategy_combo.addItem(f"⚪ {strategy}")
            
        strategy_layout.addRow(f"{self.tr('strategy', 'Strategy')}:", self.strategy_combo)
        
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
        best_pairs = ["GBPUSD", "GBPJPY", "EURUSD", "CADJPY", "USDCHF", "AUDNZD"]
        for i in range(self.symbols_list.count()):
            item = self.symbols_list.item(i)
            if item.text() in best_pairs:
                item.setSelected(True)
        
        symbols_layout.addWidget(self.symbols_list)
        strategy_layout.addRow(f"{self.tr('symbols', 'Symbols')}:", symbols_group)
        
        # Leverage selection
        self.leverage_combo = QComboBox()
        leverage_options = [
            f"1:1 ({self.tr('no_leverage', 'No Leverage')})",
            f"1:5 ({self.tr('conservative', 'Conservative')})",
            f"1:10 ({self.tr('moderate', 'Moderate')})", 
            f"1:20 ({self.tr('aggressive', 'Aggressive')})",
            f"1:50 ({self.tr('high_risk', 'High Risk')})",
            f"1:100 ({self.tr('very_high_risk', 'Very High Risk')})",
            f"1:200 ({self.tr('maximum_risk', 'Maximum Risk')})",
            f"1:300 ({self.tr('extreme_risk', 'Extreme Risk')})",
            f"1:500 ({self.tr('ultra_high_risk', 'Ultra High Risk')})",
            f"1:1000 ({self.tr('maximum_leverage', 'Maximum Leverage')})",
            f"1:2000 ({self.tr('extreme_leverage', 'Extreme Leverage')})"
        ]
        self.leverage_combo.addItems(leverage_options)
        self.leverage_combo.setCurrentText(f"1:10 ({self.tr('moderate', 'Moderate')})")
        strategy_layout.addRow(f"{self.tr('leverage', 'Leverage')}:", self.leverage_combo)
        
        layout.addWidget(strategy_group)
        
    def get_selected_symbols(self):
        """Get selected symbols."""
        selected_items = self.symbols_list.selectedItems()
        return [item.text() for item in selected_items] if selected_items else ["EURUSD"]
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            strategy_group = self.findChild(QGroupBox)
            if strategy_group:
                strategy_group.setTitle(language_manager.tr("strategy_config", "Strategy Configuration"))
            
            # Update form labels
            form_layout = strategy_group.layout()
            if form_layout:
                for i in range(form_layout.rowCount()):
                    label_item = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                    if label_item and label_item.widget():
                        label = label_item.widget()
                        text = label.text()
                        if text == "Strategy:":
                            label.setText(language_manager.tr("strategy", "Strategy:"))
                        elif text == "Symbols:":
                            label.setText(language_manager.tr("symbols", "Symbols:"))
                        elif text == "Leverage:":
                            label.setText(language_manager.tr("leverage", "Leverage:"))
        except Exception as e:
            print(f"Error updating StrategyConfigWidget language: {e}")


class PerformanceMetricsWidget(QWidget):
    """Widget showing performance metrics with real-time updates."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Performance metrics
        metrics_group = QGroupBox(self.tr("performance_metrics", "Performance Metrics"))
        metrics_layout = QGridLayout(metrics_group)
        
        # Total Trades (real-time)
        self.total_trades_label = QLabel("0")
        self.total_trades_label.setStyleSheet("font-weight: bold; color: blue;")
        metrics_layout.addWidget(QLabel(f"{self.tr('total_trades', 'Total Trades')}:"), 0, 0)
        metrics_layout.addWidget(self.total_trades_label, 0, 1)
        
        # Win Rate (real-time)
        self.win_rate_label = QLabel("0%")
        self.win_rate_label.setStyleSheet("font-weight: bold; color: green;")
        metrics_layout.addWidget(QLabel(f"{self.tr('win_rate', 'Win Rate')}:"), 1, 0)
        metrics_layout.addWidget(self.win_rate_label, 1, 1)
        
        # Profit Factor (real-time)
        self.profit_factor_label = QLabel("0.00")
        self.profit_factor_label.setStyleSheet("font-weight: bold; color: orange;")
        metrics_layout.addWidget(QLabel(f"{self.tr('profit_factor', 'Profit Factor')}:"), 2, 0)
        metrics_layout.addWidget(self.profit_factor_label, 2, 1)
        
        # Max Drawdown (real-time)
        self.max_drawdown_label = QLabel("0%")
        self.max_drawdown_label.setStyleSheet("font-weight: bold; color: red;")
        metrics_layout.addWidget(QLabel(f"{self.tr('max_drawdown', 'Max Drawdown')}:"), 3, 0)
        metrics_layout.addWidget(self.max_drawdown_label, 3, 1)
        
        layout.addWidget(metrics_group)
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            metrics_group = self.findChild(QGroupBox)
            if metrics_group:
                metrics_group.setTitle(language_manager.tr("performance_metrics", "Performance Metrics"))
            
            # Update labels
            labels = self.findChildren(QLabel)
            for label in labels:
                text = label.text()
                if text == "Total Trades:":
                    label.setText(language_manager.tr("total_trades", "Total Trades:"))
                elif text == "Win Rate:":
                    label.setText(language_manager.tr("win_rate", "Win Rate:"))
                elif text == "Profit Factor:":
                    label.setText(language_manager.tr("profit_factor", "Profit Factor:"))
                elif text == "Max Drawdown:":
                    label.setText(language_manager.tr("max_drawdown", "Max Drawdown:"))
        except Exception as e:
            print(f"Error updating PerformanceMetricsWidget language: {e}")


class TradingControlsWidget(QWidget):
    """Widget for trading controls with proper connect/disconnect and start/stop functionality."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Trading Controls
        controls_group = QGroupBox(self.tr("trading_controls", "Trading Controls"))
        controls_layout = QVBoxLayout(controls_group)
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton(self.tr("connect", "Connect"))
        self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        controls_layout.addWidget(self.connect_btn)
        
        # Start/Stop Trading button
        self.start_btn = QPushButton(self.tr("start_trading", "Start Trading"))
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
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            controls_group = self.findChild(QGroupBox)
            if controls_group:
                controls_group.setTitle(language_manager.tr("trading_controls", "Trading Controls"))
            
            # Update button texts
            if hasattr(self, 'connect_btn'):
                if self.connect_btn.text() in ["Connect", "Disconnect"]:
                    # Don't change button text based on current state
                    pass
                else:
                    self.connect_btn.setText(language_manager.tr("connect", "Connect"))
            
            if hasattr(self, 'start_btn'):
                if self.start_btn.text() in ["Start Trading", "Stop Trading"]:
                    # Don't change button text based on current state
                    pass
                else:
                    self.start_btn.setText(language_manager.tr("start_trading", "Start Trading"))
        except Exception as e:
            print(f"Error updating TradingControlsWidget language: {e}")


class OpenPositionsWidget(QWidget):
    """Widget showing open positions with real-time PnL updates."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Open Positions
        positions_group = QGroupBox(self.tr("open_positions", "Open Positions"))
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(5)
        self.positions_table.setHorizontalHeaderLabels([
            self.tr("symbol", "Symbol"), 
            self.tr("side", "Side"), 
            self.tr("entry_price", "Entry Price"), 
            self.tr("take_profit", "Take Profit"),
            self.tr("stop_loss", "Stop Loss")
        ])
        
        # Disable editing
        self.positions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        positions_layout.addWidget(self.positions_table)
        layout.addWidget(positions_group)
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            positions_group = self.findChild(QGroupBox)
            if positions_group:
                positions_group.setTitle(language_manager.tr("open_positions", "Open Positions"))
            
            # Update table headers
            if hasattr(self, 'positions_table'):
                headers = [
                    language_manager.tr("symbol", "Symbol"),
                    language_manager.tr("side", "Side"),
                    language_manager.tr("entry_price", "Entry Price"),
                    language_manager.tr("take_profit", "Take Profit"),
                    language_manager.tr("stop_loss", "Stop Loss")
                ]
                self.positions_table.setHorizontalHeaderLabels(headers)
        except Exception as e:
            print(f"Error updating OpenPositionsWidget language: {e}")
        
    def update_positions(self, positions: List[Position], current_prices: Dict[str, float]):
        """Update positions table with real-time data and advanced trade management."""
        self.positions_table.setRowCount(len(positions))
        
        for i, position in enumerate(positions):
            current_price = current_prices.get(position.symbol, position.current_price)
            # Calculate unrealized PnL with micro lots
            micro_lots = position.quantity / 1000
            pnl = position.side * micro_lots * 10 * (current_price - position.entry_price)
            
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
            
            # Stop Loss column
            sl_item = QTableWidgetItem(f"{position.stop_loss:.4f}" if position.stop_loss else "N/A")
            if position.stop_loss:
                # For Long: stop loss hit when price goes below stop loss
                # For Short: stop loss hit when price goes above stop loss
                if (position.side > 0 and current_price <= position.stop_loss) or (position.side < 0 and current_price >= position.stop_loss):
                    sl_item.setForeground(QColor("red"))  # Stop loss hit
            self.positions_table.setItem(i, 3, sl_item)
            
            # Take Profit column
            tp_item = QTableWidgetItem(f"{position.take_profit:.4f}" if position.take_profit else "N/A")
            if position.take_profit:
                # For Long: take profit hit when price goes above take profit
                # For Short: take profit hit when price goes below take profit
                if (position.side > 0 and current_price >= position.take_profit) or (position.side < 0 and current_price <= position.take_profit):
                    tp_item.setForeground(QColor("green"))  # Take profit hit
            self.positions_table.setItem(i, 4, tp_item)


class ClosePositionsWidget(QWidget):
    """Widget showing closed positions history."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Close Positions
        closed_group = QGroupBox(self.tr("closed_positions", "Closed Positions"))
        closed_layout = QVBoxLayout(closed_group)
        
        self.closed_table = QTableWidget()
        self.closed_table.setColumnCount(5)
        self.closed_table.setHorizontalHeaderLabels([
            self.tr("symbol", "Symbol"), 
            self.tr("side", "Side"), 
            self.tr("entry_price", "Entry Price"), 
            self.tr("close_price", "Close Price"), 
            self.tr("pnl", "PnL")
        ])
        
        # Disable editing
        self.closed_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.closed_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        closed_layout.addWidget(self.closed_table)
        layout.addWidget(closed_group)
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            closed_group = self.findChild(QGroupBox)
            if closed_group:
                closed_group.setTitle(language_manager.tr("closed_positions", "Closed Positions"))
            
            # Update table headers
            if hasattr(self, 'closed_table'):
                headers = [
                    language_manager.tr("symbol", "Symbol"),
                    language_manager.tr("side", "Side"),
                    language_manager.tr("entry_price", "Entry Price"),
                    language_manager.tr("close_price", "Close Price"),
                    language_manager.tr("pnl", "PnL")
                ]
                self.closed_table.setHorizontalHeaderLabels(headers)
        except Exception as e:
            print(f"Error updating ClosePositionsWidget language: {e}")
        
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
        
        # Color-code PnL
        pnl_item = QTableWidgetItem(f"{trade.pnl:+.2f}")
        if trade.pnl > 0:
            pnl_item.setForeground(QColor("green"))
        elif trade.pnl < 0:
            pnl_item.setForeground(QColor("red"))
        self.closed_table.setItem(0, 4, pnl_item)
    
    def update_language(self, language_manager):
        """Update widget text based on current language."""
        try:
            # Update group box title
            closed_group = self.findChild(QGroupBox)
            if closed_group:
                closed_group.setTitle(language_manager.tr("closed_positions", "Closed Positions"))
            
            # Update table headers
            if hasattr(self, 'closed_table'):
                headers = [
                    language_manager.tr("symbol", "Symbol"),
                    language_manager.tr("side", "Side"),
                    language_manager.tr("entry_price", "Entry Price"),
                    language_manager.tr("close_price", "Close Price"),
                    language_manager.tr("pnl", "PnL")
                ]
                self.closed_table.setHorizontalHeaderLabels(headers)
        except Exception as e:
            print(f"Error updating ClosePositionsWidget language: {e}")


class EnhancedMainWindow(QMainWindow):
    """Enhanced main window with all new features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ForexSmartBot - Advanced Trading Platform")
        
        # Initialize components
        self.settings_manager = SettingsManager()
        
        # Load window size from settings
        window_width = self.settings_manager.get('window_width', 1400)
        window_height = self.settings_manager.get('window_height', 900)
        self.setGeometry(100, 100, window_width, window_height)
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
        
        # Signal cooldown to prevent too frequent signals
        self.signal_cooldown = {}  # symbol -> last_signal_time
        
        # Daily trade counter to track trades per day
        self.daily_trade_count = 0
        self.last_trade_date = None
        
        # Initialize monitoring components (shared instance)
        from ..monitoring.strategy_monitor import StrategyMonitor
        from ..monitoring.performance_tracker import PerformanceTracker
        self.strategy_monitor = StrategyMonitor()
        self.performance_tracker = PerformanceTracker()
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        self.setup_timers()
        
        # Load settings
        self.load_settings()
        
        # Apply theme
        self.apply_theme()
        
        # Handle language settings
        self.handle_language_settings()
        
        # Update UI with current language
        self.update_ui_text()
        
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
        self.trading_status_widget = TradingStatusWidget(language_manager=self.language_manager)
        left_layout.addWidget(self.trading_status_widget)
        
        # Strategy Configuration
        self.strategy_config_widget = StrategyConfigWidget(language_manager=self.language_manager)
        left_layout.addWidget(self.strategy_config_widget)
        
        # Performance Metrics
        self.performance_metrics_widget = PerformanceMetricsWidget(language_manager=self.language_manager)
        left_layout.addWidget(self.performance_metrics_widget)
        
        # Trading Controls
        self.trading_controls_widget = TradingControlsWidget(language_manager=self.language_manager)
        left_layout.addWidget(self.trading_controls_widget)
        
        # Add stretch to push everything to top
        left_layout.addStretch()
        
        # Right panel with tabs for all features
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create tabbed interface for all features
        self.features_tabs = QTabWidget()
        
        # Tab 1: Trading (Positions and Log)
        trading_tab = QWidget()
        trading_tab_layout = QVBoxLayout(trading_tab)
        
        # Open Positions
        self.open_positions_widget = OpenPositionsWidget(language_manager=self.language_manager)
        trading_tab_layout.addWidget(self.open_positions_widget)
        
        # Closed Positions
        self.close_positions_widget = ClosePositionsWidget(language_manager=self.language_manager)
        trading_tab_layout.addWidget(self.close_positions_widget)
        
        # Trading Log
        log_group = QGroupBox(self.language_manager.tr("trading_log", "Trading Log"))
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        trading_tab_layout.addWidget(log_group)
        
        self.features_tabs.addTab(trading_tab, self.language_manager.tr("trading", "Trading"))
        
        # Tab 2: Analytics
        analytics_tab = QWidget()
        analytics_tab_layout = QVBoxLayout(analytics_tab)
        
        # Portfolio Analytics Widget
        try:
            from ..analytics.portfolio_analytics import PortfolioAnalytics
            from ..ui.analytics_widget import PortfolioAnalyticsWidget
            self.portfolio_analytics_widget = PortfolioAnalyticsWidget(self.portfolio, parent=analytics_tab)
            analytics_tab_layout.addWidget(self.portfolio_analytics_widget)
        except ImportError:
            analytics_label = QLabel(self.language_manager.tr("portfolio_analytics", "Portfolio Analytics"))
            analytics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            analytics_tab_layout.addWidget(analytics_label)
        
        self.features_tabs.addTab(analytics_tab, self.language_manager.tr("analytics", "Analytics"))
        
        # Tab 3: Charts
        charts_tab = QWidget()
        charts_tab_layout = QVBoxLayout(charts_tab)
        
        try:
            from ..ui.enhanced_charts import EnhancedChartWidget
            self.enhanced_chart_widget = EnhancedChartWidget(parent=charts_tab)
            # Pass data provider reference if available
            if hasattr(self, 'data_provider') and self.data_provider:
                self.enhanced_chart_widget.data_provider = self.data_provider
            charts_tab_layout.addWidget(self.enhanced_chart_widget)
        except ImportError:
            charts_label = QLabel(self.language_manager.tr("enhanced_charts", "Enhanced Charts"))
            charts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            charts_tab_layout.addWidget(charts_label)
        
        self.features_tabs.addTab(charts_tab, self.language_manager.tr("charts", "Charts"))
        
        # Tab 4: Strategy Builder
        builder_tab = QWidget()
        builder_tab_layout = QVBoxLayout(builder_tab)
        
        builder_label = QLabel(self.language_manager.tr("strategy_builder_info", 
            "Use the menu Tools > Strategy Builder to access the visual strategy builder"))
        builder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        builder_label.setWordWrap(True)
        builder_tab_layout.addWidget(builder_label)
        
        self.features_tabs.addTab(builder_tab, self.language_manager.tr("strategy_builder", "Strategy Builder"))
        
        # Tab 5: Marketplace
        marketplace_tab = QWidget()
        marketplace_tab_layout = QVBoxLayout(marketplace_tab)
        
        marketplace_label = QLabel(self.language_manager.tr("marketplace_info",
            "Use the menu Marketplace to browse and manage strategies"))
        marketplace_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marketplace_label.setWordWrap(True)
        marketplace_tab_layout.addWidget(marketplace_label)
        
        self.features_tabs.addTab(marketplace_tab, self.language_manager.tr("marketplace", "Marketplace"))
        
        # Tab 6: Monitoring
        monitoring_tab = QWidget()
        monitoring_tab_layout = QVBoxLayout(monitoring_tab)
        
        try:
            from ..monitoring.strategy_monitor import StrategyMonitor
            from ..ui.monitoring_widget import StrategyMonitorWidget
            self.strategy_monitor_widget = StrategyMonitorWidget(parent=monitoring_tab)
            monitoring_tab_layout.addWidget(self.strategy_monitor_widget)
        except ImportError:
            monitoring_label = QLabel(self.language_manager.tr("monitoring", "Monitoring"))
            monitoring_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            monitoring_tab_layout.addWidget(monitoring_label)
        
        self.features_tabs.addTab(monitoring_tab, self.language_manager.tr("monitoring", "Monitoring"))
        
        # Tab 7: Cloud
        cloud_tab = QWidget()
        cloud_tab_layout = QVBoxLayout(cloud_tab)
        
        # Get actual values from environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv(override=False)
        monitor_host = os.getenv('REMOTE_MONITOR_HOST', '127.0.0.1')
        monitor_port = os.getenv('REMOTE_MONITOR_PORT', '8080')
        api_host = os.getenv('API_HOST', '127.0.0.1')
        api_port = os.getenv('API_PORT', '5000')
        
        cloud_info = QLabel(self.language_manager.tr("cloud_info",
            f"Cloud Sync: Synchronize settings and data across devices\n"
            f"Remote Monitor: Access web dashboard at http://{monitor_host}:{monitor_port}\n"
            f"API Access: REST API at http://{api_host}:{api_port}/api\n"
            "Use the Cloud menu for configuration"))
        cloud_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cloud_info.setWordWrap(True)
        cloud_tab_layout.addWidget(cloud_info)
        
        self.features_tabs.addTab(cloud_tab, self.language_manager.tr("cloud", "Cloud"))
        
        right_layout.addWidget(self.features_tabs)
        
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
        file_menu = menubar.addMenu(self.language_manager.tr("file_menu", "File"))
        
        settings_action = QAction(self.language_manager.tr("settings", "Settings"), self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.language_manager.tr("exit", "Exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu(self.language_manager.tr("tools_menu", "Tools"))
        
        backtest_action = QAction(self.language_manager.tr("backtest", "Run Backtest"), self)
        backtest_action.triggered.connect(self.run_backtest)
        tools_menu.addAction(backtest_action)
        
        export_action = QAction(self.language_manager.tr("export_trades", "Export Trades"), self)
        export_action.triggered.connect(self.export_trades)
        tools_menu.addAction(export_action)
        
        tools_menu.addSeparator()
        
        # Optimization submenu
        optimization_menu = tools_menu.addMenu(self.language_manager.tr("optimization", "Optimization"))
        
        genetic_opt_action = QAction(self.language_manager.tr("genetic_optimization", "Genetic Algorithm"), self)
        genetic_opt_action.triggered.connect(self.show_genetic_optimization)
        optimization_menu.addAction(genetic_opt_action)
        
        hyperparameter_opt_action = QAction(self.language_manager.tr("hyperparameter_optimization", "Hyperparameter Optimization"), self)
        hyperparameter_opt_action.triggered.connect(self.show_hyperparameter_optimization)
        optimization_menu.addAction(hyperparameter_opt_action)
        
        walk_forward_action = QAction(self.language_manager.tr("walk_forward", "Walk-Forward Analysis"), self)
        walk_forward_action.triggered.connect(self.show_walk_forward)
        optimization_menu.addAction(walk_forward_action)
        
        monte_carlo_action = QAction(self.language_manager.tr("monte_carlo", "Monte Carlo Simulation"), self)
        monte_carlo_action.triggered.connect(self.show_monte_carlo)
        optimization_menu.addAction(monte_carlo_action)
        
        sensitivity_action = QAction(self.language_manager.tr("sensitivity_analysis", "Parameter Sensitivity"), self)
        sensitivity_action.triggered.connect(self.show_sensitivity_analysis)
        optimization_menu.addAction(sensitivity_action)
        
        multi_objective_action = QAction(self.language_manager.tr("multi_objective", "Multi-Objective Optimization"), self)
        multi_objective_action.triggered.connect(self.show_multi_objective)
        optimization_menu.addAction(multi_objective_action)
        
        adaptive_params_action = QAction(self.language_manager.tr("adaptive_parameters", "Adaptive Parameters"), self)
        adaptive_params_action.triggered.connect(self.show_adaptive_parameters)
        optimization_menu.addAction(adaptive_params_action)
        
        # Strategy Builder submenu
        builder_menu = tools_menu.addMenu(self.language_manager.tr("strategy_builder", "Strategy Builder"))
        
        visual_builder_action = QAction(self.language_manager.tr("visual_builder", "Visual Builder"), self)
        visual_builder_action.triggered.connect(self.show_strategy_builder)
        builder_menu.addAction(visual_builder_action)
        
        templates_action = QAction(self.language_manager.tr("templates", "Strategy Templates"), self)
        templates_action.triggered.connect(self.show_strategy_templates)
        builder_menu.addAction(templates_action)
        
        # Analytics menu
        analytics_menu = menubar.addMenu(self.language_manager.tr("analytics_menu", "Analytics"))
        
        portfolio_analytics_action = QAction(self.language_manager.tr("portfolio_analytics", "Portfolio Analytics"), self)
        portfolio_analytics_action.triggered.connect(self.show_portfolio_analytics)
        analytics_menu.addAction(portfolio_analytics_action)
        
        risk_analytics_action = QAction(self.language_manager.tr("risk_analytics", "Risk Analytics"), self)
        risk_analytics_action.triggered.connect(self.show_risk_analytics)
        analytics_menu.addAction(risk_analytics_action)
        
        performance_attribution_action = QAction(self.language_manager.tr("performance_attribution", "Performance Attribution"), self)
        performance_attribution_action.triggered.connect(self.show_performance_attribution)
        analytics_menu.addAction(performance_attribution_action)
        
        analytics_menu.addSeparator()
        
        enhanced_charts_action = QAction(self.language_manager.tr("enhanced_charts", "Enhanced Charts"), self)
        enhanced_charts_action.triggered.connect(self.show_enhanced_charts)
        analytics_menu.addAction(enhanced_charts_action)
        
        market_depth_action = QAction(self.language_manager.tr("market_depth", "Market Depth"), self)
        market_depth_action.triggered.connect(self.show_market_depth)
        analytics_menu.addAction(market_depth_action)
        
        correlation_matrix_action = QAction(self.language_manager.tr("correlation_matrix", "Correlation Matrix"), self)
        correlation_matrix_action.triggered.connect(self.show_correlation_matrix)
        analytics_menu.addAction(correlation_matrix_action)
        
        economic_calendar_action = QAction(self.language_manager.tr("economic_calendar", "Economic Calendar"), self)
        economic_calendar_action.triggered.connect(self.show_economic_calendar)
        analytics_menu.addAction(economic_calendar_action)
        
        trade_journal_action = QAction(self.language_manager.tr("trade_journal", "Trade Journal"), self)
        trade_journal_action.triggered.connect(self.show_trade_journal)
        analytics_menu.addAction(trade_journal_action)
        
        # Monitoring menu
        monitoring_menu = menubar.addMenu(self.language_manager.tr("monitoring_menu", "Monitoring"))
        
        strategy_monitor_action = QAction(self.language_manager.tr("strategy_monitor", "Strategy Monitor"), self)
        strategy_monitor_action.triggered.connect(self.show_strategy_monitor)
        monitoring_menu.addAction(strategy_monitor_action)
        
        performance_tracker_action = QAction(self.language_manager.tr("performance_tracker", "Performance Tracker"), self)
        performance_tracker_action.triggered.connect(self.show_performance_tracker)
        monitoring_menu.addAction(performance_tracker_action)
        
        health_check_action = QAction(self.language_manager.tr("health_check", "Health Check"), self)
        health_check_action.triggered.connect(self.show_health_check)
        monitoring_menu.addAction(health_check_action)
        
        # Marketplace menu
        marketplace_menu = menubar.addMenu(self.language_manager.tr("marketplace_menu", "Marketplace"))
        
        browse_strategies_action = QAction(self.language_manager.tr("browse_strategies", "Browse Strategies"), self)
        browse_strategies_action.triggered.connect(self.show_marketplace)
        marketplace_menu.addAction(browse_strategies_action)
        
        my_strategies_action = QAction(self.language_manager.tr("my_strategies", "My Strategies"), self)
        my_strategies_action.triggered.connect(self.show_my_strategies)
        marketplace_menu.addAction(my_strategies_action)
        
        # Cloud menu
        cloud_menu = menubar.addMenu(self.language_manager.tr("cloud_menu", "Cloud"))
        
        cloud_sync_action = QAction(self.language_manager.tr("cloud_sync", "Cloud Sync"), self)
        cloud_sync_action.triggered.connect(self.show_cloud_sync)
        cloud_menu.addAction(cloud_sync_action)
        
        remote_monitor_action = QAction(self.language_manager.tr("remote_monitor", "Remote Monitor"), self)
        remote_monitor_action.triggered.connect(self.show_remote_monitor)
        cloud_menu.addAction(remote_monitor_action)
        
        api_access_action = QAction(self.language_manager.tr("api_access", "API Access"), self)
        api_access_action.triggered.connect(self.show_api_access)
        cloud_menu.addAction(api_access_action)
        
        # Help menu
        help_menu = menubar.addMenu(self.language_manager.tr("help_menu", "Help"))
        
        about_action = QAction(self.language_manager.tr("about", "About"), self)
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
        """Create risk configuration from settings."""
        return RiskConfig(
            base_risk_pct=self.settings_manager.get('base_risk_pct', 0.1) / 100.0,
            max_risk_pct=self.settings_manager.get('max_risk_pct', 0.2) / 100.0,
            daily_risk_cap=self.settings_manager.get('daily_risk_cap', 0.2) / 100.0,
            max_drawdown_pct=self.settings_manager.get('max_drawdown_pct', 0.5) / 100.0,
            drawdown_recovery_pct=0.10,
            kelly_fraction=0.25,
            volatility_target=0.01,
            min_trade_amount=self.settings_manager.get('trade_amount_min', 10.0),
            max_trade_amount=self.settings_manager.get('trade_amount_max', 100.0)
        )
        
    def initialize_broker(self):
        """Initialize broker and data provider based on settings."""
        try:
            # Get broker mode from settings
            broker_mode = self.settings_manager.get('broker_mode', 'PAPER')
            self.append_log(f"Initializing broker: {broker_mode}")
            
            # MT4 mode - use real MT4 broker
            if broker_mode == 'MT4':
                self.append_log("MT4 mode detected - using real MT4 broker")
            
            # Initialize broker based on mode
            if broker_mode == 'PAPER':
                self.broker = PaperBroker(10000.0)
                self.append_log(self.language_manager.tr("paper_broker_initialized", "Paper broker initialized"))
            elif broker_mode == 'MT4':
                # Check if MT4 settings are configured (from settings or env vars)
                import os
                mt4_host = self.settings_manager.get('mt4_host')
                if not mt4_host:
                    mt4_host = os.getenv('MT4_ZMQ_HOST', '127.0.0.1')
                
                mt4_port = self.settings_manager.get('mt4_port')
                if not mt4_port or mt4_port == 0:
                    mt4_port = int(os.getenv('MT4_ZMQ_PORT', '5555'))
                
                self.append_log(f"MT4 settings - Host: {mt4_host}, Port: {mt4_port}")
                if not mt4_host or mt4_port == 0:
                    self.append_log("MT4 settings not configured - using paper broker")
                    self.broker = PaperBroker(10000.0)
                else:
                    from forexsmartbot.adapters.brokers.mt4_broker import MT4Broker
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
            
            # Initialize data provider (MT4 first, then fallback to others)
            self.data_provider = MultiProvider(settings_manager=self.settings_manager)
            self.append_log("Multi-provider data source initialized")
            
            # Update chart widget with data provider if it exists
            if hasattr(self, 'enhanced_chart_widget') and self.enhanced_chart_widget:
                self.enhanced_chart_widget.data_provider = self.data_provider
                # Reload data with the new provider
                self.enhanced_chart_widget.load_initial_data()
            
            # Initialize trading controller
            self.trading_controller = TradingController(
                broker=self.broker,
                data_provider=self.data_provider,
                risk_manager=self.risk_engine,
                portfolio=self.portfolio
            )
            
            # Update broker status display
            self.update_broker_status(broker_mode)
            
            self.append_log(self.language_manager.tr("broker_initialized", "Broker initialized successfully"))
            
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
                    
                    # Get real balance from MT4
                    try:
                        real_balance = self.broker.get_balance()
                        if real_balance:
                            self.trading_status_widget.balance_label.setText(f"${real_balance:,.2f}")
                            self.trading_status_widget.equity_label.setText(f"${real_balance:,.2f}")
                            self.append_log(f"Real balance retrieved: ${real_balance:,.2f}")
                        else:
                            self.append_log("Failed to get real balance: No response from MT4")
                    except Exception as e:
                        self.append_log(f"Failed to get real balance: {e}")
                    
                    # Sync positions from MT4
                    try:
                        mt4_positions = self.broker.get_positions()
                        if mt4_positions:
                            # Convert Position objects to dictionary format
                            self.positions = []
                            for symbol, position in mt4_positions.items():
                                pos_dict = {
                                    'symbol': position.symbol,
                                    'side': 'Long' if position.side > 0 else 'Short',
                                    'entry_price': position.entry_price,
                                    'current_price': position.current_price,
                                    'quantity': position.quantity,
                                    'take_profit': position.take_profit if position.take_profit else 0,
                                    'stop_loss': position.stop_loss if position.stop_loss else 0,
                                    'pnl': position.pnl if hasattr(position, 'pnl') else 0,
                                    'timestamp': datetime.now()
                                }
                                self.positions.append(pos_dict)
                            self.append_log(f"Synced {len(self.positions)} positions from MT4")
                            self.update_positions_display()
                    except Exception as e:
                        self.append_log(f"Failed to sync positions from MT4: {e}")
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
                
                # Stop trading and close positions if requested
                if reply == QMessageBox.StandardButton.Yes:
                    if self.is_trading:
                        self.stop_trading()
                    
                    # Close all open positions
                    self.close_all_positions()
                
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
                strategy_text = self.strategy_config_widget.strategy_combo.currentText()
                symbols = self.strategy_config_widget.get_selected_symbols()
                
                if not symbols:
                    QMessageBox.warning(self, "No Symbols", "Please select at least one symbol to trade")
                    return
                
                # Extract clean strategy name (remove emoji and risk level indicators)
                clean_strategy_name = strategy_text
                # Remove emoji prefixes
                for emoji in ['🟢 ', '🟡 ', '🔴 ', '⚪ ']:
                    if emoji in clean_strategy_name:
                        clean_strategy_name = clean_strategy_name.replace(emoji, '')
                # Remove risk level suffix in parentheses
                if ' (' in clean_strategy_name:
                    clean_strategy_name = clean_strategy_name.split(' (')[0]
                
                # Initialize strategy
                strategy = get_strategy(clean_strategy_name)
                if not strategy:
                    QMessageBox.warning(self, "Invalid Strategy", f"Strategy {clean_strategy_name} not found")
                    return
                
                # Register strategy with monitor
                self.strategy_monitor.register_strategy(clean_strategy_name)
                self.append_log(f"Registered {clean_strategy_name} with strategy monitor")
                
                # Start trading
                self.is_trading = True
                self.trading_status_widget.trading_status.setText("Running")
                self.trading_status_widget.trading_status.setStyleSheet("color: green; font-weight: bold;")
                self.trading_controls_widget.update_trading_state(True)
                self.append_log(f"Started trading {clean_strategy_name} on {', '.join(symbols)}")
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
    
    def close_all_positions(self):
        """Close all open positions."""
        try:
            if not self.positions:
                self.append_log("No open positions to close")
                return
            
            self.append_log(f"Closing {len(self.positions)} open positions...")
            closed_count = 0
            
            for position in self.positions[:]:  # Use slice to avoid modification during iteration
                try:
                    # Get current price for closing
                    current_price = self.data_provider.get_latest_price(position['symbol'])
                    if current_price:
                        # Close the position
                        self.close_position_from_signal(position['symbol'], current_price)
                        closed_count += 1
                        self.append_log(f"Closed position: {position['symbol']} {position['side']} at {current_price:.4f}")
                    else:
                        self.append_log(f"Warning: Could not get current price for {position['symbol']}")
                except Exception as e:
                    self.append_log(f"Error closing position {position['symbol']}: {str(e)}")
            
            # Clear positions list
            self.positions.clear()
            self.open_positions_widget.update_positions(self.positions, {})
            self.append_log(f"Successfully closed {closed_count} positions")
            
        except Exception as e:
            self.append_log(f"Error closing all positions: {str(e)}")
            
    def start_signal_generation(self, strategy, symbols):
        """Start generating trading signals with real-time monitoring."""
        try:
            self.append_log(f"Signal generation started for {strategy.name}")
            
            # Start real-time signal generation timer (less frequent to prevent freezing)
            self.signal_timer = QTimer()
            self.signal_timer.timeout.connect(lambda: self.generate_signals(strategy, symbols))
            self.signal_timer.start(300000)  # Check every 5 minutes (more frequent)
            
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
            
            # Check daily trade limits before generating signals
            if not self.check_daily_trade_limits():
                self.append_log("Daily trade limits reached - stopping signal generation")
                return
                
            # Process only a few symbols at a time to prevent blocking
            symbols_to_process = symbols[:3]  # Limit to 3 symbols per cycle
            
            for symbol in symbols_to_process:
                try:
                    # Check cooldown period (5 minutes between signals for same symbol)
                    current_time = datetime.now()
                    if symbol in self.signal_cooldown:
                        time_since_last = (current_time - self.signal_cooldown[symbol]).total_seconds()
                        if time_since_last < 600:  # 10 minute cooldown
                            continue
                    
                    # Get current price (simplified to prevent blocking)
                    current_price = self.data_provider.get_latest_price(symbol)
                    if current_price is None:
                        continue
                    
                    # Generate proper strategy signal
                    signal = self.generate_strategy_signal(strategy, symbol, current_price)
                    
                    if signal != 0:
                        # Update cooldown
                        self.signal_cooldown[symbol] = current_time
                        
                        self.append_log(f"[{symbol}] Signal: {'BUY' if signal > 0 else 'SELL'} at {current_price:.4f}")
                        
                        # Record signal with monitor
                        clean_strategy_name = self._get_current_strategy_name()
                        if clean_strategy_name:
                            import time as time_module
                            start_time = time_module.time()
                            self.strategy_monitor.record_signal(clean_strategy_name, execution_time=0.0)
                        
                        # Check if live trade confirmation is required
                        if self.settings_manager.get('confirm_live_trades', True):
                            # Show confirmation dialog
                            if not self.show_trade_confirmation(symbol, signal, current_price):
                                self.append_log(f"Trade cancelled by user for {symbol}")
                                continue
                        
                        # Create actual position when signal is generated
                        self.create_position_from_signal(symbol, signal, current_price)
                        
                        # Add a small delay to prevent rapid-fire trading
                        import time
                        time.sleep(1)  # 1 second delay between trades
                    
                except Exception as e:
                    self.append_log(f"Error processing {symbol}: {str(e)}")
                    # Record error with monitor
                    clean_strategy_name = self._get_current_strategy_name()
                    if clean_strategy_name:
                        self.strategy_monitor.record_error(clean_strategy_name, str(e))
                    
        except Exception as e:
            self.append_log(f"Signal generation error: {str(e)}")
            # Record error with monitor
            clean_strategy_name = self._get_current_strategy_name()
            if clean_strategy_name:
                self.strategy_monitor.record_error(clean_strategy_name, str(e))
    
    def _get_current_strategy_name(self):
        """Get the current strategy name from the UI."""
        try:
            strategy_text = self.strategy_config_widget.strategy_combo.currentText()
            clean_strategy_name = strategy_text
            # Remove emoji prefixes
            for emoji in ['🟢 ', '🟡 ', '🔴 ', '⚪ ']:
                if emoji in clean_strategy_name:
                    clean_strategy_name = clean_strategy_name.replace(emoji, '')
            # Remove risk level suffix in parentheses
            if ' (' in clean_strategy_name:
                clean_strategy_name = clean_strategy_name.split(' (')[0]
            return clean_strategy_name
        except:
            return None
    
    def generate_strategy_signal(self, strategy, symbol, current_price):
        """Generate trading signal using the selected strategy."""
        try:
            # Get historical data for the symbol using user's data interval setting
            data_interval = self.settings_manager.get('data_interval', '1h')
            historical_data = self.data_provider.get_historical_data(symbol, period='1d', interval=data_interval)
            if historical_data is None or len(historical_data) < 20:
                return 0
            
            # Convert to DataFrame if needed
            if hasattr(historical_data, 'to_pandas'):
                df = historical_data.to_pandas()
            else:
                df = historical_data
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                return 0
            
            # Add current price as the latest data point
            import pandas as pd
            current_row = pd.DataFrame({
                'Open': [current_price],
                'High': [current_price],
                'Low': [current_price],
                'Close': [current_price],
                'Volume': [1000]
            }, index=[df.index[-1] + pd.Timedelta(hours=1)])
            
            df = pd.concat([df, current_row])
            
            # Calculate indicators first
            df = strategy.indicators(df)
            
            # Check if required indicators exist after calculation
            # Different strategies have different required indicators
            strategy_name = strategy.name if hasattr(strategy, 'name') else str(type(strategy).__name__)
            
            # Define required indicators for each strategy
            required_indicators = {
                'ML Adaptive SuperTrend': ['SuperTrend', 'Direction'],
                'Adaptive Trend Flow': ['Trend_Flow', 'Signal_Strength'],
                'SMA Crossover': ['SMA_fast', 'SMA_slow'],
                'Breakout ATR': ['ATR', 'Breakout_High', 'Breakout_Low'],
                'RSI Reversion': ['RSI', 'ATR'],
                'Scalping MA': ['EMA_Fast', 'EMA_Medium', 'EMA_Slow'],
                'News Trading': ['Volatility', 'ATR', 'Breakout_High'],
                'Momentum Breakout': ['Momentum', 'ATR', 'Breakout_High'],
                'Mean Reversion': ['RSI', 'ATR', 'BB_Upper']
            }
            
            # Get required indicators for this strategy
            strategy_indicators = required_indicators.get(strategy_name, [])
            
            # Check if any required indicators are missing
            missing_indicators = [ind for ind in strategy_indicators if ind not in df.columns]
            if missing_indicators:
                self.append_log(f"Warning: Required indicators not calculated for {symbol}: {missing_indicators}")
                return 0
            
            # Generate signal using the strategy
            signal = strategy.signal(df)
            
            return signal
            
        except Exception as e:
            self.append_log(f"Error generating strategy signal for {symbol}: {str(e)}")
            return 0
    
    def calculate_position_size(self, entry_price, signal):
        """Calculate position size based on risk management from settings."""
        try:
            # Get risk percentage from settings (using correct key names)
            base_risk_pct = self.settings_manager.get('base_risk_pct', 0.02)  # 2% default
            max_risk_pct = self.settings_manager.get('max_risk_pct', 0.05)  # 5% default
            min_trade_amount = self.settings_manager.get('trade_amount_min', 10.0)
            max_trade_amount = self.settings_manager.get('trade_amount_max', 100.0)
            
            # Get leverage from UI
            leverage_text = self.strategy_config_widget.leverage_combo.currentText()
            leverage = self._extract_leverage(leverage_text)
            
            # Calculate position size based on current balance and risk
            current_balance = self._get_current_balance()
            
            # CRITICAL FIX: Position sizing should be extremely conservative
            # The user's max_trade_amount should be respected as the absolute maximum
            
            # Calculate risk-based position size (very conservative)
            risk_amount = current_balance * base_risk_pct
            
            # Apply leverage but cap it for safety
            max_safe_leverage = min(leverage, 3)  # Cap leverage at 3x for safety
            leveraged_risk = risk_amount * max_safe_leverage
            
            # Convert to micro lots (1 micro lot = 1,000 units)
            # Use a very conservative conversion: 1 micro lot per $100 of risk
            risk_based_micro_lots = max(1, int(leveraged_risk / 100))  # At least 1 micro lot
            risk_based_units = risk_based_micro_lots * 1000  # Convert to units
            
            # Apply user's max trade amount limit (this is the critical limit)
            # Convert max_trade_amount to units (assuming 1 unit = $1)
            max_size_units = int(max_trade_amount)  # $150 = 150 units maximum
            
            # Use the smaller of risk-based size or max trade amount
            position_size_units = min(risk_based_units, max_size_units)
            
            # CRITICAL: Ensure we never exceed 50 units for safety
            position_size_units = min(position_size_units, 50)
            
            # Apply minimum trade amount
            min_size_units = int(min_trade_amount)  # $10 minimum
            position_size_units = max(min_size_units, position_size_units)
            
            # Final safety check - never exceed 1,000 units (1 micro lot) for safety
            position_size_units = min(position_size_units, 1000)
            
            # Debug logging
            self.append_log(f"Position Size Debug - Balance: ${current_balance:.2f}, Risk: {base_risk_pct*100:.2f}%, Leverage: {leverage}x, Max Trade: ${max_trade_amount}, Units: {position_size_units}")
            
            return position_size_units
            
        except Exception as e:
            self.append_log(f"Error calculating position size: {str(e)}")
            return 1000  # Default fallback (1 micro lot)
    
    def check_daily_trade_limits(self):
        """Check if daily trade limits have been reached."""
        try:
            # Get daily risk cap and max trades from settings
            daily_risk_cap = self.settings_manager.get('daily_risk_cap', 0.05)  # 5% default
            max_drawdown_pct = self.settings_manager.get('max_drawdown_pct', 0.25)  # 25% default
            max_trades_per_day = self.settings_manager.get('max_trades_per_day', 50)  # 50 default
            
            # Get current balance and calculate daily limits
            current_balance = self._get_current_balance()
            daily_risk_limit = current_balance * daily_risk_cap
            max_drawdown_limit = current_balance * max_drawdown_pct
            
            # Calculate today's PnL and trade count from closed trades
            today = datetime.now().date()
            today_pnl = 0.0
            today_trade_count = 0
            
            # Reset daily counter if it's a new day
            if self.last_trade_date != today:
                self.daily_trade_count = 0
                self.last_trade_date = today
                self.append_log(f"New trading day: {today}")
            
            # Count closed trades - use exit_time if available, otherwise use entry_time
            for trade in self.closed_trades:
                trade_date = None
                if hasattr(trade, 'exit_time') and trade.exit_time:
                    trade_date = trade.exit_time.date()
                elif hasattr(trade, 'entry_time') and trade.entry_time:
                    trade_date = trade.entry_time.date()
                elif hasattr(trade, 'timestamp') and trade.timestamp:
                    trade_date = trade.timestamp.date()
                
                if trade_date == today:
                    today_pnl += trade.pnl
                    today_trade_count += 1
            
            # Count open positions (trades opened today) - use entry_time if available
            for position in self.positions:
                position_date = None
                if 'timestamp' in position and position['timestamp']:
                    position_date = position['timestamp'].date()
                elif 'entry_time' in position and position['entry_time']:
                    position_date = position['entry_time'].date()
                
                if position_date == today:
                    today_trade_count += 1
            
            # Use the higher of the two counts (daily counter vs calculated count)
            actual_trade_count = max(self.daily_trade_count, today_trade_count)
            
            # Debug logging for trade counting
            self.append_log(f"Trade Count Debug - Today: {actual_trade_count}, Max: {max_trades_per_day}, Daily Counter: {self.daily_trade_count}, Calculated: {today_trade_count}")
            
            # Check if max trades per day exceeded
            if actual_trade_count >= max_trades_per_day:
                self.append_log(f"Max trades per day exceeded: {actual_trade_count} >= {max_trades_per_day}")
                return False
            
            # Check if daily risk limit exceeded (only for losses)
            if today_pnl < 0 and abs(today_pnl) >= daily_risk_limit:
                self.append_log(f"Daily risk limit exceeded: ${abs(today_pnl):.2f} >= ${daily_risk_limit:.2f}")
                return False
            
            # Check if max drawdown exceeded
            if today_pnl <= -max_drawdown_limit:
                self.append_log(f"Max drawdown exceeded: ${abs(today_pnl):.2f} >= ${max_drawdown_limit:.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.append_log(f"Error checking daily trade limits: {str(e)}")
            return True  # Allow trading if check fails
    
    def show_trade_confirmation(self, symbol, signal, price):
        """Show trade confirmation dialog."""
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            signal_text = "BUY" if signal > 0 else "SELL"
            message = f"Execute {signal_text} trade for {symbol} at {price:.4f}?"
            
            reply = QMessageBox.question(
                self,
                "Trade Confirmation",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            return reply == QMessageBox.StandardButton.Yes
            
        except Exception as e:
            self.append_log(f"Error showing trade confirmation: {str(e)}")
            return True  # Allow trade if dialog fails
    
    def refresh_data_provider(self):
        """Refresh data provider when settings change."""
        try:
            # Reinitialize data provider with updated settings
            self.data_provider = MultiProvider(settings_manager=self.settings_manager)
            self.append_log("Data provider refreshed with updated settings")
            
            # Update trading controller with new data provider
            if hasattr(self, 'trading_controller'):
                self.trading_controller.data_provider = self.data_provider
                
        except Exception as e:
            self.append_log(f"Error refreshing data provider: {str(e)}")
    
    def _extract_leverage(self, leverage_text):
        """Extract leverage number from UI text."""
        try:
            # Extract number from text like "1:10 (Moderate)"
            if "1:" in leverage_text:
                parts = leverage_text.split("1:")
                if len(parts) > 1:
                    leverage_part = parts[1].split(" ")[0]
                    return float(leverage_part)
            return 1.0  # Default leverage
        except:
            return 1.0
    
    def _get_current_balance(self):
        """Get current balance from portfolio."""
        try:
            # Get real balance from MT4 broker
            if self.broker and self.broker.is_connected():
                base_balance = self.broker.get_balance()
            else:
                base_balance = 10000.0
            closed_pnl = sum(trade.pnl for trade in self.closed_trades)
            return base_balance + closed_pnl
        except:
            return 10000.0
    
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
                # Check if portfolio mode is enabled
                portfolio_mode = self.settings_manager.get('portfolio_mode', False)
                
                if portfolio_mode:
                    # In portfolio mode, allow multiple positions per symbol
                    self.append_log(f"Portfolio mode: Adding additional position for {symbol}")
                else:
                    # Evaluate closing existing position on opposite signal with net PnL guard
                    import random
                    price_variation = random.uniform(-0.001, 0.001) * price  # 0.1% variation
                    exit_price = price + price_variation

                    # Calculate hypothetical PnL including spread
                    micro_lots = existing_position['quantity'] / 1000
                    broker_spread_pips = self.settings_manager.get('broker_spread', 2.0)
                    spread_cost = broker_spread_pips * micro_lots * 10  # $10 per pip per micro lot

                    if existing_position['side'] == 'Long':
                        hypothetical_pnl = (exit_price - existing_position['entry_price']) * micro_lots * 10
                    else:
                        hypothetical_pnl = (existing_position['entry_price'] - exit_price) * micro_lots * 10
                    hypothetical_pnl -= spread_cost

                    # Only close if PnL >= -spread_cost (allow small losses but not spread-only losses) or stop loss would be hit
                    sl = existing_position.get('stop_loss')
                    stop_hit = False
                    if sl:
                        if existing_position['side'] == 'Long' and exit_price <= sl:
                            stop_hit = True
                        elif existing_position['side'] == 'Short' and exit_price >= sl:
                            stop_hit = True

                    # Allow closing if PnL is not too negative (more than 2x spread cost) or stop loss hit
                    if hypothetical_pnl >= -spread_cost * 2 or stop_hit:
                        self.close_position_from_signal(symbol, exit_price)
                    else:
                        # Skip closing to avoid locking in a significant loss
                        self.append_log(f"Skipping close for {symbol}: PnL would be {hypothetical_pnl:.2f} (too negative)")
                        return
            
            # Use real price from MT4 broker
            if self.broker and self.broker.is_connected():
                real_price = self.broker.get_price(symbol)
                if real_price is not None:
                    entry_price = real_price
                    self.append_log(f"Using real MT4 price for {symbol}: {entry_price}")
                else:
                    entry_price = price
                    self.append_log(f"Using data provider price for {symbol}: {entry_price}")
            else:
                entry_price = price
                self.append_log(f"Using data provider price for {symbol}: {entry_price}")
            
            # Calculate position size
            quantity = self.calculate_position_size(entry_price, signal)
            take_profit = entry_price * (1.02 if signal > 0 else 0.98)  # 2% take profit
            stop_loss = entry_price * (0.98 if signal > 0 else 1.02)  # 2% stop loss
            
            # Submit order to broker (MT4)
            if self.broker and self.broker.is_connected():
                order_id = self.broker.submit_order(
                    symbol=symbol,
                    side=1 if signal > 0 else -1,  # 1 for buy, -1 for sell
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                if order_id:
                    self.append_log(f"Order submitted to MT4: {order_id} for {symbol}")
                    # Wait a moment for MT4 to process the order
                    import time
                    time.sleep(1.5)  # Give MT4 time to process
                    # Sync positions from MT4 to get the actual order details
                    try:
                        mt4_positions = self.broker.get_positions()
                        if mt4_positions and symbol in mt4_positions:
                            mt4_pos = mt4_positions[symbol]
                            # Use actual MT4 entry price, SL, and TP
                            entry_price = mt4_pos.entry_price
                            stop_loss = mt4_pos.stop_loss if mt4_pos.stop_loss else stop_loss
                            take_profit = mt4_pos.take_profit if mt4_pos.take_profit else take_profit
                            quantity = mt4_pos.quantity  # Use actual quantity from MT4
                            self.append_log(f"MT4 order confirmed: {symbol} at {entry_price:.4f}, SL={stop_loss:.4f}, TP={take_profit:.4f}")
                        else:
                            self.append_log(f"Warning: Order submitted but position not found in MT4 yet for {symbol}")
                    except Exception as e:
                        self.append_log(f"Warning: Could not verify order in MT4: {e}")
                else:
                    self.append_log(f"Failed to submit order to MT4 for {symbol}")
                    return
            else:
                self.append_log(f"Broker not connected - cannot submit order for {symbol}")
                return
            
            # Create new position with actual MT4 data
            position = {
                'symbol': symbol,
                'side': 'Long' if signal > 0 else 'Short',
                'entry_price': entry_price,
                'current_price': entry_price,
                'quantity': quantity,
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'pnl': 0.0,
                'timestamp': datetime.now(),
                'status': 'Active',
                'order_id': order_id
            }
            
            self.positions.append(position)
            self.update_positions_display()
            
            # Increment daily trade counter
            self.daily_trade_count += 1
            
            # Update portfolio with new position
            self.update_portfolio_with_position(position)
            
            # Add portfolio mode indicator to log
            portfolio_mode = self.settings_manager.get('portfolio_mode', False)
            mode_text = " (Portfolio Mode)" if portfolio_mode else ""
            self.append_log(f"Position opened: {symbol} {position['side']} at {entry_price:.4f}{mode_text}")
            
            # Record trade with performance tracker
            clean_strategy_name = self._get_current_strategy_name()
            if clean_strategy_name:
                self.performance_tracker.record_trade(clean_strategy_name, {
                    'symbol': symbol,
                    'side': position['side'],
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'entry_time': datetime.now()
                })
            
            # Send notification
            self.notification_service.show_position_alert(
                "open", symbol, position['side'], entry_price, 
                take_profit=position.get('take_profit'),
                stop_loss=position.get('stop_loss')
            )
            
        except Exception as e:
            self.append_log(f"Error creating position: {str(e)}")
    
    def close_position_from_signal(self, symbol, price):
        """Close a position from a trading signal."""
        try:
            for i, pos in enumerate(self.positions):
                if pos.get('symbol') == symbol:
                    # Use the actual price for more realistic PnL calculation
                    exit_price = price
                    
                    # Calculate PnL with very conservative approach
                    # Use micro lots for calculation (1 micro lot = 1,000 units)
                    micro_lots = pos['quantity'] / 1000
                    
                    # Get broker spread from settings
                    broker_spread_pips = self.settings_manager.get('broker_spread', 2.0)  # Default 2 pips
                    spread_cost = broker_spread_pips * micro_lots * 10  # $10 per pip per micro lot
                    
                    if pos['side'] == 'Long':
                        pnl = (exit_price - pos['entry_price']) * micro_lots * 10  # $10 per pip per micro lot
                    else:
                        pnl = (pos['entry_price'] - exit_price) * micro_lots * 10  # $10 per pip per micro lot
                    
                    # Deduct broker spread cost
                    pnl -= spread_cost
                    
                    # Debug PnL calculation
                    self.append_log(f"PnL Debug - {symbol}: Entry={pos['entry_price']:.4f}, Exit={exit_price:.4f}, Qty={pos['quantity']:.2f}, Spread={spread_cost:.2f}, PnL={pnl:.2f}")
                    
                    # Close order in MT4
                    if self.broker and self.broker.is_connected() and 'order_id' in pos:
                        close_success = self.broker.close_all(symbol)
                        if close_success:
                            self.append_log(f"Order closed in MT4 for {symbol}")
                        else:
                            self.append_log(f"Failed to close order in MT4 for {symbol}")
                    
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
                        take_profit=pos.get('take_profit'),
                        stop_loss=pos.get('stop_loss'),
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
            # Sync positions from MT4 broker if connected
            if self.broker and self.broker.is_connected():
                try:
                    # Get real balance from MT4
                    real_balance = self.broker.get_balance()
                    if real_balance:
                        self.trading_status_widget.balance_label.setText(f"${real_balance:,.2f}")
                        self.trading_status_widget.equity_label.setText(f"${real_balance:,.2f}")
                    
                    # Get real positions from MT4
                    mt4_positions = self.broker.get_positions()
                    if mt4_positions:
                        # Convert Position objects to dictionary format
                        self.positions = []
                        current_prices = {}
                        for symbol, position in mt4_positions.items():
                            pos_dict = {
                                'symbol': position.symbol,
                                'side': 'Long' if position.side > 0 else 'Short',
                                'entry_price': position.entry_price,
                                'current_price': position.current_price,
                                'quantity': position.quantity,
                                'take_profit': position.take_profit if position.take_profit else 0,
                                'stop_loss': position.stop_loss if position.stop_loss else 0,
                                'pnl': position.pnl if hasattr(position, 'pnl') else 0,
                                'timestamp': datetime.now()
                            }
                            self.positions.append(pos_dict)
                            current_prices[symbol] = position.current_price
                        
                        # Update positions widget with Position objects
                        position_objects = []
                        for pos_dict in self.positions:
                            pos_obj = Position(
                                symbol=pos_dict['symbol'],
                                side=1 if pos_dict['side'] == 'Long' else -1,
                                quantity=pos_dict['quantity'],
                                entry_price=pos_dict['entry_price'],
                                current_price=pos_dict['current_price'],
                                stop_loss=pos_dict.get('stop_loss', 0),
                                take_profit=pos_dict.get('take_profit', 0),
                                unrealized_pnl=pos_dict.get('pnl', 0)
                            )
                            position_objects.append(pos_obj)
                        
                        self.open_positions_widget.update_positions(position_objects, current_prices)
                except Exception as e:
                    self.append_log(f"Error syncing MT4 data: {str(e)}")
            
            # Update portfolio with current positions
            self.update_portfolio_with_position(None)
            
            # Update positions display (fallback if MT4 sync didn't work)
            if not (self.broker and self.broker.is_connected()):
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
        dialog = SettingsDialog(self.settings_manager, self.language_manager, self, self.refresh_data_provider)
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
        dialog = BacktestDialog(self, self.language_manager)
        dialog.exec()
        
    def export_trades(self):
        """Export trades dialog."""
        dialog = ExportDialog(self.portfolio, self)
        dialog.exec()
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            self.language_manager.tr("about", "About ForexSmartBot"),
            "ForexSmartBot v3.3.0\n\n"
            "Advanced Trading Platform with Machine Learning Strategies\n\n"
            "Features:\n"
            "• Real-time trading\n"
            "• 17+ Trading Strategies (including 7 ML strategies)\n"
            "• Strategy Optimization Tools\n"
            "• Visual Strategy Builder\n"
            "• Strategy Marketplace\n"
            "• Advanced Analytics\n"
            "• Cloud Integration\n"
            "• Remote Monitoring\n"
            "• Risk management\n"
            "• Backtesting\n\n"
            "© 2026 VoxHash Technologies"
        )
    
    # Optimization menu handlers
    def show_genetic_optimization(self):
        """Show genetic optimization dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='genetic',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open genetic optimization: {e}")
    
    def show_hyperparameter_optimization(self):
        """Show hyperparameter optimization dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='hyperparameter',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open hyperparameter optimization: {e}")
    
    def show_walk_forward(self):
        """Show walk-forward analysis dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='walk_forward',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open walk-forward analysis: {e}")
    
    def show_monte_carlo(self):
        """Show Monte Carlo simulation dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='monte_carlo',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Monte Carlo simulation: {e}")
    
    def show_sensitivity_analysis(self):
        """Show parameter sensitivity analysis dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='sensitivity',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open sensitivity analysis: {e}")
    
    def show_multi_objective(self):
        """Show multi-objective optimization dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='multi_objective',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open multi-objective optimization: {e}")
    
    def show_adaptive_parameters(self):
        """Show adaptive parameters dialog."""
        try:
            from .optimization_dialog import OptimizationDialog
            dialog = OptimizationDialog(
                optimizer_type='adaptive',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open adaptive parameters: {e}")
    
    # Strategy Builder menu handlers
    def show_strategy_builder(self):
        """Show visual strategy builder."""
        try:
            from .strategy_builder_dialog import StrategyBuilderDialog
            dialog = StrategyBuilderDialog(
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open strategy builder: {e}")
    
    def show_strategy_templates(self):
        """Show strategy templates."""
        try:
            from .strategy_builder_dialog import StrategyTemplatesDialog, StrategyBuilderDialog
            templates_dialog = StrategyTemplatesDialog(
                parent=self,
                language_manager=self.language_manager
            )
            result = templates_dialog.exec()
            
            # If template was loaded, open Strategy Builder with it
            if result == QDialog.DialogCode.Accepted and templates_dialog.loaded_builder:
                builder_dialog = StrategyBuilderDialog(
                    parent=self,
                    language_manager=self.language_manager
                )
                builder_dialog.builder = templates_dialog.loaded_builder
                builder_dialog.update_strategy_tree()
                builder_dialog.validate_strategy()
                builder_dialog.show()  # Show non-modal so user can keep it open
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open strategy templates: {e}")
    
    # Analytics menu handlers
    def show_portfolio_analytics(self):
        """Show portfolio analytics."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='portfolio',
                parent=self,
                language_manager=self.language_manager,
                portfolio=self.portfolio
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open portfolio analytics: {e}")
    
    def show_risk_analytics(self):
        """Show risk analytics."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='risk',
                parent=self,
                language_manager=self.language_manager,
                portfolio=self.portfolio
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open risk analytics: {e}")
    
    def show_performance_attribution(self):
        """Show performance attribution."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='performance',
                parent=self,
                language_manager=self.language_manager,
                portfolio=self.portfolio
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open performance attribution: {e}")
    
    def show_enhanced_charts(self):
        """Show enhanced charts."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='charts',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open enhanced charts: {e}")
    
    def show_market_depth(self):
        """Show market depth."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='market_depth',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open market depth: {e}")
    
    def show_correlation_matrix(self):
        """Show correlation matrix."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='correlation',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open correlation matrix: {e}")
    
    def show_economic_calendar(self):
        """Show economic calendar."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='economic_calendar',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open economic calendar: {e}")
    
    def show_trade_journal(self):
        """Show trade journal."""
        try:
            from .analytics_dialog import AnalyticsDialog
            dialog = AnalyticsDialog(
                analytics_type='trade_journal',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open trade journal: {e}")
    
    # Monitoring menu handlers
    def show_strategy_monitor(self):
        """Show strategy monitor."""
        try:
            from .monitoring_dialog import MonitoringDialog
            dialog = MonitoringDialog(
                monitor_type='strategy',
                parent=self,
                language_manager=self.language_manager,
                trading_controller=self.trading_controller
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open strategy monitor: {e}")
    
    def show_performance_tracker(self):
        """Show performance tracker."""
        try:
            from .monitoring_dialog import MonitoringDialog
            dialog = MonitoringDialog(
                monitor_type='performance',
                parent=self,
                language_manager=self.language_manager,
                portfolio=self.portfolio
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open performance tracker: {e}")
    
    def show_health_check(self):
        """Show health check."""
        try:
            from .monitoring_dialog import MonitoringDialog
            dialog = MonitoringDialog(
                monitor_type='health',
                parent=self,
                language_manager=self.language_manager,
                broker=self.broker
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open health check: {e}")
    
    # Marketplace menu handlers
    def show_marketplace(self):
        """Show marketplace."""
        try:
            from .marketplace_dialog import MarketplaceDialog
            dialog = MarketplaceDialog(
                show_my_strategies=False,
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open marketplace: {e}")
    
    def show_my_strategies(self):
        """Show my strategies."""
        try:
            from .marketplace_dialog import MarketplaceDialog
            dialog = MarketplaceDialog(
                show_my_strategies=True,
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open my strategies: {e}")
    
    # Cloud menu handlers
    def show_cloud_sync(self):
        """Show cloud sync dialog."""
        try:
            from .cloud_dialog import CloudDialog
            dialog = CloudDialog(
                cloud_type='sync',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open cloud sync: {e}")
    
    def show_remote_monitor(self):
        """Show remote monitor dialog."""
        try:
            from .cloud_dialog import CloudDialog
            dialog = CloudDialog(
                cloud_type='remote_monitor',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open remote monitor: {e}")
    
    def show_api_access(self):
        """Show API access dialog."""
        try:
            from .cloud_dialog import CloudDialog
            dialog = CloudDialog(
                cloud_type='api',
                parent=self,
                language_manager=self.language_manager
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open API access: {e}")
        
    def append_log(self, message):
        """Append message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def load_settings(self):
        """Load application settings."""
        try:
            # Load and apply theme
            theme = self.settings_manager.get('theme', 'dark')
            self.apply_theme()
            
            # Load and apply language
            self.handle_language_settings()
            
            # Load and apply startup settings
            self.handle_startup_settings()
            
            # Load and apply window size
            self.handle_window_settings()
            
            # Update notification service configuration
            self.notification_service.update_config()
            
            # Load other settings
            self.append_log(self.language_manager.tr("settings_loaded", "Settings loaded successfully"))
            
        except Exception as e:
            self.append_log(f"Error loading settings: {str(e)}")
    
    def update_positions_display(self):
        """Update the positions table display from internal positions list."""
        try:
            # Use the correct widget reference
            self.open_positions_widget.positions_table.setRowCount(len(self.positions))
            
            for i, pos in enumerate(self.positions):
                # Get current price from data provider
                symbol = pos['symbol']
                current_price = self.data_provider.get_latest_price(symbol) if self.data_provider else pos.get('current_price', pos['entry_price'])
                
                # Calculate PnL properly
                if pos['side'] == 'Long':
                    pnl = (current_price - pos['entry_price']) * pos.get('quantity', 1.0)
                else:
                    pnl = (pos['entry_price'] - current_price) * pos.get('quantity', 1.0)
                
                # Update PnL in position
                pos['pnl'] = pnl
                pos['current_price'] = current_price
                
                # Populate table
                self.open_positions_widget.positions_table.setItem(i, 0, QTableWidgetItem(pos['symbol']))
                self.open_positions_widget.positions_table.setItem(i, 1, QTableWidgetItem(pos['side']))
                self.open_positions_widget.positions_table.setItem(i, 2, QTableWidgetItem(f"{pos['entry_price']:.4f}"))
                self.open_positions_widget.positions_table.setItem(i, 3, QTableWidgetItem(f"{pos.get('take_profit', 0):.4f}"))
                self.open_positions_widget.positions_table.setItem(i, 4, QTableWidgetItem(f"{pos.get('stop_loss', 0):.4f}"))
                
                # Note: PnL and Status columns were removed from the table
                # PnL is calculated and stored in the position but not displayed in the table
                # Status is tracked internally but not displayed in the table
                
        except Exception as e:
            self.append_log(f"Error updating positions display: {str(e)}")
    
    def update_portfolio_with_position(self, position):
        """Update portfolio with new position for real-time calculations."""
        try:
            # Calculate total PnL from closed trades and open positions
            closed_pnl = sum(trade.pnl for trade in self.closed_trades)
            open_pnl = sum(pos.get('pnl', 0) for pos in self.positions)
            total_pnl = closed_pnl + open_pnl
            
            # Update balance with closed trades PnL
            # Get real balance from MT4 broker
            if self.broker and self.broker.is_connected():
                base_balance = self.broker.get_balance()
            else:
                base_balance = 10000.0
            current_balance = base_balance + closed_pnl
            current_equity = current_balance + open_pnl

            # Update trading status display with color coding
            self.trading_status_widget.balance_label.setText(f"${current_balance:.2f}")
            if current_balance > base_balance:
                self.trading_status_widget.balance_label.setStyleSheet("color: green;")
            elif current_balance < base_balance:
                self.trading_status_widget.balance_label.setStyleSheet("color: red;")
            else:
                self.trading_status_widget.balance_label.setStyleSheet("color: blue;")
            
            self.trading_status_widget.equity_label.setText(f"${current_equity:.2f}")
            if current_equity > current_balance:
                self.trading_status_widget.equity_label.setStyleSheet("color: green;")
            elif current_equity < current_balance:
                self.trading_status_widget.equity_label.setStyleSheet("color: red;")
            else:
                self.trading_status_widget.equity_label.setStyleSheet("color: blue;")

            # Calculate drawdown based on peak equity
            if not hasattr(self, 'peak_equity'):
                self.peak_equity = current_equity
            
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            
            if self.peak_equity > 0:
                drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
            else:
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
        """Update performance metrics display."""
        try:
            # Calculate metrics from closed trades
            if self.closed_trades:
                total_trades = len(self.closed_trades)
                winning_trades = sum(1 for trade in self.closed_trades if trade.pnl > 0)
                win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                
                total_profit = sum(trade.pnl for trade in self.closed_trades if trade.pnl > 0)
                total_loss = abs(sum(trade.pnl for trade in self.closed_trades if trade.pnl < 0))
                profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
                
                # Calculate max drawdown from peak equity
                max_drawdown = 0.0
                if hasattr(self, 'peak_equity') and self.peak_equity > 0:
                    current_equity = self._get_current_balance() + sum(pos.get('pnl', 0) for pos in self.positions)
                    max_drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
                    max_drawdown = max(0, max_drawdown)  # Ensure non-negative
                
                # Update display
                self.performance_metrics_widget.total_trades_label.setText(str(total_trades))
                self.performance_metrics_widget.win_rate_label.setText(f"{win_rate:.1f}%")
                self.performance_metrics_widget.profit_factor_label.setText(f"{profit_factor:.2f}")
                self.performance_metrics_widget.max_drawdown_label.setText(f"{max_drawdown:.1f}%")
                
                # Color-code win rate
                if win_rate >= 60:
                    self.performance_metrics_widget.win_rate_label.setStyleSheet("color: green;")
                elif win_rate >= 40:
                    self.performance_metrics_widget.win_rate_label.setStyleSheet("color: orange;")
                else:
                    self.performance_metrics_widget.win_rate_label.setStyleSheet("color: red;")
                
                # Color-code max drawdown
                if max_drawdown > 10:
                    self.performance_metrics_widget.max_drawdown_label.setStyleSheet("color: red;")
                elif max_drawdown > 5:
                    self.performance_metrics_widget.max_drawdown_label.setStyleSheet("color: orange;")
                else:
                    self.performance_metrics_widget.max_drawdown_label.setStyleSheet("color: green;")
                    
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
    
    def handle_window_settings(self):
        """Handle window size and UI visibility settings changes."""
        try:
            window_width = self.settings_manager.get('window_width', 1400)
            window_height = self.settings_manager.get('window_height', 900)
            
            # Resize window if settings changed
            current_width = self.width()
            current_height = self.height()
            
            if current_width != window_width or current_height != window_height:
                self.resize(window_width, window_height)
                self.append_log(f"Window resized to {window_width}x{window_height}")
            
            # Handle toolbar visibility
            show_toolbar = self.settings_manager.get('show_toolbar', True)
            if hasattr(self, 'toolbar'):
                self.toolbar.setVisible(show_toolbar)
            else:
                # Create toolbar if it doesn't exist and should be shown
                if show_toolbar:
                    self.toolbar = self.addToolBar("Main Toolbar")
                    self.append_log("Toolbar created and shown")
            
            # Handle status bar visibility
            show_status_bar = self.settings_manager.get('show_status_bar', True)
            if hasattr(self, 'status_bar'):
                self.status_bar.setVisible(show_status_bar)
            else:
                # Create status bar if it doesn't exist and should be shown
                if show_status_bar:
                    self.status_bar = self.statusBar()
                    self.append_log("Status bar created and shown")
                
        except Exception as e:
            self.append_log(f"Error handling window settings: {str(e)}")
    
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
            self.setWindowTitle(f"{self.language_manager.tr('app_title', 'ForexSmartBot')} - Advanced Trading Platform")
            
            # Update status bar
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(self.language_manager.tr("ready", "Ready"))
            
            # Update Trading Status widget
            if hasattr(self, 'trading_status_widget'):
                self.trading_status_widget.update_language(self.language_manager)
            
            # Update Strategy Configuration widget
            if hasattr(self, 'strategy_config_widget'):
                self.strategy_config_widget.update_language(self.language_manager)
            
            # Update Performance Metrics widget
            if hasattr(self, 'performance_metrics_widget'):
                self.performance_metrics_widget.update_language(self.language_manager)
            
            # Update Trading Controls widget
            if hasattr(self, 'trading_controls_widget'):
                self.trading_controls_widget.update_language(self.language_manager)
            
            # Update Open Positions widget
            if hasattr(self, 'open_positions_widget'):
                self.open_positions_widget.update_language(self.language_manager)
            
            # Update Closed Positions widget
            if hasattr(self, 'close_positions_widget'):
                self.close_positions_widget.update_language(self.language_manager)
            
            # Update Trading Log group box
            log_group = self.findChild(QGroupBox)
            if log_group and log_group.title() == "Trading Log":
                log_group.setTitle(self.language_manager.tr("trading_log", "Trading Log"))
            
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