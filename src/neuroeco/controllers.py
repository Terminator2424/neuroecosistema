"""Controladores de referencia (sin aprendizaje).

Todos comparten la interfaz que tendrán las redes neuronales:
    act(obs, rng) -> matriz (n, 2) con giro en [-1, 1] y velocidad en [0, 1].
Reciben solo la observación normalizada, igual que lo harán las redes.
"""
import numpy as np

from .world import wrap_angle


class Controller:
    def act(self, obs, rng):
        raise NotImplementedError


class RandomController(Controller):
    """Giro y velocidad al azar en cada paso."""

    def act(self, obs, rng):
        n = obs.shape[0]
        return np.column_stack([rng.uniform(-1.0, 1.0, n), rng.uniform(0.0, 1.0, n)])


class _RuleBase(Controller):
    def __init__(self, max_turn, wall_threshold=0.12):
        self.max_turn = float(max_turn)
        self.wall_threshold = float(wall_threshold)

    def _finish(self, target, speed, wall, rng):
        """Convierte un ángulo objetivo en giro y evita quedarse contra la pared."""
        turn = np.clip(target / self.max_turn, -1.0, 1.0)
        near_wall = wall < self.wall_threshold
        if near_wall.any():
            sign = np.where(turn != 0.0, np.sign(turn), rng.choice([-1.0, 1.0], len(turn)))
            turn = np.where(near_wall, sign, turn)
            speed = np.where(near_wall, 0.4, speed)
        return np.column_stack([turn, speed])


class PreyRules(_RuleBase):
    """Presa forrajeadora-huidiza: huye si el depredador está cerca; si no, va a la planta más cercana."""

    def __init__(self, max_turn, alarm_fraction=0.6, wall_threshold=0.12):
        super().__init__(max_turn, wall_threshold)
        self.alarm_fraction = float(alarm_fraction)

    def act(self, obs, rng):
        n = obs.shape[0]
        plant_ang, plant_dist = obs[:, 1] * np.pi, obs[:, 2]
        pred_ang, pred_dist = obs[:, 3] * np.pi, obs[:, 4]
        wall = obs[:, 5]

        target = rng.uniform(-0.5, 0.5, n)  # deambular
        speed = np.full(n, 0.5)

        sees_plant = plant_dist < 1.0
        target = np.where(sees_plant, plant_ang, target)
        speed = np.where(sees_plant, 1.0, speed)

        flee = (pred_dist < 1.0) & (pred_dist < self.alarm_fraction)
        target = np.where(flee, wrap_angle(pred_ang + np.pi), target)
        speed = np.where(flee, 1.0, speed)
        return self._finish(target, speed, wall, rng)


class PredatorChaser(_RuleBase):
    """Perseguidor directo (estilo Blinky): va hacia la presa más cercana."""

    def act(self, obs, rng):
        n = obs.shape[0]
        ang, dist, wall = obs[:, 1] * np.pi, obs[:, 2], obs[:, 4]
        sees = dist < 1.0
        target = np.where(sees, ang, rng.uniform(-0.5, 0.5, n))
        speed = np.where(sees, 1.0, 0.6)
        return self._finish(target, speed, wall, rng)


class PredatorInterceptor(_RuleBase):
    """Interceptor (estilo Pinky): apunta al punto donde puede alcanzar a la presa más cercana.

    Supone que la presa avanza en línea recta a su velocidad máxima según su rumbo
    actual y resuelve el punto de encuentro exacto. Sea r = v_presa / v_depredador y
    phi el rumbo de la presa respecto a la línea de visión. El tiempo de intercepción,
    en unidades de d / v_depredador, es (para r < 1):

        tau = (r cos(phi) + sqrt(1 - r^2 sin^2(phi))) / (1 - r^2)

    y el punto de encuentro, en el sistema de la línea de visión, es
    (1 + r tau cos(phi), r tau sin(phi)). Si r >= 1 no siempre hay solución y se usa
    tau = 1 (aproximación).
    """

    def __init__(self, max_turn, speed_ratio, wall_threshold=0.12):
        super().__init__(max_turn, wall_threshold)
        self.speed_ratio = float(speed_ratio)  # velocidad máxima de la presa / del depredador

    def act(self, obs, rng):
        n = obs.shape[0]
        ang, dist = obs[:, 1] * np.pi, obs[:, 2]
        phi, wall = obs[:, 3] * np.pi, obs[:, 4]
        r = self.speed_ratio
        cos_p, sin_p = np.cos(phi), np.sin(phi)
        if r < 1.0:
            tau = (r * cos_p + np.sqrt(1.0 - (r * sin_p) ** 2)) / (1.0 - r * r)
        else:
            tau = np.ones_like(phi)
        lead = np.arctan2(r * tau * sin_p, 1.0 + r * tau * cos_p)
        sees = dist < 1.0
        target = np.where(sees, wrap_angle(ang + lead), rng.uniform(-0.5, 0.5, n))
        speed = np.where(sees, 1.0, 0.6)
        return self._finish(target, speed, wall, rng)


PREY_CONTROLLERS = ("aleatorio", "reglas")
PREDATOR_CONTROLLERS = ("aleatorio", "perseguidor", "interceptor")


def make_prey_controller(name, cfg):
    if name == "aleatorio":
        return RandomController()
    if name == "reglas":
        return PreyRules(cfg["prey"]["max_turn"])
    raise ValueError(f"Controlador de presa desconocido: {name}")


def make_predator_controller(name, cfg):
    if name == "aleatorio":
        return RandomController()
    if name == "perseguidor":
        return PredatorChaser(cfg["predators"]["max_turn"])
    if name == "interceptor":
        ratio = cfg["prey"]["max_speed"] / cfg["predators"]["max_speed"]
        return PredatorInterceptor(cfg["predators"]["max_turn"], ratio)
    raise ValueError(f"Controlador de depredador desconocido: {name}")