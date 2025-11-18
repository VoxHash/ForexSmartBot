"""
Enhanced Chart Widget for ForexSmartBot
Features: Candlesticks, Real-time updates, Strategy indicators, Trading signals
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class EnhancedChartWidget(QWidget):
    """Enhanced widget for displaying candlestick charts with strategy indicators."""
    
    # Signals
    signal_updated = pyqtSignal(str)  # Emitted when chart is updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self.trades = []
        self.strategy_signals = {}
        self.data_provider = None
        
        # Try to get data provider from parent
        if parent and hasattr(parent, 'data_provider'):
            self.data_provider = parent.data_provider
        
        self.setup_ui()
        
        # Real-time update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_realtime_data)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Load initial data after UI is set up
        # Use QTimer.singleShot to ensure UI is fully initialized
        QTimer.singleShot(100, self.load_initial_data)
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'])
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        controls_layout.addWidget(QLabel("Symbol:"))
        controls_layout.addWidget(self.symbol_combo)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(['1D', '1W', '1M', '3M', '6M', '1Y'])
        self.period_combo.setCurrentText('3M')
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        controls_layout.addWidget(QLabel("Period:"))
        controls_layout.addWidget(self.period_combo)
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['SMA_Crossover', 'RSI_Reversion', 'BreakoutATR', 'All'])
        self.strategy_combo.setCurrentText('All')
        self.strategy_combo.currentTextChanged.connect(self.update_chart)
        controls_layout.addWidget(QLabel("Strategy:"))
        controls_layout.addWidget(self.strategy_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_chart)
        controls_layout.addWidget(self.refresh_button)
        
        self.realtime_button = QPushButton("Real-time ON")
        self.realtime_button.setCheckable(True)
        self.realtime_button.setChecked(True)
        self.realtime_button.clicked.connect(self.toggle_realtime)
        controls_layout.addWidget(self.realtime_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Chart
        self.figure = Figure(figsize=(14, 10))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def set_data(self, symbol: str, data: pd.DataFrame):
        """Set price data for a symbol."""
        if data is None or data.empty:
            return
            
        self.data[symbol] = data
        if symbol not in [self.symbol_combo.itemText(i) for i in range(self.symbol_combo.count())]:
            self.symbol_combo.addItem(symbol)
        
        # Update chart if this is the current symbol
        if self.symbol_combo.currentText() == symbol or self.symbol_combo.count() == 1:
            self.update_chart()
            
    def add_trade(self, trade: Dict):
        """Add a trade mark to the chart."""
        self.trades.append(trade)
        self.update_chart()
        
    def add_strategy_signal(self, symbol: str, signal: Dict):
        """Add a strategy signal to the chart."""
        if symbol not in self.strategy_signals:
            self.strategy_signals[symbol] = []
        self.strategy_signals[symbol].append(signal)
        self.update_chart()
        
    def clear_trades(self):
        """Clear all trade marks."""
        self.trades.clear()
        self.update_chart()
        
    def on_symbol_changed(self):
        """Handle symbol change."""
        symbol = self.symbol_combo.currentText()
        if symbol not in self.data or self.data[symbol].empty:
            self.load_initial_data()
        else:
            self.update_chart()
    
    def on_period_changed(self):
        """Handle period change."""
        self.load_initial_data()
    
    def toggle_realtime(self):
        """Toggle real-time updates."""
        if self.realtime_button.isChecked():
            self.update_timer.start(5000)
            self.realtime_button.setText("Real-time ON")
        else:
            self.update_timer.stop()
            self.realtime_button.setText("Real-time OFF")
            
    def update_realtime_data(self):
        """Update data in real-time."""
        if not self.realtime_button.isChecked():
            return
            
        symbol = self.symbol_combo.currentText()
        if symbol in self.data:
            # Simulate real-time data update
            self.simulate_realtime_update(symbol)
            self.update_chart()
            
    def simulate_realtime_update(self, symbol: str):
        """Simulate real-time data update."""
        try:
            df = self.data[symbol].copy()
            if df.empty:
                return
                
            # Add new data point (simulate live price)
            last_price = df['Close'].iloc[-1]
            price_change = np.random.normal(0, 0.0001)  # Small random change
            new_price = last_price + price_change
            
            # Create new row
            new_time = df.index[-1] + timedelta(hours=1)
            new_row = pd.Series({
                'Open': last_price,
                'High': max(last_price, new_price) + abs(np.random.normal(0, 0.0001)),
                'Low': min(last_price, new_price) - abs(np.random.normal(0, 0.0001)),
                'Close': new_price,
                'Volume': np.random.randint(1000, 10000)
            }, name=new_time)
            
            # Add to dataframe
            df = pd.concat([df, new_row.to_frame().T])
            
            # Recalculate indicators
            df = self.calculate_indicators(df)
            
            # Update data
            self.data[symbol] = df
            
            # Emit signal
            self.signal_updated.emit(symbol)
            
        except Exception as e:
            print(f"Error updating real-time data: {e}")
            
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        try:
            # SMA indicators
            df['SMA_fast'] = df['Close'].rolling(window=10).mean()
            df['SMA_slow'] = df['Close'].rolling(window=20).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['ATR'] = true_range.rolling(window=14).mean()
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            
            return df
            
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return df
            
    def load_initial_data(self):
        """Load initial chart data."""
        try:
            symbol = self.symbol_combo.currentText()
            
            # Try to get data from data provider
            if self.data_provider:
                try:
                    period_map = {
                        '1D': '1d',
                        '1W': '1wk',
                        '1M': '1mo',
                        '3M': '3mo',
                        '6M': '6mo',
                        '1Y': '1y'
                    }
                    period = period_map.get(self.period_combo.currentText(), '3mo')
                    data = self.data_provider.get_historical_data(symbol, period=period, interval='1h')
                    
                    if data is not None and not data.empty:
                        # Ensure data has required columns
                        if isinstance(data, pd.DataFrame):
                            required_cols = ['Open', 'High', 'Low', 'Close']
                            if all(col in data.columns for col in required_cols):
                                # Calculate indicators
                                data = self.calculate_indicators(data)
                                self.set_data(symbol, data)
                                return
                except Exception as e:
                    print(f"Error loading data from provider: {e}")
            
            # Fallback: Generate sample data
            self.generate_sample_data(symbol)
            
        except Exception as e:
            print(f"Error loading initial data: {e}")
            # Generate sample data as fallback
            self.generate_sample_data(self.symbol_combo.currentText())
    
    def generate_sample_data(self, symbol: str):
        """Generate sample candlestick data for display."""
        try:
            # Generate 100 days of sample data
            dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
            
            # Generate realistic price movements
            base_price = 1.1000 if 'EUR' in symbol else 1.3000 if 'GBP' in symbol else 150.0 if 'JPY' in symbol else 0.7500 if 'AUD' in symbol else 1.3500
            
            np.random.seed(42)  # For reproducibility
            returns = np.random.normal(0, 0.001, len(dates))
            prices = base_price * (1 + returns).cumprod()
            
            # Create OHLC data
            data = pd.DataFrame({
                'Open': prices * (1 + np.random.normal(0, 0.0002, len(dates))),
                'High': prices * (1 + abs(np.random.normal(0, 0.0005, len(dates)))),
                'Low': prices * (1 - abs(np.random.normal(0, 0.0005, len(dates)))),
                'Close': prices,
                'Volume': np.random.randint(1000, 10000, len(dates))
            }, index=dates)
            
            # Ensure High >= max(Open, Close) and Low <= min(Open, Close)
            data['High'] = data[['Open', 'Close', 'High']].max(axis=1)
            data['Low'] = data[['Open', 'Close', 'Low']].min(axis=1)
            
            # Calculate indicators
            data = self.calculate_indicators(data)
            
            self.set_data(symbol, data)
            
        except Exception as e:
            print(f"Error generating sample data: {e}")
    
    def update_chart(self):
        """Update the chart display."""
        symbol = self.symbol_combo.currentText()
        
        # If no data for current symbol, try to load it
        if symbol not in self.data or self.data[symbol].empty:
            self.load_initial_data()
            return
        
        df = self.data[symbol]
        if df.empty:
            return
            
        # Clear previous plots
        self.figure.clear()
        
        # Create subplots
        ax1 = self.figure.add_subplot(211)  # Price chart
        ax2 = self.figure.add_subplot(212)  # Volume chart
        
        # Plot candlestick chart
        self.plot_candlesticks(ax1, df)
        
        # Plot strategy indicators
        strategy = self.strategy_combo.currentText()
        self.plot_strategy_indicators(ax1, df, strategy)
        
        # Plot volume and technical indicators
        self.plot_volume_indicators(ax2, df)
        
        # Plot trade marks
        self.plot_trade_marks(ax1, symbol)
        
        # Formatting
        ax1.set_title(f'{symbol} - Candlestick Chart with Strategy Indicators', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        if ax1.get_legend_handles_labels()[0]:
            ax1.legend(loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        ax2.set_title('Volume & Technical Indicators', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Volume / Indicators', fontsize=12)
        if ax2.get_legend_handles_labels()[0]:
            ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
            
        # Refresh canvas
        self.canvas.draw()
        
    def plot_candlesticks(self, ax, df):
        """Plot candlestick chart."""
        try:
            # Convert index to matplotlib dates
            dates = mdates.date2num(df.index)
            
            # Plot candlesticks
            for i, (date, row) in enumerate(zip(dates, df.itertuples())):
                # Determine color
                if hasattr(row, 'Close') and hasattr(row, 'Open'):
                    color = 'green' if row.Close >= row.Open else 'red'
                    edge_color = 'darkgreen' if row.Close >= row.Open else 'darkred'
                else:
                    color = 'blue'
                    edge_color = 'darkblue'
                
                # High-Low line
                ax.plot([date, date], [row.Low, row.High], color='black', linewidth=0.8)
                
                # Open-Close rectangle
                body_height = abs(row.Close - row.Open)
                body_bottom = min(row.Open, row.Close)
                
                rect = Rectangle((date - 0.3, body_bottom), 0.6, body_height, 
                               facecolor=color, edgecolor=edge_color, alpha=0.8)
                ax.add_patch(rect)
                
        except Exception as e:
            # Fallback to line chart if candlestick fails
            ax.plot(df.index, df['Close'], label='Close', linewidth=2, color='blue')
            
    def plot_strategy_indicators(self, ax, df, strategy):
        """Plot strategy indicators on price chart."""
        try:
            if strategy == 'All' or strategy == 'SMA_Crossover':
                # SMA Crossover Strategy
                if 'SMA_fast' in df.columns and 'SMA_slow' in df.columns:
                    ax.plot(df.index, df['SMA_fast'], label='SMA Fast (10)', alpha=0.8, color='orange', linewidth=2)
                    ax.plot(df.index, df['SMA_slow'], label='SMA Slow (20)', alpha=0.8, color='red', linewidth=2)
                    
                    # Highlight crossover signals
                    if len(df) > 1:
                        crossover_up = (df['SMA_fast'].iloc[1:] > df['SMA_slow'].iloc[1:]) & (df['SMA_fast'].iloc[:-1] <= df['SMA_slow'].iloc[:-1])
                        crossover_down = (df['SMA_fast'].iloc[1:] < df['SMA_slow'].iloc[1:]) & (df['SMA_fast'].iloc[:-1] >= df['SMA_slow'].iloc[:-1])
                        
                        if crossover_up.any():
                            up_signals = df.iloc[1:][crossover_up]
                            ax.scatter(up_signals.index, up_signals['Close'], color='green', marker='^', s=120, label='SMA Buy Signal', alpha=0.9, edgecolors='black', linewidth=1)
                        
                        if crossover_down.any():
                            down_signals = df.iloc[1:][crossover_down]
                            ax.scatter(down_signals.index, down_signals['Close'], color='red', marker='v', s=120, label='SMA Sell Signal', alpha=0.9, edgecolors='black', linewidth=1)
            
            if strategy == 'All' or strategy == 'RSI_Reversion':
                # RSI Reversion Strategy
                if 'RSI' in df.columns:
                    # RSI signals
                    rsi_oversold = df['RSI'] < 30
                    rsi_overbought = df['RSI'] > 70
                    
                    if rsi_oversold.any():
                        oversold_signals = df[rsi_oversold]
                        ax.scatter(oversold_signals.index, oversold_signals['Close'], color='blue', marker='o', s=100, label='RSI Oversold', alpha=0.8, edgecolors='white', linewidth=1)
                    
                    if rsi_overbought.any():
                        overbought_signals = df[rsi_overbought]
                        ax.scatter(overbought_signals.index, overbought_signals['Close'], color='orange', marker='o', s=100, label='RSI Overbought', alpha=0.8, edgecolors='white', linewidth=1)
            
            if strategy == 'All' or strategy == 'BreakoutATR':
                # ATR Breakout Strategy
                if 'ATR' in df.columns:
                    # Add ATR bands
                    atr_multiplier = 2.0
                    upper_band = df['Close'] + (df['ATR'] * atr_multiplier)
                    lower_band = df['Close'] - (df['ATR'] * atr_multiplier)
                    
                    ax.plot(df.index, upper_band, label='ATR Upper Band', alpha=0.6, color='purple', linestyle='--', linewidth=1)
                    ax.plot(df.index, lower_band, label='ATR Lower Band', alpha=0.6, color='purple', linestyle='--', linewidth=1)
                    
                    # ATR breakout signals
                    if len(df) > 1:
                        breakout_up = df['Close'] > upper_band.shift(1)
                        breakout_down = df['Close'] < lower_band.shift(1)
                        
                        if breakout_up.any():
                            up_breakouts = df[breakout_up]
                            ax.scatter(up_breakouts.index, up_breakouts['Close'], color='cyan', marker='s', s=100, label='ATR Breakout Up', alpha=0.8, edgecolors='black', linewidth=1)
                        
                        if breakout_down.any():
                            down_breakouts = df[breakout_down]
                            ax.scatter(down_breakouts.index, down_breakouts['Close'], color='magenta', marker='s', s=100, label='ATR Breakout Down', alpha=0.8, edgecolors='black', linewidth=1)
                        
        except Exception as e:
            print(f"Error plotting strategy indicators: {e}")
            
    def plot_volume_indicators(self, ax, df):
        """Plot volume and technical indicators."""
        try:
            # Volume bars
            if 'Volume' in df.columns and not df['Volume'].isna().all():
                ax.bar(df.index, df['Volume'], alpha=0.6, color='blue', label='Volume', width=0.8)
            else:
                # Create sample volume data
                sample_volume = np.random.randint(1000, 10000, len(df))
                ax.bar(df.index, sample_volume, alpha=0.6, color='blue', label='Volume', width=0.8)
            
            # RSI on separate axis
            if 'RSI' in df.columns:
                ax2 = ax.twinx()
                ax2.plot(df.index, df['RSI'], label='RSI', color='purple', alpha=0.8, linewidth=2)
                ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought (70)')
                ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Oversold (30)')
                ax2.set_ylim(0, 100)
                ax2.set_ylabel('RSI', fontsize=10)
                ax2.legend(loc='upper right', fontsize=8)
            
            # MACD if available
            if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
                ax3 = ax.twinx()
                ax3.plot(df.index, df['MACD'], label='MACD', color='blue', alpha=0.8, linewidth=1)
                ax3.plot(df.index, df['MACD_Signal'], label='MACD Signal', color='red', alpha=0.8, linewidth=1)
                ax3.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
                ax3.set_ylabel('MACD', fontsize=10)
                ax3.legend(loc='lower right', fontsize=8)
                
        except Exception as e:
            print(f"Error plotting volume indicators: {e}")
            
    def plot_trade_marks(self, ax, symbol):
        """Plot trade marks on chart."""
        try:
            symbol_trades = [t for t in self.trades if t.get('symbol') == symbol]
            for i, trade in enumerate(symbol_trades):
                if 'entry_time' in trade and 'entry_price' in trade:
                    ax.scatter(trade['entry_time'], trade['entry_price'], 
                               color='green' if trade.get('side', 0) > 0 else 'red',
                               marker='^' if trade.get('side', 0) > 0 else 'v',
                               s=150, alpha=0.9, edgecolors='black', linewidth=2,
                               label='Trade Entry' if i == 0 else "")
        except Exception as e:
            print(f"Error plotting trade marks: {e}")
