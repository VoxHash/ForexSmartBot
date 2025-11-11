"""Hyperparameter optimization using Optuna."""

from typing import Dict, Any, Callable, Optional, Tuple
import optuna
from optuna.samplers import TPESampler


class HyperparameterOptimizer:
    """Hyperparameter optimizer using Optuna (TPE algorithm)."""
    
    def __init__(self, param_space: Dict[str, Dict[str, Any]], 
                 n_trials: int = 100, direction: str = 'maximize'):
        """
        Initialize hyperparameter optimizer.
        
        Args:
            param_space: Dictionary mapping parameter names to Optuna distributions
            n_trials: Number of optimization trials
            direction: 'maximize' or 'minimize'
        """
        self.param_space = param_space
        self.n_trials = n_trials
        self.direction = direction
        self.study = None
        
    def optimize(self, objective_function: Callable[[Dict[str, Any]], float],
                 verbose: bool = True) -> Tuple[Dict[str, Any], float]:
        """
        Run hyperparameter optimization.
        
        Args:
            objective_function: Function that takes trial and returns objective value
            verbose: Whether to print progress
            
        Returns:
            Tuple of (best_parameters, best_value)
        """
        sampler = TPESampler(seed=42)
        self.study = optuna.create_study(
            direction=self.direction,
            sampler=sampler
        )
        
        def objective(trial):
            params = {}
            for name, dist_config in self.param_space.items():
                dist_type = dist_config['type']
                if dist_type == 'float':
                    params[name] = trial.suggest_float(
                        name, dist_config['low'], dist_config['high'],
                        log=dist_config.get('log', False)
                    )
                elif dist_type == 'int':
                    params[name] = trial.suggest_int(
                        name, dist_config['low'], dist_config['high'],
                        log=dist_config.get('log', False)
                    )
                elif dist_type == 'categorical':
                    params[name] = trial.suggest_categorical(
                        name, dist_config['choices']
                    )
            
            return objective_function(params)
        
        self.study.optimize(objective, n_trials=self.n_trials, show_progress_bar=verbose)
        
        best_params = self.study.best_params
        best_value = self.study.best_value
        
        return best_params, best_value
        
    def get_trial_history(self) -> list:
        """Get history of all trials."""
        if self.study is None:
            return []
        return [trial.value for trial in self.study.trials if trial.value is not None]

