"""Strategy plugins for ForexSmartBot."""

from .sma_crossover import SMACrossover
from .breakout_atr import BreakoutATR
from .rsi_reversion import RSIRevertion

# Strategy registry
STRATEGIES = {
    'SMA_Crossover': SMACrossover,
    'BreakoutATR': BreakoutATR,
    'RSI_Reversion': RSIRevertion,
}

def get_strategy(name: str, **params):
    """Get strategy instance by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGIES[name](**params)

def list_strategies():
    """List available strategies."""
    return list(STRATEGIES.keys())
