import copy
import json

import numpy as np
import pytest

from neuroeco.config import load_scenario
from neuroeco.evolution import Evolution
from neuroeco.fitness import fitness_predator, fitness_prey
from neuroeco.network import Network, NeuralController, layer_sizes, load_neural_controller
from neuroeco.training import train


@pytest.fixture
def cfg():
    return load_scenario("A")


# ---------------------------------------------------------------- red neuronal
def test_numero_de_parametros_coincide_con_el_diseno(cfg):
    assert Network(layer_sizes(cfg, "presa")).n_params == 206
    assert Network(layer_sizes(cfg, "depredador")).n_params == 166


def test_forma_y_rango_de_las_salidas(cfg):
    rng = np.random.default_rng(0)
    for species, n_in in (("presa", 6), ("depredador", 5)):
        net = Network(layer_sizes(cfg, species))
        ctrl = NeuralController(net.sizes, net.random_genome(rng))
        out = ctrl.act(rng.uniform(-1, 1, size=(40, n_in)))
        assert out.shape == (40, 2)
        assert out[:, 0].min() >= -1.0 and out[:, 0].max() <= 1.0   # giro
        assert out[:, 1].min() >= 0.0 and out[:, 1].max() <= 1.0    # velocidad


def test_la_red_es_determinista_y_depende_de_los_pesos(cfg):
    rng = np.random.default_rng(1)
    net = Network(layer_sizes(cfg, "presa"))
    g = net.random_genome(rng)
    x = rng.uniform(-1, 1, size=(10, 6))
    a = NeuralController(net.sizes, g).act(x)
    b = NeuralController(net.sizes, g).act(x)
    np.testing.assert_array_equal(a, b)
    g2 = g.copy()
    g2[0] += 0.5
    assert not np.allclose(a, NeuralController(net.sizes, g2).act(x))


def test_genoma_con_tamano_incorrecto_da_error(cfg):
    net = Network(layer_sizes(cfg, "presa"))
    with pytest.raises(ValueError):
        net.unpack(np.zeros(net.n_params + 1))


def test_forward_coincide_con_calculo_manual():
    net = Network([2, 3, 2])
    rng = np.random.default_rng(2)
    g = rng.normal(size=net.n_params)
    (W1, b1), (W2, b2) = net.unpack(g)
    x = rng.normal(size=(4, 2))
    h = np.tanh(x @ W1 + b1)
    z = h @ W2 + b2
    esperado = np.column_stack([np.tanh(z[:, 0]), 1.0 / (1.0 + np.exp(-z[:, 1]))])
    np.testing.assert_allclose(NeuralController(net.sizes, g).act(x), esperado)


def test_activaciones_para_inspeccionar_decisiones(cfg):
    net = Network(layer_sizes(cfg, "presa"))
    ctrl = NeuralController(net.sizes, net.random_genome(np.random.default_rng(3)))
    out, acts = ctrl.decide(np.zeros((1, 6)))
    assert out.shape == (1, 2)
    assert [a.shape[1] for a in acts] == net.sizes


def test_guardar_y_cargar_un_modelo(cfg, tmp_path):
    net = Network(layer_sizes(cfg, "depredador"))
    g = net.random_genome(np.random.default_rng(4))
    np.save(tmp_path / "best_genome.npy", g)
    ctrl = load_neural_controller(tmp_path, "depredador", cfg)
    np.testing.assert_array_equal(ctrl.genome, g)


# ---------------------------------------------------------------- fitness
def test_fitness_en_rango_y_variantes(cfg):
    m = {"prey_survival": 0.6, "food_eaten_per_prey": 4.0, "captures_total": 9,
         "pred_final_energy": 0.5}
    assert fitness_prey(m, cfg) == pytest.approx(0.7 * 0.6 + 0.3 * 0.5)
    assert fitness_predator(m, cfg) == pytest.approx(0.7 * (9 / 30) + 0.3 * 0.5)
    c2 = copy.deepcopy(cfg)
    c2["fitness"].update(variant_prey="supervivencia", variant_predator="capturas")
    assert fitness_prey(m, c2) == pytest.approx(0.6)
    assert fitness_predator(m, c2) == pytest.approx(9 / 30)


# ---------------------------------------------------------------- evolución
def _evo(**kw):
    base = dict(elite=2, tournament_size=3, mutation_rate=0.2, mutation_sigma=0.1, crossover_rate=0.0)
    base.update(kw)
    return Evolution(base)


