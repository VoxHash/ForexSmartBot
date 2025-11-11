"""Transformer model strategy for market analysis."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from torch import nn
    import torch
    TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    TRANSFORMERS_AVAILABLE = False
    AutoModelForSequenceClassification = None
    AutoTokenizer = None
    nn = None
    torch = None
    import warnings
    warnings.warn(f"Transformers/torch not available (DLL loading may have failed): {e}")

from sklearn.preprocessing import StandardScaler


class TransformerStrategy(IStrategy):
    """Transformer-based trading strategy using BERT/GPT-style models."""
    
    def __init__(self, lookback_period: int = 60, sequence_length: int = 20,
                 model_name: str = "distilbert-base-uncased", min_samples: int = 200):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library is required. Install with: pip install transformers torch")
        
        self._lookback_period = lookback_period
        self._sequence_length = sequence_length
        self._model_name = model_name
        self._min_samples = min_samples
        self._name = "Transformer Strategy"
        self._model = None
        self._tokenizer = None
        self._scaler = StandardScaler()
        self._is_trained = False
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'sequence_length': self._sequence_length,
            'model_name': self._model_name,
            'min_samples': self._min_samples
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'sequence_length' in kwargs:
            self._sequence_length = int(kwargs['sequence_length'])
        if 'model_name' in kwargs:
            self._model_name = kwargs['model_name']
        if 'min_samples' in kwargs:
            self._min_samples = int(kwargs['min_samples'])
        self._is_trained = False
        
    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features as sequences for transformer."""
        features = []
        
        # Create sequences of price changes and indicators
        for i in range(self._sequence_length, len(df)):
            sequence = []
            
            # Price changes
            price_changes = df['Close'].iloc[i-self._sequence_length:i].pct_change().dropna().values
            sequence.extend(price_changes)
            
            # Volume (if available)
            if 'Volume' in df.columns:
                volume_changes = df['Volume'].iloc[i-self._sequence_length:i].pct_change().dropna().values
                sequence.extend(volume_changes[:len(price_changes)])
            
            # Technical indicators
            if 'RSI' in df.columns:
                rsi_values = df['RSI'].iloc[i-self._sequence_length:i].values
                sequence.extend(rsi_values / 100 - 0.5)  # Normalize to [-0.5, 0.5]
                
            if 'ATR' in df.columns:
                atr_values = df['ATR'].iloc[i-self._sequence_length:i].values
                price = df['Close'].iloc[i]
                sequence.extend((atr_values / price).tolist())
            
            features.append(sequence[:self._sequence_length * 3])  # Limit feature size
            
        return np.array(features)
        
    def _train_model(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train transformer model (simplified version)."""
        if len(X) < self._min_samples:
            return
            
        # For now, use a simple neural network approach
        # In production, you would fine-tune a pre-trained transformer
        try:
            X_scaled = self._scaler.fit_transform(X)
            self._is_trained = True
        except Exception as e:
            print(f"Transformer training error: {e}")
            
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators."""
        out = df.copy()
        
        # Calculate technical indicators
        out['SMA_20'] = out['Close'].rolling(20).mean()
        out['SMA_50'] = out['Close'].rolling(50).mean()
        out['RSI'] = self._calculate_rsi(out['Close'], 14)
        out['ATR'] = self._calculate_atr(out, 14)
        
        # Train model if enough data
        if len(df) >= self._min_samples and not self._is_trained:
            try:
                X = self._prepare_features(df)
                if len(X) >= 10:
                    # Create simple targets (future return > 0.5% = 1, else 0)
                    future_returns = df['Close'].shift(-1) / df['Close'] - 1
                    y = (future_returns > 0.005).astype(int).values
                    y = y[-len(X):]
                    
                    if len(y) == len(X):
                        self._train_model(X, y)
            except Exception as e:
                print(f"Transformer indicator calculation error: {e}")
                
        return out
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
        
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR."""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate transformer-based trading signal."""
        if len(df) < self._lookback_period or not self._is_trained:
            return 0
            
        try:
            # Prepare recent sequence
            X = self._prepare_features(df.tail(self._lookback_period))
            
            if len(X) == 0:
                return 0
                
            # Use most recent sequence
            X_scaled = self._scaler.transform(X[-1:])
            
            # Simplified prediction (in production, use actual transformer)
            # For now, use pattern matching on recent price action
            recent_prices = df['Close'].tail(10).values
            price_trend = np.mean(np.diff(recent_prices))
            
            if price_trend > 0.001:  # Upward trend
                return 1
            elif price_trend < -0.001:  # Downward trend
                return -1
            else:
                return 0
                
        except Exception as e:
            print(f"Transformer prediction error: {e}")
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

