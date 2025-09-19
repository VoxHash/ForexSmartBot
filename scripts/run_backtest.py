import argparse
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.strategies import get_strategy
from forexsmartbot.core.risk_engine import RiskConfig
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(description='Run backtest for ForexSmartBot')
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--symbol', required=True, help='Symbol to test')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--min', dest='min_amt', type=float, default=10.0, help='Minimum trade amount')
    parser.add_argument('--max', dest='max_amt', type=float, default=100.0, help='Maximum trade amount')
    parser.add_argument('--risk', dest='risk_pct', type=float, default=0.02, help='Risk percentage')
    parser.add_argument('--plot', action='store_true', help='Generate plots')
    
    args = parser.parse_args()
    
    # Initialize data provider
    data_provider = YFinanceProvider()
    
    # Initialize backtest service
    backtest_service = BacktestService(data_provider)
    
    # Get strategy
    try:
        strategy = get_strategy(args.strategy)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
        
    # Create risk config
    risk_config = RiskConfig(
        min_trade_amount=args.min_amt,
        max_trade_amount=args.max_amt,
        base_risk_pct=args.risk_pct
    )
    
    # Run backtest
    print(f"Running backtest for {args.strategy} on {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    
    results = backtest_service.run_backtest(
        strategy=strategy,
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        initial_balance=10000.0,
        risk_config=risk_config
    )
    
    if 'error' in results:
        print(f"Error: {results['error']}")
        return 1
        
    # Print results
    print(f"\n=== BACKTEST RESULTS ===")
    print(f"Symbol: {results['symbol']}")
    print(f"Strategy: {results['strategy']}")
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print(f"Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Final Equity: ${results['final_equity']:,.2f}")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}" if results['sharpe_ratio'] else "Sharpe Ratio: N/A")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']}")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Average Win: ${results['avg_win']:.2f}")
    print(f"Average Loss: ${results['avg_loss']:.2f}")
    
    # Save results
    os.makedirs("data/backtests", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/backtests/{args.strategy}_{args.symbol}_{timestamp}"
    
    # Save CSV
    import pandas as pd
    equity_df = pd.DataFrame({
        'Equity': results['equity_series'],
        'Balance': results['balance_series']
    }, index=pd.to_datetime(results['timestamps']))
    
    equity_df.to_csv(f"{filename}.csv")
    print(f"\nResults saved to: {filename}.csv")
    
    # Generate plots if requested
    if args.plot:
        try:
            plt.figure(figsize=(12, 8))
            
            # Plot equity curve
            plt.subplot(2, 1, 1)
            plt.plot(equity_df.index, equity_df['Equity'], label='Equity', linewidth=2)
            plt.plot(equity_df.index, equity_df['Balance'], label='Balance', linewidth=1, alpha=0.7)
            plt.title(f'Equity Curve - {args.strategy} on {args.symbol}')
            plt.ylabel('Value ($)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Plot drawdown
            plt.subplot(2, 1, 2)
            peak = equity_df['Equity'].expanding().max()
            drawdown = (equity_df['Equity'] - peak) / peak * 100
            plt.fill_between(equity_df.index, drawdown, 0, alpha=0.3, color='red')
            plt.plot(equity_df.index, drawdown, color='red', linewidth=1)
            plt.title('Drawdown')
            plt.ylabel('Drawdown (%)')
            plt.xlabel('Date')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f"{filename}_plot.png", dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"Plot saved to: {filename}_plot.png")
            
        except ImportError:
            print("Matplotlib not available for plotting")
        except Exception as e:
            print(f"Error generating plot: {e}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
