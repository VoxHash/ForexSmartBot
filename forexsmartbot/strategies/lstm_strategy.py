"""LSTM-based trading strategy for time series prediction."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    TENSORFLOW_AVAILABLE = False
    Sequential = None
    LSTM = None
    Dense = None
    Dropout = None
    Adam = None
    import warnings
    warnings.warn(f"TensorFlow not available (DLL loading may have failed): {e}")

from sklearn.preprocessing import MinMaxScaler
from ..utils.gpu_utils import get_gpu_manager


class LSTMStrategy(IStrategy):
    """LSTM-based trading strategy for time series prediction."""
    
    def __init__(self, lookback_period: int = 60, sequence_length: int = 20,
                 lstm_units: int = 50, epochs: int = 50, batch_size: int = 32,
                 prediction_threshold: float = 0.02, min_samples: int = 200,
                 use_gpu: bool = True):
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM strategy. Install with: pip install tensorflow")
        
        self._lookback_period = lookback_period
        self._sequence_length = sequence_length
        self._lstm_units = lstm_units
        self._epochs = epochs
        self._batch_size = batch_size
        self._prediction_threshold = prediction_threshold
        self._min_samples = min_samples
        self._name = "LSTM Strategy"
        self._model = None
        self._scaler = MinMaxScaler()
        self._is_trained = False
        
        # GPU support for TensorFlow
        self._gpu_manager = get_gpu_manager(use_gpu=use_gpu)
        if TENSORFLOW_AVAILABLE and self._gpu_manager.use_gpu:
            # Configure TensorFlow to use GPU
            try:
                import tensorflow as tf
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    # Enable memory growth to avoid allocating all GPU memory
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    print(f"LSTM Strategy: Using GPU {gpus[0].name}")
            except Exception as e:
                print(f"LSTM Strategy: GPU configuration error: {e}")
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'sequence_length': self._sequence_length,
            'lstm_units': self._lstm_units,
            'epochs': self._epochs,
            'batch_size': self._batch_size,
            'prediction_threshold': self._prediction_threshold,
            'min_samples': self._min_samples
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'sequence_length' in kwargs:
            self._sequence_length = int(kwargs['sequence_length'])
        if 'lstm_units' in kwargs:
            self._lstm_units = int(kwargs['lstm_units'])
        if 'epochs' in kwargs:
            self._epochs = int(kwargs['epochs'])
        if 'batch_size' in kwargs:
            self._batch_size = int(kwargs['batch_size'])
        if 'prediction_threshold' in kwargs:
            self._prediction_threshold = float(kwargs['prediction_threshold'])
        if 'min_samples' in kwargs:
            self._min_samples = int(kwargs['min_samples'])
        self._is_trained = False  # Reset training flag when params change
        
    def _prepare_data(self, df: pd.DataFrame) -> tuple:
        """Prepare data for LSTM training/prediction."""
        # Use price changes and technical indicators as features
        features = pd.DataFrame()
        features['price_change'] = df['Close'].pct_change()
        features['high_low'] = (df['High'] - df['Low']) / df['Close']
        features['volume'] = df.get('Volume', pd.Series([1.0] * len(df)))
        features['sma_20'] = df['Close'].rolling(20).mean() / df['Close'] - 1
        features['sma_50'] = df['Close'].rolling(50).mean() / df['Close'] - 1
        features['rsi'] = self._calculate_rsi(df['Close'], 14) / 100 - 0.5
        
        # Target: future price change
        target = df['Close'].shift(-1) / df['Close'] - 1
        
        # Drop NaN values
        features = features.dropna()
        target = target[features.index]
        
        return features.values, target.values
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
        
    def _build_model(self, input_shape: tuple) -> Sequential:
        """Build LSTM model."""
        model = Sequential()
        model.add(LSTM(self._lstm_units, return_sequences=True, input_shape=input_shape))
        model.add(Dropout(0.2))
        model.add(LSTM(self._lstm_units, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(25))
        model.add(Dense(1))
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model
        
    def _train_model(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train LSTM model."""
        if len(X) < self._min_samples:
            return
            
        # Scale features
        X_scaled = self._scaler.fit_transform(X)
        
        # Reshape for LSTM (samples, timesteps, features)
        X_reshaped = []
        y_reshaped = []
        
        for i in range(self._sequence_length, len(X_scaled)):
            X_reshaped.append(X_scaled[i - self._sequence_length:i])
            y_reshaped.append(y[i])
            
        if len(X_reshaped) < 10:
            return
            
        X_reshaped = np.array(X_reshaped)
        y_reshaped = np.array(y_reshaped)
        
        # Build and train model
        input_shape = (self._sequence_length, X_scaled.shape[1])
        self._model = self._build_model(input_shape)
        
        # Train with minimal epochs for real-time use
        self._model.fit(X_reshaped, y_reshaped, epochs=min(10, self._epochs), 
                       batch_size=self._batch_size, verbose=0)
        self._is_trained = True
        
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators and train model if needed."""
        out = df.copy()
        
        if len(df) >= self._min_samples and not self._is_trained:
            try:
                X, y = self._prepare_data(df)
                if len(X) >= self._min_samples:
                    self._train_model(X, y)
            except Exception as e:
                print(f"LSTM training error: {e}")
                
        # Add technical indicators
        out['SMA_20'] = out['Close'].rolling(20).mean()
        out['SMA_50'] = out['Close'].rolling(50).mean()
        out['RSI'] = self._calculate_rsi(out['Close'], 14)
        out['ATR'] = self._calculate_atr(out, 14)
        
        return out
        
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR."""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()
        
    def signal(self, df: pd.DataFrame) -> int:
        """Generate LSTM-based trading signal."""
        if len(df) < self._lookback_period or not self._is_trained or self._model is None:
            return 0
            
        try:
            # Prepare recent data for prediction
            X, _ = self._prepare_data(df.tail(self._lookback_period))
            
            if len(X) < self._sequence_length:
                return 0
                
            # Scale and reshape
            X_scaled = self._scaler.transform(X[-self._sequence_length:])
            X_reshaped = X_scaled.reshape(1, self._sequence_length, X_scaled.shape[1])
            
            # Predict future price change
            prediction = self._model.predict(X_reshaped, verbose=0)[0][0]
            
            # Generate signal based on prediction
            if prediction > self._prediction_threshold:
                return 1  # Buy
            elif prediction < -self._prediction_threshold:
                return -1  # Sell
            else:
                return 0  # Hold
                
        except Exception as e:
            print(f"LSTM prediction error: {e}")
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

