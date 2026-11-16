"""Ejecución de episodios completos (sin interfaz gráfica)."""
import numpy as np

from .world import World


def run_episode(cfg, prey_controller, predator_controller, seed, callback=None):
    """Corre un episodio y devuelve sus métricas.

    El mundo y los controladores usan generadores de azar independientes
    derivados de la misma semilla, de modo que el resultado es reproducible.
    """
    world = World(cfg, seed)
    ctrl_rng = np.random.default_rng([int(seed), 1])
    while not world.done:
        prey_out = prey_controller.act(world.observe_prey(), ctrl_rng)
        pred_out = predator_controller.act(world.observe_predator(), ctrl_rng)
        world.step(prey_out, pred_out)
        if callback is not None:
            callback(world)
    return world.metrics()