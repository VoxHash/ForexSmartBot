"""Strategy template library with pre-built components."""

from typing import Dict, Any, List
from .strategy_builder import StrategyBuilder, ComponentType


class StrategyTemplate:
    """Pre-built strategy templates."""
    
    @staticmethod
    def create_sma_crossover_template() -> StrategyBuilder:
        """Create SMA Crossover template."""
        builder = StrategyBuilder()
        
        # Add indicators
        sma_fast_id = builder.add_component(
            ComponentType.INDICATOR,
            "SMA Fast",
            {"period": 20}
        )
        
        sma_slow_id = builder.add_component(
            ComponentType.INDICATOR,
            "SMA Slow",
            {"period": 50}
        )
        
        # Add signal
        signal_id = builder.add_component(
            ComponentType.SIGNAL,
            "Crossover Signal",
            {"type": "crossover"}
        )
        
        # Connect components
        builder.connect_components(sma_fast_id, signal_id)
        builder.connect_components(sma_slow_id, signal_id)
        
        return builder
        
    @staticmethod
    def create_rsi_template() -> StrategyBuilder:
        """Create RSI template."""
        builder = StrategyBuilder()
        
        # Add RSI indicator
        rsi_id = builder.add_component(
            ComponentType.INDICATOR,
            "RSI",
            {"period": 14}
        )
        
        # Add filter
        filter_id = builder.add_component(
            ComponentType.FILTER,
            "RSI Filter",
            {"oversold": 30, "overbought": 70}
        )
        
        # Add signal
        signal_id = builder.add_component(
            ComponentType.SIGNAL,
            "RSI Signal",
            {"type": "mean_reversion"}
        )
        
        # Connect components
        builder.connect_components(rsi_id, filter_id)
        builder.connect_components(filter_id, signal_id)
        
        return builder
        
    @staticmethod
    def create_breakout_template() -> StrategyBuilder:
        """Create Breakout template."""
        builder = StrategyBuilder()
        
        # Add ATR indicator
        atr_id = builder.add_component(
            ComponentType.INDICATOR,
            "ATR",
            {"period": 14}
        )
        
        # Add breakout signal
        signal_id = builder.add_component(
            ComponentType.SIGNAL,
            "Breakout Signal",
            {"lookback_period": 20, "atr_multiplier": 1.5}
        )
        
        # Add risk management
        risk_id = builder.add_component(
            ComponentType.RISK_MANAGEMENT,
            "ATR-based SL/TP",
            {"sl_multiplier": 2.0, "tp_multiplier": 3.0}
        )
        
        # Connect components
        builder.connect_components(atr_id, signal_id)
        builder.connect_components(atr_id, risk_id)
        
        return builder
        
    @staticmethod
    def list_templates() -> List[str]:
        """List available templates."""
        return [
            "SMA Crossover",
            "RSI Reversion",
            "Breakout ATR"
        ]
        
    @staticmethod
    def get_template(name: str) -> StrategyBuilder:
        """Get a template by name."""
        # Map display names to internal names
        template_map = {
            "SMA Crossover": "SMA Crossover",
            "RSI Reversion": "RSI Mean Reversion",
            "RSI Mean Reversion": "RSI Mean Reversion",
            "Breakout ATR": "Breakout",
            "Breakout": "Breakout"
        }
        
        actual_name = template_map.get(name, name)
        
        templates = {
            "SMA Crossover": StrategyTemplate.create_sma_crossover_template,
            "RSI Mean Reversion": StrategyTemplate.create_rsi_template,
            "Breakout": StrategyTemplate.create_breakout_template
        }
        
        if actual_name not in templates:
            raise ValueError(f"Unknown template: {name}")
            
        return templates[actual_name]()

