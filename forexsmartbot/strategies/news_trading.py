"""News Trading strategy for high-risk, high-reward trading."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class NewsTrading(IStrategy):
    """High-risk news trading strategy based on volatility spikes."""
    
    def __init__(self, volatility_period: int = 20, volatility_threshold: float = 0.015,
                 atr_period: int = 14, breakout_period: int = 5, 
                 momentum_period: int = 10, lookback_period: int = 20):
        self._volatility_period = volatility_period
        self._volatility_threshold = volatility_threshold
        self._atr_period = atr_period
        self._breakout_period = breakout_period
        self._momentum_period = momentum_period
        self._lookback_period = lookback_period
        self._name = "News Trading"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'volatility_period': self._volatility_period,
            'volatility_threshold': self._volatility_threshold,
            'atr_period': self._atr_period,
            'breakout_period': self._breakout_period,
            'momentum_period': self._momentum_period,
            'lookback_period': self._lookback_period
        }
        
    def set_params(self, **kwargs) -> None:
        if 'volatility_period' in kwargs:
            self._volatility_period = int(kwargs['volatility_period'])
        if 'volatility_threshold' in kwargs:
            self._volatility_threshold = float(kwargs['volatility_threshold'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
        if 'breakout_period' in kwargs:
            self._breakout_period = int(kwargs['breakout_period'])
        if 'momentum_period' in kwargs:
            self._momentum_period = int(kwargs['momentum_period'])
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate news trading indicators."""
        out = df.copy()
        
        # Calculate price changes
        out['Price_Change'] = out['Close'].pct_change()
        out['High_Low_Range'] = (out['High'] - out['Low']) / out['Close']
        
        # Calculate volatility
        out['Volatility'] = out['Price_Change'].rolling(self._volatility_period).std()
        out['Volatility_Ratio'] = out['Volatility'] / out['Volatility'].rolling(50).mean()
        
        # Calculate ATR
        tr = np.maximum(
            out['High'] - out['Low'],
            np.maximum(
                abs(out['High'] - out['Close'].shift(1)),
                abs(out['Low'] - out['Close'].shift(1))
            )
        )
        out['ATR'] = tr.rolling(self._atr_period, min_periods=1).mean()
        out['ATR_Ratio'] = out['ATR'] / out['Close']
        
        # Calculate momentum
        out['Momentum'] = out['Close'].pct_change(self._momentum_period)
        out['Momentum_Strength'] = abs(out['Momentum'])
        
        # Calculate breakout levels
        out['Breakout_High'] = out['High'].rolling(self._breakout_period).max()
        out['Breakout_Low'] = out['Low'].rolling(self._breakout_period).min()
        
        # Calculate news impact score
        out['News_Impact'] = (out['Volatility_Ratio'] * out['ATR_Ratio'] * 
                             out['Momentum_Strength'] * 100)
        
        # Calculate trend strength
        out['Trend_Strength'] = out['Close'].rolling(10).apply(
            lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1
        )
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate news trading signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        volatility_ratio = float(row.get('Volatility_Ratio', 1))
        atr_ratio = float(row.get('ATR_Ratio', 0))
        news_impact = float(row.get('News_Impact', 0))
        momentum = float(row.get('Momentum', 0))
        trend_strength = float(row.get('Trend_Strength', 0))
        
        current_price = float(row['Close'])
        breakout_high = float(row.get('Breakout_High', current_price))
        breakout_low = float(row.get('Breakout_Low', current_price))
        
        # Check for valid values
        if pd.isna(volatility_ratio) or pd.isna(momentum) or pd.isna(news_impact):
            return 0
        
        # More sensitive volatility detection
        if (volatility_ratio > 1.5 and atr_ratio > self._volatility_threshold * 0.5 and 
            news_impact > 25):
            
            # Bullish momentum with breakout
            if (momentum > 0.005 and current_price > breakout_high * 0.999 and 
                trend_strength > 0):
                return 1  # Buy signal
                
            # Bearish momentum with breakdown
            elif (momentum < -0.005 and current_price < breakout_low * 1.001 and 
                  trend_strength < 0):
                return -1  # Sell signal
                
        # Moderate volatility with momentum
        elif (volatility_ratio > 1.2 and news_impact > 15):
            
            # Bullish momentum
            if (momentum > 0.003 and trend_strength > 0 and 
                current_price > row.get('Close', current_price) * 1.0002):
                return 1  # Buy signal
                
            # Bearish momentum
            elif (momentum < -0.003 and trend_strength < 0 and 
                  current_price < row.get('Close', current_price) * 0.9998):
                return -1  # Sell signal
        
        # Simple momentum signals
        elif momentum > 0.01 and volatility_ratio > 1.1:
            return 1  # Buy signal
        elif momentum < -0.01 and volatility_ratio > 1.1:
            return -1  # Sell signal
                
        return 0  # Hold
        
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate volatility using ATR ratio."""
        if 'ATR_Ratio' not in df or len(df) == 0:
            return None
            
        atr_ratio = float(df['ATR_Ratio'].iloc[-1])
        
        if pd.isna(atr_ratio):
            return None
            
        return atr_ratio
    
    def stop_loss(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate stop loss level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 0.90  # 10% stop loss fallback for high volatility
            
        return current_price - (3 * atr)  # 3 ATR stop loss for news trading
    
    def take_profit(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate take profit level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 1.10  # 10% take profit fallback for high volatility
            
        return current_price + (5 * atr)  # 5 ATR take profit for news trading
