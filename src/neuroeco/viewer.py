"""Visor en tiempo real (pygame): simulación, consulta de decisiones y modo defensa.

- Clic en un animal: muestra qué percibe (entradas), qué activan las capas ocultas de su red
  y qué decide (giro y velocidad). Si el controlador es por reglas, muestra la acción aplicada.
- Panel de estadísticas en vivo (presas vivas y capturas acumuladas).
- Modo defensa: cambiar escenario, número de depredadores, cantidad de comida, tipo de
  controlador de cada especie y semilla sin salir del visor. Cada cambio reinicia el episodio
  con la misma semilla, para poder comparar.

El visor solo observa la simulación: usa el mismo World y los mismos controladores que los
experimentos.
"""
import copy
from collections import deque

import numpy as np
import pygame

from .config import ROOT, load_scenario
from .world import World

HUD = 66
PANEL = 340
BG = (24, 28, 34)
PANEL_BG = (32, 37, 45)
PLANT = (80, 190, 100)
PREY = (90, 160, 255)
PRED = (240, 90, 90)
TEXT = (230, 230, 230)
MUTED = (150, 158, 170)
ACCENT = (255, 200, 90)
NEUTRAL = (60, 60, 70)

PREY_INPUTS = ["energía", "ángulo planta", "distancia planta",
               "ángulo depredador", "distancia depredador", "pared al frente"]
PRED_INPUTS = ["energía", "ángulo presa", "distancia presa",
               "rumbo de la presa", "pared al frente"]
SIGNED = {"presa": {1, 3}, "depredador": {1, 3}}  # entradas con signo (ángulos y rumbo)


# ---------------------------------------------------------------- lógica sin pygame (se puede probar sola)
def nearest_agent(world, x, y, radius=14.0):
    """Presa o depredador vivo más cercano al punto (x, y) del mundo: ("presa", i), ("depredador", i) o None."""
    best, best_d = None, radius
    for species, pos, alive in (("presa", world.prey_pos, world.prey_alive),
                                ("depredador", world.pred_pos, world.pred_alive)):
        if len(pos) == 0:
            continue
        d = np.where(alive, np.hypot(pos[:, 0] - x, pos[:, 1] - y), np.inf)
        i = int(np.argmin(d))
        if d[i] < best_d:
            best, best_d = (species, i), float(d[i])
    return best


def modify_cfg(cfg, change):
    """Devuelve una copia de la configuración con un cambio del modo defensa.

    Cambios: "pred+", "pred-" (número de depredadores) y "comida+", "comida-"
    (plantas iniciales en pasos de 10 y tasa de aparición multiplicada o dividida por 1.5).
    """
    c = copy.deepcopy(cfg)
    if change == "pred+":
        c["predators"]["initial"] = min(int(c["predators"]["initial"]) + 1, 20)
    elif change == "pred-":
        c["predators"]["initial"] = max(int(c["predators"]["initial"]) - 1, 1)
    elif change in ("comida+", "comida-"):
        up = change == "comida+"
        c["plants"]["initial"] = int(np.clip(int(c["plants"]["initial"]) + (10 if up else -10), 0, 200))
        rate = float(c["plants"]["respawn_rate"]) * (1.5 if up else 1 / 1.5)
        c["plants"]["respawn_rate"] = float(np.clip(rate, 0.001, 0.5))
        c["plants"]["max_plants"] = max(int(c["plants"]["max_plants"]), c["plants"]["initial"] + 20)
    else:
        raise ValueError(f"Cambio desconocido: {change}")
    return c


