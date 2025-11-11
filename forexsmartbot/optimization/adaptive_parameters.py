"""Real-time parameter adaptation based on market conditions."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class MarketRegime:
    """Market regime classification."""
    regime_type: str  # 'trending', 'ranging', 'volatile', 'calm'
    volatility: float
    trend_strength: float
    confidence: float


@dataclass
class AdaptiveParameter:
    """Adaptive parameter configuration."""
    parameter_name: str
    base_value: float
    regime_multipliers: Dict[str, float]  # Multiplier per regime
    min_value: float
    max_value: float
    adaptation_rate: float  # How fast to adapt (0-1)


class AdaptiveParameterManager:
    """Manages real-time parameter adaptation based on market conditions."""
    
    def __init__(self, strategy_params: Dict[str, float],
                 adaptation_config: Dict[str, AdaptiveParameter]):
        """
        Initialize adaptive parameter manager.
        
        Args:
            strategy_params: Base strategy parameters
            adaptation_config: Configuration for adaptive parameters
        """
        self.base_params = strategy_params.copy()
        self.adaptation_config = adaptation_config
        self.current_regime: Optional[MarketRegime] = None
        self.regime_history: List[MarketRegime] = []
        self.param_history: List[Dict[str, float]] = []
        
    def detect_market_regime(self, df: pd.DataFrame) -> MarketRegime:
        """
        Detect current market regime.
        
        Args:
            df: Recent price data
            
        Returns:
            MarketRegime object
        """
        if len(df) < 20:
            return MarketRegime('calm', 0.01, 0.0, 0.5)
        
        # Calculate volatility (ATR-based)
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        volatility = (atr / df['Close'].iloc[-1]) if df['Close'].iloc[-1] > 0 else 0.01
        
        # Calculate trend strength (ADX-like)
        price_change = df['Close'].pct_change()
        positive_changes = price_change[price_change > 0].sum()
        negative_changes = abs(price_change[price_change < 0].sum())
        total_change = abs(positive_changes) + abs(negative_changes)
        trend_strength = abs(positive_changes - abs(negative_changes)) / total_change if total_change > 0 else 0.0
        
        # Classify regime
        if volatility > 0.02 and trend_strength > 0.5:
            regime_type = 'trending'
        elif volatility > 0.02 and trend_strength < 0.3:
            regime_type = 'volatile'
        elif volatility < 0.01:
            regime_type = 'calm'
        else:
            regime_type = 'ranging'
        
        confidence = min(volatility * 10, 1.0) * trend_strength if trend_strength > 0 else 0.5
        
        return MarketRegime(
            regime_type=regime_type,
            volatility=volatility,
            trend_strength=trend_strength,
            confidence=confidence
        )
        
    def adapt_parameters(self, current_regime: MarketRegime) -> Dict[str, float]:
        """
        Adapt parameters based on current market regime.
        
        Args:
            current_regime: Current market regime
            
        Returns:
            Adapted parameters
        """
        adapted_params = self.base_params.copy()
        
        for param_name, adaptive_param in self.adaptation_config.items():
            if param_name not in adapted_params:
                continue
                
            # Get multiplier for current regime
            multiplier = adaptive_param.regime_multipliers.get(
                current_regime.regime_type,
                1.0  # Default: no change
            )
            
            # Apply adaptation with smoothing
            base_value = adaptive_param.base_value
            target_value = base_value * multiplier
            
            # Smooth adaptation
            current_value = adapted_params.get(param_name, base_value)
            adaptation_rate = adaptive_param.adaptation_rate
            
            new_value = current_value * (1 - adaptation_rate) + target_value * adaptation_rate
            
            # Clamp to bounds
            new_value = max(adaptive_param.min_value, 
                          min(adaptive_param.max_value, new_value))
            
            adapted_params[param_name] = new_value
        
        # Store history
        self.current_regime = current_regime
        self.regime_history.append(current_regime)
        self.param_history.append(adapted_params.copy())
        
        # Keep only recent history
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]
        if len(self.param_history) > 100:
            self.param_history = self.param_history[-100:]
        
        return adapted_params
        
    def get_current_parameters(self) -> Dict[str, float]:
        """Get current adapted parameters."""
        if self.param_history:
            return self.param_history[-1]
        return self.base_params.copy()
        
    def get_regime_statistics(self) -> Dict[str, Any]:
        """Get statistics about regime history."""
        if not self.regime_history:
            return {}
        
        regime_counts = {}
        for regime in self.regime_history:
            regime_counts[regime.regime_type] = regime_counts.get(regime.regime_type, 0) + 1
        
        total = len(self.regime_history)
        
        return {
            'total_periods': total,
            'regime_distribution': {k: v/total for k, v in regime_counts.items()},
            'current_regime': self.current_regime.regime_type if self.current_regime else None,
            'avg_volatility': np.mean([r.volatility for r in self.regime_history]),
            'avg_trend_strength': np.mean([r.trend_strength for r in self.regime_history])
        }


class RealTimeParameterAdapter:
    """Real-time parameter adaptation system."""
    
    def __init__(self, strategy_factory: Callable[[Dict[str, float]], Any],
                 base_params: Dict[str, float],
                 adaptation_config: Dict[str, AdaptiveParameter],
                 lookback_period: int = 50):
        """
        Initialize real-time parameter adapter.
        
        Args:
            strategy_factory: Function to create strategy from parameters
            base_params: Base strategy parameters
            adaptation_config: Adaptive parameter configuration
            lookback_period: Period for regime detection
        """
        self.strategy_factory = strategy_factory
        self.param_manager = AdaptiveParameterManager(base_params, adaptation_config)
        self.lookback_period = lookback_period
        self.current_strategy = None
        
    def update(self, df: pd.DataFrame) -> Any:
        """
        Update strategy parameters based on current market conditions.
        
        Args:
            df: Recent price data (last lookback_period rows)
            
        Returns:
            Updated strategy instance
        """
        # Detect market regime
        regime = self.param_manager.detect_market_regime(df.tail(self.lookback_period))
        
        # Adapt parameters
        adapted_params = self.param_manager.adapt_parameters(regime)
        
        # Create/update strategy
        self.current_strategy = self.strategy_factory(adapted_params)
        
        return self.current_strategy
        
    def get_strategy(self) -> Any:
        """Get current strategy instance."""
        if self.current_strategy is None:
            # Initialize with base parameters
            self.current_strategy = self.strategy_factory(self.param_manager.base_params)
        return self.current_strategy
        
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Get adaptation statistics."""
        return self.param_manager.get_regime_statistics()

