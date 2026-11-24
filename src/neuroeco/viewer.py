"""Visor en tiempo real (pygame): simulación, consulta de decisiones y modo defensa.

- Clic en un animal: muestra qué percibe (entradas), qué activan las capas ocultas de su red
  y qué decide (giro y velocidad). Si el controlador es por reglas, muestra la acción aplicada.
- Panel de estadísticas en vivo (presas vivas y capturas acumuladas).
- Modo defensa: cambiar escenario, número de depredadores, cantidad de comida, tipo de
  controlador de cada especie y semilla sin salir del visor. Cada cambio reinicia el episodio
  con la misma semilla, para poder comparar.

El visor solo observa la simulación: usa el mismo World y los mismos controladores que los
experimentos. Todo el aspecto visual (pradera, conejitos, zorros, partículas) se dibuja por
código, sin archivos de imagen externos.
"""
import copy
import math
import random
from collections import deque

import numpy as np
import pygame
import pygame.gfxdraw

from .config import ROOT, load_scenario
from .world import World

# --- MEJORA UI: Aumentamos la altura del HUD para que los comandos respiren ---
HUD = 96 
PANEL = 340

# Colores de interfaz
BG = (16, 20, 28)
BG_TOP, BG_BOTTOM = (14, 22, 34), (22, 34, 40)
GRASS_TOP, GRASS_BOTTOM = (92, 164, 96), (64, 132, 80)
PANEL_BG = (22, 27, 37)
CARD = (33, 40, 53)
CARD_EDGE = (55, 66, 84)
PLANT = (92, 200, 110)
PREY = (96, 178, 255)
PREY_DIM = (40, 70, 110)
PRED = (245, 96, 96)
TEXT = (234, 238, 244)
MUTED = (150, 162, 180)
ACCENT = (255, 204, 96)
NEUTRAL = (60, 60, 70)
EFFECT_FRAMES = 22

# Ajustes de aspecto
SCALE_PREY = 1.0
SCALE_PRED = 1.0
LEVELS = 5
ANGLE_STEP = 5
MAX_PARTICLES = 500

PREY_INPUTS = ["energía", "ángulo planta", "distancia planta",
               "ángulo depredador", "distancia depredador", "pared al frente"]
PRED_INPUTS = ["energía", "ángulo presa", "distancia presa",
               "rumbo de la presa", "pared al frente"]
SIGNED = {"presa": {1, 3}, "depredador": {1, 3}}


# ---------------------------------------------------------------- lógica sin pygame
def nearest_agent(world, x, y, radius=14.0):
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


def _dark(c, f=0.55):
    return tuple(int(v * f) for v in c)


def activation_color(v):
    v = float(np.clip(v, -1.0, 1.0))
    return _lerp(NEUTRAL, (255, 170, 60), v) if v >= 0 else _lerp(NEUTRAL, (70, 140, 255), -v)


def _energy_color(frac):
    frac = float(np.clip(frac, 0.0, 1.0))
    if frac < 0.5:
        return _lerp((240, 90, 90), ACCENT, frac * 2)
    return _lerp(ACCENT, (110, 210, 120), (frac - 0.5) * 2)


# ---------------------------------------------------------------- dibujo de sprites
class _Canvas:
    def __init__(self, size, S=4):
        self.S, self.size = S, size
        self.surf = pygame.Surface((size * S, size * S), pygame.SRCALPHA)
        self.c = size * S / 2.0

    def _p(self, x, y):
        return (int(self.c + x * self.S), int(self.c + y * self.S))

    def circ(self, x, y, r, fill, out=None, ow=0.8):
        p, R = self._p(x, y), max(1, int(r * self.S))
        pygame.draw.circle(self.surf, fill, p, R)
        if out:
            pygame.draw.circle(self.surf, out, p, R, max(1, int(ow * self.S)))

    def poly(self, pts, fill, out=None, ow=0.8):
        P = [self._p(x, y) for x, y in pts]
        pygame.draw.polygon(self.surf, fill, P)
        if out:
            pygame.draw.polygon(self.surf, out, P, max(1, int(ow * self.S)))

    def ell(self, x, y, rx, ry, ang, fill, out=None, ow=0.8):
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for k in range(24):
            t = 2 * math.pi * k / 24
            ex, ey = rx * math.cos(t), ry * math.sin(t)
            pts.append((x + ex * ca - ey * sa, y + ex * sa + ey * ca))
        self.poly(pts, fill, out, ow)

    def line(self, a, b, color, w=0.8):
        pygame.draw.line(self.surf, color, self._p(*a), self._p(*b), max(1, int(w * self.S)))

    def done(self, px):
        return pygame.transform.smoothscale(self.surf, (px, px))


def _make_prey(frac):
    cv = _Canvas(30)
    body = _lerp((135, 135, 152), (160, 212, 255), frac)
    head = _lerp(body, (255, 255, 255), 0.25)
    out = _dark(body, 0.42)
    pink = _lerp((165, 150, 160), (255, 160, 195), frac)
    cv.circ(-10, 0, 3.4, (246, 249, 255), out)
    for sgn in (-1, 1):
        cv.ell(-2.5, 5.6 * sgn, 6.5, 2.4, -0.39 * sgn, body, out)
        cv.ell(-2.5, 5.6 * sgn, 4.6, 1.1, -0.39 * sgn, pink)
    cv.ell(-1.5, 0, 8.5, 6.8, 0.0, body, out)
    cv.ell(-2.5, -2.4, 4.0, 1.7, 0.0, _lerp(body, (255, 255, 255), 0.35))
    cv.circ(5.5, 0, 5.4, head, out)
    for sgn in (-1, 1):
        cv.circ(8.0, 3.8 * sgn, 1.5, _lerp(head, (255, 150, 185), 0.6))
        cv.circ(8.0, 2.5 * sgn, 1.35, (30, 35, 60))
        cv.circ(8.4, 2.1 * sgn, 0.5, (255, 255, 255))
    cv.circ(10.9, 0, 1.1, (255, 140, 170))
    return cv.done(int(30 * SCALE_PREY))


