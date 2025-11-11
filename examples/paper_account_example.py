"""Example: Real-time strategy testing on paper account."""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.testing import PaperAccountTester
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.core.risk_engine import RiskConfig


def main():
    """Example: Paper account testing."""
    print("=" * 70)
    print("Paper Account Testing Example")
    print("=" * 70)
    
    data_provider = YFinanceProvider()
    tester = PaperAccountTester(
        data_provider=data_provider,
        initial_balance=10000.0,
        risk_config=RiskConfig()
    )
    
    # Create strategy
    strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)
    
    print("\nStarting paper account test...")
    print(f"Strategy: {strategy.name}")
    print(f"Initial Balance: $10,000.00")
    print()
    
    # Start test
    test_id = tester.start_test(
        strategy_name=strategy.name,
        strategy=strategy,
        symbol='EURUSD=X',
        update_interval=60
    )
    
    print(f"Test ID: {test_id}")
    print("\nSimulating real-time updates...")
    print()
    
    # Simulate updates (in real scenario, this would be called periodically)
    for i in range(5):
        print(f"Update {i+1}/5...", end=' ', flush=True)
        
        status = tester.update_test(test_id)
        
        if 'error' not in status:
            print(f"✓ Equity: ${status.get('current_equity', 0):,.2f}, "
                  f"Return: {status.get('total_return', 0):.2%}, "
                  f"Trades: {status.get('total_trades', 0)}")
        else:
            print(f"✗ Error: {status.get('error')}")
        
        time.sleep(0.1)  # Simulate time passing
    
    # Get test status
    print("\n" + "=" * 70)
    print("Test Status")
    print("=" * 70)
    
    status = tester.get_test_status(test_id)
    for key, value in status.items():
        if key != 'test_id':
            print(f"{key}: {value}")
    
    # Stop test and get results
    print("\nStopping test...")
    result = tester.stop_test(test_id)
    
    print("\n" + "=" * 70)
    print("Test Results")
    print("=" * 70)
    print(f"Strategy: {result.strategy_name}")
    print(f"Test Duration: {result.test_duration}")
    print(f"Total Trades: {result.total_trades}")
    print(f"Winning Trades: {result.winning_trades}")
    print(f"Losing Trades: {result.losing_trades}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.4f}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"Final Balance: ${result.final_balance:,.2f}")
    
    print("\n" + "=" * 70)
    print("Paper account test complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

