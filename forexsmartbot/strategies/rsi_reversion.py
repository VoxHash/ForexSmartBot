"""RSI Reversion strategy."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class RSIRevertion(IStrategy):
    """RSI mean reversion strategy with trend filter."""
    
    def __init__(self, rsi_period: int = 14, oversold_level: float = 30.0, 
                 overbought_level: float = 70.0, trend_period: int = 50,
                 atr_period: int = 14):
        self._rsi_period = rsi_period
        self._oversold_level = oversold_level
        self._overbought_level = overbought_level
        self._trend_period = trend_period
        self._atr_period = atr_period
        self._name = "RSI Reversion"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'rsi_period': self._rsi_period,
            'oversold_level': self._oversold_level,
            'overbought_level': self._overbought_level,
            'trend_period': self._trend_period,
            'atr_period': self._atr_period
        }
        
    def set_params(self, **kwargs) -> None:
        if 'rsi_period' in kwargs:
            self._rsi_period = int(kwargs['rsi_period'])
        if 'oversold_level' in kwargs:
            self._oversold_level = float(kwargs['oversold_level'])
        if 'overbought_level' in kwargs:
            self._overbought_level = float(kwargs['overbought_level'])
        if 'trend_period' in kwargs:
            self._trend_period = int(kwargs['trend_period'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI, trend filter, and ATR."""
        out = df.copy()
        
        # RSI calculation
        delta = out['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self._rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self._rsi_period).mean()
        rs = gain / loss
        out['RSI'] = 100 - (100 / (1 + rs))
        
        # Trend filter (SMA)
        out['Trend'] = out['Close'].rolling(self._trend_period).mean()
        
        # ATR
        tr = np.maximum(
            out['High'] - out['Low'],
            np.maximum(
                abs(out['High'] - out['Close'].shift(1)),
                abs(out['Low'] - out['Close'].shift(1))
            )
        )
        out['ATR'] = tr.rolling(self._atr_period).mean()
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate RSI reversion signal."""
        if len(df) < max(self._rsi_period, self._trend_period) + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        current_rsi = float(row['RSI'])
        current_price = float(row['Close'])
        trend = float(row['Trend'])
        
        # Check if RSI is valid
        if pd.isna(current_rsi) or pd.isna(current_price) or pd.isna(trend):
            return 0
            
        # Only trade in direction of trend
        if current_price > trend:  # Uptrend
            # Look for oversold conditions
            if (current_rsi < self._oversold_level and 
                float(prev['RSI']) >= self._oversold_level):
                return 1  # Buy signal
                
        elif current_price < trend:  # Downtrend
            # Look for overbought conditions
            if (current_rsi > self._overbought_level and 
                float(prev['RSI']) <= self._overbought_level):
                return -1  # Sell signal
                
        return 0  # Hold
        
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate volatility using ATR."""
        if 'ATR' not in df or len(df) == 0:
            return None
            
        atr = float(df['ATR'].iloc[-1])
        price = float(df['Close'].iloc[-1])
        
        if pd.isna(atr) or pd.isna(price) or price == 0:
            return None
            
        return atr / price
        
    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate stop loss based on ATR."""
        if 'ATR' not in df or len(df) == 0:
            return None
            
        atr = float(df['ATR'].iloc[-1])
        if pd.isna(atr) or atr == 0:
            return None
            
        # 1.5x ATR stop loss for mean reversion
        if side > 0:  # Long position
            return entry_price - (1.5 * atr)
        else:  # Short position
            return entry_price + (1.5 * atr)
            
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit based on RSI levels."""
        if 'RSI' not in df or len(df) == 0:
            return None
            
        current_rsi = float(df['RSI'].iloc[-1])
        if pd.isna(current_rsi):
            return None
            
        # Target RSI levels for exit
        if side > 0:  # Long position
            # Exit when RSI reaches overbought
            target_rsi = self._overbought_level
        else:  # Short position
            # Exit when RSI reaches oversold
            target_rsi = self._oversold_level
            
        # Simple price target based on RSI movement
        rsi_diff = abs(current_rsi - target_rsi)
        if rsi_diff == 0:
            return None
            
        # Estimate price movement based on RSI change
        price_change_pct = rsi_diff / 100.0  # Rough approximation
        price_change = entry_price * price_change_pct
        
        if side > 0:  # Long position
            return entry_price + price_change
        else:  # Short position
            return entry_price - price_change
