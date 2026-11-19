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
import pygame.gfxdraw

from .config import ROOT, load_scenario
from .world import World

HUD = 68
PANEL = 340
BG = (18, 24, 32)
BG_TOP, BG_BOTTOM = (14, 22, 34), (22, 34, 40)
PANEL_BG = (26, 31, 40)
CARD = (35, 42, 54)
CARD_EDGE = (52, 62, 78)
PLANT = (92, 200, 110)
PREY = (96, 178, 255)
PREY_DIM = (40, 70, 110)
PRED = (245, 96, 96)
TEXT = (232, 236, 242)
MUTED = (150, 160, 176)
ACCENT = (255, 204, 96)
NEUTRAL = (60, 60, 70)
EFFECT_FRAMES = 22

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
        self.font_t = pygame.font.SysFont("consolas", 20, bold=True)
        self.clock = pygame.time.Clock()
        self.frame = 0
        self.bg = self._make_background(W, H)
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
        self.effects = []
        self.hist = {"vivas": [], "capturas": []}

    @staticmethod
    def _make_background(W, H):
        """Fondo con degradado vertical y una cuadrícula tenue."""
        bg = pygame.Surface((W, H))
        for y in range(H):
            bg.fill(_lerp(BG_TOP, BG_BOTTOM, y / max(H - 1, 1)), (0, y, W, 1))
        for x in range(0, W, 100):
            pygame.draw.line(bg, (28, 40, 52), (x, 0), (x, H))
        for y in range(0, H, 100):
            pygame.draw.line(bg, (28, 40, 52), (0, y), (W, y))
        return bg

    def step_once(self):
        w = self.world
        if w.done:
            return
        obs_p, obs_q = w.observe_prey(), w.observe_predator()
        po = self.prey_ctrl.act(obs_p, self.rng)
        qo = self.pred_ctrl.act(obs_q, self.rng)
        vivas_antes = w.prey_alive.copy()
        w.step(po, qo)
        self.last = (po, qo)
        for i in np.flatnonzero(vivas_antes & ~w.prey_alive):   # muertes de este paso
            tipo = "captura" if w.prey_energy[i] > 0 else "hambre"
            self.effects.append((float(w.prey_pos[i, 0]), float(w.prey_pos[i, 1]), self.frame, tipo))
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
        pygame.draw.rect(self.screen, (50, 58, 72), (x, y, w, 8), border_radius=4)
        span = hi - lo
        zero = x + int(w * (0 - lo) / span) if lo < 0 else x
        pos = x + int(w * (np.clip(value, lo, hi) - lo) / span)
        pygame.draw.rect(self.screen, color, (min(zero, pos), y, max(abs(pos - zero), 3), 8), border_radius=4)
        if lo < 0:
            pygame.draw.line(self.screen, MUTED, (zero, y - 1), (zero, y + 9))

    def _triangle(self, cx, cy, head, size, color, outline=(255, 255, 255)):
        """Triángulo apuntando hacia el rumbo del agente."""
        pts = [(cx + np.cos(head) * size * 1.5, cy + np.sin(head) * size * 1.5),
               (cx + np.cos(head + 2.5) * size, cy + np.sin(head + 2.5) * size),
               (cx + np.cos(head - 2.5) * size, cy + np.sin(head - 2.5) * size)]
        pts = [(int(x), int(y)) for x, y in pts]
        pygame.gfxdraw.filled_polygon(self.screen, pts, color)
        pygame.gfxdraw.aapolygon(self.screen, pts, outline)

    def _draw_arena(self):
        w, s = self.world, self.screen
        s.blit(self.bg, (0, HUD))
        for i in np.flatnonzero(w.plant_active):
            x, y = int(w.plant_pos[i, 0]), int(w.plant_pos[i, 1]) + HUD
            pygame.gfxdraw.filled_circle(s, x, y, 5, (40, 110, 60))
            pygame.gfxdraw.filled_circle(s, x, y, 3, PLANT)
            pygame.gfxdraw.aacircle(s, x, y, 5, (120, 220, 140))
        if self.show_trail and len(self.trail) > 1:
            n = len(self.trail)
            for k in range(1, n):
                a, b = self.trail[k - 1], self.trail[k]
                color = _lerp((50, 60, 70), ACCENT, k / n)
                pygame.draw.line(s, color, (int(a[0]), int(a[1]) + HUD), (int(b[0]), int(b[1]) + HUD), 2)
        for pos, head, alive, energy, emax, kind in ((w.prey_pos, w.prey_heading, w.prey_alive, w.prey_energy, self.cfg["prey"]["max_energy"], "presa"),
                                                      (w.pred_pos, w.pred_heading, w.pred_alive, w.pred_energy, self.cfg["predators"]["max_energy"], "depredador")):
            for i in range(len(pos)):
                if not alive[i]:
                    continue
                x, y = float(pos[i, 0]), float(pos[i, 1]) + HUD
                frac = float(np.clip(energy[i] / emax, 0.0, 1.0))
                if kind == "presa":
                    self._triangle(x, y, head[i], 6, _lerp(PREY_DIM, PREY, frac))
                else:
                    pygame.gfxdraw.aacircle(s, int(x), int(y), 15, (120, 50, 55))
                    self._triangle(x, y, head[i], 9, _lerp((120, 40, 45), PRED, frac), (255, 220, 200))
        # efectos: anillo rojo si fue capturada, amarillo apagado si murió de hambre
        vivos = []
        for (ex, ey, born, tipo) in self.effects:
            edad = self.frame - born
            if edad > EFFECT_FRAMES:
                continue
            vivos.append((ex, ey, born, tipo))
            r = 6 + int(edad * 1.2)
            color = _lerp((255, 90, 90) if tipo == "captura" else (200, 180, 90), BG_BOTTOM, edad / EFFECT_FRAMES)
            pygame.gfxdraw.aacircle(s, int(ex), int(ey) + HUD, r, color)
            pygame.gfxdraw.aacircle(s, int(ex), int(ey) + HUD, r + 1, color)
        self.effects = vivos
        if self.selected is not None:
            sp, i = self.selected
            pos, alive, vis = ((w.prey_pos, w.prey_alive, self.cfg["prey"]["vision_range"]) if sp == "presa"
                               else (w.pred_pos, w.pred_alive, self.cfg["predators"]["vision_range"]))
            if alive[i]:
                c = (int(pos[i, 0]), int(pos[i, 1]) + HUD)
                pygame.gfxdraw.aacircle(s, c[0], c[1], 16, ACCENT)
                pygame.gfxdraw.aacircle(s, c[0], c[1], 17, ACCENT)
                pygame.gfxdraw.aacircle(s, c[0], c[1], int(vis), (90, 110, 130))
        self._draw_legend()

    def _draw_legend(self):
        s = self.screen
        x, y = 10, HUD + int(self.world.H) - 30
        pygame.draw.rect(s, (16, 22, 30), (x, y, 292, 22), border_radius=8)
        pygame.draw.rect(s, CARD_EDGE, (x, y, 292, 22), 1, border_radius=8)
        pygame.gfxdraw.filled_circle(s, x + 14, y + 11, 4, PLANT)
        self._text("planta", x + 24, y + 4, MUTED)
        self._triangle(x + 88, y + 11, 0.0, 5, PREY)
        self._text("presa", x + 100, y + 4, MUTED)
        self._triangle(x + 158, y + 11, 0.0, 6, PRED)
        self._text("depredador", x + 170, y + 4, MUTED)

    def _chip(self, texto, x, y, color=TEXT):
        surf = self.font.render(texto, True, color)
        r = pygame.Rect(x, y, surf.get_width() + 16, 22)
        pygame.draw.rect(self.screen, CARD, r, border_radius=11)
        pygame.draw.rect(self.screen, CARD_EDGE, r, 1, border_radius=11)
        self.screen.blit(surf, (x + 8, y + 4))
        return x + r.width + 6

    def _draw_hud(self):
        w = self.world
        pygame.draw.rect(self.screen, (20, 25, 34), (0, 0, int(w.W) + PANEL, HUD))
        pygame.draw.line(self.screen, CARD_EDGE, (0, HUD - 1), (int(w.W) + PANEL, HUD - 1))
        self.screen.blit(self.font_t.render("NeuroEcosistema", True, ACCENT), (10, 5))
        x = 220
        for texto, color in ((f"paso {w.t}/{w.max_steps}", TEXT), (f"presas {int(w.prey_alive.sum())}", PREY),
                             (f"depredadores {int(w.pred_alive.sum())}", PRED), (f"plantas {int(w.plant_active.sum())}", PLANT),
                             (f"capturas {int(w.pred_captures.sum())}", ACCENT), (f"x{self.speed}", MUTED),
                             ("PAUSA" if self.paused else f"semilla {self.seed}", ACCENT if self.paused else MUTED)):
            x = self._chip(texto, x, 6, color)
        l2 = "[clic] elegir animal  [ESPACIO] pausa  [→] un paso  [↑ ↓] velocidad  [N] otra semilla  [R] reiniciar"
        l3 = ("MODO DEFENSA: [1 2 3] escenario  [Z X] depredadores - +  [V B] comida - +  "
              "[P] presa  [D] depredador  [T] estela  [S] captura  [ESC] salir")
        self._text(l2, 10, 30, MUTED)
        self._text(l3, 10, 47, ACCENT)

    def _card(self, x, y, w, h):
        pygame.draw.rect(self.screen, CARD, (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, CARD_EDGE, (x, y, w, h), 1, border_radius=10)

    def _draw_panel(self):
        w = self.world
        x0, H = int(w.W), int(w.H)
        pygame.draw.rect(self.screen, PANEL_BG, (x0, HUD, PANEL, H))
        cx, cw = x0 + 8, PANEL - 16
        self._card(cx, HUD + 8, cw, 138)
        self._card(cx, HUD + 154, cw, H - 154 - 114)
        self._card(cx, HUD + H - 106, cw, 98)
        x, y = x0 + 18, HUD + 14
        y = self._text("MODO DEFENSA", x, y, ACCENT, bold=True)
        y = self._text(f"escenario {self.scenario}   semilla {self.seed}", x, y)
        y = self._text(f"presa: {self.prey_options[self.pi][0]}", x, y)
        y = self._text(f"depredador: {self.pred_options[self.qi][0]}", x, y)
        y = self._text(f"depredadores {self.cfg['predators']['initial']}   plantas iniciales {self.cfg['plants']['initial']}", x, y)
        y = self._text(f"aparición de plantas por paso {self.cfg['plants']['respawn_rate']:.3f}", x, y)
        if self.mensaje:
            self._text(self.mensaje, x, y, MUTED)
        self._draw_agent(x, HUD + 162)
        self._draw_chart(x, HUD + H - 100)

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
                    pygame.draw.rect(self.screen, activation_color(val), (x + j * (size + 2), y, size, size), border_radius=3)
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

    def _draw_chart(self, x, y, w=PANEL - 36, h=64):
        pygame.draw.rect(self.screen, (20, 25, 33), (x, y, w, h), border_radius=6)
        for frac in (0.25, 0.5, 0.75):
            yy = y + h - 2 - int((h - 4) * frac)
            pygame.draw.line(self.screen, (40, 48, 60), (x + 4, yy), (x + w - 4, yy))
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
        self._text(f"{n_prey}", x + 4, y + 2, MUTED)
        self._text("presas vivas", x + 2, y + h + 4, PREY)
        self._text("capturas acumuladas", x + 112, y + h + 4, PRED)

    def draw(self):
        self.frame += 1
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