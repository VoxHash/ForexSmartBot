"""
Example demonstrating v3.2.0 Advanced Analytics features.
"""

from forexsmartbot.analytics import (
    PortfolioAnalytics, RiskAnalytics, ChartPatternRecognizer,
    PerformanceAttribution, CorrelationAnalyzer, TradeJournalManager
)
from forexsmartbot.core.interfaces import Trade
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


def example_portfolio_analytics():
    """Example of portfolio analytics."""
    print("=== Portfolio Analytics Example ===\n")
    
    analytics = PortfolioAnalytics()
    
    # Add sample trades
    for i in range(10):
        trade = Trade(
            symbol="EURUSD",
            side=1 if i % 2 == 0 else -1,
            quantity=1000,
            entry_price=1.1000 + (i * 0.001),
            exit_price=1.1000 + (i * 0.001) + (0.0005 if i % 2 == 0 else -0.0005),
            pnl=50.0 if i % 2 == 0 else -30.0,
            entry_time=datetime.now() - timedelta(days=10-i),
            exit_time=datetime.now() - timedelta(days=9-i)
        )
        analytics.add_trade(trade)
        
    # Calculate metrics
    sharpe = analytics.calculate_sharpe_ratio()
    sortino = analytics.calculate_sortino_ratio()
    max_dd = analytics.calculate_max_drawdown()
    summary = analytics.get_performance_summary()
    
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Sortino Ratio: {sortino:.2f}")
    print(f"Max Drawdown: ${max_dd['max_drawdown']:.2f} ({max_dd['max_drawdown_pct']:.2f}%)")
    print(f"\nPerformance Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()


def example_risk_analytics():
    """Example of risk analytics."""
    print("=== Risk Analytics Example ===\n")
    
    risk = RiskAnalytics()
    
    # Add sample trades
    for i in range(20):
        trade = Trade(
            symbol="GBPUSD",
            side=1 if i % 2 == 0 else -1,
            quantity=1000,
            entry_price=1.2500 + (i * 0.001),
            exit_price=1.2500 + (i * 0.001) + np.random.normal(0, 0.0005),
            pnl=np.random.normal(0, 50),
            entry_time=datetime.now() - timedelta(days=20-i),
            exit_time=datetime.now() - timedelta(days=19-i)
        )
        risk.add_trade(trade)
        
    # Calculate VaR and CVaR
    var_result = risk.calculate_var(confidence_level=0.95, method='historical')
    cvar_result = risk.calculate_cvar(confidence_level=0.95, method='historical')
    
    print(f"VaR (95%): {var_result['var']:.2f} ({var_result['var_pct']:.2f}%)")
    print(f"CVaR (95%): {cvar_result['cvar']:.2f} ({cvar_result['cvar_pct']:.2f}%)")
    
    # Stress testing
    scenarios = [
        {'name': 'Market Crash', 'shock_pct': -20},
        {'name': 'Market Rally', 'shock_pct': 20},
        {'name': 'Volatility Spike', 'shock_pct': -10}
    ]
    stress_results = risk.stress_test(scenarios)
    
    print("\nStress Test Results:")
    for name, result in stress_results.items():
        print(f"  {name}: Loss ${result['loss']:.2f} ({result['loss_pct']:.2f}%)")
    
    # Risk-adjusted returns
    risk_adj = risk.calculate_risk_adjusted_returns()
    print("\nRisk-Adjusted Returns:")
    for metric, value in risk_adj.items():
        print(f"  {metric}: {value:.2f}")
    print()


def example_chart_patterns():
    """Example of chart pattern recognition."""
    print("=== Chart Pattern Recognition Example ===\n")
    
    recognizer = ChartPatternRecognizer()
    
    # Generate sample price data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = 1.1000 + np.cumsum(np.random.randn(100) * 0.001)
    
    data = pd.DataFrame({
        'Open': prices + np.random.randn(100) * 0.0001,
        'High': prices + abs(np.random.randn(100) * 0.0002),
        'Low': prices - abs(np.random.randn(100) * 0.0002),
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Detect patterns
    patterns = recognizer.detect_patterns(data)
    
    print(f"Detected {len(patterns)} patterns:")
    for pattern in patterns:
        print(f"  {pattern['pattern']} ({pattern['type']}) - Confidence: {pattern['confidence']:.2f}")
    print()


def example_performance_attribution():
    """Example of performance attribution."""
    print("=== Performance Attribution Example ===\n")
    
    attribution = PerformanceAttribution()
    
    # Add trades with different strategies and symbols
    strategies = ['SMA_Crossover', 'RSI_Reversion', 'ML_Adaptive_SuperTrend']
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    for i in range(30):
        trade = Trade(
            symbol=np.random.choice(symbols),
            side=1 if i % 2 == 0 else -1,
            quantity=1000,
            entry_price=1.1000 + (i * 0.001),
            exit_price=1.1000 + (i * 0.001) + np.random.normal(0, 0.0005),
            pnl=np.random.normal(0, 50),
            entry_time=datetime.now() - timedelta(days=30-i),
            exit_time=datetime.now() - timedelta(days=29-i)
        )
        trade.strategy = np.random.choice(strategies)
        attribution.add_trade(trade)
        
    # Analyze by strategy
    by_strategy = attribution.analyze_by_strategy()
    print("Performance by Strategy:")
    for strategy, metrics in by_strategy.items():
        print(f"  {strategy}:")
        print(f"    Total PnL: ${metrics['total_pnl']:.2f}")
        print(f"    Win Rate: {metrics['win_rate']:.1f}%")
        print(f"    Profit Factor: {metrics['profit_factor']:.2f}")
        
    # Analyze by symbol
    by_symbol = attribution.analyze_by_symbol()
    print("\nPerformance by Symbol:")
    for symbol, metrics in by_symbol.items():
        print(f"  {symbol}:")
        print(f"    Total PnL: ${metrics['total_pnl']:.2f}")
        print(f"    Win Rate: {metrics['win_rate']:.1f}%")
    print()


def example_correlation():
    """Example of correlation analysis."""
    print("=== Correlation Analysis Example ===\n")
    
    analyzer = CorrelationAnalyzer()
    
    # Generate sample price data for multiple symbols
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    for symbol in symbols:
        prices = 1.1000 + np.cumsum(np.random.randn(100) * 0.001)
        analyzer.add_price_data(symbol, pd.Series(prices, index=dates))
        
    # Calculate correlation
    correlation_matrix = analyzer.calculate_correlation(symbols)
    print("Correlation Matrix:")
    print(correlation_matrix)
    
    # Get summary
    summary = analyzer.get_correlation_summary(symbols)
    print("\nAverage Correlations:")
    for symbol, avg_corr in summary.items():
        print(f"  {symbol}: {avg_corr:.3f}")
    print()


def example_trade_journal():
    """Example of trade journaling."""
    print("=== Trade Journaling Example ===\n")
    
    journal = TradeJournalManager(journal_dir="example_journals")
    
    # Create sample trade
    trade = Trade(
        symbol="EURUSD",
        side=1,
        quantity=1000,
        entry_price=1.1000,
        exit_price=1.1050,
        pnl=50.0,
        entry_time=datetime.now() - timedelta(hours=2),
        exit_time=datetime.now()
    )
    trade.strategy = "SMA_Crossover"
    
    # Journal the trade
    filepath = journal.journal_trade(trade, notes="Good entry, hit TP target")
    print(f"Trade journaled to: {filepath}")
    print()


if __name__ == "__main__":
    print("ForexSmartBot v3.2.0 - Advanced Analytics Examples\n")
    print("=" * 60 + "\n")
    
    example_portfolio_analytics()
    example_risk_analytics()
    example_chart_patterns()
    example_performance_attribution()
    example_correlation()
    example_trade_journal()
    
    print("=" * 60)
    print("All examples completed!")

