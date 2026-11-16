import numpy as np
import pytest

from neuroeco.config import load_scenario
from neuroeco.estadistica import holm, mean_ci95, paired_comparison
from neuroeco.evaluation import evaluate_jobs, run_job
from neuroeco.network import Network, layer_sizes, load_model, load_neural_controller


# ---------------------------------------------------------------- estadística
def test_holm_coincide_con_el_calculo_a_mano():
    np.testing.assert_allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_holm_no_supera_uno_y_conserva_el_orden():
    adj = holm([0.5, 0.9, 0.001])
    assert adj.max() <= 1.0
    assert adj[2] == pytest.approx(0.003)


def test_ic95_de_la_media_con_valores_conocidos():
    mean, lo, hi = mean_ci95([1.0, 2.0, 3.0, 4.0, 5.0])
    assert mean == pytest.approx(3.0)
    assert lo == pytest.approx(3.0 - 2.7764451 * np.sqrt(2.5) / np.sqrt(5), abs=1e-4)
    assert hi == pytest.approx(3.0 + 2.7764451 * np.sqrt(2.5) / np.sqrt(5), abs=1e-4)


def test_comparacion_pareada_detecta_una_diferencia_clara():
    rng = np.random.default_rng(0)
    b = rng.normal(0.5, 0.05, 30)
    a = b + 0.2 + rng.normal(0, 0.02, 30)
    r = paired_comparison(a, b)
    assert r["diferencia"] == pytest.approx(0.2, abs=0.02)
    assert r["p_wilcoxon"] < 1e-5
    assert r["rango_biserial"] == pytest.approx(1.0)
    assert r["ic95_inf"] > 0.15 and r["ic95_sup"] < 0.25


def test_comparacion_pareada_sin_diferencia_no_es_significativa():
    rng = np.random.default_rng(1)
    b = rng.normal(0.5, 0.05, 30)
    a = b + rng.normal(0, 0.01, 30)
    r = paired_comparison(a, b)
    assert r["p_wilcoxon"] > 0.05
    assert r["ic95_inf"] < 0 < r["ic95_sup"]


def test_comparacion_identica_no_falla():
    x = np.array([0.1, 0.2, 0.3])
    r = paired_comparison(x, x)
    assert r["p_wilcoxon"] == 1.0 and r["diferencia"] == 0.0


def test_comparacion_exige_mismas_semillas():
    with pytest.raises(ValueError):
        paired_comparison([1, 2, 3], [1, 2])


# ---------------------------------------------------------------- evaluación
def _jobs():
    cfg = load_scenario("A")
    cfg["world"]["max_steps"] = 80
    sizes = layer_sizes(cfg, "presa")
    net = Network(sizes)
    genome = net.random_genome(np.random.default_rng(0))
    prey = {"tipo": "red", "sizes": sizes, "genome": genome}
    ref = {"tipo": "ref", "nombre": "perseguidor"}
    meta = {"experimento": "presa", "escenario": "A", "condicion": "red", "variante": "", "oponente": "perseguidor"}
    return [(cfg, meta, prey, ref, s) for s in (5000, 5001, 5002)]


def test_una_fila_trae_metadatos_metricas_y_fitness():
    fila = run_job(_jobs()[0])
    for k in ("experimento", "escenario", "condicion", "semilla", "prey_survival", "captures_total",
              "fitness_presa", "fitness_depredador"):
        assert k in fila
    assert 0.0 <= fila["fitness_presa"] <= 1.0


def test_evaluacion_serie_y_paralelo_dan_lo_mismo():
    jobs = _jobs()
    a = evaluate_jobs(jobs, processes=1, log=lambda *_: None)
    b = evaluate_jobs(jobs, processes=2, log=lambda *_: None)
    np.testing.assert_equal(a, b)


# ---------------------------------------------------------------- cargar redes de distinto tamaño
def test_load_model_usa_la_arquitectura_guardada_en_la_corrida(tmp_path):
    import copy
    import yaml
    cfg = load_scenario("A")
    chica = copy.deepcopy(cfg)
    chica["network"]["prey_hidden"] = [6, 4]
    net = Network(layer_sizes(chica, "presa"))
    np.save(tmp_path / "best_genome.npy", net.random_genome(np.random.default_rng(0)))
    with open(tmp_path / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(chica, f)
    sizes, genome = load_model(tmp_path, "presa", cfg)  # cfg tiene la arquitectura base, pero manda la guardada
    assert sizes == [6, 6, 4, 2] and genome.shape == (80,)
    assert load_neural_controller(tmp_path, "presa", cfg).act(np.zeros((1, 6))).shape == (1, 2)