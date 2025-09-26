"""Walk-forward analysis script for ForexSmartBot."""

import argparse
import sys
import os
import json
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider, CSVProvider
from forexsmartbot.strategies import get_strategy
from forexsmartbot.core.risk_engine import RiskConfig


def main():
    parser = argparse.ArgumentParser(description='Run walk-forward analysis')
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--symbol', required=True, help='Symbol to test')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--training', type=int, default=252, help='Training period (days)')
    parser.add_argument('--testing', type=int, default=63, help='Testing period (days)')
    parser.add_argument('--step', type=int, default=21, help='Step size (days)')
    parser.add_argument('--data-provider', choices=['yfinance', 'csv'], default='yfinance')
    parser.add_argument('--output', help='Output directory for results')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    
    args = parser.parse_args()
    
    # Initialize data provider
    if args.data_provider == 'yfinance':
        data_provider = YFinanceProvider()
    else:
        data_provider = CSVProvider()
        
    # Initialize backtest service
    backtest_service = BacktestService(data_provider)
    
    # Get strategy
    try:
        strategy = get_strategy(args.strategy)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
        
    # Create risk config
    risk_config = RiskConfig()
    
    # Run walk-forward analysis
    print(f"Running walk-forward analysis for {args.strategy} on {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Training: {args.training} days, Testing: {args.testing} days, Step: {args.step} days")
    
    results = backtest_service.run_walk_forward_analysis(
        strategy=strategy,
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        training_period=args.training,
        testing_period=args.testing,
        step_size=args.step,
        risk_config=risk_config
    )
    
    if 'error' in results:
        print(f"Error: {results['error']}")
        return 1
        
    # Print summary
    print("\n=== WALK-FORWARD ANALYSIS RESULTS ===")
    print(f"Symbol: {results['symbol']}")
    print(f"Strategy: {results['strategy']}")
    print(f"Total Splits: {results['splits']}")
    
    agg_metrics = results['aggregate_metrics']
    print(f"\nAggregate Metrics:")
    print(f"Average Return: {agg_metrics['avg_return']:.4f}")
    print(f"Return Std Dev: {agg_metrics['std_return']:.4f}")
    print(f"Min Return: {agg_metrics['min_return']:.4f}")
    print(f"Max Return: {agg_metrics['max_return']:.4f}")
    print(f"Average Max Drawdown: {agg_metrics['avg_max_drawdown']:.4f}")
    print(f"Max Max Drawdown: {agg_metrics['max_max_drawdown']:.4f}")
    print(f"Average Win Rate: {agg_metrics['avg_win_rate']:.4f}")
    print(f"Average Profit Factor: {agg_metrics['avg_profit_factor']:.4f}")
    print(f"Average Sharpe Ratio: {agg_metrics['avg_sharpe_ratio']:.4f}")
    print(f"Profitable Splits: {agg_metrics['profitable_splits']}/{agg_metrics['total_splits']}")
    
    # Save results
    output_dir = args.output or "data/walk_forward"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{args.strategy}_{args.symbol}_{timestamp}"
    
    # Save JSON results
    json_file = os.path.join(output_dir, f"{filename}.json")
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {json_file}")
    
    # Save CSV summary
    csv_file = os.path.join(output_dir, f"{filename}_summary.csv")
    summary_data = []
    for result in results['results']:
        summary_data.append({
            'split': result['split'],
            'test_start': result['test_start'],
            'test_end': result['test_end'],
            'total_return': result['total_return'],
            'max_drawdown': result['max_drawdown'],
            'win_rate': result['win_rate'],
            'profit_factor': result['profit_factor'],
            'sharpe_ratio': result['sharpe_ratio'],
            'total_trades': result['total_trades']
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(csv_file, index=False)
    print(f"Summary saved to: {csv_file}")
    
    # Generate plots if requested
    if args.plot:
        try:
            import matplotlib.pyplot as plt
            
            # Plot returns distribution
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            returns = [r['total_return'] for r in results['results']]
            plt.hist(returns, bins=20, alpha=0.7, edgecolor='black')
            plt.title('Returns Distribution')
            plt.xlabel('Total Return')
            plt.ylabel('Frequency')
            
            # Plot drawdown distribution
            plt.subplot(2, 2, 2)
            drawdowns = [r['max_drawdown'] for r in results['results']]
            plt.hist(drawdowns, bins=20, alpha=0.7, edgecolor='black', color='red')
            plt.title('Max Drawdown Distribution')
            plt.xlabel('Max Drawdown')
            plt.ylabel('Frequency')
            
            # Plot returns over time
            plt.subplot(2, 2, 3)
            plt.plot(returns, marker='o', alpha=0.7)
            plt.title('Returns Over Time')
            plt.xlabel('Split')
            plt.ylabel('Total Return')
            plt.grid(True, alpha=0.3)
            
            # Plot win rate over time
            plt.subplot(2, 2, 4)
            win_rates = [r['win_rate'] for r in results['results']]
            plt.plot(win_rates, marker='o', alpha=0.7, color='green')
            plt.title('Win Rate Over Time')
            plt.xlabel('Split')
            plt.ylabel('Win Rate')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            plot_file = os.path.join(output_dir, f"{filename}_plots.png")
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"Plots saved to: {plot_file}")
            
        except ImportError:
            print("Matplotlib not available for plotting")
        except Exception as e:
            print(f"Error generating plots: {e}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
