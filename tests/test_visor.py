import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from neuroeco.config import load_scenario
from neuroeco.controllers import make_predator_controller, make_prey_controller
from neuroeco.network import Network, NeuralController, layer_sizes
from neuroeco.viewer import HUD, Visor, activation_color, modify_cfg, nearest_agent
from neuroeco.world import World


@pytest.fixture
def cfg():
    c = load_scenario("A")
    c["world"]["max_steps"] = 60
    return c


def _opciones(cfg):
    rng = np.random.default_rng(0)
    red_presa = NeuralController(layer_sizes(cfg, "presa"), Network(layer_sizes(cfg, "presa")).random_genome(rng))
    red_dep = NeuralController(layer_sizes(cfg, "depredador"), Network(layer_sizes(cfg, "depredador")).random_genome(rng))
    prey = [("red", red_presa), ("por reglas", make_prey_controller("reglas", cfg))]
    pred = [("red", red_dep), ("perseguidor", make_predator_controller("perseguidor", cfg))]
    return prey, pred


# ---------------------------------------------------------------- lógica sin ventana
def test_nearest_agent_elige_el_vivo_mas_cercano(cfg):
    w = World(cfg, 1)
    w.prey_pos[0] = [100.0, 100.0]
    w.pred_pos[0] = [300.0, 300.0]
    assert nearest_agent(w, 103, 98) == ("presa", 0)
    assert nearest_agent(w, 298, 304) == ("depredador", 0)
    assert nearest_agent(w, 700, 20, radius=5) is None
    w.prey_alive[0] = False
    assert nearest_agent(w, 100, 100, radius=5) is None


def test_modify_cfg_cambia_depredadores_y_comida_sin_tocar_el_original(cfg):
    base_pred, base_plants = cfg["predators"]["initial"], cfg["plants"]["initial"]
    assert modify_cfg(cfg, "pred+")["predators"]["initial"] == base_pred + 1
    assert modify_cfg(cfg, "pred-")["predators"]["initial"] == base_pred - 1
    mas = modify_cfg(cfg, "comida+")
    assert mas["plants"]["initial"] == base_plants + 10
    assert mas["plants"]["respawn_rate"] > cfg["plants"]["respawn_rate"]
    assert mas["plants"]["max_plants"] >= mas["plants"]["initial"]
    assert modify_cfg(cfg, "comida-")["plants"]["respawn_rate"] < cfg["plants"]["respawn_rate"]
    assert cfg["predators"]["initial"] == base_pred and cfg["plants"]["initial"] == base_plants


def test_modify_cfg_respeta_limites(cfg):
    c = cfg
    for _ in range(40):
        c = modify_cfg(c, "pred-")
    assert c["predators"]["initial"] == 1
    for _ in range(40):
        c = modify_cfg(c, "pred+")
    assert c["predators"]["initial"] == 20
    with pytest.raises(ValueError):
        modify_cfg(cfg, "otro")


def test_color_de_activacion_es_neutro_en_cero_y_distingue_signos():
    assert activation_color(0.0) == (60, 60, 70)
    assert activation_color(1.0)[0] > activation_color(-1.0)[0]
    assert activation_color(-1.0)[2] > activation_color(1.0)[2]


# ---------------------------------------------------------------- visor sin ventana
def test_visor_corre_dibuja_y_guarda_captura(cfg, tmp_path):
    prey, pred = _opciones(cfg)
    visor = Visor(cfg, prey, pred, seed=5, fps=1000)
    ruta = tmp_path / "visor.png"
    visor.run(max_frames=20, screenshot=ruta, select=("presa", 0))
    assert ruta.exists() and ruta.stat().st_size > 1000


def test_visor_consulta_de_decisiones_con_red_y_con_reglas(cfg, tmp_path):
    prey, pred = _opciones(cfg)
    visor = Visor(cfg, prey, pred, seed=5, fps=1000)
    visor.selected = ("presa", 2)
    for _ in range(5):
        visor.step_once()
    visor.draw()                              # con red: dibuja entradas, capas ocultas y salidas
    visor.handle_key(pygame.K_p)              # cambia a presa por reglas
    visor.selected = ("depredador", 0)
    for _ in range(5):
        visor.step_once()
    visor.draw()                              # depredador con red
    visor.handle_key(pygame.K_d)              # depredador por reglas
    visor.selected = ("presa", 0)
    for _ in range(3):
        visor.step_once()
    visor.draw()                              # sin red: muestra la acción aplicada
    pygame.quit()


def test_visor_modo_defensa_reinicia_con_la_misma_semilla(cfg):
    prey, pred = _opciones(cfg)
    visor = Visor(cfg, prey, pred, seed=7, fps=1000)
    for _ in range(10):
        visor.step_once()
    visor.handle_key(pygame.K_x)              # un depredador más
    assert visor.cfg["predators"]["initial"] == cfg["predators"]["initial"] + 1
    assert visor.world.t == 0 and len(visor.world.pred_pos) == cfg["predators"]["initial"] + 1
    visor.handle_key(pygame.K_2)              # escenario B
    assert visor.scenario == "B" and visor.cfg["plants"]["initial"] == load_scenario("B")["plants"]["initial"]
    visor.handle_key(pygame.K_n)
    assert visor.seed == 8
    visor.handle_key(pygame.K_SPACE)
    assert visor.paused
    t = visor.world.t
    visor.handle_key(pygame.K_RIGHT)          # un paso en pausa
    assert visor.world.t == t + 1
    pygame.quit()


def test_visor_clic_selecciona_un_animal(cfg):
    prey, pred = _opciones(cfg)
    visor = Visor(cfg, prey, pred, seed=3, fps=1000)
    x, y = visor.world.prey_pos[4]
    visor.handle_click(int(x), int(y) + HUD)
    assert visor.selected == ("presa", 4)
    visor.handle_click(int(visor.world.W) + 50, HUD + 10)   # clic en el panel: no cambia
    assert visor.selected == ("presa", 4)
    pygame.quit()


def test_visor_registra_un_efecto_cuando_una_presa_es_capturada(cfg):
    prey, pred = _opciones(cfg)
    visor = Visor(cfg, prey, pred, seed=2, fps=1000)
    w = visor.world
    w.pred_pos[0] = w.prey_pos[0].copy()      # un depredador justo encima de una presa
    visor.step_once()
    assert any(e[3] == "captura" for e in visor.effects)
    visor.draw()
    pygame.quit()
