"""Real-time strategy monitoring and health checks."""

import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class StrategyHealth:
    """Strategy health metrics."""
    strategy_name: str
    status: HealthStatus
    last_signal_time: Optional[datetime] = None
    signal_count: int = 0
    error_count: int = 0
    execution_time_avg: float = 0.0
    execution_time_max: float = 0.0
    memory_usage_mb: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class StrategyMonitor:
    """Monitor strategy execution in real-time."""
    
    def __init__(self, check_interval: float = 60.0):
        """
        Initialize strategy monitor.
        
        Args:
            check_interval: Interval between health checks in seconds
        """
        self.check_interval = check_interval
        self.strategies: Dict[str, StrategyHealth] = {}
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.callbacks: List[Callable[[str, StrategyHealth], None]] = []
        
    def register_strategy(self, strategy_name: str) -> None:
        """Register a strategy for monitoring."""
        self.strategies[strategy_name] = StrategyHealth(
            strategy_name=strategy_name,
            status=HealthStatus.UNKNOWN
        )
        self.metrics_history[strategy_name] = []
        
    def record_signal(self, strategy_name: str, execution_time: float = 0.0) -> None:
        """Record a signal generation event."""
        if strategy_name not in self.strategies:
            self.register_strategy(strategy_name)
            
        health = self.strategies[strategy_name]
        health.last_signal_time = datetime.now()
        health.signal_count += 1
        
        # Update execution time metrics
        if execution_time > 0:
            if health.execution_time_avg == 0:
                health.execution_time_avg = execution_time
            else:
                health.execution_time_avg = (health.execution_time_avg * 0.9) + (execution_time * 0.1)
            health.execution_time_max = max(health.execution_time_max, execution_time)
            
        self._update_health_status(strategy_name)
        
    def record_error(self, strategy_name: str, error_message: str) -> None:
        """Record an error event."""
        if strategy_name not in self.strategies:
            self.register_strategy(strategy_name)
            
        health = self.strategies[strategy_name]
        health.error_count += 1
        health.errors.append(f"{datetime.now()}: {error_message}")
        
        # Keep only last 10 errors
        if len(health.errors) > 10:
            health.errors = health.errors[-10:]
            
        self._update_health_status(strategy_name)
        
    def record_warning(self, strategy_name: str, warning_message: str) -> None:
        """Record a warning event."""
        if strategy_name not in self.strategies:
            self.register_strategy(strategy_name)
            
        health = self.strategies[strategy_name]
        health.warnings.append(f"{datetime.now()}: {warning_message}")
        
        # Keep only last 10 warnings
        if len(health.warnings) > 10:
            health.warnings = health.warnings[-10:]
            
        self._update_health_status(strategy_name)
        
    def _update_health_status(self, strategy_name: str) -> None:
        """Update health status based on metrics."""
        health = self.strategies[strategy_name]
        
        # Determine status
        if health.error_count > 10:
            health.status = HealthStatus.CRITICAL
        elif health.error_count > 5 or len(health.warnings) > 5:
            health.status = HealthStatus.WARNING
        elif health.last_signal_time and (datetime.now() - health.last_signal_time).total_seconds() < 3600:
            health.status = HealthStatus.HEALTHY
        else:
            health.status = HealthStatus.UNKNOWN
            
        # Store metrics snapshot
        self.metrics_history[strategy_name].append({
            'timestamp': datetime.now(),
            'status': health.status.value,
            'signal_count': health.signal_count,
            'error_count': health.error_count,
            'execution_time_avg': health.execution_time_avg
        })
        
        # Keep only last 1000 metrics
        if len(self.metrics_history[strategy_name]) > 1000:
            self.metrics_history[strategy_name] = self.metrics_history[strategy_name][-1000:]
            
        # Trigger callbacks
        for callback in self.callbacks:
            try:
                callback(strategy_name, health)
            except Exception as e:
                print(f"Error in monitor callback: {e}")
                
    def get_health(self, strategy_name: str) -> Optional[StrategyHealth]:
        """Get current health status for a strategy."""
        return self.strategies.get(strategy_name)
        
    def get_all_health(self) -> Dict[str, StrategyHealth]:
        """Get health status for all strategies."""
        return self.strategies.copy()
        
    def add_callback(self, callback: Callable[[str, StrategyHealth], None]) -> None:
        """Add a callback function for health updates."""
        self.callbacks.append(callback)
        
    def get_metrics_history(self, strategy_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metrics history for a strategy."""
        history = self.metrics_history.get(strategy_name, [])
        return history[-limit:]
    
    def get_strategy_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all strategies in a format suitable for UI display.
        
        Returns:
            Dictionary mapping strategy names to status dictionaries with 'status' and 'performance' keys
        """
        statuses = {}
        for strategy_name, health in self.strategies.items():
            # Calculate performance as a simple metric (signal count - error count)
            performance = health.signal_count - (health.error_count * 2)
            
            statuses[strategy_name] = {
                'status': health.status.value,
                'performance': performance,
                'signal_count': health.signal_count,
                'error_count': health.error_count,
                'last_signal_time': health.last_signal_time.isoformat() if health.last_signal_time else None
            }
        return statuses

