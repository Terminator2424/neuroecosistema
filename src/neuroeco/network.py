"""Red neuronal multicapa (MLP) escrita a mano con NumPy.

Una red es un vector de números (el "genoma"): todos los pesos y sesgos de cada
capa, uno detrás de otro. La arquitectura (los tamaños de las capas) se guarda
aparte. Esto permite que el algoritmo evolutivo trate cada red como un vector.

Orden del genoma: W1, b1, W2, b2, ... donde Wi tiene forma (entradas, salidas).

Salidas de la red (2 neuronas):
- giro: tanh, en [-1, 1];
- velocidad: sigmoide, en [0, 1].
Las capas ocultas usan tanh.
"""
from pathlib import Path

import numpy as np
import yaml


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


class Network:
    """Arquitectura de un MLP: define cuántos parámetros tiene y cómo se leen."""

    def __init__(self, sizes):
        self.sizes = [int(s) for s in sizes]
        if len(self.sizes) < 3:
            raise ValueError("Se necesitan al menos entrada, una capa oculta y salida")
        self.shapes = [(self.sizes[i], self.sizes[i + 1]) for i in range(len(self.sizes) - 1)]
        self.n_params = sum(i * o + o for i, o in self.shapes)

    def random_genome(self, rng):
        """Pesos ~ Normal(0, 1/entradas) y sesgos en cero (escala tipo Xavier)."""
        parts = []
        for n_in, n_out in self.shapes:
            parts.append(rng.normal(0.0, 1.0 / np.sqrt(n_in), size=n_in * n_out))
            parts.append(np.zeros(n_out))
        return np.concatenate(parts)

    def unpack(self, genome):
        """Convierte el vector en una lista de (W, b) sin copiar datos."""
        genome = np.asarray(genome, dtype=float)
        if genome.shape != (self.n_params,):
            raise ValueError(f"El genoma debe tener {self.n_params} parámetros, tiene {genome.shape}")
        layers, k = [], 0
        for n_in, n_out in self.shapes:
            W = genome[k:k + n_in * n_out].reshape(n_in, n_out)
            k += n_in * n_out
            b = genome[k:k + n_out]
            k += n_out
            layers.append((W, b))
        return layers

    @staticmethod
    def forward(obs, layers, return_activations=False):
        """Propaga una matriz de observaciones (n, entradas) por la red.

        Devuelve una matriz (n, 2) con giro y velocidad. Con
        return_activations=True devuelve además la lista de activaciones de cada
        capa (útil para inspeccionar las decisiones).
        """
        x = np.asarray(obs, dtype=float)
        activations = [x]
        for i, (W, b) in enumerate(layers):
            z = x @ W + b
            if i < len(layers) - 1:
                x = np.tanh(z)
            else:
                x = np.column_stack([np.tanh(z[:, 0]), sigmoid(z[:, 1])])
            activations.append(x)
        return (x, activations) if return_activations else x


class NeuralController:
    """Controlador basado en una red: misma interfaz que los controladores de referencia."""

    def __init__(self, sizes, genome):
        self.network = Network(sizes)
        self.genome = np.asarray(genome, dtype=float)
        self.layers = self.network.unpack(self.genome)

    def act(self, obs, rng=None):
        return self.network.forward(obs, self.layers)

    def decide(self, obs):
        """Como act, pero devuelve también las activaciones de cada capa."""
        return self.network.forward(obs, self.layers, return_activations=True)


def layer_sizes(cfg, species):
    """Tamaños de capa de la especie según la configuración (entradas, ocultas, 2 salidas)."""
    if species == "presa":
        return [6] + list(cfg["network"]["prey_hidden"]) + [2]
    if species == "depredador":
        return [5] + list(cfg["network"]["predator_hidden"]) + [2]
    raise ValueError(f"Especie desconocida: {species}")


def load_model(path, species, cfg):
    """Devuelve (tamaños de capa, genoma) de un modelo guardado.

    Si path es la carpeta de una corrida, usa la arquitectura guardada en su
    config.yaml (así se pueden cargar redes de distinto tamaño); si es un .npy,
    usa la arquitectura de cfg.
    """
    path = Path(path)
    sizes = layer_sizes(cfg, species)
    if path.is_dir():
        run_cfg = path / "config.yaml"
        if run_cfg.exists():
            with open(run_cfg, encoding="utf-8") as f:
                sizes = layer_sizes(yaml.safe_load(f), species)
        path = path / "best_genome.npy"
    return sizes, np.load(path)


def load_neural_controller(path, species, cfg):
    """Carga un modelo desde un .npy o desde la carpeta de una corrida (best_genome.npy)."""
    sizes, genome = load_model(path, species, cfg)
    return NeuralController(sizes, genome)