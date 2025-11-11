"""Example: CI/CD pipeline usage."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.testing import StrategyTestPipeline


def main():
    """Example: Using CI/CD pipeline."""
    print("=" * 70)
    print("CI/CD Pipeline Example")
    print("=" * 70)
    
    # Test configuration
    test_config = {
        'symbol': 'EURUSD=X',
        'start_date': '2023-01-01',
        'end_date': '2023-12-31',
        'initial_balance': 10000.0,
        'min_sharpe': 0.5,
        'max_drawdown': 0.3,
        'min_trades': 10,
        'min_win_rate': 0.4
    }
    
    # Create pipeline
    pipeline = StrategyTestPipeline(test_config)
    
    # Test specific strategies
    strategies_to_test = ['SMA_Crossover', 'RSI_Reversion', 'BreakoutATR']
    
    print(f"\nTesting {len(strategies_to_test)} strategies...")
    print(f"Criteria:")
    print(f"  Min Sharpe: {test_config['min_sharpe']}")
    print(f"  Max Drawdown: {test_config['max_drawdown']:.0%}")
    print(f"  Min Trades: {test_config['min_trades']}")
    print(f"  Min Win Rate: {test_config['min_win_rate']:.0%}")
    print()
    
    # Run tests
    results = pipeline.run_tests(strategies_to_test)
    
    # Generate report
    report = pipeline.generate_report(results)
    print(report)
    
    # Export JSON
    pipeline.export_json(results, 'ci_cd_test_results.json')
    
    # Exit with appropriate code
    exit_code = pipeline.exit_with_code(results)
    
    print(f"\nExit code: {exit_code} ({'PASS' if exit_code == 0 else 'FAIL'})")
    
    print("\n" + "=" * 70)
    print("CI/CD pipeline example complete!")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

