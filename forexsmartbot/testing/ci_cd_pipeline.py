"""Automated strategy testing pipeline for CI/CD integration."""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .strategy_sandbox import StrategySandbox
from ..strategies import get_strategy, list_strategies
from ..adapters.data import YFinanceProvider
from ..core.risk_engine import RiskConfig


@dataclass
class TestResult:
    """Test result for CI/CD."""
    strategy_name: str
    passed: bool
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    errors: List[str]
    warnings: List[str]
    timestamp: datetime


class StrategyTestPipeline:
    """Automated testing pipeline for strategies."""
    
    def __init__(self, test_config: Optional[Dict[str, Any]] = None):
        """
        Initialize test pipeline.
        
        Args:
            test_config: Test configuration
        """
        self.test_config = test_config or {
            'symbol': 'EURUSD=X',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'initial_balance': 10000.0,
            'min_sharpe': 0.5,
            'max_drawdown': 0.3,
            'min_trades': 10,
            'min_win_rate': 0.4
        }
        self.sandbox = StrategySandbox(
            initial_balance=self.test_config['initial_balance'],
            max_drawdown_limit=self.test_config.get('max_drawdown', 0.3)
        )
        self.data_provider = YFinanceProvider()
        
    def run_tests(self, strategy_names: Optional[List[str]] = None) -> List[TestResult]:
        """
        Run tests for strategies.
        
        Args:
            strategy_names: List of strategy names to test (None = all)
            
        Returns:
            List of test results
        """
        if strategy_names is None:
            strategy_names = list_strategies()
        
        results = []
        
        # Get test data
        df = self.data_provider.get_data(
            self.test_config['symbol'],
            self.test_config['start_date'],
            self.test_config['end_date'],
            '1h'
        )
        
        if df.empty:
            return [TestResult(
                strategy_name='DATA_ERROR',
                passed=False,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                total_trades=0,
                win_rate=0.0,
                errors=['No data available'],
                warnings=[],
                timestamp=datetime.now()
            )]
        
        for strategy_name in strategy_names:
            try:
                # Get strategy
                strategy = get_strategy(strategy_name)
                
                # Run sandbox test
                test_result = self.sandbox.test_strategy(strategy, df, self.test_config['symbol'])
                
                # Validate results
                passed = self._validate_test_result(test_result)
                
                # Create test result
                result = TestResult(
                    strategy_name=strategy_name,
                    passed=passed,
                    total_return=test_result['total_return'],
                    sharpe_ratio=test_result.get('sharpe_ratio', 0.0),
                    max_drawdown=test_result['max_drawdown'],
                    total_trades=test_result['total_trades'],
                    win_rate=test_result['win_rate'],
                    errors=[v['message'] for v in test_result.get('safety_violations', []) 
                           if v['type'] in ['exception', 'invalid_signal']],
                    warnings=[v['message'] for v in test_result.get('safety_violations', []) 
                             if v['type'] not in ['exception', 'invalid_signal']],
                    timestamp=datetime.now()
                )
                
                results.append(result)
                
            except Exception as e:
                results.append(TestResult(
                    strategy_name=strategy_name,
                    passed=False,
                    total_return=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    total_trades=0,
                    win_rate=0.0,
                    errors=[str(e)],
                    warnings=[],
                    timestamp=datetime.now()
                ))
        
        return results
        
    def _validate_test_result(self, test_result: Dict[str, Any]) -> bool:
        """Validate test result against criteria."""
        # Check safety
        if not test_result.get('is_safe', False):
            return False
        
        # Check Sharpe ratio
        sharpe = test_result.get('sharpe_ratio', 0.0)
        if sharpe < self.test_config.get('min_sharpe', 0.5):
            return False
        
        # Check drawdown
        max_drawdown = test_result.get('max_drawdown', 1.0)
        if max_drawdown > self.test_config.get('max_drawdown', 0.3):
            return False
        
        # Check minimum trades
        total_trades = test_result.get('total_trades', 0)
        if total_trades < self.test_config.get('min_trades', 10):
            return False
        
        # Check win rate
        win_rate = test_result.get('win_rate', 0.0)
        if win_rate < self.test_config.get('min_win_rate', 0.4):
            return False
        
        return True
        
    def generate_report(self, results: List[TestResult], 
                       output_file: Optional[str] = None) -> str:
        """
        Generate test report.
        
        Args:
            results: Test results
            output_file: Optional file to save report
            
        Returns:
            Report text
        """
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        report_lines = [
            "Strategy Test Pipeline Report",
            "=" * 80,
            f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Strategies: {len(results)}",
            f"Passed: {passed}",
            f"Failed: {failed}",
            "",
            "Results:",
            "-" * 80,
            f"{'Strategy':<30} {'Status':<10} {'Return':<10} {'Sharpe':<10} {'Trades':<8}",
            "-" * 80
        ]
        
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            report_lines.append(
                f"{result.strategy_name:<30} "
                f"{status:<10} "
                f"{result.total_return:>8.2%}  "
                f"{result.sharpe_ratio:>8.4f}  "
                f"{result.total_trades:>6}"
            )
            
            if result.errors:
                report_lines.append(f"  Errors: {', '.join(result.errors)}")
            if result.warnings:
                report_lines.append(f"  Warnings: {', '.join(result.warnings)}")
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to {output_file}")
        
        return report
        
    def export_json(self, results: List[TestResult], output_file: str) -> None:
        """Export results as JSON."""
        data = {
            'test_date': datetime.now().isoformat(),
            'test_config': self.test_config,
            'results': [asdict(r) for r in results]
        }
        
        # Convert datetime to string
        for result in data['results']:
            result['timestamp'] = result['timestamp'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results exported to {output_file}")
        
    def exit_with_code(self, results: List[TestResult]) -> int:
        """
        Exit with appropriate code for CI/CD.
        
        Returns:
            Exit code (0 = all passed, 1 = some failed)
        """
        all_passed = all(r.passed for r in results)
        return 0 if all_passed else 1


def main():
    """Main function for CI/CD integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Strategy test pipeline for CI/CD')
    parser.add_argument('--strategies', nargs='+', help='Strategy names to test')
    parser.add_argument('--config', help='Test configuration JSON file')
    parser.add_argument('--output', help='Output report file')
    parser.add_argument('--json', help='Output JSON file')
    
    args = parser.parse_args()
    
    # Load config if provided
    test_config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            test_config = json.load(f)
    
    # Create pipeline
    pipeline = StrategyTestPipeline(test_config)
    
    # Run tests
    results = pipeline.run_tests(args.strategies)
    
    # Generate report
    report = pipeline.generate_report(results, args.output)
    print(report)
    
    # Export JSON if requested
    if args.json:
        pipeline.export_json(results, args.json)
    
    # Exit with appropriate code
    sys.exit(pipeline.exit_with_code(results))


if __name__ == "__main__":
    main()

