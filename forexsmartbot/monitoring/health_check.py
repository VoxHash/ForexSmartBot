"""Health check system for strategies."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .strategy_monitor import StrategyMonitor, HealthStatus


class HealthChecker:
    """Perform health checks on strategies."""
    
    def __init__(self, monitor: StrategyMonitor):
        self.monitor = monitor
        
    def check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all strategies."""
        results = {}
        
        for strategy_name in self.monitor.strategies.keys():
            results[strategy_name] = self.check(strategy_name)
            
        return results
        
    def check(self, strategy_name: str) -> Dict[str, Any]:
        """Perform health check on a specific strategy."""
        health = self.monitor.get_health(strategy_name)
        
        if not health:
            return {
                'status': 'unknown',
                'message': 'Strategy not registered',
                'checks': []
            }
            
        checks = []
        
        # Check 1: Recent signal generation
        if health.last_signal_time:
            time_since_signal = (datetime.now() - health.last_signal_time).total_seconds()
            if time_since_signal > 3600:  # 1 hour
                checks.append({
                    'name': 'Signal Generation',
                    'status': 'warning',
                    'message': f'No signals generated in {time_since_signal/3600:.1f} hours'
                })
            else:
                checks.append({
                    'name': 'Signal Generation',
                    'status': 'ok',
                    'message': 'Signals generated recently'
                })
        else:
            checks.append({
                'name': 'Signal Generation',
                'status': 'warning',
                'message': 'No signals generated yet'
            })
            
        # Check 2: Error rate
        if health.error_count > 10:
            checks.append({
                'name': 'Error Rate',
                'status': 'critical',
                'message': f'High error count: {health.error_count}'
            })
        elif health.error_count > 5:
            checks.append({
                'name': 'Error Rate',
                'status': 'warning',
                'message': f'Moderate error count: {health.error_count}'
            })
        else:
            checks.append({
                'name': 'Error Rate',
                'status': 'ok',
                'message': f'Error count: {health.error_count}'
            })
            
        # Check 3: Execution time
        if health.execution_time_max > 5.0:  # 5 seconds
            checks.append({
                'name': 'Execution Time',
                'status': 'warning',
                'message': f'Max execution time: {health.execution_time_max:.2f}s'
            })
        else:
            checks.append({
                'name': 'Execution Time',
                'status': 'ok',
                'message': f'Avg execution time: {health.execution_time_avg:.3f}s'
            })
            
        # Overall status
        critical_count = sum(1 for c in checks if c['status'] == 'critical')
        warning_count = sum(1 for c in checks if c['status'] == 'warning')
        
        if critical_count > 0:
            overall_status = 'critical'
        elif warning_count > 0:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
            
        return {
            'status': overall_status,
            'health_status': health.status.value,
            'checks': checks,
            'timestamp': datetime.now()
        }

