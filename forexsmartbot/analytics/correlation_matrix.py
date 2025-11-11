"""
Multi-Currency Correlation Matrix and Heatmaps Module
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
from PyQt6.QtCore import QTimer


class CorrelationMatrixWidget(QWidget):
    """Widget for displaying correlation matrix heatmap."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.correlation_data = None
        self.setup_ui()
        # Load sample data after UI is set up
        QTimer.singleShot(100, self.load_sample_data)
        
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Currency Correlation Matrix")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Chart
        self.fig = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
    def update_correlation(self, correlation_matrix: pd.DataFrame):
        """
        Update correlation matrix.
        
        Args:
            correlation_matrix: DataFrame with correlation values
        """
        self.correlation_data = correlation_matrix
        self._plot_heatmap()
        
    def _plot_heatmap(self):
        """Plot correlation heatmap."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if self.correlation_data is None or self.correlation_data.empty:
            ax.text(0.5, 0.5, 'No correlation data available', 
                   ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
            return
            
        # Create heatmap
        sns.heatmap(self.correlation_data, annot=True, fmt='.2f', 
                   cmap='coolwarm', center=0, vmin=-1, vmax=1,
                   square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
                   ax=ax)
        
        ax.set_title('Currency Correlation Matrix', fontsize=14, fontweight='bold')
        
        self.canvas.draw()
    
    def load_sample_data(self):
        """Load sample correlation data for display."""
        try:
            # Generate sample correlation matrix for major currency pairs
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD']
            
            # Generate realistic correlation matrix
            # EUR/USD and GBP/USD are typically highly correlated
            # USD pairs are typically negatively correlated with EUR/USD
            np.random.seed(42)
            n = len(symbols)
            correlation_matrix = np.eye(n)  # Start with identity matrix
            
            # Set realistic correlations
            for i in range(n):
                for j in range(i + 1, n):
                    if i == 0 and j == 1:  # EUR/USD and GBP/USD
                        corr = 0.85  # High positive correlation
                    elif (i < 2 and j >= 2) or (i >= 2 and j < 2):  # USD pairs vs EUR/GBP
                        corr = -0.6  # Negative correlation
                    elif i >= 2 and j >= 2:  # USD pairs with each other
                        corr = 0.4  # Moderate positive correlation
                    else:
                        corr = np.random.uniform(-0.3, 0.7)
                    
                    correlation_matrix[i, j] = corr
                    correlation_matrix[j, i] = corr
            
            # Convert to DataFrame
            correlation_df = pd.DataFrame(correlation_matrix, index=symbols, columns=symbols)
            self.update_correlation(correlation_df)
            
        except Exception as e:
            print(f"Error loading sample correlation data: {e}")
            import traceback
            traceback.print_exc()


class CorrelationAnalyzer:
    """Analyzer for currency correlations."""
    
    def __init__(self):
        self.price_data = {}
        
    def add_price_data(self, symbol: str, prices: pd.Series):
        """Add price data for a symbol."""
        self.price_data[symbol] = prices
        
    def calculate_correlation(self, symbols: List[str], 
                            period: int = 30) -> pd.DataFrame:
        """
        Calculate correlation matrix for symbols.
        
        Args:
            symbols: List of symbols to analyze
            period: Number of periods to use
            
        Returns:
            DataFrame with correlation matrix
        """
        if not symbols:
            return pd.DataFrame()
            
        # Get returns for each symbol
        returns_data = {}
        for symbol in symbols:
            if symbol in self.price_data:
                prices = self.price_data[symbol]
                if len(prices) > period:
                    prices = prices.tail(period)
                returns = prices.pct_change().dropna()
                returns_data[symbol] = returns
                
        if not returns_data:
            return pd.DataFrame()
            
        # Align returns by date
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()
        
        if returns_df.empty:
            return pd.DataFrame()
            
        # Calculate correlation
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
        
    def get_correlation_summary(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get correlation summary for symbols.
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dictionary with average correlations
        """
        correlation_matrix = self.calculate_correlation(symbols)
        
        if correlation_matrix.empty:
            return {}
            
        summary = {}
        for symbol in symbols:
            if symbol in correlation_matrix.columns:
                # Average correlation with other symbols
                other_symbols = [s for s in symbols if s != symbol]
                correlations = [correlation_matrix.loc[symbol, s] 
                              for s in other_symbols if s in correlation_matrix.columns]
                if correlations:
                    summary[symbol] = np.mean(correlations)
                    
        return summary

