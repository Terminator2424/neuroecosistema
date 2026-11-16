import copy

import numpy as np
import pytest

from neuroeco.config import load_scenario
from neuroeco.controllers import make_predator_controller, make_prey_controller
from neuroeco.runner import run_episode
from neuroeco.world import World


@pytest.fixture
def cfg():
    return load_scenario("A")


def _quiet_cfg(cfg, prey=1, preds=1, plants=0):
    """Configuración mínima y sin gasto de energía para probar mecánicas puntuales."""
    c = copy.deepcopy(cfg)
    c["plants"].update(initial=plants, max_plants=max(plants, 1), respawn_rate=0.0)
    c["prey"].update(initial=prey, energy_cost_base=0.0, energy_cost_move=0.0)
    c["predators"].update(initial=preds, energy_cost_base=0.0, energy_cost_move=0.0)
    return c


def _stand_still(n):
    return np.zeros((n, 2))


# ---------------------------------------------------------------- reproducibilidad
def test_misma_semilla_mismo_resultado(cfg):
    a = run_episode(cfg, make_prey_controller("reglas", cfg), make_predator_controller("interceptor", cfg), 123)
    b = run_episode(cfg, make_prey_controller("reglas", cfg), make_predator_controller("interceptor", cfg), 123)
    np.testing.assert_equal(a, b)


def test_semillas_distintas_dan_resultados_distintos(cfg):
    res = [
        run_episode(cfg, make_prey_controller("aleatorio", cfg), make_predator_controller("aleatorio", cfg), s)["captures_total"]
        for s in (1, 2, 3, 4)
    ]
    assert len(set(res)) > 1


# ---------------------------------------------------------------- observaciones y límites
def test_observaciones_en_rango_y_forma(cfg):
    w = World(cfg, 7)
    prey_c = make_prey_controller("reglas", cfg)
    pred_c = make_predator_controller("perseguidor", cfg)
    rng = np.random.default_rng(0)
    for _ in range(300):
        op, oq = w.observe_prey(), w.observe_predator()
        assert op.shape == (cfg["prey"]["initial"], 6)
        assert oq.shape == (cfg["predators"]["initial"], 5)
        for o in (op, oq):
            assert np.all(np.isfinite(o))
            assert o.min() >= -1.0 - 1e-9 and o.max() <= 1.0 + 1e-9
        w.step(prey_c.act(op, rng), pred_c.act(oq, rng))


def test_agentes_dentro_del_mundo_y_energia_acotada(cfg):
    w = World(cfg, 11)
    rng = np.random.default_rng(0)
    prey_c = make_prey_controller("aleatorio", cfg)
    pred_c = make_predator_controller("aleatorio", cfg)
    for _ in range(400):
        w.step(prey_c.act(w.observe_prey(), rng), pred_c.act(w.observe_predator(), rng))
        for pos in (w.prey_pos, w.pred_pos):
            assert pos[:, 0].min() >= 0 and pos[:, 0].max() <= w.W
            assert pos[:, 1].min() >= 0 and pos[:, 1].max() <= w.H
        assert w.prey_energy.max() <= cfg["prey"]["max_energy"] + 1e-9
        assert w.pred_energy.max() <= cfg["predators"]["max_energy"] + 1e-9


# ---------------------------------------------------------------- mecánicas
def test_presa_come_planta_y_gana_energia(cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=1)
    w = World(c, 1)
    w.prey_pos[0] = [100.0, 100.0]
    w.plant_pos[0] = [105.0, 100.0]
    w.pred_pos[0] = [700.0, 500.0]
    w.prey_energy[0] = 50.0
    w.step(_stand_still(1), _stand_still(1))
    assert w.prey_food[0] == 1
    assert w.prey_energy[0] == pytest.approx(50.0 + c["plants"]["energy_value"])
    assert not w.plant_active[0]


def test_depredador_captura_presa_cercana(cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=0)
    w = World(c, 1)
    w.prey_pos[0] = [200.0, 200.0]
    w.pred_pos[0] = [204.0, 200.0]
    e0 = w.pred_energy[0]
    w.step(_stand_still(1), _stand_still(1))
    assert not w.prey_alive[0]
    assert w.pred_captures[0] == 1
    assert w.pred_energy[0] == pytest.approx(min(e0 + c["predators"]["energy_gain_capture"], c["predators"]["max_energy"]))
    assert w.done


def test_presa_lejana_no_es_capturada(cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=0)
    w = World(c, 1)
    w.prey_pos[0] = [200.0, 200.0]
    w.pred_pos[0] = [300.0, 200.0]
    w.step(_stand_still(1), _stand_still(1))
    assert w.prey_alive[0] and w.pred_captures[0] == 0


