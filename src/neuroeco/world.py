"""Entorno 2D de presas y depredadores.

El mundo no sabe nada de redes neuronales: recibe acciones (giro, velocidad) y
devuelve observaciones. Así las mismas reglas del mundo sirven para agentes
aleatorios, por reglas o entrenados.

Convenciones:
- Ángulos en radianes, medidos en sentido antihorario. Todas las entradas de
  observación son relativas al agente y están normalizadas.
- Acción de cada agente: columna 0 = giro en [-1, 1] (se multiplica por
  max_turn), columna 1 = velocidad en [0, 1] (se multiplica por max_speed).
"""
import numpy as np


def wrap_angle(a):
    """Lleva ángulos al intervalo [-pi, pi)."""
    return (a + np.pi) % (2.0 * np.pi) - np.pi


class World:
    def __init__(self, cfg, seed):
        self.cfg = cfg
        self.seed = int(seed)
        self.rng = np.random.default_rng([self.seed, 0])

        w = cfg["world"]
        self.W = float(w["width"])
        self.H = float(w["height"])
        self.max_steps = int(w["max_steps"])
        self.pl = cfg["plants"]
        self.pr = cfg["prey"]
        self.pd = cfg["predators"]

        # Plantas: arreglo de tamaño fijo con máscara de activas.
        self.max_plants = int(self.pl["max_plants"])
        if int(self.pl["initial"]) > self.max_plants:
            raise ValueError("plants.initial no puede superar plants.max_plants")
        self.plant_pos = self._random_positions(self.max_plants)
        self.plant_active = np.zeros(self.max_plants, dtype=bool)
        self.plant_active[: int(self.pl["initial"])] = True

        # Presas.
        n = int(self.pr["initial"])
        self.prey_pos = self._random_positions(n)
        self.prey_heading = self.rng.uniform(-np.pi, np.pi, n)
        self.prey_energy = np.full(n, float(self.pr["start_energy"]))
        self.prey_alive = np.ones(n, dtype=bool)
        self.prey_steps_alive = np.zeros(n, dtype=np.int64)
        self.prey_food = np.zeros(n, dtype=np.int64)

        # Depredadores.
        m = int(self.pd["initial"])
        self.pred_pos = self._random_positions(m)
        self.pred_heading = self.rng.uniform(-np.pi, np.pi, m)
        self.pred_energy = np.full(m, float(self.pd["start_energy"]))
        self.pred_alive = np.ones(m, dtype=bool)
        self.pred_captures = np.zeros(m, dtype=np.int64)

        self.t = 0
        self.capture_steps = []

    # ------------------------------------------------------------------ utilidades
    def _random_positions(self, n):
        return np.column_stack(
            [self.rng.uniform(0, self.W, n), self.rng.uniform(0, self.H, n)]
        )

    @property
    def done(self):
        """El episodio termina al llegar a max_steps o si mueren todas las presas.

        Si mueren todos los depredadores el episodio continúa, para no sesgar
        las métricas de las presas.
        """
        return self.t >= self.max_steps or not self.prey_alive.any()

    @staticmethod
    def _dist_matrix(a_pos, b_pos, a_mask, b_mask):
        """Distancias (n_a, n_b); infinito donde alguno de los dos no está activo."""
        if len(a_pos) == 0 or len(b_pos) == 0:
            return np.full((len(a_pos), len(b_pos)), np.inf)
        d = b_pos[None, :, :] - a_pos[:, None, :]
        dist = np.hypot(d[..., 0], d[..., 1])
        invalid = ~(a_mask[:, None] & b_mask[None, :])
        return np.where(invalid, np.inf, dist)

    def _nearest(self, src_pos, dst_pos, dst_mask):
        """Para cada origen, el destino activo más cercano: distancia y vector."""
        n = len(src_pos)
        if len(dst_pos) == 0:
            return np.full(n, np.inf), np.zeros((n, 2)), np.zeros(n, dtype=np.int64)
        d = dst_pos[None, :, :] - src_pos[:, None, :]
        dist = np.hypot(d[..., 0], d[..., 1])
        dist = np.where(dst_mask[None, :], dist, np.inf)
        idx = np.argmin(dist, axis=1)
        rows = np.arange(n)
        return dist[rows, idx], d[rows, idx], idx

    def _wall_ahead(self, pos, heading, vision):
        """Distancia a la pared siguiendo el rumbo, normalizada por la visión."""
        c, s = np.cos(heading), np.sin(heading)
        with np.errstate(divide="ignore", invalid="ignore"):
            tx = np.where(c > 1e-9, (self.W - pos[:, 0]) / c,
                          np.where(c < -1e-9, -pos[:, 0] / c, np.inf))
            ty = np.where(s > 1e-9, (self.H - pos[:, 1]) / s,
                          np.where(s < -1e-9, -pos[:, 1] / s, np.inf))
        return np.clip(np.minimum(tx, ty) / vision, 0.0, 1.0)

    # ------------------------------------------------------------------ observaciones
    def observe_prey(self):
        """Matriz (n_presas, 6): energía, planta (ángulo, dist), depredador (ángulo, dist), pared."""
        vis = float(self.pr["vision_range"])
        n = len(self.prey_pos)
        obs = np.zeros((n, 6))
        obs[:, 0] = np.clip(self.prey_energy / float(self.pr["max_energy"]), 0.0, 1.0)

        dist, vec, _ = self._nearest(self.prey_pos, self.plant_pos, self.plant_active)
        ang = wrap_angle(np.arctan2(vec[:, 1], vec[:, 0]) - self.prey_heading)
        seen = dist <= vis
        obs[:, 1] = np.where(seen, ang / np.pi, 0.0)
        obs[:, 2] = np.where(seen, dist / vis, 1.0)

        dist, vec, _ = self._nearest(self.prey_pos, self.pred_pos, self.pred_alive)
        ang = wrap_angle(np.arctan2(vec[:, 1], vec[:, 0]) - self.prey_heading)
        seen = dist <= vis
        obs[:, 3] = np.where(seen, ang / np.pi, 0.0)
        obs[:, 4] = np.where(seen, dist / vis, 1.0)

        obs[:, 5] = self._wall_ahead(self.prey_pos, self.prey_heading, vis)
        return obs

    def observe_predator(self):
        """Matriz (n_depredadores, 5): energía, presa (ángulo, dist, rumbo relativo), pared."""
        vis = float(self.pd["vision_range"])
        m = len(self.pred_pos)
        obs = np.zeros((m, 5))
        obs[:, 0] = np.clip(self.pred_energy / float(self.pd["max_energy"]), 0.0, 1.0)

        dist, vec, idx = self._nearest(self.pred_pos, self.prey_pos, self.prey_alive)
        los = np.arctan2(vec[:, 1], vec[:, 0])  # línea de visión depredador -> presa
        ang = wrap_angle(los - self.pred_heading)
        seen = dist <= vis
        obs[:, 1] = np.where(seen, ang / np.pi, 0.0)
        obs[:, 2] = np.where(seen, dist / vis, 1.0)
        if len(self.prey_pos) > 0:
            rel = wrap_angle(self.prey_heading[idx] - los)
        else:
            rel = np.zeros(m)
        obs[:, 3] = np.where(seen, rel / np.pi, 0.0)

        obs[:, 4] = self._wall_ahead(self.pred_pos, self.pred_heading, vis)
        return obs

    # ------------------------------------------------------------------ dinámica
    def _move(self, pos, heading, out, alive, params):
        out = np.asarray(out, dtype=float)
        turn = np.clip(out[:, 0], -1.0, 1.0)
        speed = np.clip(out[:, 1], 0.0, 1.0)
        speed = np.where(alive, speed, 0.0) * float(params["max_speed"])
        heading += np.where(alive, turn, 0.0) * float(params["max_turn"])
        heading[:] = wrap_angle(heading)
        pos[:, 0] = np.clip(pos[:, 0] + np.cos(heading) * speed, 0.0, self.W)
        pos[:, 1] = np.clip(pos[:, 1] + np.sin(heading) * speed, 0.0, self.H)
        return speed

    def step(self, prey_out, pred_out):
        """Avanza un paso. prey_out y pred_out son matrices (n, 2): giro y velocidad."""
        if self.done:
            return
        self.t += 1
        self.prey_steps_alive[self.prey_alive] += 1

        # 1) Movimiento y gasto de energía.
        prey_speed = self._move(self.prey_pos, self.prey_heading, prey_out,
                                self.prey_alive, self.pr)
        pred_speed = self._move(self.pred_pos, self.pred_heading, pred_out,
                                self.pred_alive, self.pd)
        self.prey_energy -= self.prey_alive * (
            float(self.pr["energy_cost_base"]) + float(self.pr["energy_cost_move"]) * prey_speed)
        self.pred_energy -= self.pred_alive * (
            float(self.pd["energy_cost_base"]) + float(self.pd["energy_cost_move"]) * pred_speed)

        # 2) Las presas comen: cada planta la toma la presa más cercana dentro del radio.
        D = self._dist_matrix(self.prey_pos, self.plant_pos, self.prey_alive, self.plant_active)
        if D.size:
            best = np.argmin(D, axis=0)
            dmin = D[best, np.arange(D.shape[1])]
            eaten = dmin <= float(self.pl["eat_radius"])
            if eaten.any():
                np.add.at(self.prey_food, best[eaten], 1)
                np.add.at(self.prey_energy, best[eaten], float(self.pl["energy_value"]))
                self.plant_active[eaten] = False
        np.minimum(self.prey_energy, float(self.pr["max_energy"]), out=self.prey_energy)

        # 3) Los depredadores capturan: cada presa la toma el depredador más cercano dentro del radio.
        D = self._dist_matrix(self.pred_pos, self.prey_pos, self.pred_alive, self.prey_alive)
        if D.size:
            best = np.argmin(D, axis=0)
            dmin = D[best, np.arange(D.shape[1])]
            caught = dmin <= float(self.pd["capture_radius"])
            if caught.any():
                np.add.at(self.pred_captures, best[caught], 1)
                np.add.at(self.pred_energy, best[caught], float(self.pd["energy_gain_capture"]))
                self.prey_alive[caught] = False
                self.capture_steps.extend([self.t] * int(caught.sum()))
        np.minimum(self.pred_energy, float(self.pd["max_energy"]), out=self.pred_energy)

        # 4) Muerte por falta de energía.
        self.prey_alive &= self.prey_energy > 0.0
        self.pred_alive &= self.pred_energy > 0.0

        # 5) Reaparición de plantas.
        if self.rng.random() < float(self.pl["respawn_rate"]):
            free = np.flatnonzero(~self.plant_active)
            if len(free) > 0:
                j = int(self.rng.choice(free))
                self.plant_pos[j] = [self.rng.uniform(0, self.W), self.rng.uniform(0, self.H)]
                self.plant_active[j] = True

    # ------------------------------------------------------------------ métricas
    def metrics(self):
        n_prey = max(len(self.prey_pos), 1)
        n_pred = max(len(self.pred_pos), 1)
        captures = int(self.pred_captures.sum())
        pred_energy = np.where(self.pred_alive, self.pred_energy, 0.0)
        prey_energy = np.where(self.prey_alive, self.prey_energy, 0.0)
        return {
            "steps": self.t,
            "prey_survival": float(self.prey_steps_alive.mean() / self.max_steps),
            "prey_alive_final": int(self.prey_alive.sum()),
            "pred_alive_final": int(self.pred_alive.sum()),
            "food_eaten_total": int(self.prey_food.sum()),
            "food_eaten_per_prey": float(self.prey_food.sum() / n_prey),
            "captures_total": captures,
            "captures_per_pred": float(captures / n_pred),
            "pred_final_energy": float(pred_energy.mean() / float(self.pd["max_energy"])),
            "prey_final_energy": float(prey_energy.mean() / float(self.pr["max_energy"])),
            "first_capture_step": float(min(self.capture_steps)) if self.capture_steps else float("nan"),
            "mean_time_to_capture": float(np.mean(self.capture_steps)) if self.capture_steps else float("nan"),
        }