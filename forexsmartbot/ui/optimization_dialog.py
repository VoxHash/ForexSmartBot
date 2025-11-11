"""
Optimization Dialog
Provides UI for various optimization tools.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QDoubleSpinBox, QSpinBox,
    QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Dict, Tuple, Any
import inspect
import numpy as np


def get_strategy_param_bounds(strategy_name: str) -> Dict[str, Tuple[float, float]]:
    """
    Get parameter bounds for a strategy by inspecting its __init__ signature.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Dictionary mapping parameter names to (min, max) bounds
    """
    from ..strategies import get_strategy, STRATEGIES
    
    if strategy_name not in STRATEGIES:
        return {}
    
    strategy_class = STRATEGIES[strategy_name]
    sig = inspect.signature(strategy_class.__init__)
    
    bounds = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        # Get default value
        default = param.default if param.default != inspect.Parameter.empty else None
        
        # Skip non-numeric parameters (strings, etc.)
        if default is None:
            continue
        if isinstance(default, str):
            continue
        if not isinstance(default, (int, float)):
            continue
        
        # Create bounds: ±50% of default, with sensible limits
        if isinstance(default, int):
            min_val = max(1, int(default * 0.5))
            max_val = int(default * 1.5)
            # Ensure min <= max
            if min_val >= max_val:
                max_val = min_val + 1
        else:  # float
            min_val = max(0.001, default * 0.5)  # Lower minimum for floats
            max_val = default * 1.5
            # Ensure min <= max, handle edge cases
            if min_val >= max_val:
                # If default is very small, create a reasonable range
                if default < 0.01:
                    min_val = max(0.001, default * 0.1)
                    max_val = default * 10.0
                else:
                    max_val = min_val + (default * 0.1)  # Add small buffer
            # Final safety check
            if min_val >= max_val:
                max_val = min_val + 0.01
        
        # Special handling for common parameters (only adjust if needed, don't override valid ranges)
        if 'period' in param_name.lower() or 'lookback' in param_name.lower():
            min_val = max(5, min_val)
            max_val = min(200, max_val)
        elif 'rsi' in param_name.lower():
            if 'oversold' in param_name.lower():
                min_val = 10
                max_val = 40
            elif 'overbought' in param_name.lower():
                min_val = 60
                max_val = 90
            else:
                min_val = max(5, min_val)
                max_val = min(30, max_val)
        elif 'std' in param_name.lower() or 'dev' in param_name.lower():
            min_val = max(0.5, min_val)
            max_val = min(5.0, max_val)
        elif 'threshold' in param_name.lower() or 'pct' in param_name.lower():
            # For thresholds and percentages, create reasonable range around default
            if default < 0.001:
                # Very small values: wider range
                min_val = max(0.0001, default * 0.1)
                max_val = min(0.01, default * 10.0)
            elif default < 0.01:
                # Small values: moderate range
                min_val = max(0.001, default * 0.5)
                max_val = min(0.1, default * 2.0)
            else:
                # Normal values: standard range
                min_val = max(0.001, default * 0.5)
                max_val = min(0.1, default * 1.5)
            # Ensure min < max
            if min_val >= max_val:
                if default < 0.01:
                    max_val = min(0.1, min_val + 0.005)
                else:
                    max_val = min(0.1, min_val + 0.01)
        
        # Final validation: ensure min < max before adding to bounds
        if min_val < max_val:
            bounds[param_name] = (float(min_val), float(max_val))
        else:
            # Skip invalid bounds to avoid errors
            print(f"Warning: Skipping invalid bounds for {param_name}: min={min_val}, max={max_val}, default={default}")
    
    return bounds


def get_strategy_param_space(strategy_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get parameter space for Optuna hyperparameter optimization.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Dictionary mapping parameter names to Optuna distribution configs
    """
    param_bounds = get_strategy_param_bounds(strategy_name)
    param_space = {}
    
    for param_name, (min_val, max_val) in param_bounds.items():
        # Determine if it's int or float based on bounds
        if min_val == int(min_val) and max_val == int(max_val):
            param_space[param_name] = {
                'type': 'int',
                'low': int(min_val),
                'high': int(max_val)
            }
        else:
            param_space[param_name] = {
                'type': 'float',
                'low': float(min_val),
                'high': float(max_val)
            }
    
    return param_space


