"""SMA Crossover strategy."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class SMACrossover(IStrategy):
    """Simple Moving Average Crossover strategy."""
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50, atr_period: int = 14):
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._atr_period = atr_period
        self._name = "SMA Crossover"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'fast_period': self._fast_period,
            'slow_period': self._slow_period,
            'atr_period': self._atr_period
        }
        
    def set_params(self, **kwargs) -> None:
        if 'fast_period' in kwargs:
            self._fast_period = int(kwargs['fast_period'])
        if 'slow_period' in kwargs:
            self._slow_period = int(kwargs['slow_period'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate SMA and ATR indicators."""
        out = df.copy()
        
        # SMAs
        out['SMA_fast'] = out['Close'].rolling(self._fast_period).mean()
        out['SMA_slow'] = out['Close'].rolling(self._slow_period).mean()
        
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
        """Generate trading signal based on SMA crossover."""
        if len(df) < max(self._fast_period, self._slow_period) + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Check for crossover
        if (float(row['SMA_fast']) > float(row['SMA_slow']) and 
            float(prev['SMA_fast']) <= float(prev['SMA_slow'])):
            return 1  # Buy signal
            
        if (float(row['SMA_fast']) < float(row['SMA_slow']) and 
            float(prev['SMA_fast']) >= float(prev['SMA_slow'])):
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
            
        # 2x ATR stop loss
        if side > 0:  # Long position
            return entry_price - (2 * atr)
        else:  # Short position
            return entry_price + (2 * atr)
            
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit based on ATR."""
        if 'ATR' not in df or len(df) == 0:
            return None
            
        atr = float(df['ATR'].iloc[-1])
        if pd.isna(atr) or atr == 0:
            return None
            
        # 3x ATR take profit (1.5:1 risk/reward)
        if side > 0:  # Long position
            return entry_price + (3 * atr)
        else:  # Short position
            return entry_price - (3 * atr)
