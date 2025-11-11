#!/usr/bin/env python3
"""Command-line tool for parameter sensitivity analysis."""

import argparse
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import ParameterSensitivityAnalyzer
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.core.risk_engine import RiskConfig


def main():
    parser = argparse.ArgumentParser(description='Analyze parameter sensitivity')
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--symbol', default='EURUSD=X', help='Trading symbol')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--base-params', required=True,
                       help='Base parameters as JSON string or file path')
    parser.add_argument('--param-ranges', required=True,
                       help='Parameter ranges as JSON string or file path')
    parser.add_argument('--n-points', type=int, default=10,
                       help='Number of points to test per parameter')
    parser.add_argument('--method', choices=['linear', 'log', 'random'], default='linear',
                       help='Sampling method')
    parser.add_argument('--balance', type=float, default=10000.0,
                       help='Initial balance')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--plot', action='store_true',
                       help='Generate sensitivity plots')
    
    args = parser.parse_args()
    
    # Parse parameters
    if os.path.exists(args.base_params):
        with open(args.base_params, 'r') as f:
            base_params = json.load(f)
    else:
        base_params = json.loads(args.base_params)
    
    if os.path.exists(args.param_ranges):
        with open(args.param_ranges, 'r') as f:
            param_ranges_data = json.load(f)
    else:
        param_ranges_data = json.loads(args.param_ranges)
    
    # Convert ranges to tuples
    param_ranges = {}
    for param, range_data in param_ranges_data.items():
        if isinstance(range_data, dict) and 'min' in range_data and 'max' in range_data:
            param_ranges[param] = (range_data['min'], range_data['max'])
        elif isinstance(range_data, list) and len(range_data) == 2:
            param_ranges[param] = tuple(range_data)
        else:
            print(f"Warning: Invalid range for {param}, skipping", file=sys.stderr)
            continue
    
    # Create strategy factory
    def strategy_factory(params):
        return get_strategy(args.strategy, **params)
    
    # Create performance function
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    
    def performance_function(strategy):
        results = backtest_service.run_backtest(
            strategy=strategy,
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            initial_balance=args.balance,
            risk_config=RiskConfig()
        )
        if 'error' in results:
            return 0.0
        metrics = results.get('metrics', {})
        return metrics.get('total_return', 0.0)
    
    # Run analysis
    print(f"Analyzing sensitivity for {args.strategy} on {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    print()
    
    analyzer = ParameterSensitivityAnalyzer(
        n_points=args.n_points,
        method=args.method
    )
    
    results = analyzer.analyze(
        strategy_factory, base_params, param_ranges, performance_function
    )
    
    # Generate report
    report = analyzer.generate_report(results)
    print(report)
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {args.output}")
    
    # Generate plots if requested
    if args.plot:
        plot_path = args.output.replace('.txt', '.png') if args.output else 'sensitivity_plot.png'
        analyzer.plot_sensitivity(results, save_path=plot_path)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

