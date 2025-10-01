"""Adaptive Trend Flow strategy based on QuantAlgo."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from ..core.interfaces import IStrategy


class AdaptiveTrendFlow(IStrategy):
    """Adaptive Trend Flow strategy using machine learning for trend detection."""
    
    def __init__(self, lookback_period: int = 20, ema_fast: int = 12, ema_slow: int = 26,
                 rsi_period: int = 14, atr_period: int = 14, ml_period: int = 50,
                 trend_threshold: float = 0.6, min_samples: int = 100):
        self._lookback_period = lookback_period
        self._ema_fast = ema_fast
        self._ema_slow = ema_slow
        self._rsi_period = rsi_period
        self._atr_period = atr_period
        self._ml_period = ml_period
        self._trend_threshold = trend_threshold
        self._min_samples = min_samples
        self._name = "Adaptive Trend Flow"
        self._scaler = StandardScaler()
        self._ml_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self._is_trained = False
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'ema_fast': self._ema_fast,
            'ema_slow': self._ema_slow,
            'rsi_period': self._rsi_period,
            'atr_period': self._atr_period,
            'ml_period': self._ml_period,
            'trend_threshold': self._trend_threshold,
            'min_samples': self._min_samples
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'ema_fast' in kwargs:
            self._ema_fast = int(kwargs['ema_fast'])
        if 'ema_slow' in kwargs:
            self._ema_slow = int(kwargs['ema_slow'])
        if 'rsi_period' in kwargs:
            self._rsi_period = int(kwargs['rsi_period'])
        if 'atr_period' in kwargs:
            self._atr_period = int(kwargs['atr_period'])
        if 'ml_period' in kwargs:
            self._ml_period = int(kwargs['ml_period'])
        if 'trend_threshold' in kwargs:
            self._trend_threshold = float(kwargs['trend_threshold'])
        if 'min_samples' in kwargs:
            self._min_samples = int(kwargs['min_samples'])
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Adaptive Trend Flow indicators."""
        out = df.copy()
        
        # Calculate EMAs
        out['EMA_fast'] = out['Close'].ewm(span=self._ema_fast).mean()
        out['EMA_slow'] = out['Close'].ewm(span=self._ema_slow).mean()
        
        # Calculate RSI
        delta = out['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self._rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self._rsi_period).mean()
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
        out['ATR'] = tr.rolling(self._atr_period).mean()
        
        # Calculate price momentum features
        out['Price_Momentum'] = out['Close'].pct_change(5)
        out['Volume_Momentum'] = out['Close'].rolling(5).std() / out['Close'].rolling(20).std()
        out['Trend_Strength'] = abs(out['EMA_fast'] - out['EMA_slow']) / out['Close']
        
        # Calculate volatility features
        out['Volatility'] = out['Close'].rolling(20).std() / out['Close'].rolling(20).mean()
        out['ATR_Ratio'] = out['ATR'] / out['Close']
        
        # Calculate traditional trend signals
        out['EMA_Signal'] = np.where(out['EMA_fast'] > out['EMA_slow'], 1, -1)
        out['RSI_Signal'] = np.where(out['RSI'] > 70, -1, np.where(out['RSI'] < 30, 1, 0))
        
        # Calculate ML-based trend prediction
        out['ML_Trend_Score'] = self._calculate_ml_trend_score(out)
        
        # Calculate adaptive trend flow
        out['Trend_Flow'] = self._calculate_trend_flow(out)
        
        # Calculate signal strength
        out['Signal_Strength'] = self._calculate_signal_strength(out)
        
        return out
        
    def _calculate_ml_trend_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate ML-based trend score."""
        ml_scores = pd.Series(index=df.index, dtype=float)
        
        for i in range(self._min_samples, len(df)):
            try:
                # Prepare training data
                train_data = df.iloc[max(0, i - self._ml_period):i]
                
                if len(train_data) < self._min_samples:
                    ml_scores.iloc[i] = 0
                    continue
                
                # Extract features
                features = self._extract_ml_features(train_data)
                target = self._extract_target(train_data)
                
                if len(features) < self._min_samples or features.isna().any().any():
                    ml_scores.iloc[i] = 0
                    continue
                
                # Train model
                self._scaler.fit(features)
                features_scaled = self._scaler.transform(features)
                
                self._ml_model.fit(features_scaled, target)
                
                # Predict current trend
                current_features = self._extract_ml_features(df.iloc[i:i+1])
                if not current_features.isna().any().any():
                    current_features_scaled = self._scaler.transform(current_features)
                    prediction = self._ml_model.predict(current_features_scaled)[0]
                    ml_scores.iloc[i] = prediction
                else:
                    ml_scores.iloc[i] = 0
                    
            except Exception:
                ml_scores.iloc[i] = 0
                
        return ml_scores
        
    def _extract_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features for ML model."""
        features = pd.DataFrame(index=df.index)
        
        # Price features
        features['Price_Change'] = df['Close'].pct_change()
        features['High_Low_Ratio'] = (df['High'] - df['Low']) / df['Close']
        features['Open_Close_Ratio'] = (df['Open'] - df['Close']) / df['Close']
        
        # Technical indicators
        features['EMA_Ratio'] = df['EMA_fast'] / df['EMA_slow']
        features['RSI_Normalized'] = (df['RSI'] - 50) / 50
        features['ATR_Ratio'] = df['ATR'] / df['Close']
        
        # Momentum features
        features['Momentum_5'] = df['Close'].pct_change(5)
        features['Momentum_10'] = df['Close'].pct_change(10)
        features['Momentum_20'] = df['Close'].pct_change(20)
        
        # Volatility features
        features['Volatility_5'] = df['Close'].rolling(5).std() / df['Close'].rolling(5).mean()
        features['Volatility_20'] = df['Close'].rolling(20).std() / df['Close'].rolling(20).mean()
        
        return features.dropna()
        
    def _extract_target(self, df: pd.DataFrame) -> pd.Series:
        """Extract target variable for ML model."""
        # Use future price movement as target
        future_returns = df['Close'].shift(-5) / df['Close'] - 1
        return future_returns.dropna()
        
    def _calculate_trend_flow(self, df: pd.DataFrame) -> pd.Series:
        """Calculate adaptive trend flow."""
        trend_flow = pd.Series(index=df.index, dtype=float)
        
        for i in range(len(df)):
            # Combine traditional and ML signals
            ema_signal = df['EMA_Signal'].iloc[i] if not pd.isna(df['EMA_Signal'].iloc[i]) else 0
            rsi_signal = df['RSI_Signal'].iloc[i] if not pd.isna(df['RSI_Signal'].iloc[i]) else 0
            ml_score = df['ML_Trend_Score'].iloc[i] if not pd.isna(df['ML_Trend_Score'].iloc[i]) else 0
            
            # Weighted combination
            trend_flow.iloc[i] = (0.4 * ema_signal + 0.3 * rsi_signal + 0.3 * ml_score)
            
        return trend_flow
        
    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """Calculate signal strength."""
        signal_strength = pd.Series(index=df.index, dtype=float)
        
        for i in range(len(df)):
            # Calculate strength based on multiple factors
            trend_consistency = abs(df['Trend_Flow'].iloc[i])
            volatility_factor = 1 / (1 + df['Volatility'].iloc[i]) if not pd.isna(df['Volatility'].iloc[i]) else 1
            momentum_factor = abs(df['Price_Momentum'].iloc[i]) if not pd.isna(df['Price_Momentum'].iloc[i]) else 0
            
            signal_strength.iloc[i] = trend_consistency * volatility_factor * (1 + momentum_factor)
            
        return signal_strength
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate Adaptive Trend Flow signal."""
        if len(df) < self._lookback_period + 2:
            return 0
            
        row = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Get basic indicators
        ema_fast = float(row.get('EMA_fast', 0))
        ema_slow = float(row.get('EMA_slow', 0))
        rsi = float(row.get('RSI', 50))
        atr = float(row.get('ATR', 0))
        
        # Check for valid values
        if pd.isna(ema_fast) or pd.isna(ema_slow) or pd.isna(rsi):
            return 0
        
        # Simplified signal generation based on EMA crossover and RSI
        ema_signal = 1 if ema_fast > ema_slow else -1
        rsi_signal = 1 if rsi < 30 else (-1 if rsi > 70 else 0)
        
        # Get previous values for trend change detection
        prev_ema_fast = float(prev.get('EMA_fast', 0))
        prev_ema_slow = float(prev.get('EMA_slow', 0))
        prev_rsi = float(prev.get('RSI', 50))
        
        if pd.isna(prev_ema_fast) or pd.isna(prev_ema_slow) or pd.isna(prev_rsi):
            return 0
        
        prev_ema_signal = 1 if prev_ema_fast > prev_ema_slow else -1
        prev_rsi_signal = 1 if prev_rsi < 30 else (-1 if prev_rsi > 70 else 0)
        
        # Generate signals based on trend changes
        if ema_signal != prev_ema_signal:
            if ema_signal > 0 and rsi < 50:  # EMA bullish crossover with RSI not overbought
                return 1  # Buy signal
            elif ema_signal < 0 and rsi > 50:  # EMA bearish crossover with RSI not oversold
                return -1  # Sell signal
        
        # RSI divergence signals
        if rsi_signal != prev_rsi_signal:
            if rsi_signal > 0 and ema_signal > 0:  # RSI oversold with EMA bullish
                return 1  # Buy signal
            elif rsi_signal < 0 and ema_signal < 0:  # RSI overbought with EMA bearish
                return -1  # Sell signal
        
        # Strong trend continuation signals
        if ema_signal > 0 and rsi > 50 and rsi < 70:  # Strong bullish trend
            return 1  # Buy signal
        elif ema_signal < 0 and rsi < 50 and rsi > 30:  # Strong bearish trend
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
            
        # 3:1 risk/reward ratio
        if side > 0:  # Long position
            return entry_price + (3 * atr)
        else:  # Short position
            return entry_price - (3 * atr)