class OptimizationWorker(QThread):
    """Worker thread for optimization tasks."""
    
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int, str)
    
    def __init__(self, optimizer_type: str, strategy_name: str, **kwargs):
        super().__init__()
        self.optimizer_type = optimizer_type
        self.strategy_name = strategy_name
        self.kwargs = kwargs
        
    def run(self):
        """Run optimization."""
        try:
            if self.optimizer_type == 'genetic':
                from ..optimization.genetic_optimizer import GeneticOptimizer
                # Get parameter bounds for the strategy
                param_bounds = get_strategy_param_bounds(self.strategy_name)
                if not param_bounds:
                    self.finished.emit({'error': f'Could not determine parameter bounds for {self.strategy_name}'})
                    return
                
                # Create optimizer with param_bounds
                optimizer = GeneticOptimizer(param_bounds=param_bounds, **self.kwargs)
                
                # Create fitness function that uses backtesting
                def fitness_function(params):
                    from ..services.backtest import BacktestService
                    from ..strategies import get_strategy
                    from ..adapters.data import DummyProvider
                    from datetime import datetime, timedelta
                    
                    try:
                        strategy = get_strategy(self.strategy_name, **params)
                        data_provider = DummyProvider()
                        backtest_service = BacktestService(data_provider)
                        
                        # Run a simple backtest
                        end_date = datetime.now().strftime('%Y-%m-%d')
                        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                        results = backtest_service.run_backtest(
                            strategy, 'EURUSD', start_date, end_date
                        )
                        # Return total return as fitness
                        if 'error' in results:
                            return -float('inf')
                        return results.get('total_return', 0.0)
                    except Exception as e:
                        print(f"Error in fitness function: {e}")
                        return -float('inf')
                
                best_params, best_fitness = optimizer.optimize(fitness_function)
                result = {
                    'best_parameters': best_params,
                    'best_fitness': best_fitness
                }
            elif self.optimizer_type == 'hyperparameter':
                from ..optimization.hyperparameter_optimizer import HyperparameterOptimizer
                # Get parameter space for the strategy
                param_space = get_strategy_param_space(self.strategy_name)
                if not param_space:
                    self.finished.emit({'error': f'Could not determine parameter space for {self.strategy_name}'})
                    return
                
                # Create optimizer with param_space
                optimizer = HyperparameterOptimizer(param_space=param_space, **self.kwargs)
                
                # Create objective function that uses backtesting
                def objective_function(params):
                    from ..services.backtest import BacktestService
                    from ..strategies import get_strategy
                    from ..adapters.data import DummyProvider
                    from datetime import datetime, timedelta
                    
                    try:
                        strategy = get_strategy(self.strategy_name, **params)
                        data_provider = DummyProvider()
                        backtest_service = BacktestService(data_provider)
                        
                        # Run a simple backtest
                        end_date = datetime.now().strftime('%Y-%m-%d')
                        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                        results = backtest_service.run_backtest(
                            strategy, 'EURUSD', start_date, end_date
                        )
                        # Return total return as objective
                        if 'error' in results:
                            return -float('inf')
                        return results.get('total_return', 0.0)
                    except Exception as e:
                        print(f"Error in objective function: {e}")
                        return -float('inf')
                
                best_params, best_value = optimizer.optimize(objective_function)
                result = {
                    'best_parameters': best_params,
                    'best_value': best_value
                }
            elif self.optimizer_type == 'walk_forward':
                from ..optimization.walk_forward import WalkForwardAnalyzer
                from ..strategies import get_strategy
                from ..adapters.data import DummyProvider
                from ..services.backtest import BacktestService
                import pandas as pd
                from datetime import datetime, timedelta
                
                analyzer = WalkForwardAnalyzer(**self.kwargs)
                
                # Get initial parameters
                param_bounds = get_strategy_param_bounds(self.strategy_name)
                initial_params = {name: (bounds[0] + bounds[1]) / 2 
                                 for name, bounds in param_bounds.items()}
                
                # Create strategy factory
                def strategy_factory(params):
                    return get_strategy(self.strategy_name, **params)
                
                # Create optimization function
                def optimize_function(train_data, initial_params):
                    # Simple optimization: use initial params (can be enhanced with actual optimization)
                    # For now, return initial params
                    return initial_params
                
                # Get sample data
                data_provider = DummyProvider()
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)  # 1 year of data
                
                # Create sample data for walk-forward
                dates = pd.date_range(start=start_date, end=end_date, freq='1H')
                sample_data = pd.DataFrame({
                    'Open': 1.0 + np.random.randn(len(dates)).cumsum() * 0.0001,
                    'High': 1.0 + np.random.randn(len(dates)).cumsum() * 0.0001 + 0.0002,
                    'Low': 1.0 + np.random.randn(len(dates)).cumsum() * 0.0001 - 0.0002,
                    'Close': 1.0 + np.random.randn(len(dates)).cumsum() * 0.0001,
                    'Volume': np.random.randint(1000, 10000, len(dates))
                }, index=dates)
                
                result = analyzer.analyze(
                    data=sample_data,
                    strategy_factory=strategy_factory,
                    optimize_function=optimize_function,
                    initial_params=initial_params
                )
            elif self.optimizer_type == 'monte_carlo':
                from ..optimization.monte_carlo import MonteCarloSimulator
                from ..services.backtest import BacktestService
                from ..strategies import get_strategy
                from ..adapters.data import DummyProvider
                from datetime import datetime, timedelta
                import pandas as pd
                
                simulator = MonteCarloSimulator(**self.kwargs)
                
                # Get strategy and run backtest to get returns
                strategy = get_strategy(self.strategy_name)
                data_provider = DummyProvider()
                backtest_service = BacktestService(data_provider)
                
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                backtest_results = backtest_service.run_backtest(
                    strategy, 'EURUSD', start_date, end_date
                )
                
                # Create returns series from backtest results
                if 'error' not in backtest_results and 'equity_curve' in backtest_results:
                    equity = backtest_results['equity_curve']
                    returns = pd.Series(equity).pct_change().dropna()
                else:
                    # Fallback: create sample returns
                    returns = pd.Series(np.random.randn(100) * 0.01)
                
                result = simulator.simulate(returns)
                
            elif self.optimizer_type == 'sensitivity':
                from ..optimization.parameter_sensitivity import ParameterSensitivityAnalyzer
                from ..strategies import get_strategy
                from ..services.backtest import BacktestService
                from ..adapters.data import DummyProvider
                from datetime import datetime, timedelta
                
                analyzer = ParameterSensitivityAnalyzer(**self.kwargs)
                
                # Get parameter bounds
                param_bounds = get_strategy_param_bounds(self.strategy_name)
                if not param_bounds:
                    self.finished.emit({'error': f'Could not determine parameter bounds for {self.strategy_name}'})
                    return
                
                # Create base params (midpoint of bounds)
                base_params = {name: (bounds[0] + bounds[1]) / 2 
                              for name, bounds in param_bounds.items()}
                
                # Create strategy factory
                def strategy_factory(params):
                    return get_strategy(self.strategy_name, **params)
                
                # Create performance function
                def performance_function(strategy):
                    data_provider = DummyProvider()
                    backtest_service = BacktestService(data_provider)
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    results = backtest_service.run_backtest(
                        strategy, 'EURUSD', start_date, end_date
                    )
                    if 'error' in results:
                        return -float('inf')
                    return results.get('total_return', 0.0)
                
                result = analyzer.analyze(
                    strategy_factory=strategy_factory,
                    base_params=base_params,
                    param_ranges=param_bounds,
                    performance_function=performance_function
                )
                
            elif self.optimizer_type == 'multi_objective':
                from ..optimization.multi_objective_optimizer import MultiObjectiveOptimizer, OptimizationObjective
                from ..strategies import get_strategy
                from ..services.backtest import BacktestService
                from ..adapters.data import DummyProvider
                from datetime import datetime, timedelta
                
                # Get parameter bounds
                param_bounds = get_strategy_param_bounds(self.strategy_name)
                if not param_bounds:
                    self.finished.emit({'error': f'Could not determine parameter bounds for {self.strategy_name}'})
                    return
                
                # Create optimizer with objectives
                objectives = [
                    OptimizationObjective.MAXIMIZE_RETURN,
                    OptimizationObjective.MINIMIZE_RISK
                ]
                optimizer = MultiObjectiveOptimizer(
                    param_bounds=param_bounds,
                    objectives=objectives,
                    **self.kwargs
                )
                
                # Create fitness function
                def fitness_function(params):
                    strategy = get_strategy(self.strategy_name, **params)
                    data_provider = DummyProvider()
                    backtest_service = BacktestService(data_provider)
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    results = backtest_service.run_backtest(
                        strategy, 'EURUSD', start_date, end_date
                    )
                    if 'error' in results:
                        return {
                            'return': -float('inf'),
                            'risk': float('inf'),
                            'sharpe': -float('inf'),
                            'sortino': -float('inf'),
                            'max_drawdown': float('inf')
                        }
                    return {
                        'return': results.get('total_return', 0.0),
                        'risk': abs(results.get('max_drawdown', 0.0)),
                        'sharpe': results.get('sharpe_ratio', 0.0),
                        'sortino': results.get('sortino_ratio', 0.0),
                        'max_drawdown': abs(results.get('max_drawdown', 0.0))
                    }
                
                results_list = optimizer.optimize(fitness_function)
                # Convert to dict format
                result = {
                    'pareto_solutions': [
                        {
                            'parameters': r.parameters,
                            'return': r.return_value,
                            'risk': r.risk_value,
                            'sharpe': r.sharpe_ratio
                        }
                        for r in results_list
                    ]
                }
                
            elif self.optimizer_type == 'adaptive':
                from ..optimization.adaptive_parameters import AdaptiveParameterManager, AdaptiveParameter
                from ..strategies import get_strategy
                
                # Get parameter bounds and create base params
                param_bounds = get_strategy_param_bounds(self.strategy_name)
                if not param_bounds:
                    self.finished.emit({'error': f'Could not determine parameter bounds for {self.strategy_name}'})
                    return
                
                # Create base params (midpoint of bounds)
                base_params = {name: (bounds[0] + bounds[1]) / 2 
                              for name, bounds in param_bounds.items()}
                
                # Create adaptation config (simplified - all params can adapt ±20%)
                adaptation_config = {}
                for param_name, (min_val, max_val) in param_bounds.items():
                    adaptation_config[param_name] = AdaptiveParameter(
                        base_value=base_params[param_name],
                        min_value=min_val,
                        max_value=max_val,
                        adaptation_rate=0.2
                    )
                
                manager = AdaptiveParameterManager(
                    strategy_params=base_params,
                    adaptation_config=adaptation_config
                )
                
                # Get base strategy
                strategy = get_strategy(self.strategy_name, **base_params)
                
                # Return manager info (actual adaptation happens in real-time during trading)
                result = {
                    'message': 'Adaptive parameter manager initialized',
                    'strategy': self.strategy_name,
                    'base_params': base_params,
                    'adaptable_params': list(adaptation_config.keys())
                }
            else:
                result = {'error': 'Unknown optimizer type'}
                
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({'error': str(e)})


