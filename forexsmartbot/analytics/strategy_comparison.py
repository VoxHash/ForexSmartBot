"""Strategy performance comparison tools."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StrategyComparisonResult:
    """Result of strategy comparison."""
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    rank: int  # Overall rank (1 = best)


class StrategyComparator:
    """Compare multiple strategies."""
    
    def __init__(self):
        self.comparison_results: Dict[str, Dict[str, Any]] = {}
        
    def add_strategy_result(self, strategy_name: str, backtest_results: Dict[str, Any]) -> None:
        """Add strategy backtest results for comparison."""
        metrics = backtest_results.get('metrics', {})
        trades = backtest_results.get('trades', [])
        
        # Calculate additional metrics
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) < 0]
        
        total_profit = sum(t.get('profit', 0) for t in winning_trades)
        total_loss = abs(sum(t.get('profit', 0) for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Calculate average trade duration
        durations = []
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds()
                durations.append(duration)
        avg_duration = np.mean(durations) if durations else 0
        
        self.comparison_results[strategy_name] = {
            'total_return': backtest_results.get('total_return', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'sortino_ratio': metrics.get('sortino_ratio', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'profit_factor': profit_factor,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_trade_duration': avg_duration,
            'total_profit': total_profit,
            'total_loss': total_loss
        }
        
    def compare(self, sort_by: str = 'sharpe_ratio') -> List[StrategyComparisonResult]:
        """
        Compare all strategies.
        
        Args:
            sort_by: Metric to sort by ('sharpe_ratio', 'total_return', 'win_rate', etc.)
            
        Returns:
            List of comparison results, sorted
        """
        results = []
        
        for strategy_name, metrics in self.comparison_results.items():
            results.append(StrategyComparisonResult(
                strategy_name=strategy_name,
                total_return=metrics['total_return'],
                sharpe_ratio=metrics['sharpe_ratio'],
                sortino_ratio=metrics['sortino_ratio'],
                max_drawdown=metrics['max_drawdown'],
                win_rate=metrics['win_rate'],
                profit_factor=metrics['profit_factor'],
                total_trades=metrics['total_trades'],
                avg_trade_duration=metrics['avg_trade_duration'],
                rank=0  # Will be set after sorting
            ))
        
        # Sort by specified metric
        reverse = sort_by in ['sharpe_ratio', 'sortino_ratio', 'total_return', 'win_rate', 'profit_factor']
        results.sort(key=lambda x: getattr(x, sort_by, 0), reverse=reverse)
        
        # Assign ranks
        for i, result in enumerate(results, 1):
            result.rank = i
        
        return results
        
    def generate_comparison_report(self, sort_by: str = 'sharpe_ratio') -> str:
        """Generate text comparison report."""
        results = self.compare(sort_by)
        
        report_lines = [
            "Strategy Performance Comparison",
            "=" * 80,
            f"Sorted by: {sort_by}",
            "",
            f"{'Strategy':<25} {'Return':<10} {'Sharpe':<10} {'Win%':<8} {'Trades':<8} {'Rank':<6}",
            "-" * 80
        ]
        
        for result in results:
            report_lines.append(
                f"{result.strategy_name:<25} "
                f"{result.total_return:>8.2%}  "
                f"{result.sharpe_ratio:>8.4f}  "
                f"{result.win_rate:>6.2%}  "
                f"{result.total_trades:>6}  "
                f"{result.rank:>4}"
            )
        
        return "\n".join(report_lines)
        
    def plot_comparison(self, metrics: List[str] = None, save_path: Optional[str] = None) -> None:
        """
        Plot strategy comparison.
        
        Args:
            metrics: List of metrics to plot (default: ['total_return', 'sharpe_ratio'])
            save_path: Path to save plot
        """
        try:
            import matplotlib.pyplot as plt
            
            if metrics is None:
                metrics = ['total_return', 'sharpe_ratio']
            
            results = self.compare()
            strategy_names = [r.strategy_name for r in results]
            
            n_metrics = len(metrics)
            fig, axes = plt.subplots(1, n_metrics, figsize=(6 * n_metrics, 6))
            
            if n_metrics == 1:
                axes = [axes]
            
            for idx, metric in enumerate(metrics):
                ax = axes[idx]
                values = [getattr(r, metric, 0) for r in results]
                
                ax.barh(strategy_names, values)
                ax.set_xlabel(metric.replace('_', ' ').title())
                ax.set_title(f'Strategy Comparison: {metric.replace("_", " ").title()}')
                ax.grid(True, alpha=0.3, axis='x')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Comparison plot saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("Matplotlib not available for plotting")
            
    def get_best_strategy(self, metric: str = 'sharpe_ratio') -> Optional[StrategyComparisonResult]:
        """Get best strategy by metric."""
        results = self.compare(metric)
        return results[0] if results else None
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get comparison statistics."""
        if not self.comparison_results:
            return {}
        
        all_returns = [m['total_return'] for m in self.comparison_results.values()]
        all_sharpes = [m['sharpe_ratio'] for m in self.comparison_results.values()]
        
        return {
            'num_strategies': len(self.comparison_results),
            'avg_return': np.mean(all_returns),
            'std_return': np.std(all_returns),
            'best_return': max(all_returns),
            'worst_return': min(all_returns),
            'avg_sharpe': np.mean(all_sharpes),
            'best_sharpe': max(all_sharpes),
            'worst_sharpe': min(all_sharpes)
        }

