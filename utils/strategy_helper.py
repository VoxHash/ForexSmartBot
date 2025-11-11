"""Helper utilities for working with strategies."""

from typing import Dict, Any, List, Optional
from forexsmartbot.strategies import get_strategy, list_strategies, STRATEGIES


def get_strategy_info(strategy_name: str) -> Dict[str, Any]:
    """Get information about a strategy."""
    if strategy_name not in STRATEGIES:
        return {'error': f'Strategy {strategy_name} not found'}
    
    try:
        strategy_class = STRATEGIES[strategy_name]
        strategy = strategy_class()
        
        return {
            'name': strategy.name,
            'params': strategy.params,
            'available': True
        }
    except Exception as e:
        return {
            'name': strategy_name,
            'error': str(e),
            'available': False
        }


def list_ml_strategies() -> List[str]:
    """List all available ML strategies."""
    ml_strategies = [
        'LSTM_Strategy',
        'SVM_Strategy',
        'Ensemble_ML_Strategy',
        'Transformer_Strategy',
        'RL_Strategy',
        'ML_Adaptive_SuperTrend',
        'Adaptive_Trend_Flow'
    ]
    
    available = []
    for strategy_name in ml_strategies:
        if strategy_name in STRATEGIES:
            available.append(strategy_name)
    
    return available


def list_optimization_strategies() -> List[str]:
    """List strategies suitable for optimization."""
    # Strategies with numeric parameters that can be optimized
    optimizable = [
        'SMA_Crossover',
        'BreakoutATR',
        'RSI_Reversion',
        'Mean_Reversion',
        'Scalping_MA',
        'Momentum_Breakout'
    ]
    
    available = []
    for strategy_name in optimizable:
        if strategy_name in STRATEGIES:
            available.append(strategy_name)
    
    return available


def get_default_params(strategy_name: str) -> Dict[str, Any]:
    """Get default parameters for a strategy."""
    if strategy_name not in STRATEGIES:
        return {}
    
    try:
        strategy = get_strategy(strategy_name)
        return strategy.params
    except Exception:
        return {}


def validate_strategy_params(strategy_name: str, params: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate parameters for a strategy."""
    errors = []
    
    if strategy_name not in STRATEGIES:
        return False, [f'Strategy {strategy_name} not found']
    
    try:
        strategy = get_strategy(strategy_name, **params)
        return True, []
    except TypeError as e:
        errors.append(f'Invalid parameter type: {str(e)}')
    except ValueError as e:
        errors.append(f'Invalid parameter value: {str(e)}')
    except Exception as e:
        errors.append(f'Error: {str(e)}')
    
    return False, errors


def compare_strategies(strategy_names: List[str]) -> Dict[str, Any]:
    """Compare multiple strategies."""
    comparison = {
        'strategies': [],
        'common_params': [],
        'unique_params': {}
    }
    
    all_params = {}
    for name in strategy_names:
        if name in STRATEGIES:
            try:
                strategy = get_strategy(name)
                params = set(strategy.params.keys())
                all_params[name] = params
                comparison['strategies'].append({
                    'name': name,
                    'param_count': len(params),
                    'params': list(params)
                })
            except Exception as e:
                comparison['strategies'].append({
                    'name': name,
                    'error': str(e)
                })
    
    # Find common parameters
    if all_params:
        common = set.intersection(*all_params.values())
        comparison['common_params'] = list(common)
        
        # Find unique parameters
        for name, params in all_params.items():
            unique = params - common
            if unique:
                comparison['unique_params'][name] = list(unique)
    
    return comparison


def suggest_optimization_params(strategy_name: str) -> Dict[str, tuple]:
    """Suggest parameter ranges for optimization."""
    suggestions = {
        'SMA_Crossover': {
            'fast_period': (10, 30),
            'slow_period': (40, 80),
            'atr_period': (10, 20)
        },
        'BreakoutATR': {
            'lookback_period': (15, 30),
            'atr_period': (10, 20),
            'atr_multiplier': (1.0, 3.0)
        },
        'RSI_Reversion': {
            'rsi_period': (10, 20),
            'oversold_level': (20, 40),
            'overbought_level': (60, 80)
        },
        'Mean_Reversion': {
            'lookback_period': (10, 30),
            'deviation_threshold': (1.0, 3.0)
        }
    }
    
    return suggestions.get(strategy_name, {})

