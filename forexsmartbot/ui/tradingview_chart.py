"""TradingView-style interactive candlestick chart widget."""

import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QComboBox, QLabel, QSlider, QCheckBox, QSpinBox,
                             QFrame, QSplitter, QScrollArea, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import mplfinance as mpf
from mplfinance.original_flavor import candlestick_ohlc
import talib


class TradingViewChart(QWidget):
    """Professional TradingView-style interactive candlestick chart."""
    
    # Signals
    signal_generated = pyqtSignal(str, int)  # symbol, signal
    chart_updated = pyqtSignal(dict)  # chart data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.data = None
        self.current_symbol = "EURUSD"
        self.current_timeframe = "1h"
        self.indicators = {}
        self.trades = []
        self.signals = []
        self.zoom_level = 100
        self.pan_offset = 0
        self.is_dragging = False
        self.last_mouse_pos = None
        
        self.setup_ui()
        self.setup_chart()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Top toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Main chart area
        chart_layout = QHBoxLayout()
        
        # Left panel for indicators
        left_panel = self.create_left_panel()
        chart_layout.addWidget(left_panel, 1)
        
        # Chart widget
        self.chart_widget = self.create_chart_widget()
        chart_layout.addWidget(self.chart_widget, 4)
        
        # Right panel for controls
        right_panel = self.create_right_panel()
        chart_layout.addWidget(right_panel, 1)
        
        layout.addLayout(chart_layout)
        
        # Bottom status bar
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)
        
        self.setLayout(layout)
        
    def create_toolbar(self) -> QWidget:
        """Create the top toolbar."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar.setMaximumHeight(50)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Symbol selector
        symbol_label = QLabel("Symbol:")
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP"])
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        layout.addWidget(symbol_label)
        layout.addWidget(self.symbol_combo)
        
        # Timeframe selector
        timeframe_label = QLabel("Timeframe:")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"])
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        layout.addWidget(timeframe_label)
        layout.addWidget(self.timeframe_combo)
        
        layout.addStretch()
        
        # Chart type buttons
        self.candlestick_btn = QPushButton("Candles")
        self.candlestick_btn.setCheckable(True)
        self.candlestick_btn.setChecked(True)
        self.candlestick_btn.clicked.connect(self.on_chart_type_changed)
        layout.addWidget(self.candlestick_btn)
        
        self.line_btn = QPushButton("Line")
        self.line_btn.setCheckable(True)
        self.line_btn.clicked.connect(self.on_chart_type_changed)
        layout.addWidget(self.line_btn)
        
        self.bar_btn = QPushButton("Bars")
        self.bar_btn.setCheckable(True)
        self.bar_btn.clicked.connect(self.on_chart_type_changed)
        layout.addWidget(self.bar_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_chart)
        layout.addWidget(refresh_btn)
        
        toolbar.setLayout(layout)
        return toolbar
        
    def create_left_panel(self) -> QWidget:
        """Create the left indicators panel."""
        panel = QGroupBox("Indicators")
        panel.setMaximumWidth(200)
        
        layout = QVBoxLayout()
        
        # Price indicators
        price_group = QGroupBox("Price")
        price_layout = QVBoxLayout()
        
        self.sma_check = QCheckBox("SMA 20")
        self.sma_check.toggled.connect(self.update_indicators)
        price_layout.addWidget(self.sma_check)
        
        self.ema_check = QCheckBox("EMA 20")
        self.ema_check.toggled.connect(self.update_indicators)
        price_layout.addWidget(self.ema_check)
        
        self.bb_check = QCheckBox("Bollinger Bands")
        self.bb_check.toggled.connect(self.update_indicators)
        price_layout.addWidget(self.bb_check)
        
        price_group.setLayout(price_layout)
        layout.addWidget(price_group)
        
        # Oscillators
        osc_group = QGroupBox("Oscillators")
        osc_layout = QVBoxLayout()
        
        self.rsi_check = QCheckBox("RSI")
        self.rsi_check.toggled.connect(self.update_indicators)
        osc_layout.addWidget(self.rsi_check)
        
        self.macd_check = QCheckBox("MACD")
        self.macd_check.toggled.connect(self.update_indicators)
        osc_layout.addWidget(self.macd_check)
        
        self.stoch_check = QCheckBox("Stochastic")
        self.stoch_check.toggled.connect(self.update_indicators)
        osc_layout.addWidget(self.stoch_check)
        
        osc_group.setLayout(osc_layout)
        layout.addWidget(osc_group)
        
        # Volume
        vol_group = QGroupBox("Volume")
        vol_layout = QVBoxLayout()
        
        self.volume_check = QCheckBox("Volume")
        self.volume_check.toggled.connect(self.update_indicators)
        vol_layout.addWidget(self.volume_check)
        
        self.vwap_check = QCheckBox("VWAP")
        self.vwap_check.toggled.connect(self.update_indicators)
        vol_layout.addWidget(self.vwap_check)
        
        vol_group.setLayout(vol_layout)
        layout.addWidget(vol_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_chart_widget(self) -> QWidget:
        """Create the main chart widget."""
        # Create figure with subplots
        self.fig = Figure(figsize=(12, 8), facecolor='#1e1e1e')
        self.fig.patch.set_facecolor('#1e1e1e')
        
        # Main price chart
        self.ax_main = self.fig.add_subplot(3, 1, (1, 2))
        self.ax_main.set_facecolor('#1e1e1e')
        self.ax_main.tick_params(colors='white')
        
        # Volume chart
        self.ax_volume = self.fig.add_subplot(3, 1, 3)
        self.ax_volume.set_facecolor('#1e1e1e')
        self.ax_volume.tick_params(colors='white')
        
        # Create canvas
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: #1e1e1e;")
        
        # Enable mouse interactions
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        return self.canvas
        
    def create_right_panel(self) -> QWidget:
        """Create the right controls panel."""
        panel = QGroupBox("Controls")
        panel.setMaximumWidth(200)
        
        layout = QVBoxLayout()
        
        # Zoom controls
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QVBoxLayout()
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        # Drawing tools
        draw_group = QGroupBox("Drawing Tools")
        draw_layout = QVBoxLayout()
        
        self.trend_line_btn = QPushButton("Trend Line")
        self.trend_line_btn.setCheckable(True)
        draw_layout.addWidget(self.trend_line_btn)
        
        self.horizontal_line_btn = QPushButton("Horizontal Line")
        self.horizontal_line_btn.setCheckable(True)
        draw_layout.addWidget(self.horizontal_line_btn)
        
        self.fibonacci_btn = QPushButton("Fibonacci")
        self.fibonacci_btn.setCheckable(True)
        draw_layout.addWidget(self.fibonacci_btn)
        
        draw_group.setLayout(draw_layout)
        layout.addWidget(draw_group)
        
        # Trading signals
        signals_group = QGroupBox("Signals")
        signals_layout = QVBoxLayout()
        
        self.show_signals_check = QCheckBox("Show Signals")
        self.show_signals_check.setChecked(True)
        self.show_signals_check.toggled.connect(self.update_chart)
        signals_layout.addWidget(self.show_signals_check)
        
        self.show_trades_check = QCheckBox("Show Trades")
        self.show_trades_check.setChecked(True)
        self.show_trades_check.toggled.connect(self.update_chart)
        signals_layout.addWidget(self.show_trades_check)
        
        signals_group.setLayout(signals_layout)
        layout.addWidget(signals_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_status_bar(self) -> QWidget:
        """Create the bottom status bar."""
        status_bar = QFrame()
        status_bar.setFrameStyle(QFrame.Shape.StyledPanel)
        status_bar.setMaximumHeight(30)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Ready")
        self.price_label = QLabel("Price: --")
        self.change_label = QLabel("Change: --")
        self.time_label = QLabel("Time: --")
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.price_label)
        layout.addWidget(self.change_label)
        layout.addWidget(self.time_label)
        
        status_bar.setLayout(layout)
        return status_bar
        
    def setup_chart(self):
        """Setup the chart appearance."""
        # Set dark theme
        plt.style.use('dark_background')
        
        # Configure main chart
        self.ax_main.set_facecolor('#1e1e1e')
        self.ax_main.spines['bottom'].set_color('white')
        self.ax_main.spines['top'].set_color('white')
        self.ax_main.spines['right'].set_color('white')
        self.ax_main.spines['left'].set_color('white')
        
        # Configure volume chart
        self.ax_volume.set_facecolor('#1e1e1e')
        self.ax_volume.spines['bottom'].set_color('white')
        self.ax_volume.spines['top'].set_color('white')
        self.ax_volume.spines['right'].set_color('white')
        self.ax_volume.spines['left'].set_color('white')
        
        # Set initial data
        self.load_sample_data()
        
    def setup_timer(self):
        """Setup the update timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_realtime_data)
        self.timer.start(30000)  # Update every 30 seconds to reduce warnings
        
    def load_sample_data(self):
        """Load sample data for demonstration."""
        # Generate sample OHLCV data (reduced to prevent ticker issues)
        dates = pd.date_range(start='2024-11-01', end='2024-12-31', freq='h')
        n = len(dates)
        
        # Generate realistic price data
        np.random.seed(42)
        base_price = 1.1000
        returns = np.random.normal(0, 0.001, n)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # Generate realistic OHLC from price
            high = price * (1 + abs(np.random.normal(0, 0.0005)))
            low = price * (1 - abs(np.random.normal(0, 0.0005)))
            open_price = prices[i-1] if i > 0 else price
            close = price
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'Date': date,
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close,
                'Volume': volume
            })
        
        self.data = pd.DataFrame(data)
        self.data.set_index('Date', inplace=True)
        
        # Generate some sample signals
        self.generate_sample_signals()
        
        self.update_chart()
        
    def generate_sample_signals(self):
        """Generate sample trading signals."""
        if self.data is None or len(self.data) < 50:
            return
            
        # Generate SMA crossover signals
        sma_20 = self.data['Close'].rolling(20).mean()
        sma_50 = self.data['Close'].rolling(50).mean()
        
        self.signals = []
        for i in range(50, len(self.data)):
            if sma_20.iloc[i] > sma_50.iloc[i] and sma_20.iloc[i-1] <= sma_50.iloc[i-1]:
                self.signals.append({
                    'date': self.data.index[i],
                    'price': self.data['Close'].iloc[i],
                    'signal': 1,  # Buy
                    'type': 'SMA Crossover'
                })
            elif sma_20.iloc[i] < sma_50.iloc[i] and sma_20.iloc[i-1] >= sma_50.iloc[i-1]:
                self.signals.append({
                    'date': self.data.index[i],
                    'price': self.data['Close'].iloc[i],
                    'signal': -1,  # Sell
                    'type': 'SMA Crossover'
                })
        
    def update_chart(self):
        """Update the chart display."""
        if self.data is None:
            return
            
        # Clear previous plots
        self.ax_main.clear()
        self.ax_volume.clear()
        
        # Get visible data range
        visible_data = self.get_visible_data()
        if visible_data.empty:
            return
            
        # Plot candlesticks
        self.plot_candlesticks(visible_data)
        
        # Plot indicators
        self.plot_indicators(visible_data)
        
        # Plot signals
        if self.show_signals_check.isChecked():
            self.plot_signals(visible_data)
            
        # Plot trades
        if self.show_trades_check.isChecked():
            self.plot_trades(visible_data)
        
        # Plot volume
        self.plot_volume(visible_data)
        
        # Update layout
        self.fig.tight_layout()
        self.canvas.draw()
        
        # Update status
        self.update_status(visible_data)
        
    def get_visible_data(self) -> pd.DataFrame:
        """Get the visible data range based on zoom and pan."""
        if self.data is None or self.data.empty:
            return pd.DataFrame()
            
        total_bars = len(self.data)
        visible_bars = int(total_bars * (self.zoom_level / 100))
        
        start_idx = max(0, total_bars - visible_bars - self.pan_offset)
        end_idx = total_bars - self.pan_offset
        
        return self.data.iloc[start_idx:end_idx]
        
    def plot_candlesticks(self, data: pd.DataFrame):
        """Plot candlestick chart."""
        if data.empty:
            return
            
        # Prepare data for candlestick
        ohlc_data = []
        for i, (date, row) in enumerate(data.iterrows()):
            ohlc_data.append([
                mdates.date2num(date),
                row['Open'],
                row['High'],
                row['Low'],
                row['Close']
            ])
        
        # Plot candlesticks
        candlestick_ohlc(self.ax_main, ohlc_data, width=0.6, 
                        colorup='#00ff88', colordown='#ff4444')
        
        # Format x-axis with better tick management
        self.ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        # Use fewer ticks to prevent warnings
        if len(data) > 100:
            interval = max(1, len(data) // 20)  # Max 20 ticks
            self.ax_main.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
        else:
            self.ax_main.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        
        # Set labels
        self.ax_main.set_ylabel('Price', color='white')
        self.ax_main.grid(True, alpha=0.3)
        
    def plot_indicators(self, data: pd.DataFrame):
        """Plot technical indicators."""
        if data.empty or len(data) < 20:
            return
            
        # SMA 20
        if self.sma_check.isChecked():
            sma_20 = data['Close'].rolling(20).mean()
            self.ax_main.plot(data.index, sma_20, '--', color='#ffaa00', linewidth=1, label='SMA 20')
            
        # EMA 20
        if self.ema_check.isChecked():
            ema_20 = data['Close'].ewm(span=20).mean()
            self.ax_main.plot(data.index, ema_20, '-', color='#00aaff', linewidth=1, label='EMA 20')
            
        # Bollinger Bands
        if self.bb_check.isChecked():
            sma_20 = data['Close'].rolling(20).mean()
            std_20 = data['Close'].rolling(20).std()
            upper_band = sma_20 + (std_20 * 2)
            lower_band = sma_20 - (std_20 * 2)
            
            self.ax_main.plot(data.index, upper_band, '-', color='#ff6666', alpha=0.7, label='BB Upper')
            self.ax_main.plot(data.index, lower_band, '-', color='#ff6666', alpha=0.7, label='BB Lower')
            self.ax_main.fill_between(data.index, upper_band, lower_band, alpha=0.1, color='#ff6666')
            
        # RSI (in separate subplot)
        if self.rsi_check.isChecked():
            rsi = self.calculate_rsi(data['Close'])
            if not rsi.empty:
                # Create RSI subplot
                ax_rsi = self.ax_main.inset_axes([0.02, 0.02, 0.3, 0.2])
                ax_rsi.plot(data.index, rsi, color='#ffaa00', linewidth=1)
                ax_rsi.axhline(y=70, color='r', linestyle='--', alpha=0.7)
                ax_rsi.axhline(y=30, color='g', linestyle='--', alpha=0.7)
                ax_rsi.set_ylabel('RSI', color='white', fontsize=8)
                ax_rsi.tick_params(colors='white', labelsize=6)
                ax_rsi.set_ylim(0, 100)
                
    def plot_signals(self, data: pd.DataFrame):
        """Plot trading signals."""
        if not self.signals:
            return
            
        for signal in self.signals:
            if signal['date'] in data.index:
                color = '#00ff00' if signal['signal'] > 0 else '#ff0000'
                marker = '^' if signal['signal'] > 0 else 'v'
                self.ax_main.scatter(signal['date'], signal['price'], 
                                   color=color, marker=marker, s=100, 
                                   zorder=5, alpha=0.8)
                
    def plot_trades(self, data: pd.DataFrame):
        """Plot completed trades."""
        if not self.trades:
            return
            
        for trade in self.trades:
            if trade['entry_time'] in data.index:
                # Entry point
                color = '#00ff00' if trade['side'] > 0 else '#ff0000'
                self.ax_main.scatter(trade['entry_time'], trade['entry_price'], 
                                   color=color, marker='o', s=80, zorder=5)
                
                # Exit point
                if trade['exit_time'] in data.index:
                    exit_color = '#ffaa00' if trade['pnl'] > 0 else '#ff4444'
                    self.ax_main.scatter(trade['exit_time'], trade['exit_price'], 
                                       color=exit_color, marker='x', s=80, zorder=5)
                    
                    # Draw trade line
                    self.ax_main.plot([trade['entry_time'], trade['exit_time']], 
                                    [trade['entry_price'], trade['exit_price']], 
                                    color=exit_color, alpha=0.7, linewidth=2)
                    
    def plot_volume(self, data: pd.DataFrame):
        """Plot volume bars."""
        if data.empty or not self.volume_check.isChecked():
            return
            
        # Plot volume bars
        colors = ['#00ff88' if close >= open_price else '#ff4444' 
                 for close, open_price in zip(data['Close'], data['Open'])]
        
        self.ax_volume.bar(data.index, data['Volume'], color=colors, alpha=0.7)
        self.ax_volume.set_ylabel('Volume', color='white')
        self.ax_volume.grid(True, alpha=0.3)
        
        # Format x-axis with better tick management
        if len(data) > 100:
            interval = max(1, len(data) // 20)  # Max 20 ticks
            self.ax_volume.xaxis.set_major_locator(mdates.HourLocator(interval=interval))
        else:
            self.ax_volume.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        self.ax_volume.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return pd.Series()
            
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def update_status(self, data: pd.DataFrame):
        """Update status bar information."""
        if data.empty:
            return
            
        latest = data.iloc[-1]
        self.price_label.setText(f"Price: {latest['Close']:.5f}")
        
        if len(data) > 1:
            change = latest['Close'] - data.iloc[-2]['Close']
            change_pct = (change / data.iloc[-2]['Close']) * 100
            self.change_label.setText(f"Change: {change:+.5f} ({change_pct:+.2f}%)")
            
        self.time_label.setText(f"Time: {latest.name.strftime('%H:%M:%S')}")
        
    def update_realtime_data(self):
        """Update chart with real-time data."""
        # This would typically fetch new data from a data provider
        # For now, we'll just update the existing data slightly
        if self.data is not None and not self.data.empty:
            # Add a small random change to the last price
            last_price = self.data['Close'].iloc[-1]
            change = np.random.normal(0, 0.0001)
            new_price = last_price * (1 + change)
            
            # Update the last row
            self.data.iloc[-1, self.data.columns.get_loc('Close')] = new_price
            self.data.iloc[-1, self.data.columns.get_loc('High')] = max(
                self.data.iloc[-1]['High'], new_price)
            self.data.iloc[-1, self.data.columns.get_loc('Low')] = min(
                self.data.iloc[-1]['Low'], new_price)
            
            self.update_chart()
            
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change."""
        self.current_symbol = symbol
        self.load_sample_data()  # In real implementation, load new data
        
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change."""
        self.current_timeframe = timeframe
        self.load_sample_data()  # In real implementation, load new data
        
    def on_chart_type_changed(self):
        """Handle chart type change."""
        sender = self.sender()
        
        # Uncheck other buttons
        for btn in [self.candlestick_btn, self.line_btn, self.bar_btn]:
            if btn != sender:
                btn.setChecked(False)
                
        self.update_chart()
        
    def on_zoom_changed(self, value: int):
        """Handle zoom change."""
        self.zoom_level = value
        self.zoom_label.setText(f"{value}%")
        self.update_chart()
        
    def on_mouse_press(self, event):
        """Handle mouse press for panning."""
        if event.inaxes == self.ax_main:
            self.is_dragging = True
            self.last_mouse_pos = event.xdata
            
    def on_mouse_release(self, event):
        """Handle mouse release."""
        self.is_dragging = False
        self.last_mouse_pos = None
        
    def on_mouse_move(self, event):
        """Handle mouse move for panning."""
        if self.is_dragging and event.inaxes == self.ax_main and self.last_mouse_pos:
            delta = int(event.xdata - self.last_mouse_pos) if event.xdata else 0
            self.pan_offset = max(0, self.pan_offset - delta)
            self.last_mouse_pos = event.xdata
            self.update_chart()
            
    def on_scroll(self, event):
        """Handle mouse scroll for zooming."""
        if event.inaxes == self.ax_main:
            if event.button == 'up':
                self.zoom_level = min(200, self.zoom_level + 10)
            elif event.button == 'down':
                self.zoom_level = max(10, self.zoom_level - 10)
                
            self.zoom_slider.setValue(self.zoom_level)
            self.update_chart()
            
    def update_indicators(self):
        """Update indicators when checkboxes change."""
        self.update_chart()
        
    def refresh_chart(self):
        """Refresh the chart data."""
        self.load_sample_data()
        
    def add_trade(self, trade: Dict):
        """Add a completed trade to the chart."""
        self.trades.append(trade)
        self.update_chart()
        
    def add_signal(self, signal: Dict):
        """Add a trading signal to the chart."""
        self.signals.append(signal)
        self.update_chart()
        
    def clear_signals(self):
        """Clear all signals."""
        self.signals.clear()
        self.update_chart()
        
    def clear_trades(self):
        """Clear all trades."""
        self.trades.clear()
        self.update_chart()
        
    def set_data(self, symbol: str, data: pd.DataFrame):
        """Set chart data (compatibility method)."""
        try:
            if data is not None and not data.empty:
                self.data = data.copy()
                self.current_symbol = symbol
                self.update_chart()
                self.append_log(f"Chart data updated for {symbol}")
            else:
                self.append_log(f"No data available for {symbol}")
        except Exception as e:
            self.append_log(f"Error setting chart data: {str(e)}")
            
    def append_log(self, message: str):
        """Append log message (compatibility method)."""
        print(f"[TradingViewChart] {message}")
