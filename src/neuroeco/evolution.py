"""Algoritmo genético (neuroevolución) sobre vectores de pesos.

Cada generación: se ordena la población por fitness, los mejores pasan sin
cambios (elitismo) y el resto se genera eligiendo padres por torneo y aplicando
mutación gaussiana (y, opcionalmente, cruce uniforme con evolution.crossover_rate).
"""
import numpy as np


class Evolution:
    def __init__(self, evo_cfg):
        self.elite = int(evo_cfg["elite"])
        self.tournament_size = int(evo_cfg["tournament_size"])
        self.mutation_rate = float(evo_cfg["mutation_rate"])
        self.mutation_sigma = float(evo_cfg["mutation_sigma"])
        self.crossover_rate = float(evo_cfg.get("crossover_rate", 0.0))

    def _tournament(self, fitness, rng):
        """Elige k individuos al azar y devuelve el índice del mejor."""
        idx = rng.integers(0, len(fitness), size=self.tournament_size)
        return int(idx[np.argmax(fitness[idx])])

    def next_population(self, population, fitness, rng):
        """Genera la siguiente población a partir de la actual y su fitness."""
        fitness = np.asarray(fitness, dtype=float)
        n, n_params = population.shape
        order = np.argsort(-fitness, kind="stable")
        new = np.empty_like(population)
        new[: self.elite] = population[order[: self.elite]]
        for i in range(self.elite, n):
            child = population[self._tournament(fitness, rng)].copy()
            if self.crossover_rate > 0.0 and rng.random() < self.crossover_rate:
                other = population[self._tournament(fitness, rng)]
                child = np.where(rng.random(n_params) < 0.5, child, other)
            mutate = rng.random(n_params) < self.mutation_rate
            child = child + mutate * rng.normal(0.0, self.mutation_sigma, n_params)
            new[i] = child
        return new