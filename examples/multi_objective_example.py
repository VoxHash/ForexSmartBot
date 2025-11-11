"""Example: Multi-objective optimization (risk vs. return)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import MultiObjectiveOptimizer, OptimizationObjective
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.core.risk_engine import RiskConfig


def main():
    """Example: Multi-objective optimization."""
    print("=" * 70)
    print("Multi-Objective Optimization Example")
    print("=" * 70)
    
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    
    def fitness_function(params):
        """Fitness function returning multiple objectives."""
        try:
            strategy = get_strategy('SMA_Crossover', **params)
            results = backtest_service.run_backtest(
                strategy=strategy,
                symbol='EURUSD=X',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_balance=10000.0,
                risk_config=RiskConfig()
            )
            
            if 'error' in results:
                return {
                    'return': -1.0,
                    'risk': 1.0,
                    'sharpe': -10.0,
                    'sortino': -10.0,
                    'max_drawdown': 1.0
                }
            
            metrics = results.get('metrics', {})
            equity_series = results.get('equity_series', [])
            
            # Calculate risk (volatility of returns)
            if len(equity_series) > 1:
                returns = pd.Series(equity_series).pct_change().dropna()
                risk = returns.std() if len(returns) > 0 else 1.0
            else:
                risk = 1.0
            
            return {
                'return': results.get('total_return', 0.0),
                'risk': risk,
                'sharpe': metrics.get('sharpe_ratio', 0.0),
                'sortino': metrics.get('sortino_ratio', 0.0),
                'max_drawdown': metrics.get('max_drawdown', 1.0)
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                'return': -1.0,
                'risk': 1.0,
                'sharpe': -10.0,
                'sortino': -10.0,
                'max_drawdown': 1.0
            }
    
    # Define parameter bounds
    param_bounds = {
        'fast_period': (10, 30),
        'slow_period': (40, 80)
    }
    
    # Define objectives
    objectives = [
        OptimizationObjective.MAXIMIZE_RETURN,
        OptimizationObjective.MINIMIZE_RISK
    ]
    
    # Create optimizer
    optimizer = MultiObjectiveOptimizer(
        param_bounds=param_bounds,
        objectives=objectives,
        population_size=20,
        generations=10
    )
    
    print("\nRunning multi-objective optimization...")
    print("Objectives: Maximize Return, Minimize Risk")
    print()
    
    # Run optimization
    results = optimizer.optimize(fitness_function, verbose=True)
    
    # Get Pareto-optimal solutions
    pareto_optimal = optimizer.get_pareto_front(results)
    
    print(f"\n✓ Optimization complete")
    print(f"  Total solutions: {len(results)}")
    print(f"  Pareto-optimal: {len(pareto_optimal)}")
    print()
    
    print("Pareto-Optimal Solutions:")
    print("-" * 70)
    print(f"{'Solution':<10} {'Return':<12} {'Risk':<12} {'Sharpe':<12} {'Parameters'}")
    print("-" * 70)
    
    for i, result in enumerate(pareto_optimal[:10], 1):  # Show top 10
        params_str = f"fast={result.parameters.get('fast_period', 0):.0f}, slow={result.parameters.get('slow_period', 0):.0f}"
        print(f"{i:<10} {result.return_value:>10.2%}  {result.risk_value:>10.4f}  {result.sharpe_ratio:>10.4f}  {params_str}")
    
    # Plot Pareto front if matplotlib available
    try:
        optimizer.plot_pareto_front(pareto_optimal, save_path='pareto_front.png')
    except Exception as e:
        print(f"\nNote: Could not generate plot: {e}")
    
    print("\n" + "=" * 70)
    print("Multi-objective optimization complete!")
    print("=" * 70)


if __name__ == "__main__":
    import pandas as pd
    main()

