"""Genetic algorithm optimization for strategy parameters."""

import numpy as np
from typing import Dict, Any, List, Tuple, Callable, Optional
from deap import base, creator, tools, algorithms
import random


class GeneticOptimizer:
    """Genetic algorithm optimizer for strategy parameters."""
    
    def __init__(self, param_bounds: Dict[str, Tuple[float, float]], 
                 population_size: int = 50, generations: int = 30,
                 mutation_rate: float = 0.2, crossover_rate: float = 0.7):
        """
        Initialize genetic optimizer.
        
        Args:
            param_bounds: Dictionary mapping parameter names to (min, max) bounds
            population_size: Size of population
            generations: Number of generations
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
        """
        self.param_bounds = param_bounds
        self.param_names = list(param_bounds.keys())
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # Setup DEAP
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        
        # Register functions
        for i, (name, (min_val, max_val)) in enumerate(param_bounds.items()):
            self.toolbox.register(f"attr_{i}", random.uniform, min_val, max_val)
        
        attrs = [getattr(self.toolbox, f"attr_{i}") for i in range(len(param_bounds))]
        self.toolbox.register("individual", tools.initCycle, creator.Individual, attrs, n=1)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        self.toolbox.register("mate", tools.cxBlend, alpha=0.5)
        self.toolbox.register("mutate", self._mutate, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        
    def _mutate(self, individual, indpb):
        """Mutate individual within bounds."""
        for i, (name, (min_val, max_val)) in enumerate(self.param_bounds.items()):
            if random.random() < indpb:
                individual[i] = random.uniform(min_val, max_val)
        return individual,
        
    def optimize(self, fitness_function: Callable[[Dict[str, float]], float],
                 verbose: bool = True) -> Tuple[Dict[str, float], float]:
        """
        Run genetic algorithm optimization.
        
        Args:
            fitness_function: Function that takes parameter dict and returns fitness score
            verbose: Whether to print progress
            
        Returns:
            Tuple of (best_parameters, best_fitness)
        """
        self.toolbox.register("evaluate", self._evaluate_wrapper, fitness_function)
        
        # Create initial population
        population = self.toolbox.population(n=self.population_size)
        
        # Evaluate initial population
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
            
        # Evolution loop
        for generation in range(self.generations):
            # Select and clone next generation
            offspring = algorithms.varAnd(population, self.toolbox, 
                                         self.crossover_rate, self.mutation_rate)
            
            # Evaluate offspring
            fitnesses = list(map(self.toolbox.evaluate, offspring))
            for ind, fit in zip(offspring, fitnesses):
                ind.fitness.values = fit
                
            # Select next generation
            population = self.toolbox.select(offspring, len(population))
            
            # Get best individual
            best_ind = tools.selBest(population, 1)[0]
            best_fitness = best_ind.fitness.values[0]
            
            if verbose and generation % 5 == 0:
                print(f"Generation {generation}: Best fitness = {best_fitness:.4f}")
                
        # Get best solution
        best_ind = tools.selBest(population, 1)[0]
        best_params = {name: best_ind[i] for i, name in enumerate(self.param_names)}
        best_fitness = best_ind.fitness.values[0]
        
        return best_params, best_fitness
        
    def _evaluate_wrapper(self, fitness_function: Callable, individual):
        """Wrapper to convert individual to parameter dict."""
        params = {name: individual[i] for i, name in enumerate(self.param_names)}
        try:
            fitness = fitness_function(params)
            return (fitness,)
        except Exception as e:
            print(f"Error evaluating parameters: {e}")
            return (-float('inf'),)

