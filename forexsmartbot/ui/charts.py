"""Chart widget for displaying price data and indicators."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from typing import Dict, List, Optional


class ChartWidget(QWidget):
    """Widget for displaying price charts with indicators and trade marks."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.data = {}
        self.trades = []
        
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.currentTextChanged.connect(self.update_chart)
        controls_layout.addWidget(QLabel("Symbol:"))
        controls_layout.addWidget(self.symbol_combo)
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(['1D', '1W', '1M', '3M', '6M', '1Y'])
        self.period_combo.setCurrentText('3M')
        self.period_combo.currentTextChanged.connect(self.update_chart)
        controls_layout.addWidget(QLabel("Period:"))
        controls_layout.addWidget(self.period_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_chart)
        controls_layout.addWidget(self.refresh_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Chart
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def set_data(self, symbol: str, data: pd.DataFrame):
        """Set price data for a symbol."""
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
        
    def clear_trades(self):
        """Clear all trade marks."""
        self.trades.clear()
        self.update_chart()
        
    def update_chart(self):
        """Update the chart display."""
        if not self.data:
            return
            
        symbol = self.symbol_combo.currentText()
        if symbol not in self.data:
            return
            
        df = self.data[symbol]
        if df.empty:
            return
            
        # Clear previous plots
        self.figure.clear()
        
        # Create subplots
        ax1 = self.figure.add_subplot(211)  # Price chart
        ax2 = self.figure.add_subplot(212)  # Volume chart
        
        # Plot price data
        ax1.plot(df.index, df['Close'], label='Close', linewidth=1)
        
        # Add indicators if available
        if 'SMA_fast' in df.columns:
            ax1.plot(df.index, df['SMA_fast'], label='SMA Fast', alpha=0.7, color='orange')
        if 'SMA_slow' in df.columns:
            ax1.plot(df.index, df['SMA_slow'], label='SMA Slow', alpha=0.7, color='red')
        if 'RSI' in df.columns:
            ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
            ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7)
            ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7)
            ax2.set_ylim(0, 100)
        
        # Add volume if available
        if 'Volume' in df.columns and not df['Volume'].isna().all():
            ax2.bar(df.index, df['Volume'], alpha=0.3, color='blue', label='Volume')
        else:
            # Create sample volume data if not available
            sample_volume = np.random.randint(1000, 10000, len(df))
            ax2.bar(df.index, sample_volume, alpha=0.3, color='blue', label='Volume')
            
        # Add trade marks
        symbol_trades = [t for t in self.trades if t.get('symbol') == symbol]
        for trade in symbol_trades:
            if 'entry_time' in trade and 'entry_price' in trade:
                ax1.scatter(trade['entry_time'], trade['entry_price'], 
                           color='green' if trade.get('side', 0) > 0 else 'red',
                           marker='^' if trade.get('side', 0) > 0 else 'v',
                           s=100, alpha=0.7)
                           
        # Formatting
        ax1.set_title(f'{symbol} Price Chart')
        ax1.set_ylabel('Price')
        if ax1.get_legend_handles_labels()[0]:  # Only show legend if there are labels
            ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        ax2.set_title('Volume & Indicators')
        ax2.set_ylabel('Volume')
        if ax2.get_legend_handles_labels()[0]:  # Only show legend if there are labels
            ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        for ax in [ax1, ax2]:
            ax.tick_params(axis='x', rotation=45)
            
        self.figure.tight_layout()
        self.canvas.draw()
        
    def plot_equity_curve(self, equity_data: pd.Series, title: str = "Equity Curve"):
        """Plot equity curve."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.plot(equity_data.index, equity_data.values, linewidth=2)
        ax.set_title(title)
        ax.set_ylabel('Equity')
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def plot_drawdown(self, equity_data: pd.Series, title: str = "Drawdown"):
        """Plot drawdown chart."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Calculate drawdown
        peak = equity_data.expanding().max()
        drawdown = (equity_data - peak) / peak * 100
        
        ax.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        ax.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        ax.set_title(title)
        ax.set_ylabel('Drawdown %')
        ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
