"""Mean Reversion strategy for low-risk trading."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class MeanReversion(IStrategy):
    """Mean Reversion strategy using Bollinger Bands and RSI."""
    
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 14,
                 rsi_oversold: float = 30, rsi_overbought: float = 70, 
                 lookback_period: int = 20):
        self._bb_period = bb_period
        self._bb_std = bb_std
        self._rsi_period = rsi_period
        self._rsi_oversold = rsi_oversold
        self._rsi_overbought = rsi_overbought
        self._lookback_period = lookback_period
        self._name = "Mean Reversion"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'bb_period': self._bb_period,
            'bb_std': self._bb_std,
            'rsi_period': self._rsi_period,
            'rsi_oversold': self._rsi_oversold,
            'rsi_overbought': self._rsi_overbought,
            'lookback_period': self._lookback_period
        }
        
    def set_params(self, **kwargs) -> None:
        if 'bb_period' in kwargs:
            self._bb_period = int(kwargs['bb_period'])
        if 'bb_std' in kwargs:
            self._bb_std = float(kwargs['bb_std'])
        if 'rsi_period' in kwargs:
            self._rsi_period = int(kwargs['rsi_period'])
        if 'rsi_oversold' in kwargs:
            self._rsi_oversold = float(kwargs['rsi_oversold'])
        if 'rsi_overbought' in kwargs:
            self._rsi_overbought = float(kwargs['rsi_overbought'])
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate mean reversion indicators."""
        out = df.copy()
        
        # Calculate Bollinger Bands
        out['BB_Middle'] = out['Close'].rolling(self._bb_period).mean()
        bb_std = out['Close'].rolling(self._bb_period).std()
        out['BB_Upper'] = out['BB_Middle'] + (self._bb_std * bb_std)
        out['BB_Lower'] = out['BB_Middle'] - (self._bb_std * bb_std)
        
        # Calculate RSI
        delta = out['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self._rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self._rsi_period).mean()
        rs = gain / loss
        out['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate price position within Bollinger Bands
        out['BB_Position'] = (out['Close'] - out['BB_Lower']) / (out['BB_Upper'] - out['BB_Lower'])
        
        # Calculate mean reversion strength
        out['Mean_Reversion_Strength'] = abs(out['BB_Position'] - 0.5) * 2
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate mean reversion signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        rsi = float(row.get('RSI', 50))
        bb_position = float(row.get('BB_Position', 0.5))
        prev_bb_position = float(prev.get('BB_Position', 0.5))
        
        # Check for valid values
        if pd.isna(rsi) or pd.isna(bb_position) or pd.isna(prev_bb_position):
            return 0
        
        # More sensitive mean reversion signals
        if rsi < 40 and bb_position < 0.3:  # More sensitive oversold
            return 1  # Buy signal (oversold)
        elif rsi > 60 and bb_position > 0.7:  # More sensitive overbought
            return -1  # Sell signal (overbought)
        elif bb_position < 0.2 and prev_bb_position >= 0.2:  # More sensitive bounce
            return 1  # Buy signal (bounce from lower band)
        elif bb_position > 0.8 and prev_bb_position <= 0.8:  # More sensitive bounce
            return -1  # Sell signal (bounce from upper band)
        
        # RSI divergence signals
        if rsi < 50 and prev.get('RSI', 50) >= 50:
            return 1  # Buy signal (RSI turning up)
        elif rsi > 50 and prev.get('RSI', 50) <= 50:
            return -1  # Sell signal (RSI turning down)
            
        return 0  # Hold
        
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate volatility using Bollinger Band width."""
        if 'BB_Upper' not in df or 'BB_Lower' not in df or len(df) == 0:
            return None
            
        bb_width = float(df['BB_Upper'].iloc[-1] - df['BB_Lower'].iloc[-1])
        price = float(df['Close'].iloc[-1])
        
        if pd.isna(bb_width) or pd.isna(price) or price == 0:
            return None
            
        return bb_width / price
    
    def stop_loss(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate stop loss level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 0.98  # 2% stop loss fallback
            
        return current_price - (2 * atr)  # 2 ATR stop loss
    
    def take_profit(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate take profit level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 1.02  # 2% take profit fallback
            
        return current_price + (3 * atr)  # 3 ATR take profit
