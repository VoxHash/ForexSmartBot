"""
Market Depth (Level 2 Order Book) Visualization Module
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MarketDepthWidget(QWidget):
    """Widget for visualizing Level 2 order book (market depth)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bid_data = []
        self.ask_data = []
        self.setup_ui()
        # Load sample data after UI is set up
        QTimer.singleShot(100, self.load_sample_data)
        
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Market Depth (Level 2 Order Book)")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Chart
        self.fig = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
    def update_depth(self, bid_data: List[Tuple[float, float]], 
                    ask_data: List[Tuple[float, float]]):
        """
        Update market depth data.
        
        Args:
            bid_data: List of (price, volume) tuples for bids
            ask_data: List of (price, volume) tuples for asks
        """
        self.bid_data = bid_data
        self.ask_data = ask_data
        self._plot_depth()
        
    def _plot_depth(self):
        """Plot market depth chart."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not self.bid_data and not self.ask_data:
            ax.text(0.5, 0.5, 'No market depth data available', 
                   ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
            return
            
        # Plot bids (green)
        if self.bid_data:
            bid_prices, bid_volumes = zip(*self.bid_data)
            ax.barh(bid_prices, bid_volumes, color='green', alpha=0.6, label='Bids')
            
        # Plot asks (red)
        if self.ask_data:
            ask_prices, ask_volumes = zip(*self.ask_data)
            ax.barh(ask_prices, ask_volumes, color='red', alpha=0.6, label='Asks')
            
        ax.set_xlabel('Volume')
        ax.set_ylabel('Price')
        ax.set_title('Market Depth')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def load_sample_data(self, symbol: str = 'EURUSD'):
        """Load sample market depth data for display."""
        try:
            depth_provider = MarketDepthProvider()
            bid_data, ask_data = depth_provider.get_depth(symbol)
            self.update_depth(bid_data, ask_data)
        except Exception as e:
            print(f"Error loading sample market depth data: {e}")
            import traceback
            traceback.print_exc()


class MarketDepthProvider:
    """Provider for market depth data (simulated for now)."""
    
    def __init__(self):
        self.depth_data = {}
        
    def get_depth(self, symbol: str) -> Tuple[List[Tuple[float, float]], 
                                              List[Tuple[float, float]]]:
        """
        Get market depth for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (bid_data, ask_data) where each is a list of (price, volume) tuples
        """
        # Simulated market depth (in production, this would come from broker API)
        if symbol not in self.depth_data:
            # Generate simulated depth
            base_price = 1.1000 if 'EUR' in symbol else 1.2500
            
            # Generate bid levels (below base price)
            bid_data = []
            for i in range(10):
                price = base_price - (i * 0.0001)
                volume = np.random.uniform(0.1, 1.0)
                bid_data.append((price, volume))
                
            # Generate ask levels (above base price)
            ask_data = []
            for i in range(10):
                price = base_price + (i * 0.0001)
                volume = np.random.uniform(0.1, 1.0)
                ask_data.append((price, volume))
                
            self.depth_data[symbol] = (bid_data, ask_data)
            
        return self.depth_data[symbol]