class OptimizationDialog(QDialog):
    """Dialog for optimization tools."""
    
    def __init__(self, optimizer_type: str, parent=None, language_manager=None):
        super().__init__(parent)
        self.optimizer_type = optimizer_type
        self.language_manager = language_manager
        self.worker = None
        self.setWindowTitle(f"Optimization: {optimizer_type.replace('_', ' ').title()}")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        
        # Strategy selection
        self.strategy_combo = QComboBox()
        from ..strategies import list_strategies
        strategies = list_strategies()
        self.strategy_combo.addItems(strategies)
        config_layout.addRow("Strategy:", self.strategy_combo)
        
        # Optimizer-specific parameters
        if self.optimizer_type == 'genetic':
            self.population_spin = QSpinBox()
            self.population_spin.setRange(10, 1000)
            self.population_spin.setValue(50)
            config_layout.addRow("Population Size:", self.population_spin)
            
            self.generations_spin = QSpinBox()
            self.generations_spin.setRange(10, 500)
            self.generations_spin.setValue(100)
            config_layout.addRow("Generations:", self.generations_spin)
        
        layout.addWidget(config_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Results
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.results_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Run Optimization")
        self.run_btn.clicked.connect(self.run_optimization)
        button_layout.addWidget(self.run_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def run_optimization(self):
        """Run optimization."""
        strategy_name = self.strategy_combo.currentText()
        
        kwargs = {}
        if self.optimizer_type == 'genetic':
            kwargs['population_size'] = self.population_spin.value()
            kwargs['generations'] = self.generations_spin.value()
        
        self.worker = OptimizationWorker(self.optimizer_type, strategy_name, **kwargs)
        self.worker.finished.connect(self.on_optimization_finished)
        self.worker.progress.connect(self.on_progress)
        self.worker.start()
        
        self.run_btn.setEnabled(False)
        self.results_text.setText("Running optimization...")
    
    def on_progress(self, value: int, message: str):
        """Update progress."""
        self.progress_bar.setValue(value)
        self.results_text.append(message)
    
    def on_optimization_finished(self, result: dict):
        """Handle optimization finished."""
        self.run_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        
        if 'error' in result:
            QMessageBox.critical(self, "Error", result['error'])
        else:
            import json
            self.results_text.setText(json.dumps(result, indent=2))

