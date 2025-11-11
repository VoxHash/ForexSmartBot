"""Parameter sensitivity analysis for strategies."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Callable, Optional
from dataclasses import dataclass


@dataclass
class SensitivityResult:
    """Result of parameter sensitivity analysis."""
    parameter_name: str
    base_value: float
    tested_values: List[float]
    performance_metrics: List[float]
    optimal_value: float
    sensitivity_score: float  # Higher = more sensitive
    impact_range: Tuple[float, float]  # (min, max) performance impact


class ParameterSensitivityAnalyzer:
    """Analyze parameter sensitivity for trading strategies."""
    
    def __init__(self, n_points: int = 10, method: str = 'linear'):
        """
        Initialize sensitivity analyzer.
        
        Args:
            n_points: Number of points to test per parameter
            method: Sampling method ('linear', 'log', 'random')
        """
        self.n_points = n_points
        self.method = method
        
    def analyze(self, strategy_factory: Callable[[Dict[str, Any]], Any],
               base_params: Dict[str, Any],
               param_ranges: Dict[str, Tuple[float, float]],
               performance_function: Callable[[Any], float]) -> Dict[str, SensitivityResult]:
        """
        Analyze sensitivity of parameters.
        
        Args:
            strategy_factory: Function that creates strategy from parameters
            base_params: Base parameter values
            param_ranges: Dictionary mapping parameter names to (min, max) ranges
            performance_function: Function that takes strategy and returns performance metric
            
        Returns:
            Dictionary mapping parameter names to SensitivityResult
        """
        results = {}
        
        for param_name, (min_val, max_val) in param_ranges.items():
            # Generate test values
            test_values = self._generate_test_values(min_val, max_val)
            
            # Test each value
            performance_metrics = []
            for test_value in test_values:
                try:
                    # Create strategy with modified parameter
                    test_params = base_params.copy()
                    test_params[param_name] = test_value
                    strategy = strategy_factory(test_params)
                    
                    # Calculate performance
                    performance = performance_function(strategy)
                    performance_metrics.append(performance)
                    
                except Exception as e:
                    print(f"Error testing {param_name}={test_value}: {e}")
                    performance_metrics.append(np.nan)
                    
            # Find optimal value
            valid_indices = [i for i, p in enumerate(performance_metrics) if not np.isnan(p)]
            if valid_indices:
                optimal_idx = valid_indices[np.argmax([performance_metrics[i] for i in valid_indices])]
                optimal_value = test_values[optimal_idx]
            else:
                optimal_value = base_params.get(param_name, (min_val + max_val) / 2)
                
            # Calculate sensitivity score (coefficient of variation)
            valid_metrics = [p for p in performance_metrics if not np.isnan(p)]
            if len(valid_metrics) > 1:
                sensitivity_score = np.std(valid_metrics) / (np.mean(valid_metrics) + 1e-10)
                impact_range = (min(valid_metrics), max(valid_metrics))
            else:
                sensitivity_score = 0.0
                impact_range = (0.0, 0.0)
                
            results[param_name] = SensitivityResult(
                parameter_name=param_name,
                base_value=base_params.get(param_name, (min_val + max_val) / 2),
                tested_values=test_values,
                performance_metrics=performance_metrics,
                optimal_value=optimal_value,
                sensitivity_score=sensitivity_score,
                impact_range=impact_range
            )
            
        return results
        
    def _generate_test_values(self, min_val: float, max_val: float) -> List[float]:
        """Generate test values based on method."""
        if self.method == 'linear':
            return np.linspace(min_val, max_val, self.n_points).tolist()
        elif self.method == 'log':
            if min_val > 0 and max_val > 0:
                return np.logspace(np.log10(min_val), np.log10(max_val), self.n_points).tolist()
            else:
                return np.linspace(min_val, max_val, self.n_points).tolist()
        elif self.method == 'random':
            return np.random.uniform(min_val, max_val, self.n_points).tolist()
        else:
            return np.linspace(min_val, max_val, self.n_points).tolist()
            
    def generate_report(self, results: Dict[str, SensitivityResult]) -> str:
        """Generate text report of sensitivity analysis."""
        report_lines = [
            "Parameter Sensitivity Analysis Report",
            "=" * 60,
            ""
        ]
        
        # Sort by sensitivity score
        sorted_params = sorted(results.items(), 
                            key=lambda x: x[1].sensitivity_score, 
                            reverse=True)
        
        for param_name, result in sorted_params:
            report_lines.extend([
                f"Parameter: {param_name}",
                f"  Base Value: {result.base_value:.4f}",
                f"  Optimal Value: {result.optimal_value:.4f}",
                f"  Sensitivity Score: {result.sensitivity_score:.4f}",
                f"  Performance Impact Range: [{result.impact_range[0]:.4f}, {result.impact_range[1]:.4f}]",
                f"  Impact Spread: {result.impact_range[1] - result.impact_range[0]:.4f}",
                ""
            ])
            
        return "\n".join(report_lines)
        
    def plot_sensitivity(self, results: Dict[str, SensitivityResult], 
                        save_path: Optional[str] = None) -> None:
        """Plot sensitivity analysis (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
            
            n_params = len(results)
            if n_params == 0:
                return
                
            fig, axes = plt.subplots(n_params, 1, figsize=(10, 3 * n_params))
            if n_params == 1:
                axes = [axes]
                
            for idx, (param_name, result) in enumerate(results.items()):
                ax = axes[idx]
                
                # Filter out NaN values
                valid_indices = [i for i, p in enumerate(result.performance_metrics) 
                               if not np.isnan(p)]
                valid_values = [result.tested_values[i] for i in valid_indices]
                valid_metrics = [result.performance_metrics[i] for i in valid_indices]
                
                ax.plot(valid_values, valid_metrics, 'b-o', linewidth=2, markersize=4)
                ax.axvline(result.base_value, color='r', linestyle='--', 
                          label=f'Base: {result.base_value:.4f}')
                ax.axvline(result.optimal_value, color='g', linestyle='--', 
                          label=f'Optimal: {result.optimal_value:.4f}')
                ax.set_xlabel(f'{param_name} Value')
                ax.set_ylabel('Performance Metric')
                ax.set_title(f'{param_name} Sensitivity (Score: {result.sensitivity_score:.4f})')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Sensitivity plot saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("Matplotlib not available for plotting")

