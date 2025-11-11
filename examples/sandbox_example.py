"""Example: Strategy sandbox testing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.testing import StrategySandbox
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.core.risk_engine import RiskConfig


def main():
    """Example: Strategy sandbox testing."""
    print("=" * 70)
    print("Strategy Sandbox Testing Example")
    print("=" * 70)
    
    data_provider = YFinanceProvider()
    
    # Create sandbox
    sandbox = StrategySandbox(
        initial_balance=10000.0,
        risk_config=RiskConfig(),
        max_drawdown_limit=0.3,  # 30% max drawdown
        max_loss_per_trade=0.1   # 10% max loss per trade
    )
    
    # Get test data
    df = data_provider.get_data('EURUSD=X', '2023-01-01', '2023-12-31', '1h')
    
    if df.empty:
        print("No data available")
        return
    
    # Test strategy
    strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)
    
    print(f"\nTesting strategy: {strategy.name}")
    print(f"Max Drawdown Limit: 30%")
    print(f"Max Loss Per Trade: 10%")
    print()
    
    # Validate strategy first
    print("Validating strategy...")
    validation = sandbox.validate_strategy(strategy, df.tail(100))
    
    if validation['is_valid']:
        print("✓ Strategy is valid")
    else:
        print("✗ Strategy validation failed:")
        for error in validation['errors']:
            print(f"  - {error}")
        return
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    # Run sandbox test
    print("\nRunning sandbox test...")
    result = sandbox.test_strategy(strategy, df, 'EURUSD=X')
    
    # Display results
    print("\n" + "=" * 70)
    print("Sandbox Test Results")
    print("=" * 70)
    print(f"Strategy: {result['strategy_name']}")
    print(f"Total Return: {result['total_return']:.2%}")
    print(f"Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Winning Trades: {result['winning_trades']}")
    print(f"Win Rate: {result['win_rate']:.2%}")
    print(f"Final Balance: ${result['final_balance']:,.2f}")
    print(f"Safety Status: {'✓ SAFE' if result['is_safe'] else '✗ UNSAFE'}")
    
    # Safety violations
    if result['safety_violations']:
        print(f"\nSafety Violations: {len(result['safety_violations'])}")
        for violation in result['safety_violations'][:5]:  # Show first 5
            print(f"  Step {violation['step']}: {violation['type']} - {violation['message']}")
    else:
        print("\n✓ No safety violations")
    
    print("\n" + "=" * 70)
    print("Sandbox test complete!")
    print("=" * 70)


if __name__ == "__main__":
    import pandas as pd
    main()

