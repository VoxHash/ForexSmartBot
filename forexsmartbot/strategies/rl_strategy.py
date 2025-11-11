"""Reinforcement Learning trading strategy using DQN/PPO."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.interfaces import IStrategy

try:
    import gymnasium as gym
    from gymnasium import spaces
    from stable_baselines3 import DQN, PPO
    from stable_baselines3.common.env_checker import check_env
    RL_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    RL_AVAILABLE = False
    gym = None
    spaces = None
    DQN = None
    PPO = None
    import warnings
    warnings.warn(f"Reinforcement Learning libraries not available (DLL loading may have failed): {e}")

from sklearn.preprocessing import StandardScaler


class TradingEnv:
    """Trading environment for RL."""
    
    def __init__(self, data: pd.DataFrame, initial_balance: float = 10000.0):
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0  # 0: no position, 1: long, -1: short
        self.entry_price = 0.0
        self.current_step = 0
        self.max_steps = len(data) - 1
        
        # Action space: 0 = hold, 1 = buy, 2 = sell, 3 = close
        self.action_space = spaces.Discrete(4)
        
        # Observation space: price features + portfolio state
        n_features = 10  # price, volume, indicators, etc.
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(n_features,), dtype=np.float32
        )
        
    def reset(self):
        """Reset environment."""
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0.0
        self.current_step = 0
        return self._get_observation()
        
    def step(self, action):
        """Take a step in the environment."""
        if self.current_step >= self.max_steps:
            return self._get_observation(), 0, True, {}
            
        current_price = float(self.data['Close'].iloc[self.current_step])
        reward = 0.0
        
        # Execute action
        if action == 1 and self.position == 0:  # Buy
            self.position = 1
            self.entry_price = current_price
        elif action == 2 and self.position == 0:  # Sell (short)
            self.position = -1
            self.entry_price = current_price
        elif action == 3 and self.position != 0:  # Close position
            pnl = self.position * (current_price - self.entry_price) / self.entry_price
            reward = pnl * 100  # Scale reward
            self.balance *= (1 + pnl)
            self.position = 0
            self.entry_price = 0.0
        # action == 0: hold, do nothing
            
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        # Calculate reward based on portfolio value
        if self.position != 0:
            unrealized_pnl = self.position * (current_price - self.entry_price) / self.entry_price
            reward = unrealized_pnl * 10  # Small reward for unrealized gains
            
        obs = self._get_observation()
        return obs, reward, done, {}
        
    def _get_observation(self):
        """Get current observation."""
        if self.current_step >= len(self.data):
            return np.zeros(self.observation_space.shape[0], dtype=np.float32)
            
        row = self.data.iloc[self.current_step]
        
        # Features: price change, volume, indicators, portfolio state
        features = [
            float(row.get('Close', 0)),
            float(row.get('Volume', 0)) if 'Volume' in row else 0.0,
            float(row.get('RSI', 50)) / 100 - 0.5 if 'RSI' in row else 0.0,
            float(row.get('ATR', 0)) / float(row.get('Close', 1)) if 'ATR' in row and row.get('Close', 0) > 0 else 0.0,
            float(row.get('SMA_20', 0)) / float(row.get('Close', 1)) - 1 if 'SMA_20' in row and row.get('Close', 0) > 0 else 0.0,
            self.position,
            self.balance / self.initial_balance - 1,
            float(self.entry_price) / float(row.get('Close', 1)) - 1 if self.entry_price > 0 else 0.0,
            (self.current_step / self.max_steps) if self.max_steps > 0 else 0.0,
            0.0  # Placeholder
        ]
        
        return np.array(features[:self.observation_space.shape[0]], dtype=np.float32)


class RLStrategy(IStrategy):
    """Reinforcement Learning trading strategy."""
    
    def __init__(self, lookback_period: int = 100, algorithm: str = "DQN",
                 min_samples: int = 500, training_steps: int = 10000):
        if not RL_AVAILABLE:
            raise ImportError("Reinforcement Learning libraries required. Install with: pip install gymnasium stable-baselines3")
        
        self._lookback_period = lookback_period
        self._algorithm = algorithm
        self._min_samples = min_samples
        self._training_steps = training_steps
        self._name = "RL Strategy"
        self._model = None
        self._env = None
        self._is_trained = False
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'lookback_period': self._lookback_period,
            'algorithm': self._algorithm,
            'min_samples': self._min_samples,
            'training_steps': self._training_steps
        }
        
    def set_params(self, **kwargs) -> None:
        if 'lookback_period' in kwargs:
            self._lookback_period = int(kwargs['lookback_period'])
        if 'algorithm' in kwargs:
            self._algorithm = kwargs['algorithm']
        if 'min_samples' in kwargs:
            self._min_samples = int(kwargs['min_samples'])
        if 'training_steps' in kwargs:
            self._training_steps = int(kwargs['training_steps'])
        self._is_trained = False
        
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators and train RL model if needed."""
        out = df.copy()
        
        # Calculate technical indicators
        out['SMA_20'] = out['Close'].rolling(20).mean()
        out['SMA_50'] = out['Close'].rolling(50).mean()
        out['RSI'] = self._calculate_rsi(out['Close'], 14)
        out['ATR'] = self._calculate_atr(out, 14)
        
        # Train RL model if enough data
        if len(df) >= self._min_samples and not self._is_trained:
            try:
                self._train_model(out)
            except Exception as e:
                print(f"RL training error: {e}")
                
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
        
    def _train_model(self, df: pd.DataFrame) -> None:
        """Train RL model."""
        try:
            # Create environment
            self._env = TradingEnv(df.tail(self._lookback_period))
            
            # Create model
            if self._algorithm == "DQN":
                self._model = DQN("MlpPolicy", self._env, verbose=0)
            elif self._algorithm == "PPO":
                self._model = PPO("MlpPolicy", self._env, verbose=0)
            else:
                raise ValueError(f"Unknown algorithm: {self._algorithm}")
                
            # Train model
            self._model.learn(total_timesteps=min(self._training_steps, 5000))
            self._is_trained = True
            
        except Exception as e:
            print(f"RL model training error: {e}")
            self._is_trained = False
            
    def signal(self, df: pd.DataFrame) -> int:
        """Generate RL-based trading signal."""
        if not self._is_trained or self._model is None or self._env is None:
            return 0
            
        try:
            # Get current observation
            obs = self._env._get_observation()
            
            # Predict action
            action, _ = self._model.predict(obs, deterministic=True)
            
            # Convert action to signal: 1 = buy, 2 = sell, 0/3 = hold
            if action == 1:
                return 1  # Buy
            elif action == 2:
                return -1  # Sell
            else:
                return 0  # Hold
                
        except Exception as e:
            print(f"RL prediction error: {e}")
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

