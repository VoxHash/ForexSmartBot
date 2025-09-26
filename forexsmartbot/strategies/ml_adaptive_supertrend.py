"""Machine Learning Adaptive SuperTrend strategy based on AlgoAlpha."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from ..core.interfaces import IStrategy


class MLAdaptiveSuperTrend(IStrategy):
    """Machine Learning Adaptive SuperTrend strategy using k-means clustering."""
    
    def __init__(self, lookback_period: int = 20, atr_period: int = 14, 
                 atr_multiplier: float = 2.0, volatility_period: int = 50,
                 n_clusters: int = 3, min_samples: int = 100):
        self._lookback_period = lookback_period
        self._atr_period = atr_period
        self._atr_multiplier = atr_multiplier
        self._volatility_period = volatility_period
        self._n_clusters = n_clusters
        self._min_samples = min_samples
        self._name = "ML Adaptive SuperTrend"
        self._scaler = StandardScaler()
        self._kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self._volatility_clusters = None
        self._adaptive_multipliers = {0: 1.5, 1: 2.0, 2: 2.5}  # Low, Medium, High volatility
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'atr_period': self._atr_period,
            'atr_multiplier': self._atr_multiplier,
            'volatility_period': self._volatility_period,
            'n_clusters': self._n_clusters,
            'min_samples': self._min_samples
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
        if 'atr_multiplier' in kwargs:
            self._atr_multiplier = float(kwargs['atr_multiplier'])
        if 'volatility_period' in kwargs:
            self._volatility_period = int(kwargs['volatility_period'])
        if 'n_clusters' in kwargs:
            self._n_clusters = int(kwargs['n_clusters'])
        if 'min_samples' in kwargs:
            self._min_samples = int(kwargs['min_samples'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ML Adaptive SuperTrend indicators."""
        out = df.copy()
        
        # Calculate ATR with proper handling of NaN values
        tr = np.maximum(
            out['High'] - out['Low'],
            np.maximum(
                abs(out['High'] - out['Close'].shift(1)),
                abs(out['Low'] - out['Close'].shift(1))
            )
        )
        out['ATR'] = tr.rolling(self._atr_period, min_periods=1).mean()
        
        # Fill any remaining NaN values with a small default value
        out['ATR'] = out['ATR'].fillna(0.001)
        
        # Calculate volatility features for ML
        out['Price_Change'] = out['Close'].pct_change()
        out['Volatility'] = out['Price_Change'].rolling(self._volatility_period).std()
        out['ATR_Ratio'] = out['ATR'] / out['Close']
        out['High_Low_Ratio'] = (out['High'] - out['Low']) / out['Close']
        
        # Calculate traditional SuperTrend
        out['HL2'] = (out['High'] + out['Low']) / 2
        out['Upper_Band'] = out['HL2'] + (self._atr_multiplier * out['ATR'])
        out['Lower_Band'] = out['HL2'] - (self._atr_multiplier * out['ATR'])
        
        # Initialize SuperTrend with proper values
        out['SuperTrend'] = 0.0
        out['Direction'] = 1
        
        # Calculate adaptive SuperTrend using vectorized operations where possible
        supertrend_values = np.zeros(len(out))
        direction_values = np.ones(len(out))
        
        for i in range(1, len(out)):
            if i < self._min_samples:
                # Use traditional SuperTrend for initial periods
                if out['Close'].iloc[i] <= out['Lower_Band'].iloc[i-1]:
                    supertrend_values[i] = out['Lower_Band'].iloc[i]
                    direction_values[i] = 1
                elif out['Close'].iloc[i] >= out['Upper_Band'].iloc[i-1]:
                    supertrend_values[i] = out['Upper_Band'].iloc[i]
                    direction_values[i] = -1
                else:
                    supertrend_values[i] = supertrend_values[i-1]
                    direction_values[i] = direction_values[i-1]
            else:
                # Use ML adaptive approach
                adaptive_multiplier = self._get_adaptive_multiplier(out, i)
                
                # Recalculate bands with adaptive multiplier
                upper_band = out['HL2'].iloc[i] + (adaptive_multiplier * out['ATR'].iloc[i])
                lower_band = out['HL2'].iloc[i] - (adaptive_multiplier * out['ATR'].iloc[i])
                
                if out['Close'].iloc[i] <= lower_band:
                    supertrend_values[i] = lower_band
                    direction_values[i] = 1
                elif out['Close'].iloc[i] >= upper_band:
                    supertrend_values[i] = upper_band
                    direction_values[i] = -1
                else:
                    supertrend_values[i] = supertrend_values[i-1]
                    direction_values[i] = direction_values[i-1]
        
        # Assign values using loc to avoid chained assignment warnings
        out.loc[:, 'SuperTrend'] = supertrend_values
        out.loc[:, 'Direction'] = direction_values
        
        # Calculate trend strength
        out['Trend_Strength'] = abs(out['Direction'].diff()).rolling(10).sum()
        
        return out
        
    def _get_adaptive_multiplier(self, df: pd.DataFrame, current_idx: int) -> float:
        """Get adaptive multiplier based on volatility clustering."""
        if current_idx < self._min_samples:
            return self._atr_multiplier
            
        # Prepare features for clustering
        lookback_data = df.iloc[max(0, current_idx - self._volatility_period):current_idx]
        
        if len(lookback_data) < self._min_samples:
            return self._atr_multiplier
            
        # Extract features
        features = lookback_data[['Volatility', 'ATR_Ratio', 'High_Low_Ratio']].dropna()
        
        if len(features) < self._min_samples:
            return self._atr_multiplier
            
        try:
            # Normalize features
            features_scaled = self._scaler.fit_transform(features)
            
            # Perform clustering
            clusters = self._kmeans.fit_predict(features_scaled)
            
            # Get current volatility cluster
            current_features = df.iloc[current_idx][['Volatility', 'ATR_Ratio', 'High_Low_Ratio']].values.reshape(1, -1)
            current_features_scaled = self._scaler.transform(current_features)
            current_cluster = self._kmeans.predict(current_features_scaled)[0]
            
            # Return adaptive multiplier
            return self._adaptive_multipliers.get(current_cluster, self._atr_multiplier)
            
        except Exception:
            return self._atr_multiplier
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate ML Adaptive SuperTrend signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        current_price = float(row['Close'])
        supertrend = float(row['SuperTrend'])
        direction = float(row['Direction'])
        prev_direction = float(prev['Direction'])
        
        # Check for valid values
        if pd.isna(supertrend) or pd.isna(direction) or pd.isna(prev_direction):
            return 0
        
        # Check for trend change (primary signal)
        if direction != prev_direction:
            if direction > 0:  # Bullish trend
                return 1  # Buy signal
            else:  # Bearish trend
                return -1  # Sell signal
        
        # Additional signal conditions for more sensitivity
        atr = float(row.get('ATR', 0))
        if atr > 0:
            # Price breakout above/below SuperTrend with momentum
            price_distance = abs(current_price - supertrend) / atr
            
            # More sensitive thresholds
            if current_price > supertrend and direction > 0 and price_distance > 0.2:
                return 1  # Buy signal
            elif current_price < supertrend and direction < 0 and price_distance > 0.2:
                return -1  # Sell signal
        
        # Simple price momentum signals
        price_change = current_price - float(prev['Close'])
        if price_change > 0 and direction > 0:
            return 1  # Buy signal
        elif price_change < 0 and direction < 0:
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
        """Calculate stop loss based on SuperTrend."""
        if 'SuperTrend' not in df or len(df) == 0:
            return None
            
        supertrend = float(df['SuperTrend'].iloc[-1])
        
        if pd.isna(supertrend):
            return None
            
        return supertrend
        
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