def _make_pred(frac):
    cv = _Canvas(56)
    fur = _lerp((132, 78, 78), (238, 118, 52), frac)
    dark = _dark(fur, 0.6)
    out = _dark(fur, 0.38)
    cream = (255, 230, 208)
    cv.ell(-15, 0, 10, 5, 0.0, fur, out)
    cv.circ(-21.5, 0, 4.0, (250, 244, 236), out)
    for sgn in (-1, 1):
        cv.ell(-8, 8.2 * sgn, 3.0, 1.9, 0.2 * sgn, dark, out)
        cv.ell(7, 8.0 * sgn, 3.0, 1.9, -0.2 * sgn, dark, out)
    cv.ell(-3, 0, 13, 7.6, 0.0, fur, out)
    cv.ell(-4, 0, 8, 2.0, 0.0, dark)
    for sgn in (-1, 1):
        cv.poly([(5, 4.5 * sgn), (10, 5.5 * sgn), (5.5, 11.5 * sgn)], fur, out)
        cv.poly([(6.2, 5.4 * sgn), (9, 5.8 * sgn), (6, 9.5 * sgn)], (70, 38, 40))
    cv.ell(10, 0, 7, 6.4, 0.0, fur, out)
    for sgn in (-1, 1):
        cv.ell(12.5, 4.3 * sgn, 3.4, 1.8, 0.35 * sgn, (250, 244, 236))
    cv.poly([(14, -3.4), (22.5, 0), (14, 3.4)], cream, out)
    cv.circ(22, 0, 1.5, (35, 25, 25))
    for sgn in (-1, 1):
        cv.circ(14, 2.6 * sgn, 1.7, (255, 226, 100), (60, 40, 20), 0.4)
        cv.circ(14.3, 2.6 * sgn, 0.8, (30, 20, 20))
        cv.line((12.2, 4.9 * sgn), (16.2, 2.9 * sgn), (50, 30, 30), 0.8)
    return cv.done(int(56 * SCALE_PRED))


def _make_plant():
    cv = _Canvas(26)
    leaf, leaf_out = (48, 130, 74), (24, 78, 46)
    for x, y, r in ((-3.8, 2.0, 4.4), (3.8, 2.0, 4.4), (0.0, -2.8, 4.8)):
        cv.circ(x, y, r, leaf, leaf_out)
    cv.circ(0, 0.6, 4.2, PLANT)
    for x, y in ((-3.2, 2.2), (3.0, 1.6), (0.2, -2.6), (-0.6, 1.4)):
        cv.circ(x, y, 1.6, (236, 72, 92), (140, 30, 50), 0.4)
        cv.circ(x - 0.5, y - 0.5, 0.5, (255, 235, 235))
    return cv.done(26)


def _make_glow(r=16):
    s = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
    for k, rr in enumerate(range(r, 3, -3)):
        pygame.draw.circle(s, (170, 255, 170, 7 + k * 5), (r, r), rr)
    return s


