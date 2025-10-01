"""Breakout ATR strategy."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class BreakoutATR(IStrategy):
    """Donchian-like breakout strategy with ATR filter."""
    
    def __init__(self, lookback_period: int = 20, atr_period: int = 14, 
                 atr_multiplier: float = 1.5, min_breakout_pct: float = 0.001):
        self._lookback_period = lookback_period
        self._atr_period = atr_period
        self._atr_multiplier = atr_multiplier
        self._min_breakout_pct = min_breakout_pct
        self._name = "Breakout ATR"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'atr_period': self._atr_period,
            'atr_multiplier': self._atr_multiplier,
            'min_breakout_pct': self._min_breakout_pct
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
        if 'atr_multiplier' in kwargs:
            self._atr_multiplier = float(kwargs['atr_multiplier'])
        if 'min_breakout_pct' in kwargs:
            self._min_breakout_pct = float(kwargs['min_breakout_pct'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Donchian channels and ATR."""
        out = df.copy()
        
        # Donchian channels
        out['Donchian_high'] = out['High'].rolling(self._lookback_period).max()
        out['Donchian_low'] = out['Low'].rolling(self._lookback_period).min()
        out['Donchian_mid'] = (out['Donchian_high'] + out['Donchian_low']) / 2
        
        # ATR
        tr = np.maximum(
            out['High'] - out['Low'],
            np.maximum(
                abs(out['High'] - out['Close'].shift(1)),
                abs(out['Low'] - out['Close'].shift(1))
            )
        )
        out['ATR'] = tr.rolling(self._atr_period).mean()
        
        # ATR filter
        out['ATR_filter'] = out['ATR'] * self._atr_multiplier
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate breakout signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        current_price = float(row['Close'])
        donchian_high = float(row['Donchian_high'])
        donchian_low = float(row['Donchian_low'])
        atr_filter = float(row['ATR_filter'])
        
        # Check for valid breakout (more sensitive)
        breakout_pct = (donchian_high - donchian_low) / donchian_low
        
        if breakout_pct < self._min_breakout_pct:
            return 0  # Not enough volatility
            
        # Breakout above Donchian high (more sensitive)
        if current_price > donchian_high:
            return 1  # Buy signal
            
        # Breakout below Donchian low (more sensitive)
        if current_price < donchian_low:
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
        """Calculate stop loss based on Donchian channel."""
        if len(df) == 0:
            return None
            
        row = df.iloc[-1]
        donchian_low = float(row['Donchian_low'])
        donchian_high = float(row['Donchian_high'])
        
        if side > 0:  # Long position
            return donchian_low
        else:  # Short position
            return donchian_high
            
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit based on ATR."""
        if 'ATR' not in df or len(df) == 0:
            return None
            
        atr = float(df['ATR'].iloc[-1])
        if pd.isna(atr) or atr == 0:
            return None
            
        # 2:1 risk/reward ratio
        if side > 0:  # Long position
            return entry_price + (2 * atr)
        else:  # Short position
            return entry_price - (2 * atr)
