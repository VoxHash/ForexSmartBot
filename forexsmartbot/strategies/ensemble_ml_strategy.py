"""Ensemble ML models combining multiple algorithms."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from ..core.interfaces import IStrategy


class EnsembleMLStrategy(IStrategy):
    """Ensemble ML strategy combining Random Forest, Gradient Boosting, and other models."""
    
    def __init__(self, lookback_period: int = 50, n_estimators: int = 100,
                 max_depth: int = 10, learning_rate: float = 0.1, min_samples: int = 100):
        self._lookback_period = lookback_period
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._learning_rate = learning_rate
        self._min_samples = min_samples
        self._name = "Ensemble ML Strategy"
        
        # Create ensemble of models
        rf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        gb = GradientBoostingClassifier(n_estimators=n_estimators, max_depth=max_depth,
                                       learning_rate=learning_rate, random_state=42)
        self._model = VotingClassifier(estimators=[('rf', rf), ('gb', gb)], voting='soft')
        self._scaler = StandardScaler()
        self._is_trained = False
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'n_estimators': self._n_estimators,
            'max_depth': self._max_depth,
            'learning_rate': self._learning_rate,
            'min_samples': self._min_samples
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'n_estimators' in kwargs:
            self._n_estimators = int(kwargs['n_estimators'])
        if 'max_depth' in kwargs:
            self._max_depth = int(kwargs['max_depth'])
        if 'learning_rate' in kwargs:
            self._learning_rate = float(kwargs['learning_rate'])
        if 'min_samples' in kwargs:
            self._min_samples = int(kwargs['min_samples'])
        
        # Recreate model with new params
        rf = RandomForestClassifier(n_estimators=self._n_estimators, max_depth=self._max_depth, random_state=42)
        gb = GradientBoostingClassifier(n_estimators=self._n_estimators, max_depth=self._max_depth,
                                       learning_rate=self._learning_rate, random_state=42)
        self._model = VotingClassifier(estimators=[('rf', rf), ('gb', gb)], voting='soft')
        self._is_trained = False
        
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ensemble models."""
        features = pd.DataFrame()
        features['price_change'] = df['Close'].pct_change()
        features['high_low'] = (df['High'] - df['Low']) / df['Close']
        features['sma_20'] = df['Close'].rolling(20).mean() / df['Close'] - 1
        features['sma_50'] = df['Close'].rolling(50).mean() / df['Close'] - 1
        features['ema_12'] = df['Close'].ewm(span=12).mean() / df['Close'] - 1
        features['ema_26'] = df['Close'].ewm(span=26).mean() / df['Close'] - 1
        features['rsi'] = self._calculate_rsi(df['Close'], 14) / 100 - 0.5
        features['macd'] = self._calculate_macd(df['Close'])
        features['atr_ratio'] = self._calculate_atr(df, 14) / df['Close']
        features['volume_ratio'] = df.get('Volume', pd.Series([1.0] * len(df))) / df.get('Volume', pd.Series([1.0] * len(df))).rolling(20).mean() - 1
        
        return features.dropna()
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
        
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """Calculate MACD."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        return macd / prices
        
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR."""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()
        
    def _prepare_target(self, df: pd.DataFrame) -> pd.Series:
        """Prepare target labels."""
        future_return = df['Close'].shift(-1) / df['Close'] - 1
        target = pd.Series(0, index=df.index)
        target[future_return > 0.005] = 1
        target[future_return < -0.005] = -1
        return target
        
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators and train model if needed."""
        out = df.copy()
        
        if len(df) >= self._min_samples and not self._is_trained:
            try:
                features = self._prepare_features(df)
                target = self._prepare_target(df)
                
                common_idx = features.index.intersection(target.index)
                features = features.loc[common_idx]
                target = target.loc[common_idx]
                
                if len(features) >= self._min_samples:
                    X = self._scaler.fit_transform(features)
                    y = target.values
                    self._model.fit(X, y)
                    self._is_trained = True
            except Exception as e:
                print(f"Ensemble ML training error: {e}")
                
        # Add technical indicators
        out['SMA_20'] = out['Close'].rolling(20).mean()
        out['SMA_50'] = out['Close'].rolling(50).mean()
        out['RSI'] = self._calculate_rsi(out['Close'], 14)
        out['ATR'] = self._calculate_atr(out, 14)
        
        return out
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate ensemble ML-based trading signal."""
        if len(df) < self._lookback_period or not self._is_trained:
            return 0
            
        try:
            features = self._prepare_features(df.tail(self._lookback_period))
            
            if len(features) == 0:
                return 0
                
            X = self._scaler.transform(features.tail(1))
            prediction = self._model.predict(X)[0]
            
            # Get average probability from ensemble
            proba = self._model.predict_proba(X)[0]
            confidence = max(proba)
            
            if confidence > 0.65:  # Higher threshold for ensemble
                return int(prediction)
            else:
                return 0
                
        except Exception as e:
            print(f"Ensemble ML prediction error: {e}")
            return 0
            
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
            
        if side > 0:  # Long
            return entry_price - (2 * atr)
        else:  # Short
            return entry_price + (2 * atr)
            
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        """Calculate take profit based on ATR."""
        if 'ATR' not in df or len(df) == 0:
            return None
            
        atr = float(df['ATR'].iloc[-1])
        if pd.isna(atr) or atr == 0:
            return None
            
        # 2:1 risk/reward
        if side > 0:  # Long
            return entry_price + (4 * atr)
        else:  # Short
            return entry_price - (4 * atr)