def _make_shadow(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for a, f in ((22, 1.0), (30, 0.78), (42, 0.56)):
        pygame.draw.ellipse(s, (0, 0, 0, a), ((w * (1 - f)) / 2, (h * (1 - f)) / 2, w * f, h * f))
    return s


# ---------------------------------------------------------------- visor
class Visor:
    def __init__(self, cfg, prey_options, pred_options, seed=1000, scenario="A", fps=60,
                 title="NeuroEcosistema"):
        pygame.init()
        self.cfg = copy.deepcopy(cfg)
        self.scenario = scenario
        self.seed = int(seed)
        self.fps = fps
        self.prey_options = list(prey_options)
        self.pred_options = list(pred_options)
        self.pi, self.qi = 0, 0
        self.paused, self.running, self.show_trail = False, True, True
        self.speed = 1
        self.selected = None
        self.hover = None
        self.trail = deque(maxlen=150)
        self._mensaje, self._mensaje_frame = "", 0
        self.frame = 0
        W, H = int(cfg["world"]["width"]), int(cfg["world"]["height"])
        self.screen = pygame.display.set_mode((W + PANEL, H + HUD))
        pygame.display.set_caption(title)
        names = "segoeui,calibri,arial,dejavusans"
        
        # --- MEJORA UI: Fuentes un poco más grandes ---
        self.font = pygame.font.SysFont(names, 15)
        self.font_s = pygame.font.SysFont(names, 14)
        self.font_k = pygame.font.SysFont(names, 13, bold=True)
        self.font_b = pygame.font.SysFont(names, 16, bold=True)
        self.font_t = pygame.font.SysFont(names, 24, bold=True)
        self.font_big = pygame.font.SysFont(names, 28, bold=True)
        
        self.clock = pygame.time.Clock()
        self.vrng = random.Random(3)
        self.bg = self._make_background(W, H)
        self.hud_bg = self._make_hud_bg(W + PANEL)
        self._build_assets()
        self.reset()

    @property
    def mensaje(self):
        return self._mensaje

    @mensaje.setter
    def mensaje(self, texto):
        self._mensaje = texto
        self._mensaje_frame = self.frame

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
        self.hover = None
        self.trail.clear()
        self.effects = []
        self.particles = []
        self.hist = {"vivas": [], "capturas": []}

    @staticmethod
    def _make_background(W, H):
        rnd = random.Random(7)
        bg = pygame.Surface((W, H))
        for y in range(H):
            bg.fill(_lerp(GRASS_TOP, GRASS_BOTTOM, y / max(H - 1, 1)), (0, y, W, 1))
        patches = pygame.Surface((W, H), pygame.SRCALPHA)
        for _ in range(max(10, int(W * H / 8000))):
            c = rnd.choice(((255, 255, 170, 11), (20, 70, 40, 16), (130, 210, 100, 11)))
            pygame.draw.circle(patches, c, (rnd.randint(0, W), rnd.randint(0, H)), rnd.randint(30, 95))
        bg.blit(patches, (0, 0))
        for _ in range(int(W * H / 240)):
            x, y = rnd.randint(0, W - 1), rnd.randint(0, H - 1)
            sh = rnd.randint(-16, 16)
            col = tuple(int(np.clip(v + sh, 0, 255)) for v in (58, 126, 70))
            pygame.draw.line(bg, col, (x, y), (x + rnd.randint(-2, 2), y - rnd.randint(3, 6)))
        for _ in range(int(W * H / 8500)):
            x, y = rnd.randint(4, W - 4), rnd.randint(4, H - 4)
            col = rnd.choice(((255, 250, 250), (255, 226, 120), (255, 170, 200), (200, 185, 255)))
            pygame.draw.circle(bg, col, (x, y), 2)
            pygame.draw.circle(bg, (255, 215, 90), (x, y), 1)
        vig = pygame.Surface((W, H), pygame.SRCALPHA)
        steps = 46
        for i in range(steps):
            a = int(85 * (1 - i / steps) ** 2)
            pygame.draw.rect(vig, (0, 0, 0, a), (i, i, W - 2 * i, H - 2 * i), 1)
        bg.blit(vig, (0, 0))
        return bg

    @staticmethod
    def _make_hud_bg(total_w):
        s = pygame.Surface((total_w, HUD))
        for y in range(HUD):
            s.fill(_lerp((30, 37, 50), (19, 24, 33), y / (HUD - 1)), (0, y, total_w, 1))
        return s

    def _build_assets(self):
        self._base, self._rot, self._vis_cache = {}, {}, {}
        self._plant_sprite = _make_plant().convert_alpha()
        self._glow = _make_glow().convert_alpha()
        self._shadows = {
            "planta": (_make_shadow(18, 7).convert_alpha(), 9, 5),
            "presa": (_make_shadow(24, 10).convert_alpha(), 12, 5),
            "depredador": (_make_shadow(42, 15).convert_alpha(), 21, 8),
        }
        top = LEVELS - 1
        self._icons = {
            "planta": pygame.transform.smoothscale(self._plant_sprite, (22, 22)),
            "presa": pygame.transform.smoothscale(self._base_sprite("presa", top), (24, 24)),
            "depredador": pygame.transform.smoothscale(self._base_sprite("depredador", top), (34, 34)),
        }

    def _base_sprite(self, kind, level):
        key = (kind, level)
        if key not in self._base:
            frac = level / max(LEVELS - 1, 1)
            surf = _make_prey(frac) if kind == "presa" else _make_pred(frac)
            self._base[key] = surf.convert_alpha()
        return self._base[key]

    def _sprite(self, kind, frac, head):
        level = int(round(float(np.clip(frac, 0.0, 1.0)) * (LEVELS - 1)))
        idx = int(round(((-math.degrees(float(head))) % 360.0) / ANGLE_STEP)) % int(360 / ANGLE_STEP)
        key = (kind, level, idx)
        surf = self._rot.get(key)
        if surf is None:
            surf = pygame.transform.rotozoom(self._base_sprite(kind, level), idx * ANGLE_STEP, 1.0).convert_alpha()
            self._rot[key] = surf
        return surf

    def _spawn(self, x, y, kind, color, n, speed, life, size, gravity=0.0):
        if len(self.particles) > MAX_PARTICLES:
            return
        for _ in range(n):
            a = self.vrng.uniform(0, 2 * math.pi)
            sp = self.vrng.uniform(0.3, 1.0) * speed
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 0,
                                   life + self.vrng.randint(-4, 4), color,
                                   size * self.vrng.uniform(0.7, 1.2), kind, gravity])

    def _draw_particles(self):
        s, keep = self.screen, []
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[9]
            p[2] *= 0.95
            p[4] += 1
            if p[4] >= p[5]:
                continue
            keep.append(p)
            r = max(1.0, p[7] * (1 - p[4] / p[5]))
            x, y = int(p[0]), int(p[1]) + HUD
            if p[8] == "spark":
                c, ri = _lerp(p[6], (255, 255, 255), 0.4), int(r) + 1
                pygame.draw.line(s, c, (x - ri, y), (x + ri, y))
                pygame.draw.line(s, c, (x, y - ri), (x, y + ri))
            else:
                pygame.gfxdraw.filled_circle(s, x, y, int(r), p[6])
        self.particles = keep

    def step_once(self):
        w = self.world
        if w.done:
            return
        obs_p, obs_q = w.observe_prey(), w.observe_predator()
        po = self.prey_ctrl.act(obs_p, self.rng)
        qo = self.pred_ctrl.act(obs_q, self.rng)
        vivas_antes = w.prey_alive.copy()
        plantas_antes, plantas_pos = w.plant_active.copy(), w.plant_pos.copy()
        w.step(po, qo)
        self.last = (po, qo)
        for i in np.flatnonzero(vivas_antes & ~w.prey_alive):
            tipo = "captura" if w.prey_energy[i] > 0 else "hambre"
            ex, ey = float(w.prey_pos[i, 0]), float(w.prey_pos[i, 1])
            self.effects.append((ex, ey, self.frame, tipo))
            if tipo == "captura":
                self._spawn(ex, ey, "dot", (255, 120, 90), 12, 2.6, 26, 3.4)
                self._spawn(ex, ey, "spark", (255, 220, 120), 6, 2.0, 22, 3.0)
            else:
                self._spawn(ex, ey, "dot", (200, 200, 220), 8, 0.9, 38, 4.0, gravity=-0.04)
        comidas = plantas_antes & (~w.plant_active | (plantas_pos != w.plant_pos).any(axis=1))
        for j in np.flatnonzero(comidas):
            self._spawn(float(plantas_pos[j, 0]), float(plantas_pos[j, 1]), "spark", (140, 235, 140), 5, 1.6, 20, 3.0)
        self.hist["vivas"].append(int(w.prey_alive.sum()))
        self.hist["capturas"].append(int(w.pred_captures.sum()))
        if self.selected is not None:
            sp, i = self.selected
            pos, alive = (w.prey_pos, w.prey_alive) if sp == "presa" else (w.pred_pos, w.pred_alive)
            if alive[i]:
                self.trail.append(pos[i].copy())

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

    def _text(self, s, x, y, color=TEXT, bold=False, small=False, gap=6):
        # --- MEJORA UI: Se añade 'gap' para separar mejor las líneas ---
        font = self.font_b if bold else (self.font_s if small else self.font)
        self.screen.blit(font.render(s, True, color), (x, y))
        return y + (22 if bold else 20 if not small else 18) + gap

    def _text_right(self, s, xr, y, color=TEXT, small=True):
        surf = (self.font_s if small else self.font).render(s, True, color)
        self.screen.blit(surf, (xr - surf.get_width(), y))

    def _bar(self, x, y, w, value, lo, hi, color):
        pygame.draw.rect(self.screen, (46, 54, 69), (x, y, w, 8), border_radius=4)
        span = hi - lo
        zero = x + int(w * (0 - lo) / span) if lo < 0 else x
        pos = x + int(w * (np.clip(value, lo, hi) - lo) / span)
        pygame.draw.rect(self.screen, color, (min(zero, pos), y, max(abs(pos - zero), 3), 8), border_radius=4)
        if lo < 0:
            pygame.draw.line(self.screen, MUTED, (zero, y - 1), (zero, y + 9))

    def _bar_pill(self, x, y, w, frac, color, h=8):
        pygame.draw.rect(self.screen, (46, 54, 69), (x, y, w, h), border_radius=h // 2)
        fw = max(int(w * float(np.clip(frac, 0, 1))), h if frac > 0 else 0)
        if fw:
            pygame.draw.rect(self.screen, color, (x, y, fw, h), border_radius=h // 2)

    def _card(self, x, y, w, h):
        pygame.draw.rect(self.screen, (13, 16, 22), (x, y + 3, w, h), border_radius=12)
        pygame.draw.rect(self.screen, CARD, (x, y, w, h), border_radius=12)
        pygame.draw.line(self.screen, _lerp(CARD, (255, 255, 255), 0.07), (x + 12, y + 1), (x + w - 12, y + 1))
        pygame.draw.rect(self.screen, CARD_EDGE, (x, y, w, h), 1, border_radius=12)

    def _draw_arena(self):
        w, s = self.world, self.screen
        W = int(w.W)
        s.blit(self.bg, (0, HUD))

        sh, sx, sy = self._shadows["planta"]
        for i in np.flatnonzero(w.plant_active):
            x, y = int(w.plant_pos[i, 0]), int(w.plant_pos[i, 1]) + HUD
            bob = int(round(math.sin(self.frame * 0.07 + i * 1.7) * 1.3))
            s.blit(sh, (x - sx, y + sy))
            s.blit(self._glow, (x - 16, y - 16 + bob))
            s.blit(self._plant_sprite, (x - 13, y - 13 + bob))

        if self.show_trail and len(self.trail) > 1:
            n = len(self.trail)
            for k in range(1, n):
                a, b = self.trail[k - 1], self.trail[k]
                color = _lerp((70, 130, 85), ACCENT, k / n)
                pygame.draw.line(s, color, (int(a[0]), int(a[1]) + HUD), (int(b[0]), int(b[1]) + HUD), 3)

        sel_pos = None
        if self.selected is not None:
            sp, i = self.selected
            pos, alive, vis = ((w.prey_pos, w.prey_alive, self.cfg["prey"]["vision_range"]) if sp == "presa"
                               else (w.pred_pos, w.pred_alive, self.cfg["predators"]["vision_range"]))
            if alive[i]:
                sel_pos = (int(pos[i, 0]), int(pos[i, 1]) + HUD)
                r = int(vis)
                vs = self._vis_cache.get(r)
                if vs is None:
                    vs = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
                    pygame.draw.circle(vs, (255, 255, 255, 24), (r + 2, r + 2), r)
                    pygame.draw.circle(vs, (255, 255, 255, 95), (r + 2, r + 2), r, 2)
                    self._vis_cache[r] = vs = vs.convert_alpha()
                s.blit(vs, (sel_pos[0] - r - 2, sel_pos[1] - r - 2))

        agentes = []
        for kind, pos, alive in (("presa", w.prey_pos, w.prey_alive), ("depredador", w.pred_pos, w.pred_alive)):
            for i in np.flatnonzero(alive):
                agentes.append((float(pos[i, 1]), kind, int(i)))
        agentes.sort()
        for yy, kind, i in agentes:
            xx = float((w.prey_pos if kind == "presa" else w.pred_pos)[i, 0])
            sh, sx, sy = self._shadows[kind]
            s.blit(sh, (int(xx) - sx, int(yy) + HUD + sy))
        for yy, kind, i in agentes:
            if kind == "presa":
                pos, head, energy, emax = w.prey_pos, w.prey_heading, w.prey_energy, self.cfg["prey"]["max_energy"]
            else:
                pos, head, energy, emax = w.pred_pos, w.pred_heading, w.pred_energy, self.cfg["predators"]["max_energy"]
            x, y = float(pos[i, 0]), float(pos[i, 1]) + HUD
            frac = float(np.clip(energy[i] / emax, 0.0, 1.0))
            spr = self._sprite(kind, frac, head[i])
            s.blit(spr, spr.get_rect(center=(int(x), int(y))))
            es = self.selected == (kind, i)
            if kind == "depredador" or frac < 0.35 or es:
                bw = 30 if kind == "depredador" else 18
                by = int(y) - (24 if kind == "depredador" else 17)
                pygame.draw.rect(s, (24, 28, 34), (int(x) - bw // 2 - 1, by - 1, bw + 2, 6), border_radius=3)
                pygame.draw.rect(s, _energy_color(frac), (int(x) - bw // 2, by, max(2, int(bw * frac)), 4), border_radius=2)

        self._draw_particles()
        vivos = []
        for (ex, ey, born, tipo) in self.effects:
            edad = self.frame - born
            if edad > EFFECT_FRAMES:
                continue
            vivos.append((ex, ey, born, tipo))
            r = 6 + int(edad * 1.4)
            color = _lerp((255, 90, 90) if tipo == "captura" else (225, 225, 235), (70, 135, 85), edad / EFFECT_FRAMES)
            pygame.gfxdraw.aacircle(s, int(ex), int(ey) + HUD, r, color)
            pygame.gfxdraw.aacircle(s, int(ex), int(ey) + HUD, r + 1, color)
        self.effects = vivos

        self.hover = None
        try:
            if pygame.mouse.get_focused():
                mx, my = pygame.mouse.get_pos()
                if mx < W and my >= HUD:
                    self.hover = nearest_agent(w, mx, my - HUD)
        except pygame.error:
            self.hover = None
        if self.hover is not None and self.hover != self.selected:
            hs, hi = self.hover
            hp = (w.prey_pos if hs == "presa" else w.pred_pos)[hi]
            pygame.gfxdraw.aacircle(s, int(hp[0]), int(hp[1]) + HUD, 14 if hs == "presa" else 21, (255, 255, 255, 150))

        if sel_pos is not None:
            sp = self.selected[0]
            r0 = (15 if sp == "presa" else 22) + int(round(1.6 * math.sin(self.frame * 0.15)))
            pygame.gfxdraw.aacircle(s, sel_pos[0], sel_pos[1], r0, ACCENT)
            pygame.gfxdraw.aacircle(s, sel_pos[0], sel_pos[1], r0 + 1, ACCENT)
            ty = sel_pos[1] - r0 - 5
            tri = [(sel_pos[0] - 5, ty - 8), (sel_pos[0] + 5, ty - 8), (sel_pos[0], ty)]
            pygame.gfxdraw.filled_polygon(s, tri, ACCENT)
            pygame.gfxdraw.aapolygon(s, tri, ACCENT)

        self._draw_legend()
        self._draw_toast()
        self._draw_status_badges()

    def _draw_legend(self):
        s = self.screen
        x, y, wl, hl = 10, HUD + int(self.world.H) - 44, 292, 34
        pill = pygame.Surface((wl, hl), pygame.SRCALPHA)
        pygame.draw.rect(pill, (14, 18, 26, 190), (0, 0, wl, hl), border_radius=17)
        pygame.draw.rect(pill, (255, 255, 255, 40), (0, 0, wl, hl), 1, border_radius=17)
        s.blit(pill, (x, y))
        cx = x + 12
        for nombre, color in (("planta", MUTED), ("presa", MUTED), ("depredador", MUTED)):
            ic = self._icons[nombre]
            s.blit(ic, ic.get_rect(center=(cx + ic.get_width() // 2, y + hl // 2)))
            cx += ic.get_width() + 6
            t = self.font_s.render(nombre, True, color)
            s.blit(t, (cx, y + (hl - t.get_height()) // 2))
            cx += t.get_width() + 16

    def _draw_toast(self):
        if not self._mensaje:
            return
        edad = self.frame - self._mensaje_frame
        if edad > 200:
            return
        alpha = 255 if edad < 150 else int(255 * (1 - (edad - 150) / 50))
        txt = self.font.render(self._mensaje, True, TEXT)
        wt, ht = txt.get_width() + 28, 32
        t = pygame.Surface((wt, ht), pygame.SRCALPHA)
        pygame.draw.rect(t, (16, 20, 28, 225), (0, 0, wt, ht), border_radius=16)
        pygame.draw.rect(t, (*ACCENT, 255), (0, 0, wt, ht), 1, border_radius=16)
        t.blit(txt, (14, (ht - txt.get_height()) // 2))
        t.set_alpha(alpha)
        self.screen.blit(t, (int(self.world.W) // 2 - wt // 2, HUD + 12))

    def _draw_status_badges(self):
        s, w = self.screen, self.world
        W, H = int(w.W), int(w.H)
        if self.paused:
            bx, by = W - 96, HUD + 12
            pill = pygame.Surface((84, 28), pygame.SRCALPHA)
            pygame.draw.rect(pill, (16, 20, 28, 225), (0, 0, 84, 28), border_radius=14)
            pygame.draw.rect(pill, (*ACCENT, 255), (0, 0, 84, 28), 1, border_radius=14)
            pygame.draw.rect(pill, ACCENT, (13, 8, 4, 12), border_radius=1)
            pygame.draw.rect(pill, ACCENT, (21, 8, 4, 12), border_radius=1)
            pill.blit(self.font_k.render("PAUSA", True, ACCENT), (33, 7))
            s.blit(pill, (bx, by))
        if w.done:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((8, 12, 18, 120))
            s.blit(veil, (0, HUD))
            cw, ch = 360, 150
            cx, cy = W // 2 - cw // 2, HUD + H // 2 - ch // 2
            self._card(cx, cy, cw, ch)
            n0 = int(self.cfg["prey"]["initial"])
            titulo = self.font_big.render("Episodio terminado", True, ACCENT)
            s.blit(titulo, (cx + (cw - titulo.get_width()) // 2, cy + 16))
            lines = [(f"presas vivas  {int(w.prey_alive.sum())} / {n0}", PREY),
                     (f"capturas  {int(w.pred_captures.sum())}", PRED),
                     (f"pasos  {w.t} / {w.max_steps}", MUTED)]
            yy = cy + 58
            for txt, col in lines:
                t = self.font.render(txt, True, col)
                s.blit(t, (cx + (cw - t.get_width()) // 2, yy))
                yy += 21
            hint = self.font_s.render("N otra semilla  ·  R reiniciar", True, MUTED)
            s.blit(hint, (cx + (cw - hint.get_width()) // 2, cy + ch - 26))

    def _chip(self, texto, x, y, color=TEXT, dot=None, progress=None):
        surf = self.font_s.render(texto, True, color)
        extra = 14 if dot is not None else 0
        r = pygame.Rect(x, y, surf.get_width() + 18 + extra, 26)
        pygame.draw.rect(self.screen, (13, 16, 22), r.move(0, 2), border_radius=13)
        pygame.draw.rect(self.screen, CARD, r, border_radius=13)
        pygame.draw.rect(self.screen, CARD_EDGE, r, 1, border_radius=13)
        if dot is not None:
            pygame.gfxdraw.filled_circle(self.screen, x + 13, y + 13, 4, dot)
            pygame.gfxdraw.aacircle(self.screen, x + 13, y + 13, 4, dot)
        self.screen.blit(surf, (x + 9 + extra, y + (26 - surf.get_height()) // 2))
        if progress is not None:
            pw = r.width - 20
            pygame.draw.rect(self.screen, (46, 54, 69), (x + 10, y + 22, pw, 2), border_radius=1)
            pygame.draw.rect(self.screen, ACCENT, (x + 10, y + 22, max(1, int(pw * progress)), 2), border_radius=1)
        return x + r.width + 8

    def _logo(self, x, y):
        nodos = [(x + 5, y + 14), (x + 21, y + 5), (x + 21, y + 23), (x + 39, y + 14)]
        for a, b in ((0, 1), (0, 2), (1, 2), (1, 3), (2, 3)):
            pygame.draw.aaline(self.screen, (110, 125, 150), nodos[a], nodos[b])
        for (nx, ny), c in zip(nodos, (PLANT, PREY, PRED, ACCENT)):
            pygame.gfxdraw.filled_circle(self.screen, nx, ny, 5, c)
            pygame.gfxdraw.aacircle(self.screen, nx, ny, 5, _lerp(c, (255, 255, 255), 0.4))

    def _keycap(self, key, label, x, y, color=MUTED, keycolor=TEXT):
        # --- MEJORA UI: Teclas más grandes y con mejor espaciado ---
        ks = self.font_k.render(key, True, keycolor)
        kw = max(ks.get_width() + 14, 22)
        r = pygame.Rect(x, y, kw, 22)
        pygame.draw.rect(self.screen, (12, 15, 21), r.move(0, 2), border_radius=6)
        pygame.draw.rect(self.screen, (40, 48, 62), r, border_radius=6)
        pygame.draw.rect(self.screen, CARD_EDGE, r, 1, border_radius=6)
        self.screen.blit(ks, (x + (kw - ks.get_width()) // 2, y + (22 - ks.get_height()) // 2))
        ls = self.font_s.render(label, True, color)
        self.screen.blit(ls, (x + kw + 6, y + (22 - ls.get_height()) // 2))
        return x + kw + 6 + ls.get_width() + 16

    def _draw_hud(self):
        w = self.world
        total = int(w.W) + PANEL
        self.screen.blit(self.hud_bg, (0, 0))
        pygame.draw.line(self.screen, CARD_EDGE, (0, HUD - 1), (total, HUD - 1))
        
        self._logo(10, 6)
        titulo = self.font_t.render("NeuroEcosistema", True, ACCENT)
        self.screen.blit(titulo, (62, 6))
        
        x = 62 + titulo.get_width() + 20
        chips = ((f"paso {w.t}/{w.max_steps}", TEXT, None, w.t / max(w.max_steps, 1)),
                 (f"presas {int(w.prey_alive.sum())}", PREY, PREY, None),
                 (f"depredadores {int(w.pred_alive.sum())}", PRED, PRED, None),
                 (f"plantas {int(w.plant_active.sum())}", PLANT, PLANT, None),
                 (f"capturas {int(w.pred_captures.sum())}", ACCENT, ACCENT, None),
                 (f"x{self.speed}", MUTED, None, None),
                 ("PAUSA" if self.paused else f"semilla {self.seed}", ACCENT if self.paused else MUTED, None, None))
        for texto, color, dot, prog in chips:
            if x > total - 70:
                break
            x = self._chip(texto, x, 8, color, dot, prog)

        # --- MEJORA UI: Separación de comandos en dos filas con márgenes claros ---
        row1 = (("clic", "elegir animal"), ("ESPACIO", "pausa"), ("→", "un paso"),
                ("↑ ↓", "velocidad"), ("N", "otra semilla"), ("R", "reiniciar"), ("ESC", "salir"))
        row2 = (("1 2 3", "escenario"), ("Z X", "depredadores - +"), ("V B", "comida - +"),
                ("P", "presa"), ("D", "depredador"), ("T", "estela"), ("S", "captura"))
        
        # Fila 1
        x = 10
        for k, lab in row1:
            if x > total - 60:
                break
            x = self._keycap(k, lab, x, 40)
            
        # Fila 2 (con separador visual para "MODO DEFENSA")
        x = 10
        self.screen.blit(self.font_k.render("MODO DEFENSA", True, ACCENT), (x, 70))
        x += 112
        for k, lab in row2:
            if x > total - 60:
                break
            x = self._keycap(k, lab, x, 70, MUTED, ACCENT)

    def _draw_panel(self):
        w = self.world
        x0, H = int(w.W), int(w.H)
        pygame.draw.rect(self.screen, PANEL_BG, (x0, HUD, PANEL, H))
        pygame.draw.line(self.screen, CARD_EDGE, (x0, HUD), (x0, HUD + H))
        cx, cw = x0 + 8, PANEL - 16
        
        # --- MEJORA UI: Tarjetas más grandes para dar aire ---
        self._card(cx, HUD + 8, cw, 156)
        agent_rect = pygame.Rect(cx, HUD + 172, cw, H - 172 - 120)
        self._card(*agent_rect)
        self._card(cx, HUD + H - 112, cw, 104)
        
        x, xr = x0 + 18, x0 + PANEL - 18
        y = HUD + 15
        pygame.draw.rect(self.screen, ACCENT, (x, y + 2, 3, 13), border_radius=2)
        self._text("MODO DEFENSA", x + 9, y - 1, ACCENT, bold=True)
        y += 30
        
        rate = float(self.cfg["plants"]["respawn_rate"])
        filas = (("Escenario", f"{self.scenario}   ·   semilla {self.seed}", TEXT),
                 ("Presa", str(self.prey_options[self.pi][0]), PREY),
                 ("Depredador", str(self.pred_options[self.qi][0]), PRED),
                 ("Depredadores", str(self.cfg["predators"]["initial"]), TEXT),
                 ("Plantas iniciales", str(self.cfg["plants"]["initial"]), PLANT),
                 ("Aparición por paso", f"{rate:.3f}", TEXT))
        for label, valor, color in filas:
            self._text(label, x, y, MUTED, small=True, gap=0)
            self._text_right(valor, xr, y, color)
            y += 20 # Más espacio entre filas
            
        self.screen.set_clip(agent_rect)
        self._draw_agent(x, HUD + 184)
        self.screen.set_clip(None)
        self._draw_chart(x, HUD + H - 104)

    def _draw_agent(self, x, y):
        w = self.world
        IW = PANEL - 36
        if self.selected is None:
            pygame.draw.rect(self.screen, ACCENT, (x, y + 2, 3, 13), border_radius=2)
            y = self._text("CONSULTA DE DECISIONES", x + 9, y - 1, ACCENT, bold=True)
            y += 10
            y = self._text("Haz clic en un animal para ver", x, y, MUTED, gap=2)
            y = self._text("qué percibe y qué decide su red.", x, y, MUTED, gap=16)
            for nombre in ("presa", "depredador"):
                ic = self._icons[nombre]
                self.screen.blit(ic, (x + (4 if nombre == "presa" else 52), y))
            return y
        sp, i = self.selected
        if sp == "presa":
            alive, energy, emax = w.prey_alive[i], w.prey_energy[i], self.cfg["prey"]["max_energy"]
            head, names = w.prey_heading[i], PREY_INPUTS
            obs, ctrl = w.observe_prey()[i], self.prey_ctrl
            last = None if self.last is None else self.last[0]
            ctrl_name, color = self.prey_options[self.pi][0], PREY
        else:
            alive, energy, emax = w.pred_alive[i], w.pred_energy[i], self.cfg["predators"]["max_energy"]
            head, names = w.pred_heading[i], PRED_INPUTS
            obs, ctrl = w.observe_predator()[i], self.pred_ctrl
            last = None if self.last is None else self.last[1]
            ctrl_name, color = self.pred_options[self.qi][0], PRED
            
        ic = pygame.transform.smoothscale(self._icons[sp], (28, 28))
        self.screen.blit(ic, (x, y - 4))
        titulo = self.font_b.render(f"{sp.upper()} #{i}", True, ACCENT)
        self.screen.blit(titulo, (x + 36, y - 2))
        self._text(f"({ctrl_name})", x + 36 + titulo.get_width() + 8, y + 1, MUTED, small=True)
        if not alive:
            self._text_right("MUERTO", x + IW, y + 1, PRED)
        y += 34
        
        frac = float(np.clip(energy / emax, 0.0, 1.0))
        self._text("energía", x, y - 2, MUTED, small=True, gap=0)
        self._bar_pill(x + 52, y + 1, IW - 52 - 118, frac, _energy_color(frac), h=10)
        self._text_right(f"{energy:.0f}/{emax:.0f}  ·  {np.degrees(head) % 360:.0f}°", x + IW, y - 2)
        y += 26
        
        y = self._text("Qué percibe (entradas)", x, y, MUTED, small=True, gap=10)
        for k, (name, v) in enumerate(zip(names, obs)):
            self._text(name, x, y, TEXT, small=True, gap=0)
            signed = k in SIGNED[sp]
            self._bar(x + 150, y + 5, 100, v, -1 if signed else 0, 1, color)
            self._text_right(f"{v:.2f}", x + IW, y)
            y += 20 # Más espacio para las entradas
            
        y += 8
        if hasattr(ctrl, "decide"):
            out, acts = ctrl.decide(obs[None, :])
            out = out[0]
            y = self._text("Qué calcula la red (capas ocultas)", x, y, MUTED, small=True, gap=6)
            for li, a in enumerate(acts[1:-1], start=1):
                a = a[0]
                size = min(16, (PANEL - 30) // len(a) - 2)
                for j, val in enumerate(a):
                    pygame.draw.circle(self.screen, activation_color(val),
                                       (x + j * (size + 4) + size // 2, y + size // 2), size // 2 + 1)
                y += size + 8
            y = self._text("azul: negativa  ·  naranja: positiva", x, y, MUTED, small=True, gap=12)
        else:
            out = last[i] if last is not None else np.zeros(2)
            y = self._text("Controlador sin red: acción aplicada", x, y, MUTED, small=True, gap=12)
            
        y = self._text("Qué decide (salidas)", x, y, MUTED, small=True, gap=10)
        giro, vel = float(out[0]), float(out[1])
        lado = "recto" if abs(giro) < 0.05 else ("a la derecha" if giro > 0 else "a la izquierda")
        self._text(f"giro · {lado}", x, y, TEXT, small=True, gap=0)
        self._bar(x + 150, y + 5, 100, giro, -1, 1, ACCENT)
        self._text_right(f"{giro:+.2f}", x + IW, y)
        y += 20
        self._text("velocidad", x, y, TEXT, small=True, gap=0)
        self._bar(x + 150, y + 5, 100, vel, 0, 1, ACCENT)
        self._text_right(f"{vel * 100:.0f}%", x + IW, y)
        return y + 22

    def _draw_chart(self, x, y, w=PANEL - 36, h=68):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (17, 21, 29, 255), (0, 0, w, h), border_radius=8)
        for frac in (0.25, 0.5, 0.75):
            yy = h - 3 - int((h - 6) * frac)
            pygame.draw.line(surf, (42, 50, 63, 255), (6, yy), (w - 6, yy))
        n_prey = max(int(self.cfg["prey"]["initial"]), 1)
        for key, color, relleno in (("vivas", PREY, True), ("capturas", PRED, False)):
            data = self.hist[key]
            if len(data) < 2:
                continue
            paso = max(1, len(data) // w)
            idx = list(range(0, len(data), paso))
            if idx[-1] != len(data) - 1:
                idx.append(len(data) - 1)
            pts = [(int(4 + (w - 8) * k / (len(data) - 1)),
                    h - 3 - int((h - 6) * min(data[k] / n_prey, 1.0))) for k in idx]
            if relleno and len(pts) > 1:
                pygame.draw.polygon(surf, (*color, 50), pts + [(pts[-1][0], h - 3), (pts[0][0], h - 3)])
            if len(pts) > 1:
                pygame.draw.lines(surf, color, False, pts, 2)
        self.screen.blit(surf, (x, y))
        self._text(f"{n_prey}", x + 6, y + 3, MUTED, small=True)
        ly = y + h + 6
        pygame.gfxdraw.filled_circle(self.screen, x + 6, ly + 7, 4, PREY)
        self._text("presas vivas", x + 15, ly, PREY, small=True, gap=0)
        pygame.gfxdraw.filled_circle(self.screen, x + 118, ly + 7, 4, PRED)
        self._text("capturas acumuladas", x + 127, ly, PRED, small=True, gap=0)

    def draw(self):
        self.frame += 1
        self.screen.fill(BG)
        self._draw_arena()
        self._draw_panel()
        self._draw_hud()

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
    prey = prey_controller if isinstance(prey_controller, list) else [("seleccionada", prey_controller)]
    pred = predator_controller if isinstance(predator_controller, list) else [("seleccionado", predator_controller)]
    visor = Visor(cfg, prey, pred, seed=seed, scenario=scenario, fps=fps, title=title)
    return visor.run(max_frames=max_frames, screenshot=screenshot, select=select)