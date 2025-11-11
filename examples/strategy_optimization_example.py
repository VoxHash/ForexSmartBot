"""Example: Using strategy optimization tools."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import GeneticOptimizer, HyperparameterOptimizer
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.core.risk_engine import RiskConfig


def fitness_function(params: dict) -> float:
    """Fitness function for optimization."""
    try:
        # Create strategy with parameters
        strategy = get_strategy('SMA_Crossover', **params)
        
        # Run backtest
        data_provider = YFinanceProvider()
        backtest_service = BacktestService(data_provider)
        
        results = backtest_service.run_backtest(
            strategy=strategy,
            symbol='EURUSD=X',
            start_date='2023-01-01',
            end_date='2023-12-31',
            initial_balance=10000.0,
            risk_config=RiskConfig()
        )
        
        # Return Sharpe ratio as fitness
        if 'error' in results:
            return -100.0
            
        metrics = results.get('metrics', {})
        sharpe = metrics.get('sharpe_ratio', 0.0)
        return sharpe if not isinstance(sharpe, (float, int)) or sharpe > -100 else -100.0
        
    except Exception as e:
        print(f"Error in fitness function: {e}")
        return -100.0


def main():
    """Example: Optimize strategy parameters."""
    print("Strategy Optimization Example")
    print("=" * 50)
    
    # Example 1: Genetic Algorithm Optimization
    print("\n1. Genetic Algorithm Optimization")
    print("-" * 50)
    
    param_bounds = {
        'fast_period': (10, 30),
        'slow_period': (40, 80),
        'atr_period': (10, 20)
    }
    
    ga_optimizer = GeneticOptimizer(
        param_bounds=param_bounds,
        population_size=20,
        generations=10
    )
    
    best_params, best_fitness = ga_optimizer.optimize(fitness_function, verbose=True)
    print(f"\nBest parameters: {best_params}")
    print(f"Best fitness (Sharpe ratio): {best_fitness:.4f}")
    
    # Example 2: Hyperparameter Optimization with Optuna
    print("\n2. Hyperparameter Optimization (Optuna)")
    print("-" * 50)
    
    param_space = {
        'fast_period': {'type': 'int', 'low': 10, 'high': 30},
        'slow_period': {'type': 'int', 'low': 40, 'high': 80},
        'atr_period': {'type': 'int', 'low': 10, 'high': 20}
    }
    
    optuna_optimizer = HyperparameterOptimizer(
        param_space=param_space,
        n_trials=20,
        direction='maximize'
    )
    
    def objective(params):
        return fitness_function(params)
    
    best_params_optuna, best_value = optuna_optimizer.optimize(objective, verbose=True)
    print(f"\nBest parameters: {best_params_optuna}")
    print(f"Best value (Sharpe ratio): {best_value:.4f}")
    
    print("\nOptimization complete!")


if __name__ == "__main__":
    main()