def test_el_elitismo_conserva_a_los_mejores():
    rng = np.random.default_rng(0)
    pop = rng.normal(size=(10, 6))
    fit = rng.uniform(size=10)
    nueva = _evo().next_population(pop, fit, rng)
    mejores = np.argsort(-fit)[:2]
    np.testing.assert_array_equal(nueva[:2], pop[mejores])
    assert nueva.shape == pop.shape


def test_la_mutacion_cambia_a_los_hijos_pero_poco():
    rng = np.random.default_rng(1)
    pop = np.zeros((20, 50))
    nueva = _evo(elite=1).next_population(pop, np.arange(20, dtype=float), rng)
    hijos = nueva[1:]
    assert np.any(hijos != 0.0)
    assert np.abs(hijos).max() < 1.0


def test_el_algoritmo_mejora_un_problema_sencillo():
    """Sanidad del algoritmo genético en aislamiento: minimizar la distancia a un vector objetivo."""
    rng = np.random.default_rng(5)
    objetivo = np.linspace(-1, 1, 20)
    pop = rng.normal(size=(30, 20))
    evo = _evo(elite=3, mutation_rate=0.2, mutation_sigma=0.1)
    mejor0 = None
    for g in range(60):
        fit = -np.linalg.norm(pop - objetivo, axis=1)
        if mejor0 is None:
            mejor0 = fit.max()
        pop = evo.next_population(pop, fit, rng)
    assert fit.max() > mejor0 + 1.0


# ---------------------------------------------------------------- entrenamiento
def _cfg_mini(cfg):
    c = copy.deepcopy(cfg)
    c["world"]["max_steps"] = 60
    c["prey"]["initial"] = 8
    c["predators"]["initial"] = 2
    c["plants"].update(initial=20, max_plants=30)
    c["evolution"].update(generations=3, population_size=6, elite=2, episodes_per_genome=1)
    c["training"].update(validation_top_k=2, validation_seeds=2)
    return c


@pytest.mark.parametrize("species", ["presa", "depredador"])
def test_entrenamiento_minimo_genera_los_archivos(cfg, tmp_path, species):
    c = _cfg_mini(cfg)
    resumen = train(c, species, "A", tmp_path / species, processes=1, log=lambda *_: None)
    d = tmp_path / species
    for nombre in ("best_genome.npy", "best_gen0.npy", "population_gen0.npy",
                   "population_final.npy", "history.csv", "config.yaml", "resumen.json"):
        assert (d / nombre).exists(), nombre
    assert len((d / "history.csv").read_text(encoding="utf-8").strip().splitlines()) == 1 + 3
    assert json.loads((d / "resumen.json").read_text(encoding="utf-8"))["n_parametros"] == resumen["n_parametros"]
    assert resumen["norma_cambio_de_pesos_vs_mejor_gen0"] > 0.0


def test_el_resultado_no_depende_del_numero_de_procesos(cfg, tmp_path):
    c = _cfg_mini(cfg)
    train(c, "presa", "A", tmp_path / "serie", processes=1, log=lambda *_: None)
    train(c, "presa", "A", tmp_path / "paralelo", processes=2, log=lambda *_: None)
    np.testing.assert_array_equal(np.load(tmp_path / "serie" / "best_genome.npy"),
                                  np.load(tmp_path / "paralelo" / "best_genome.npy"))


def test_semillas_de_entrenamiento_no_invaden_las_de_validacion(cfg, tmp_path):
    c = _cfg_mini(cfg)
    c["evolution"]["generations"] = 1000
    with pytest.raises(ValueError):
        train(c, "presa", "A", tmp_path / "x", processes=1, log=lambda *_: None)


def test_entrenamiento_por_etapas_parte_de_la_poblacion_dada(cfg, tmp_path):
    c = _cfg_mini(cfg)
    train(c, "depredador", "A", tmp_path / "etapa1", processes=1, log=lambda *_: None)
    previa = np.load(tmp_path / "etapa1" / "population_final.npy")
    train(c, "depredador", "A", tmp_path / "etapa2", processes=1, log=lambda *_: None,
          init_population=previa, desde="etapa1")
    np.testing.assert_array_equal(np.load(tmp_path / "etapa2" / "population_gen0.npy"), previa)
    res = json.loads((tmp_path / "etapa2" / "resumen.json").read_text(encoding="utf-8"))
    assert res["poblacion_inicial"] == "etapa1"


def test_poblacion_inicial_con_forma_incorrecta_da_error(cfg, tmp_path):
    c = _cfg_mini(cfg)
    with pytest.raises(ValueError):
        train(c, "presa", "A", tmp_path / "x", processes=1, log=lambda *_: None,
              init_population=np.zeros((6, 10)))