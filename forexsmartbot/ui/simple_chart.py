"""Simple, stable chart widget for ForexSmartBot."""

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


class SimpleChart(QWidget):
    """Simple, stable chart widget for ForexSmartBot."""
    
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
        
        self.setup_ui()
        self.setup_chart()
        
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Chart widget (no toolbar to avoid duplicates)
        self.chart_widget = self.create_chart_widget()
        layout.addWidget(self.chart_widget)
        
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
        self.timeframe_combo.addItems(["1h", "4h", "1d", "1w"])
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        layout.addWidget(timeframe_label)
        layout.addWidget(self.timeframe_combo)
        
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_chart)
        layout.addWidget(refresh_btn)
        
        toolbar.setLayout(layout)
        return toolbar
        
    def create_chart_widget(self) -> QWidget:
        """Create the main chart widget."""
        # Create figure with single chart (no volume)
        self.fig = Figure(figsize=(12, 8), facecolor='#1e1e1e')
        self.fig.patch.set_facecolor('#1e1e1e')
        
        # Main price chart (full height)
        self.ax_main = self.fig.add_subplot(1, 1, 1)
        self.ax_main.set_facecolor('#1e1e1e')
        self.ax_main.tick_params(colors='white')
        
        # Create canvas
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: #1e1e1e;")
        
        # Set initial data
        self.load_realtime_data()
        
        return self.canvas
        
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
        
    def load_realtime_data(self):
        """Load real-time data for demonstration."""
        # Generate real-time OHLCV data (last 24 hours)
        now = datetime.now()
        start_time = now - timedelta(hours=24)
        dates = pd.date_range(start=start_time, end=now, freq='5min')
        n = len(dates)
        
        # Generate realistic price data with current time
        np.random.seed(int(now.timestamp()))
        base_price = 1.1000
        returns = np.random.normal(0, 0.0001, n)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # Generate realistic OHLC from price
            high = price * (1 + abs(np.random.normal(0, 0.0002)))
            low = price * (1 - abs(np.random.normal(0, 0.0002)))
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
        
    def load_sample_data(self):
        """Load sample data for demonstration (fallback)."""
        self.load_realtime_data()
        
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
        
        # Get visible data range (limit to prevent ticker issues)
        visible_data = self.data.tail(200)  # Show only last 200 points
        
        # Plot candlesticks
        self.plot_candlesticks(visible_data)
        
        # Plot signals
        self.plot_signals(visible_data)
        
        # Update layout
        self.fig.tight_layout()
        self.canvas.draw()
        
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
        
        # Format x-axis with real-time formatting
        self.ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        # Use fewer ticks to prevent warnings
        if len(data) > 50:
            interval = max(1, len(data) // 10)  # Max 10 ticks
            self.ax_main.xaxis.set_major_locator(mdates.MinuteLocator(interval=interval*5))
        else:
            self.ax_main.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        
        # Set labels
        self.ax_main.set_ylabel('Price', color='white')
        self.ax_main.grid(True, alpha=0.3)
        
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
                
        
    def on_symbol_changed(self, symbol: str):
        """Handle symbol change."""
        self.current_symbol = symbol
        self.load_sample_data()  # In real implementation, load new data
        
    def on_timeframe_changed(self, timeframe: str):
        """Handle timeframe change."""
        self.current_timeframe = timeframe
        self.load_sample_data()  # In real implementation, load new data
        
    def refresh_chart(self):
        """Refresh the chart data."""
        self.load_sample_data()
        
    def set_data(self, symbol: str, data: pd.DataFrame):
        """Set chart data (compatibility method)."""
        try:
            if data is not None and not data.empty:
                self.data = data.copy()
                self.current_symbol = symbol
                self.update_chart()
                print(f"[SimpleChart] Chart data updated for {symbol}")
            else:
                print(f"[SimpleChart] No data available for {symbol}")
        except Exception as e:
            print(f"[SimpleChart] Error setting chart data: {str(e)}")
            
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
