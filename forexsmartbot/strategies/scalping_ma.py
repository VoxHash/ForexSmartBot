"""Scalping Moving Average strategy for medium-risk trading."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class ScalpingMA(IStrategy):
    """Medium-risk scalping strategy using multiple moving averages."""
    
    def __init__(self, ema_fast: int = 5, ema_medium: int = 10, ema_slow: int = 20,
                 rsi_period: int = 14, rsi_oversold: float = 35, rsi_overbought: float = 65,
                 atr_period: int = 14, lookback_period: int = 20):
        self._ema_fast = ema_fast
        self._ema_medium = ema_medium
        self._ema_slow = ema_slow
        self._rsi_period = rsi_period
        self._rsi_oversold = rsi_oversold
        self._rsi_overbought = rsi_overbought
        self._atr_period = atr_period
        self._lookback_period = lookback_period
        self._name = "Scalping MA"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'ema_fast': self._ema_fast,
            'ema_medium': self._ema_medium,
            'ema_slow': self._ema_slow,
            'rsi_period': self._rsi_period,
            'rsi_oversold': self._rsi_oversold,
            'rsi_overbought': self._rsi_overbought,
            'atr_period': self._atr_period,
            'lookback_period': self._lookback_period
        }
        
    def set_params(self, **kwargs) -> None:
        if 'ema_fast' in kwargs:
            self._ema_fast = int(kwargs['ema_fast'])
        if 'ema_medium' in kwargs:
            self._ema_medium = int(kwargs['ema_medium'])
        if 'ema_slow' in kwargs:
            self._ema_slow = int(kwargs['ema_slow'])
        if 'rsi_period' in kwargs:
            self._rsi_period = int(kwargs['rsi_period'])
        if 'rsi_oversold' in kwargs:
            self._rsi_oversold = float(kwargs['rsi_oversold'])
        if 'rsi_overbought' in kwargs:
            self._rsi_overbought = float(kwargs['rsi_overbought'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate scalping MA indicators."""
        out = df.copy()
        
        # Calculate EMAs
        out['EMA_Fast'] = out['Close'].ewm(span=self._ema_fast).mean()
        out['EMA_Medium'] = out['Close'].ewm(span=self._ema_medium).mean()
        out['EMA_Slow'] = out['Close'].ewm(span=self._ema_slow).mean()
        
        # Calculate RSI
        delta = out['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self._rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self._rsi_period).mean()
        rs = gain / loss
        out['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate ATR
        tr = np.maximum(
            out['High'] - out['Low'],
            np.maximum(
                abs(out['High'] - out['Close'].shift(1)),
                abs(out['Low'] - out['Close'].shift(1))
            )
        )
        out['ATR'] = tr.rolling(self._atr_period, min_periods=1).mean()
        
        # Calculate MA alignment
        out['MA_Alignment'] = 0
        out.loc[out['EMA_Fast'] > out['EMA_Medium'], 'MA_Alignment'] = 1
        out.loc[out['EMA_Medium'] > out['EMA_Slow'], 'MA_Alignment'] = out['MA_Alignment'] + 1
        out.loc[out['EMA_Fast'] < out['EMA_Medium'], 'MA_Alignment'] = -1
        out.loc[out['EMA_Medium'] < out['EMA_Slow'], 'MA_Alignment'] = out['MA_Alignment'] - 1
        
        # Calculate price distance from MAs
        out['Price_Distance_Fast'] = (out['Close'] - out['EMA_Fast']) / out['EMA_Fast']
        out['Price_Distance_Medium'] = (out['Close'] - out['EMA_Medium']) / out['EMA_Medium']
        
        # Calculate momentum
        out['Momentum'] = out['Close'].pct_change(3)
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate scalping MA signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        rsi = float(row.get('RSI', 50))
        ma_alignment = float(row.get('MA_Alignment', 0))
        prev_ma_alignment = float(prev.get('MA_Alignment', 0))
        
        price_dist_fast = float(row.get('Price_Distance_Fast', 0))
        price_dist_medium = float(row.get('Price_Distance_Medium', 0))
        momentum = float(row.get('Momentum', 0))
        
        # Check for valid values
        if pd.isna(rsi) or pd.isna(ma_alignment) or pd.isna(momentum):
            return 0
        
        # More sensitive bullish alignment
        if (ma_alignment >= 1 and rsi < 60 and 
            price_dist_fast > -0.002 and momentum > -0.001):
            return 1  # Buy signal
            
        # More sensitive bearish alignment
        elif (ma_alignment <= -1 and rsi > 40 and 
              price_dist_fast < 0.002 and momentum < 0.001):
            return -1  # Sell signal
            
        # MA alignment change signals (more sensitive)
        elif (ma_alignment > prev_ma_alignment and ma_alignment >= 0 and 
              rsi < 65 and momentum > -0.002):
            return 1  # Buy signal
            
        elif (ma_alignment < prev_ma_alignment and ma_alignment <= 0 and 
              rsi > 35 and momentum < 0.002):
            return -1  # Sell signal
            
        # RSI divergence signals (more sensitive)
        elif (rsi < 45 and ma_alignment >= -1 and 
              price_dist_medium < 0.005):
            return 1  # Buy signal
            
        elif (rsi > 55 and ma_alignment <= 1 and 
              price_dist_medium > -0.005):
            return -1  # Sell signal
        
        # Simple momentum signals
        elif momentum > 0.001 and rsi < 60:
            return 1  # Buy signal
        elif momentum < -0.001 and rsi > 40:
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
    
    def stop_loss(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate stop loss level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 0.99  # 1% stop loss fallback
            
        return current_price - (1 * atr)  # 1 ATR stop loss
    
    def take_profit(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate take profit level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 1.01  # 1% take profit fallback
            
        return current_price + (1.5 * atr)  # 1.5 ATR take profit
