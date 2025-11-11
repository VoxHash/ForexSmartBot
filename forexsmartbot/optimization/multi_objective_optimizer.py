"""Multi-objective optimization (risk vs. return)."""

import numpy as np
from typing import Dict, Any, List, Tuple, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class OptimizationObjective(Enum):
    """Optimization objectives."""
    MAXIMIZE_RETURN = "maximize_return"
    MINIMIZE_RISK = "minimize_risk"
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MAXIMIZE_SORTINO = "maximize_sortino"
    MINIMIZE_DRAWDOWN = "minimize_drawdown"


@dataclass
class MultiObjectiveResult:
    """Result of multi-objective optimization."""
    parameters: Dict[str, float]
    return_value: float
    risk_value: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    pareto_rank: int  # Lower is better (1 = Pareto optimal)
    dominance_count: int  # How many solutions this dominates


class MultiObjectiveOptimizer:
    """Multi-objective optimizer for risk vs. return optimization."""
    
    def __init__(self, param_bounds: Dict[str, Tuple[float, float]],
                 objectives: List[OptimizationObjective],
                 population_size: int = 50, generations: int = 30):
        """
        Initialize multi-objective optimizer.
        
        Args:
            param_bounds: Dictionary mapping parameter names to (min, max) bounds
            objectives: List of optimization objectives
            population_size: Size of population
            generations: Number of generations
        """
        self.param_bounds = param_bounds
        self.param_names = list(param_bounds.keys())
        self.objectives = objectives
        self.population_size = population_size
        self.generations = generations
        
    def optimize(self, fitness_function: Callable[[Dict[str, float]], Dict[str, float]],
                 verbose: bool = True) -> List[MultiObjectiveResult]:
        """
        Run multi-objective optimization.
        
        Args:
            fitness_function: Function that takes parameters and returns dict of objective values
            verbose: Whether to print progress
            
        Returns:
            List of Pareto-optimal solutions
        """
        import random
        
        # Initialize population
        population = []
        for _ in range(self.population_size):
            params = {name: random.uniform(bounds[0], bounds[1]) 
                     for name, bounds in self.param_bounds.items()}
            objectives = fitness_function(params)
            population.append((params, objectives))
        
        # Evolution loop
        for generation in range(self.generations):
            # Evaluate fitness
            evaluated_population = []
            for params, objectives in population:
                if objectives is None:
                    objectives = fitness_function(params)
                evaluated_population.append((params, objectives))
            
            # Calculate Pareto ranks
            pareto_fronts = self._calculate_pareto_fronts(evaluated_population)
            
            # Select next generation (elitism + diversity)
            population = self._select_next_generation(evaluated_population, pareto_fronts)
            
            # Crossover and mutation
            offspring = self._generate_offspring(population)
            population.extend(offspring)
            
            if verbose and generation % 5 == 0:
                front_0_size = len([f for f in pareto_fronts if f['rank'] == 0])
                print(f"Generation {generation}: Pareto front size = {front_0_size}")
        
        # Get Pareto-optimal solutions
        pareto_fronts = self._calculate_pareto_fronts(evaluated_population)
        pareto_optimal = [f for f in pareto_fronts if f['rank'] == 0]
        
        # Convert to results
        results = []
        for solution in pareto_optimal:
            params = solution['params']
            obj = solution['objectives']
            
            results.append(MultiObjectiveResult(
                parameters=params,
                return_value=obj.get('return', 0.0),
                risk_value=obj.get('risk', 0.0),
                sharpe_ratio=obj.get('sharpe', 0.0),
                sortino_ratio=obj.get('sortino', 0.0),
                max_drawdown=obj.get('max_drawdown', 0.0),
                pareto_rank=0,
                dominance_count=solution.get('dominates', 0)
            ))
        
        return results
        
    def _calculate_pareto_fronts(self, population: List[Tuple[Dict, Dict]]) -> List[Dict]:
        """Calculate Pareto fronts using NSGA-II algorithm."""
        fronts = []
        remaining = list(range(len(population)))
        rank = 0
        
        while remaining:
            front = []
            dominated = []
            
            for i in remaining:
                is_dominated = False
                dominates_count = 0
                
                for j in remaining:
                    if i == j:
                        continue
                    
                    if self._dominates(population[j][1], population[i][1]):
                        is_dominated = True
                        break
                    elif self._dominates(population[i][1], population[j][1]):
                        dominates_count += 1
                
                if not is_dominated:
                    front.append({
                        'index': i,
                        'params': population[i][0],
                        'objectives': population[i][1],
                        'rank': rank,
                        'dominates': dominates_count
                    })
                else:
                    dominated.append(i)
            
            fronts.extend(front)
            remaining = dominated
            rank += 1
            
        return fronts
        
    def _dominates(self, obj1: Dict[str, float], obj2: Dict[str, float]) -> bool:
        """Check if obj1 dominates obj2."""
        # For maximization objectives, higher is better
        # For minimization objectives, lower is better
        
        better_in_at_least_one = False
        
        for obj_type in self.objectives:
            if obj_type == OptimizationObjective.MAXIMIZE_RETURN:
                if obj1.get('return', 0) > obj2.get('return', 0):
                    better_in_at_least_one = True
                elif obj1.get('return', 0) < obj2.get('return', 0):
                    return False
            elif obj_type == OptimizationObjective.MINIMIZE_RISK:
                if obj1.get('risk', float('inf')) < obj2.get('risk', float('inf')):
                    better_in_at_least_one = True
                elif obj1.get('risk', float('inf')) > obj2.get('risk', float('inf')):
                    return False
            elif obj_type == OptimizationObjective.MAXIMIZE_SHARPE:
                if obj1.get('sharpe', -float('inf')) > obj2.get('sharpe', -float('inf')):
                    better_in_at_least_one = True
                elif obj1.get('sharpe', -float('inf')) < obj2.get('sharpe', -float('inf')):
                    return False
        
        return better_in_at_least_one
        
    def _select_next_generation(self, population: List[Tuple[Dict, Dict]], 
                               fronts: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Select next generation using crowding distance."""
        # Sort by rank, then by crowding distance
        fronts_sorted = sorted(fronts, key=lambda x: (x['rank'], -x.get('crowding_distance', 0)))
        
        # Select top solutions
        selected = []
        for front in fronts_sorted[:self.population_size]:
            selected.append((front['params'], front['objectives']))
        
        return selected
        
    def _generate_offspring(self, population: List[Tuple[Dict, Dict]]) -> List[Tuple[Dict, Dict]]:
        """Generate offspring through crossover and mutation."""
        import random
        
        offspring = []
        for _ in range(self.population_size // 2):
            # Tournament selection
            parent1 = self._tournament_select(population)
            parent2 = self._tournament_select(population)
            
            # Crossover
            child1, child2 = self._crossover(parent1[0], parent2[0])
            
            # Mutation
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            
            offspring.append((child1, None))
            offspring.append((child2, None))
        
        return offspring
        
    def _tournament_select(self, population: List[Tuple[Dict, Dict]], 
                          tournament_size: int = 3) -> Tuple[Dict, Dict]:
        """Tournament selection."""
        import random
        tournament = random.sample(population, min(tournament_size, len(population)))
        # Select based on return (simplified)
        return max(tournament, key=lambda x: x[1].get('return', 0) if x[1] else -float('inf'))
        
    def _crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Tuple[Dict, Dict]:
        """Blend crossover."""
        import random
        alpha = 0.5
        
        child1 = {}
        child2 = {}
        
        for param_name in self.param_names:
            bounds = self.param_bounds[param_name]
            p1_val = parent1.get(param_name, (bounds[0] + bounds[1]) / 2)
            p2_val = parent2.get(param_name, (bounds[0] + bounds[1]) / 2)
            
            # Blend crossover
            diff = abs(p1_val - p2_val)
            min_val = min(p1_val, p2_val) - alpha * diff
            max_val = max(p1_val, p2_val) + alpha * diff
            
            # Clamp to bounds
            min_val = max(min_val, bounds[0])
            max_val = min(max_val, bounds[1])
            
            child1[param_name] = random.uniform(min_val, max_val)
            child2[param_name] = random.uniform(min_val, max_val)
        
        return child1, child2
        
    def _mutate(self, individual: Dict[str, float], mutation_rate: float = 0.1) -> Dict[str, float]:
        """Mutate individual."""
        import random
        
        mutated = individual.copy()
        
        for param_name, bounds in self.param_bounds.items():
            if random.random() < mutation_rate:
                mutated[param_name] = random.uniform(bounds[0], bounds[1])
        
        return mutated
        
    def get_pareto_front(self, results: List[MultiObjectiveResult]) -> List[MultiObjectiveResult]:
        """Get Pareto-optimal solutions from results."""
        return [r for r in results if r.pareto_rank == 0]
        
    def plot_pareto_front(self, results: List[MultiObjectiveResult], 
                         save_path: Optional[str] = None) -> None:
        """Plot Pareto front (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
            
            pareto_optimal = self.get_pareto_front(results)
            
            returns = [r.return_value for r in pareto_optimal]
            risks = [r.risk_value for r in pareto_optimal]
            
            plt.figure(figsize=(10, 6))
            plt.scatter(risks, returns, alpha=0.6, s=100)
            plt.xlabel('Risk')
            plt.ylabel('Return')
            plt.title('Pareto Front: Risk vs. Return')
            plt.grid(True, alpha=0.3)
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Pareto front plot saved to {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("Matplotlib not available for plotting")