def test_muerte_por_falta_de_energia(cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=0)
    c["prey"]["energy_cost_base"] = 10.0
    w = World(c, 1)
    w.pred_pos[0] = [750.0, 550.0]
    w.prey_pos[0] = [50.0, 50.0]
    for _ in range(11):
        w.step(_stand_still(1), _stand_still(1))
    assert not w.prey_alive[0]


def test_episodio_termina_en_max_steps(cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=0)
    c["world"]["max_steps"] = 25
    w = World(c, 1)
    w.prey_pos[0] = [50.0, 50.0]
    w.pred_pos[0] = [750.0, 550.0]
    while not w.done:
        w.step(_stand_still(1), _stand_still(1))
    assert w.t == 25


def test_si_mueren_los_depredadores_el_episodio_continua(cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=0)
    c["predators"]["energy_cost_base"] = 1000.0
    w = World(c, 1)
    w.prey_pos[0] = [50.0, 50.0]
    w.pred_pos[0] = [750.0, 550.0]
    w.step(_stand_still(1), _stand_still(1))
    assert not w.pred_alive.any()
    assert not w.done


# ---------------------------------------------------------------- controladores de referencia
def _duelo(kind, prey_pos, prey_heading, pred_pos, cfg):
    c = _quiet_cfg(cfg, prey=1, preds=1, plants=0)
    w = World(c, 1)
    w.prey_pos[0], w.prey_heading[0] = prey_pos, prey_heading
    w.pred_pos[0], w.pred_heading[0] = pred_pos, 0.0
    ctrl = make_predator_controller(kind, c)
    rng = np.random.default_rng(0)
    straight = np.array([[0.0, 1.0]])  # la presa avanza recto a velocidad máxima
    while not w.done:
        w.step(straight, ctrl.act(w.observe_predator(), rng))
    return w.t if w.capture_steps else None


@pytest.mark.parametrize("prey_pos,prey_heading", [
    ((400.0, 200.0), np.pi / 2),
    ((400.0, 400.0), -np.pi / 2),
    ((200.0, 200.0), 0.0),
])
def test_interceptor_captura_antes_que_perseguidor_contra_presa_en_linea_recta(cfg, prey_pos, prey_heading):
    t_chase = _duelo("perseguidor", prey_pos, prey_heading, (300.0, 300.0), cfg)
    t_inter = _duelo("interceptor", prey_pos, prey_heading, (300.0, 300.0), cfg)
    assert t_chase is not None and t_inter is not None
    assert t_inter < t_chase


def test_perseguidor_captura_mas_que_depredador_aleatorio(cfg):
    prey_c = make_prey_controller("reglas", cfg)
    seeds = range(1000, 1005)
    chaser = [run_episode(cfg, prey_c, make_predator_controller("perseguidor", cfg), s)["captures_total"] for s in seeds]
    rand = [run_episode(cfg, prey_c, make_predator_controller("aleatorio", cfg), s)["captures_total"] for s in seeds]
    assert np.mean(chaser) > np.mean(rand)


# ---------------------------------------------------------------- escenarios
def _diferencias(a, b, prefix=""):
    out = []
    for k in a:
        if isinstance(a[k], dict):
            out += _diferencias(a[k], b[k], prefix + k + ".")
        elif a[k] != b[k]:
            out.append(prefix + k)
    return out


def test_escenario_C_difiere_de_A_solo_en_depredadores():
    assert _diferencias(load_scenario("A"), load_scenario("C")) == ["predators.initial"]


def test_escenario_B_difiere_de_A_solo_en_alimento():
    diff = _diferencias(load_scenario("A"), load_scenario("B"))
    assert diff and all(d.startswith("plants.") for d in diff)


def test_interceptor_sin_adelanto_si_la_presa_se_aleja_en_la_linea_de_vision(cfg):
    ctrl = make_predator_controller("interceptor", cfg)
    rng = np.random.default_rng(0)
    # presa a 0.5 de distancia normalizada, justo al frente (ángulo 0) y alejándose (rumbo relativo 0)
    obs = np.array([[1.0, 0.0, 0.5, 0.0, 1.0]])
    assert ctrl.act(obs, rng)[0, 0] == pytest.approx(0.0, abs=1e-9)
    # misma presa, pero cruzando de izquierda a derecha: el interceptor debe girar hacia donde ella va
    obs = np.array([[1.0, 0.0, 0.5, 0.5, 1.0]])  # rumbo relativo = +pi/2
    assert ctrl.act(obs, rng)[0, 0] > 0.0
