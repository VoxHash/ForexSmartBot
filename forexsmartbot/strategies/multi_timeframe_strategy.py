"""Multi-timeframe analysis strategy."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from ..core.interfaces import IStrategy
from ..adapters.data import IDataProvider


class MultiTimeframeStrategy(IStrategy):
    """Strategy that analyzes multiple timeframes simultaneously."""
    
    def __init__(self, base_strategy: IStrategy, timeframes: List[str] = ['1h', '4h', '1d'],
                 timeframe_weights: Optional[Dict[str, float]] = None):
        """
        Initialize multi-timeframe strategy.
        
        Args:
            base_strategy: Base strategy to apply on each timeframe
            timeframes: List of timeframes to analyze (e.g., ['1h', '4h', '1d'])
            timeframe_weights: Optional weights for each timeframe (default: equal weights)
        """
        self._base_strategy = base_strategy
        self._timeframes = timeframes
        self._timeframe_weights = timeframe_weights or {tf: 1.0/len(timeframes) for tf in timeframes}
        self._name = f"Multi-Timeframe {base_strategy.name}"
        self._data_provider = None
        self._timeframe_data = {}
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'base_strategy': self._base_strategy.name,
            'base_params': self._base_strategy.params,
            'timeframes': self._timeframes,
            'timeframe_weights': self._timeframe_weights
        }
        
    def set_params(self, **kwargs) -> None:
        if 'timeframes' in kwargs:
            self._timeframes = kwargs['timeframes']
            self._timeframe_weights = {tf: 1.0/len(self._timeframes) for tf in self._timeframes}
        if 'timeframe_weights' in kwargs:
            self._timeframe_weights = kwargs['timeframe_weights']
        if 'base_params' in kwargs:
            self._base_strategy.set_params(**kwargs['base_params'])
            
    def set_data_provider(self, data_provider: IDataProvider) -> None:
        """Set data provider for fetching multi-timeframe data."""
        self._data_provider = data_provider
        
    def _get_timeframe_data(self, symbol: str, current_time: pd.Timestamp, 
                           lookback_days: int = 30) -> Dict[str, pd.DataFrame]:
        """Get data for all timeframes."""
        if self._data_provider is None:
            return {}
            
        timeframe_data = {}
        end_date = current_time.strftime('%Y-%m-%d')
        start_date = (current_time - pd.Timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        for timeframe in self._timeframes:
            try:
                df = self._data_provider.get_data(symbol, start_date, end_date, timeframe)
                if not df.empty:
                    timeframe_data[timeframe] = df
            except Exception as e:
                print(f"Error fetching {timeframe} data: {e}")
                
        return timeframe_data
        
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators on base timeframe and fetch multi-timeframe data."""
        # Calculate indicators on base data
        out = self._base_strategy.indicators(df)
        
        # Store current timestamp for multi-timeframe analysis
        if len(df) > 0:
            current_time = df.index[-1]
            symbol = getattr(self, '_current_symbol', 'EURUSD=X')
            
            # Get multi-timeframe data
            self._timeframe_data = self._get_timeframe_data(symbol, current_time)
            
            # Calculate indicators for each timeframe
            for timeframe, tf_df in self._timeframe_data.items():
                if not tf_df.empty:
                    try:
                        tf_indicators = self._base_strategy.indicators(tf_df)
                        # Store aggregated indicators
                        out[f'{timeframe}_trend'] = self._calculate_trend(tf_indicators)
                        out[f'{timeframe}_momentum'] = self._calculate_momentum(tf_indicators)
                    except Exception as e:
                        print(f"Error calculating {timeframe} indicators: {e}")
                        
        return out
        
    def _calculate_trend(self, df: pd.DataFrame) -> float:
        """Calculate trend strength from timeframe data."""
        if len(df) < 2:
            return 0.0
            
        # Use SMA crossover as trend indicator
        if 'SMA_20' in df.columns and 'SMA_50' in df.columns:
            sma_fast = df['SMA_20'].iloc[-1]
            sma_slow = df['SMA_50'].iloc[-1]
            if pd.notna(sma_fast) and pd.notna(sma_slow):
                return 1.0 if sma_fast > sma_slow else -1.0
        elif 'Close' in df.columns:
            # Simple price trend
            recent_prices = df['Close'].tail(10)
            if len(recent_prices) >= 2:
                return 1.0 if recent_prices.iloc[-1] > recent_prices.iloc[0] else -1.0
        return 0.0
        
    def _calculate_momentum(self, df: pd.DataFrame) -> float:
        """Calculate momentum from timeframe data."""
        if len(df) < 2 or 'Close' not in df.columns:
            return 0.0
            
        # Calculate rate of change
        prices = df['Close']
        if len(prices) >= 10:
            roc = (prices.iloc[-1] / prices.iloc[-10] - 1) * 100
            return roc if pd.notna(roc) else 0.0
        return 0.0
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate signal based on multi-timeframe consensus."""
        if len(df) < 2:
            return 0
            
        # Get base strategy signal
        base_signal = self._base_strategy.signal(df)
        
        # Get multi-timeframe signals
        timeframe_signals = {}
        for timeframe in self._timeframes:
            trend_key = f'{timeframe}_trend'
            momentum_key = f'{timeframe}_momentum'
            
            if trend_key in df.columns and momentum_key in df.columns:
                trend = float(df[trend_key].iloc[-1]) if pd.notna(df[trend_key].iloc[-1]) else 0
                momentum = float(df[momentum_key].iloc[-1]) if pd.notna(df[momentum_key].iloc[-1]) else 0
                
                # Combine trend and momentum
                if trend > 0 and momentum > 0:
                    timeframe_signals[timeframe] = 1
                elif trend < 0 and momentum < 0:
                    timeframe_signals[timeframe] = -1
                else:
                    timeframe_signals[timeframe] = 0
                    
        # Calculate weighted consensus
        weighted_signal = 0.0
        for timeframe, signal in timeframe_signals.items():
            weight = self._timeframe_weights.get(timeframe, 0)
            weighted_signal += signal * weight
            
        # Base strategy gets 40% weight, multi-timeframe gets 60%
        final_signal = base_signal * 0.4 + weighted_signal * 0.6
        
        # Generate signal based on threshold
        if final_signal > 0.5:
            return 1  # Buy
        elif final_signal < -0.5:
            return -1  # Sell
        else:
            return 0  # Hold
            
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate volatility using base strategy."""
        return self._base_strategy.volatility(df)
        
    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate stop loss using base strategy."""
        return self._base_strategy.stop_loss(df, entry_price, side)
        
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit using base strategy."""
        return self._base_strategy.take_profit(df, entry_price, side)

