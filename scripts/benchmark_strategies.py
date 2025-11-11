#!/usr/bin/env python3
"""Benchmark and compare strategy performance."""

import argparse
import sys
import os
import time
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy, list_strategies
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.core.risk_engine import RiskConfig


def benchmark_strategy(strategy_name, symbol, start_date, end_date, initial_balance):
    """Benchmark a single strategy."""
    try:
        strategy = get_strategy(strategy_name)
        
        # Measure execution time
        start_time = time.time()
        
        service = BacktestService(YFinanceProvider())
        results = service.run_backtest(
            strategy=strategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            risk_config=RiskConfig()
        )
        
        execution_time = time.time() - start_time
        
        if 'error' in results:
            return {
                'strategy': strategy_name,
                'error': results['error'],
                'execution_time': execution_time
            }
        
        metrics = results.get('metrics', {})
        
        return {
            'strategy': strategy_name,
            'execution_time': execution_time,
            'total_return': results.get('total_return', 0),
            'total_trades': results.get('total_trades', 0),
            'winning_trades': results.get('winning_trades', 0),
            'losing_trades': results.get('losing_trades', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'win_rate': results.get('winning_trades', 0) / max(results.get('total_trades', 1), 1),
            'error_count': results.get('error_count', 0)
        }
        
    except Exception as e:
        return {
            'strategy': strategy_name,
            'error': str(e),
            'execution_time': 0
        }


def main():
    parser = argparse.ArgumentParser(description='Benchmark strategies')
    parser.add_argument('--symbol', default='EURUSD=X', help='Trading symbol')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--strategies', nargs='+', help='Strategy names (default: all)')
    parser.add_argument('--balance', type=float, default=10000.0, help='Initial balance')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--sort-by', choices=['return', 'sharpe', 'time', 'trades'], 
                       default='sharpe', help='Sort results by')
    
    args = parser.parse_args()
    
    # Get strategies to benchmark
    if args.strategies:
        strategies_to_test = args.strategies
    else:
        strategies_to_test = list_strategies()
    
    print("=" * 70)
    print("Strategy Benchmark")
    print("=" * 70)
    print(f"Symbol: {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Strategies: {len(strategies_to_test)}")
    print()
    
    results = []
    
    for i, strategy_name in enumerate(strategies_to_test, 1):
        print(f"[{i}/{len(strategies_to_test)}] Benchmarking {strategy_name}...", end=' ', flush=True)
        
        result = benchmark_strategy(
            strategy_name, args.symbol, args.start, args.end, args.balance
        )
        results.append(result)
        
        if 'error' in result:
            print(f"✗ Error: {result['error']}")
        else:
            print(f"✓ Return: {result['total_return']:.2%}, Sharpe: {result['sharpe_ratio']:.4f}, Time: {result['execution_time']:.2f}s")
    
    # Sort results
    if args.sort_by == 'return':
        results.sort(key=lambda x: x.get('total_return', -float('inf')), reverse=True)
    elif args.sort_by == 'sharpe':
        results.sort(key=lambda x: x.get('sharpe_ratio', -float('inf')), reverse=True)
    elif args.sort_by == 'time':
        results.sort(key=lambda x: x.get('execution_time', float('inf')))
    elif args.sort_by == 'trades':
        results.sort(key=lambda x: x.get('total_trades', 0), reverse=True)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Benchmark Results (sorted by " + args.sort_by + ")")
    print("=" * 70)
    print(f"{'Strategy':<30} {'Return':<10} {'Sharpe':<10} {'Trades':<8} {'Time':<8}")
    print("-" * 70)
    
    for result in results:
        if 'error' not in result:
            print(f"{result['strategy']:<30} "
                  f"{result['total_return']:>8.2%}  "
                  f"{result['sharpe_ratio']:>8.4f}  "
                  f"{result['total_trades']:>6}  "
                  f"{result['execution_time']:>6.2f}s")
        else:
            print(f"{result['strategy']:<30} ERROR: {result['error']}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'benchmark_date': datetime.now().isoformat(),
                'symbol': args.symbol,
                'start_date': args.start,
                'end_date': args.end,
                'initial_balance': args.balance,
                'results': results
            }, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

