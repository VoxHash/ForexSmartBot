"""Momentum Breakout strategy for high-risk, high-reward trading."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy


class MomentumBreakout(IStrategy):
    """High-risk momentum breakout strategy using multiple timeframes."""
    
    def __init__(self, fast_ema: int = 12, slow_ema: int = 26, signal_ema: int = 9,
                 atr_period: int = 14, breakout_period: int = 20, 
                 momentum_threshold: float = 0.02, lookback_period: int = 20):
        self._fast_ema = fast_ema
        self._slow_ema = slow_ema
        self._signal_ema = signal_ema
        self._atr_period = atr_period
        self._breakout_period = breakout_period
        self._momentum_threshold = momentum_threshold
        self._lookback_period = lookback_period
        self._name = "Momentum Breakout"
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'fast_ema': self._fast_ema,
            'slow_ema': self._slow_ema,
            'signal_ema': self._signal_ema,
            'atr_period': self._atr_period,
            'breakout_period': self._breakout_period,
            'momentum_threshold': self._momentum_threshold,
            'lookback_period': self._lookback_period
        }
        
    def set_params(self, **kwargs) -> None:
        if 'fast_ema' in kwargs:
            self._fast_ema = int(kwargs['fast_ema'])
        if 'slow_ema' in kwargs:
            self._slow_ema = int(kwargs['slow_ema'])
        if 'signal_ema' in kwargs:
            self._signal_ema = int(kwargs['signal_ema'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
        if 'breakout_period' in kwargs:
            self._breakout_period = int(kwargs['breakout_period'])
        if 'momentum_threshold' in kwargs:
            self._momentum_threshold = float(kwargs['momentum_threshold'])
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum breakout indicators."""
        out = df.copy()
        
        # Calculate EMAs
        out['EMA_Fast'] = out['Close'].ewm(span=self._fast_ema).mean()
        out['EMA_Slow'] = out['Close'].ewm(span=self._slow_ema).mean()
        out['EMA_Signal'] = out['Close'].ewm(span=self._signal_ema).mean()
        
        # Calculate MACD
        out['MACD'] = out['EMA_Fast'] - out['EMA_Slow']
        out['MACD_Signal'] = out['MACD'].ewm(span=self._signal_ema).mean()
        out['MACD_Histogram'] = out['MACD'] - out['MACD_Signal']
        
        # Calculate ATR
        tr = np.maximum(
            out['High'] - out['Low'],
            np.maximum(
                abs(out['High'] - out['Close'].shift(1)),
                abs(out['Low'] - out['Close'].shift(1))
            )
        )
        out['ATR'] = tr.rolling(self._atr_period, min_periods=1).mean()
        
        # Calculate breakout levels
        out['Breakout_High'] = out['High'].rolling(self._breakout_period).max()
        out['Breakout_Low'] = out['Low'].rolling(self._breakout_period).min()
        
        # Calculate momentum
        out['Momentum'] = out['Close'].pct_change(self._breakout_period)
        out['Momentum_Strength'] = abs(out['Momentum'])
        
        # Calculate volume momentum (using price range as proxy)
        out['Volume_Proxy'] = (out['High'] - out['Low']) / out['Close']
        out['Volume_Momentum'] = out['Volume_Proxy'].rolling(5).mean()
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate momentum breakout signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        macd = float(row.get('MACD', 0))
        macd_signal = float(row.get('MACD_Signal', 0))
        macd_hist = float(row.get('MACD_Histogram', 0))
        prev_macd_hist = float(prev.get('MACD_Histogram', 0))
        
        momentum = float(row.get('Momentum', 0))
        momentum_strength = float(row.get('Momentum_Strength', 0))
        
        current_price = float(row['Close'])
        breakout_high = float(row.get('Breakout_High', current_price))
        breakout_low = float(row.get('Breakout_Low', current_price))
        
        # Check for valid values
        if pd.isna(macd) or pd.isna(macd_signal) or pd.isna(momentum):
            return 0
        
        # More sensitive momentum breakout signals
        if (macd > macd_signal and macd_hist > prev_macd_hist and 
            momentum > self._momentum_threshold * 0.5 and 
            current_price > breakout_high * 0.999):
            return 1  # Buy signal
            
        elif (macd < macd_signal and macd_hist < prev_macd_hist and 
              momentum < -self._momentum_threshold * 0.5 and 
              current_price < breakout_low * 1.001):
            return -1  # Sell signal
            
        # MACD crossover signals (more sensitive)
        elif (macd > macd_signal and prev.get('MACD', 0) <= prev.get('MACD_Signal', 0) and
              momentum_strength > self._momentum_threshold * 0.2):
            return 1  # Buy signal
            
        elif (macd < macd_signal and prev.get('MACD', 0) >= prev.get('MACD_Signal', 0) and
              momentum_strength > self._momentum_threshold * 0.2):
            return -1  # Sell signal
        
        # Simple momentum signals
        elif momentum > 0.005 and macd > macd_signal:
            return 1  # Buy signal
        elif momentum < -0.005 and macd < macd_signal:
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
            return current_price * 0.95  # 5% stop loss fallback
            
        return current_price - (1.5 * atr)  # 1.5 ATR stop loss
    
    def take_profit(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate take profit level."""
        if len(df) == 0:
            return None
            
        current_price = float(df['Close'].iloc[-1])
        atr = float(df.get('ATR', pd.Series([0])).iloc[-1])
        
        if pd.isna(atr) or atr == 0:
            return current_price * 1.05  # 5% take profit fallback
            
        return current_price + (2.5 * atr)  # 2.5 ATR take profit