def _lerp(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def activation_color(v):
    """Color de una neurona: azul si es negativa, naranja si es positiva, gris si es cercana a 0."""
    v = float(np.clip(v, -1.0, 1.0))
    return _lerp(NEUTRAL, (255, 170, 60), v) if v >= 0 else _lerp(NEUTRAL, (70, 140, 255), -v)


# ---------------------------------------------------------------- visor
class Visor:
    def __init__(self, cfg, prey_options, pred_options, seed=1000, scenario="A", fps=60,
                 title="NeuroEcosistema"):
        pygame.init()
        self.cfg = copy.deepcopy(cfg)
        self.scenario = scenario
        self.seed = int(seed)
        self.fps = fps
        self.prey_options = list(prey_options)   # lista de (nombre, controlador)
        self.pred_options = list(pred_options)
        self.pi, self.qi = 0, 0
        self.paused, self.running, self.show_trail = False, True, True
        self.speed = 1
        self.selected = None
        self.trail = deque(maxlen=150)
        self.mensaje = ""
        W, H = int(cfg["world"]["width"]), int(cfg["world"]["height"])
        self.screen = pygame.display.set_mode((W + PANEL, H + HUD))
        pygame.display.set_caption(title)
        self.font = pygame.font.SysFont("consolas", 13)
        self.font_b = pygame.font.SysFont("consolas", 15, bold=True)
        self.clock = pygame.time.Clock()
        self.reset()

    # ----- estado
    @property
    def prey_ctrl(self):
        return self.prey_options[self.pi][1]

    @property
    def pred_ctrl(self):
        return self.pred_options[self.qi][1]

    def reset(self):
        self.world = World(self.cfg, self.seed)
        self.rng = np.random.default_rng([self.seed, 1])
        self.last = None
        self.selected = None
        self.trail.clear()
        self.hist = {"vivas": [], "capturas": []}

    def step_once(self):
        w = self.world
        if w.done:
            return
        obs_p, obs_q = w.observe_prey(), w.observe_predator()
        po = self.prey_ctrl.act(obs_p, self.rng)
        qo = self.pred_ctrl.act(obs_q, self.rng)
        w.step(po, qo)
        self.last = (po, qo)
        self.hist["vivas"].append(int(w.prey_alive.sum()))
        self.hist["capturas"].append(int(w.pred_captures.sum()))
        if self.selected is not None:
            sp, i = self.selected
            pos, alive = (w.prey_pos, w.prey_alive) if sp == "presa" else (w.pred_pos, w.pred_alive)
            if alive[i]:
                self.trail.append(pos[i].copy())

    # ----- entrada
    def handle_click(self, px, py):
        if px < int(self.world.W) and py >= HUD:
            self.selected = nearest_agent(self.world, px, py - HUD)
            self.trail.clear()

    def handle_key(self, key):
        k = pygame
        if key == k.K_ESCAPE:
            self.running = False
        elif key == k.K_SPACE:
            self.paused = not self.paused
        elif key == k.K_RIGHT and self.paused:
            self.step_once()
        elif key == k.K_UP:
            self.speed = min(self.speed * 2, 64)
        elif key == k.K_DOWN:
            self.speed = max(self.speed // 2, 1)
        elif key == k.K_n:
            self.seed += 1
            self.reset()
            self.mensaje = f"nueva semilla {self.seed}"
        elif key == k.K_r:
            self.reset()
            self.mensaje = "episodio reiniciado"
        elif key in (k.K_1, k.K_2, k.K_3):
            self.scenario = {k.K_1: "A", k.K_2: "B", k.K_3: "C"}[key]
            self.cfg = load_scenario(self.scenario)
            self.reset()
            self.mensaje = f"escenario {self.scenario}"
        elif key in (k.K_z, k.K_x):
            self.cfg = modify_cfg(self.cfg, "pred-" if key == k.K_z else "pred+")
            self.reset()
            self.mensaje = f"depredadores: {self.cfg['predators']['initial']}"
        elif key in (k.K_v, k.K_b):
            self.cfg = modify_cfg(self.cfg, "comida-" if key == k.K_v else "comida+")
            self.reset()
            self.mensaje = f"plantas iniciales: {self.cfg['plants']['initial']}"
        elif key == k.K_p:
            self.pi = (self.pi + 1) % len(self.prey_options)
            self.reset()
            self.mensaje = f"presa: {self.prey_options[self.pi][0]}"
        elif key == k.K_d:
            self.qi = (self.qi + 1) % len(self.pred_options)
            self.reset()
            self.mensaje = f"depredador: {self.pred_options[self.qi][0]}"
        elif key == k.K_t:
            self.show_trail = not self.show_trail
        elif key == k.K_s:
            carpeta = ROOT / "results" / "capturas"
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta = carpeta / f"captura_{self.scenario}_{self.seed}_{self.world.t}.png"
            pygame.image.save(self.screen, str(ruta))
            self.mensaje = f"guardada {ruta.name}"

    # ----- dibujo
    def _text(self, s, x, y, color=TEXT, bold=False):
        self.screen.blit((self.font_b if bold else self.font).render(s, True, color), (x, y))
        return y + (18 if bold else 16)

    def _bar(self, x, y, w, value, lo, hi, color):
        pygame.draw.rect(self.screen, (50, 56, 66), (x, y, w, 8))
        span = hi - lo
        zero = x + int(w * (0 - lo) / span) if lo < 0 else x
        pos = x + int(w * (np.clip(value, lo, hi) - lo) / span)
        pygame.draw.rect(self.screen, color, (min(zero, pos), y, max(abs(pos - zero), 1), 8))
        if lo < 0:
            pygame.draw.line(self.screen, MUTED, (zero, y - 1), (zero, y + 9))

    def _draw_arena(self):
        w, s = self.world, self.screen
        pygame.draw.rect(s, BG, (0, HUD, int(w.W), int(w.H)))
        for i in np.flatnonzero(w.plant_active):
            pygame.draw.circle(s, PLANT, (int(w.plant_pos[i, 0]), int(w.plant_pos[i, 1]) + HUD), 4)
        if self.show_trail and len(self.trail) > 1:
            pts = [(int(p[0]), int(p[1]) + HUD) for p in self.trail]
            pygame.draw.lines(s, ACCENT, False, pts, 2)
        for pos, head, alive, color, r in ((w.prey_pos, w.prey_heading, w.prey_alive, PREY, 5),
                                           (w.pred_pos, w.pred_heading, w.pred_alive, PRED, 8)):
            for i in range(len(pos)):
                if not alive[i]:
                    continue
                x, y = int(pos[i, 0]), int(pos[i, 1]) + HUD
                pygame.draw.circle(s, color, (x, y), r)
                pygame.draw.line(s, (255, 255, 255), (x, y),
                                 (x + int(np.cos(head[i]) * r * 1.8), y + int(np.sin(head[i]) * r * 1.8)), 2)
        if self.selected is not None:
            sp, i = self.selected
            pos, alive, vis = ((w.prey_pos, w.prey_alive, self.cfg["prey"]["vision_range"]) if sp == "presa"
                               else (w.pred_pos, w.pred_alive, self.cfg["predators"]["vision_range"]))
            if alive[i]:
                c = (int(pos[i, 0]), int(pos[i, 1]) + HUD)
                pygame.draw.circle(s, ACCENT, c, 13, 2)
                pygame.draw.circle(s, (90, 100, 115), c, int(vis), 1)

    def _draw_hud(self):
        w = self.world
        pygame.draw.rect(self.screen, (40, 46, 56), (0, 0, int(w.W) + PANEL, HUD))
        l1 = (f"semilla {self.seed}  paso {w.t}/{w.max_steps}  presas {int(w.prey_alive.sum())}"
              f"  depredadores {int(w.pred_alive.sum())}  plantas {int(w.plant_active.sum())}"
              f"  capturas {int(w.pred_captures.sum())}  x{self.speed}")
        if self.paused:
            l1 += "  [PAUSA]"
        l2 = "[clic] elegir animal  [ESPACIO] pausa  [→] un paso  [↑ ↓] velocidad  [N] otra semilla  [R] reiniciar"
        l3 = ("MODO DEFENSA: [1 2 3] escenario  [Z X] depredadores - +  [V B] comida - +  "
              "[P] presa  [D] depredador  [T] estela  [S] captura  [ESC] salir")
        self._text(l1, 8, 5)
        self._text(l2, 8, 23, MUTED)
        self._text(l3, 8, 41, ACCENT)

    def _draw_panel(self):
        w = self.world
        x0, H = int(w.W), int(w.H)
        pygame.draw.rect(self.screen, PANEL_BG, (x0, HUD, PANEL, H))
        x, y = x0 + 10, HUD + 8
        y = self._text("MODO DEFENSA", x, y, ACCENT, bold=True)
        y = self._text(f"escenario {self.scenario}   semilla {self.seed}", x, y)
        y = self._text(f"presa: {self.prey_options[self.pi][0]}", x, y)
        y = self._text(f"depredador: {self.pred_options[self.qi][0]}", x, y)
        y = self._text(f"depredadores {self.cfg['predators']['initial']}   plantas iniciales {self.cfg['plants']['initial']}", x, y)
        y = self._text(f"aparición de plantas por paso {self.cfg['plants']['respawn_rate']:.3f}", x, y)
        if self.mensaje:
            y = self._text(self.mensaje, x, y, MUTED)
        y += 6
        y = self._draw_agent(x, y)
        self._draw_chart(x, HUD + H - 92)

    def _draw_agent(self, x, y):
        w = self.world
        if self.selected is None:
            y = self._text("CONSULTA DE DECISIONES", x, y, ACCENT, bold=True)
            y = self._text("Haz clic en un animal para ver", x, y, MUTED)
            y = self._text("qué percibe y qué decide.", x, y, MUTED)
            return y
        sp, i = self.selected
        if sp == "presa":
            alive, energy, emax = w.prey_alive[i], w.prey_energy[i], self.cfg["prey"]["max_energy"]
            pos, head, names = w.prey_pos[i], w.prey_heading[i], PREY_INPUTS
            obs, ctrl = w.observe_prey()[i], self.prey_ctrl
            last = None if self.last is None else self.last[0]
            ctrl_name = self.prey_options[self.pi][0]
        else:
            alive, energy, emax = w.pred_alive[i], w.pred_energy[i], self.cfg["predators"]["max_energy"]
            pos, head, names = w.pred_pos[i], w.pred_heading[i], PRED_INPUTS
            obs, ctrl = w.observe_predator()[i], self.pred_ctrl
            last = None if self.last is None else self.last[1]
            ctrl_name = self.pred_options[self.qi][0]
        titulo = f"{sp.upper()} #{i}  ({ctrl_name})" + ("" if alive else "  [MUERTO]")
        y = self._text(titulo, x, y, ACCENT, bold=True)
        y = self._text(f"energía {energy:.0f}/{emax:.0f}   rumbo {np.degrees(head) % 360:.0f}°", x, y)
        y += 2
        y = self._text("Qué percibe (entradas)", x, y, MUTED)
        for k, (name, v) in enumerate(zip(names, obs)):
            self._text(f"{name:<21}{v:6.2f}", x, y)
            signed = k in SIGNED[sp]
            self._bar(x + 222, y + 4, 90, v, -1 if signed else 0, 1, PREY if sp == "presa" else PRED)
            y += 16
        y += 4
        if hasattr(ctrl, "decide"):
            out, acts = ctrl.decide(obs[None, :])
            out = out[0]
            y = self._text("Qué calcula la red (capas ocultas)", x, y, MUTED)
            for li, a in enumerate(acts[1:-1], start=1):
                a = a[0]
                size = min(14, (PANEL - 30) // len(a) - 2)
                for j, val in enumerate(a):
                    pygame.draw.rect(self.screen, activation_color(val), (x + j * (size + 2), y, size, size))
                y += size + 4
        else:
            out = last[i] if last is not None else np.zeros(2)
            y = self._text("Controlador sin red: acción aplicada", x, y, MUTED)
        y += 2
        y = self._text("Qué decide (salidas)", x, y, MUTED)
        giro, vel = float(out[0]), float(out[1])
        lado = "recto" if abs(giro) < 0.05 else ("a la derecha" if giro > 0 else "a la izquierda")
        self._text(f"giro {giro:+.2f} {lado}", x, y)
        self._bar(x + 222, y + 4, 90, giro, -1, 1, ACCENT)
        y += 16
        self._text(f"velocidad {vel * 100:3.0f} % del máx.", x, y)
        self._bar(x + 222, y + 4, 90, vel, 0, 1, ACCENT)
        return y + 18

    def _draw_chart(self, x, y, w=PANEL - 20, h=70):
        pygame.draw.rect(self.screen, (22, 26, 32), (x, y, w, h))
        n_prey = max(int(self.cfg["prey"]["initial"]), 1)
        for key, color in (("vivas", PREY), ("capturas", PRED)):
            data = self.hist[key]
            if len(data) < 2:
                continue
            step = max(1, len(data) // w)
            pts = [(x + int(w * k / max(len(data) - 1, 1)), y + h - 2 - int((h - 4) * v / n_prey))
                   for k, v in list(enumerate(data))[::step]]
            if len(pts) > 1:
                pygame.draw.lines(self.screen, color, False, pts, 2)
        self._text("presas vivas", x + 4, y + h + 2, PREY)
        self._text("capturas acumuladas", x + 110, y + h + 2, PRED)

    def draw(self):
        self.screen.fill(BG)
        self._draw_arena()
        self._draw_panel()
        self._draw_hud()

    # ----- ciclo principal
    def run(self, max_frames=None, screenshot=None, select=None):
        if select is not None:
            self.selected = select
        frames = 0
        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.KEYDOWN:
                    self.handle_key(ev.key)
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.handle_click(*ev.pos)
            if not self.paused:
                for _ in range(self.speed):
                    self.step_once()
            self.draw()
            pygame.display.flip()
            self.clock.tick(self.fps)
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        if screenshot:
            pygame.image.save(self.screen, str(screenshot))
        pygame.quit()
        return self.world


def run_viewer(cfg, prey_controller, predator_controller, seed, fps=60, max_frames=None,
               screenshot=None, title="NeuroEcosistema", scenario="A", select=None):
    """Abre el visor. Los controladores pueden ser uno solo o listas de (nombre, controlador)."""
    prey = prey_controller if isinstance(prey_controller, list) else [("seleccionada", prey_controller)]
    pred = predator_controller if isinstance(predator_controller, list) else [("seleccionado", predator_controller)]
    visor = Visor(cfg, prey, pred, seed=seed, scenario=scenario, fps=fps, title=title)
    return visor.run(max_frames=max_frames, screenshot=screenshot, select=select)