"""Example: Strategy performance comparison."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.analytics import StrategyComparator
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.core.risk_engine import RiskConfig


def main():
    """Example: Compare multiple strategies."""
    print("=" * 70)
    print("Strategy Performance Comparison Example")
    print("=" * 70)
    
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    comparator = StrategyComparator()
    
    # Strategies to compare
    strategies_to_test = [
        'SMA_Crossover',
        'RSI_Reversion',
        'BreakoutATR',
        'Mean_Reversion'
    ]
    
    print(f"\nRunning backtests for {len(strategies_to_test)} strategies...")
    print()
    
    # Run backtests and add to comparator
    for strategy_name in strategies_to_test:
        try:
            print(f"Testing {strategy_name}...", end=' ', flush=True)
            
            strategy = get_strategy(strategy_name)
            results = backtest_service.run_backtest(
                strategy=strategy,
                symbol='EURUSD=X',
                start_date='2023-01-01',
                end_date='2023-12-31',
                initial_balance=10000.0,
                risk_config=RiskConfig()
            )
            
            if 'error' not in results:
                comparator.add_strategy_result(strategy_name, results)
                print(f"✓ Return: {results.get('total_return', 0):.2%}")
            else:
                print(f"✗ Error: {results.get('error')}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Compare strategies
    print("\n" + "=" * 70)
    print("Comparison Results (sorted by Sharpe ratio)")
    print("=" * 70)
    
    comparison_results = comparator.compare(sort_by='sharpe_ratio')
    
    # Print comparison
    report = comparator.generate_comparison_report(sort_by='sharpe_ratio')
    print(report)
    
    # Get best strategy
    best = comparator.get_best_strategy('sharpe_ratio')
    if best:
        print(f"\n✓ Best Strategy: {best.strategy_name}")
        print(f"  Sharpe Ratio: {best.sharpe_ratio:.4f}")
        print(f"  Total Return: {best.total_return:.2%}")
        print(f"  Win Rate: {best.win_rate:.2%}")
    
    # Get statistics
    stats = comparator.get_statistics()
    print(f"\nComparison Statistics:")
    print(f"  Number of Strategies: {stats.get('num_strategies', 0)}")
    print(f"  Average Return: {stats.get('avg_return', 0):.2%}")
    print(f"  Best Return: {stats.get('best_return', 0):.2%}")
    print(f"  Best Sharpe: {stats.get('best_sharpe', 0):.4f}")
    
    # Plot comparison if matplotlib available
    try:
        comparator.plot_comparison(
            metrics=['total_return', 'sharpe_ratio'],
            save_path='strategy_comparison.png'
        )
    except Exception as e:
        print(f"\nNote: Could not generate plot: {e}")
    
    print("\n" + "=" * 70)
    print("Strategy comparison complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

