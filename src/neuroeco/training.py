"""Entrenamiento por neuroevolución de una especie contra un oponente de referencia fijo.

Etapa A: la presa evoluciona contra un depredador de referencia.
Etapa B: el depredador evoluciona contra una presa de referencia.

Dentro de un episodio todos los individuos de la especie usan el mismo genoma.
En cada generación todos los genomas se evalúan con las mismas semillas (así la
comparación entre ellos es justa) y las semillas cambian de una generación a otra
(así no se sobreajusta a unos pocos mapas). Al final, los mejores genomas de la
última generación se re-evalúan con semillas de validación que nunca se usaron
para entrenar, y el modelo final es el mejor en esa validación.
"""
import csv
import json
import multiprocessing as mp
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import yaml

from .config import ROOT
from .controllers import make_predator_controller, make_prey_controller
from .evolution import Evolution
from .fitness import fitness_for
from .network import Network, NeuralController, layer_sizes
from .runner import run_episode

HISTORY_COLUMNS = ["generacion", "mejor", "media", "desviacion", "minimo",
                   "metrica_clave_media", "metrica_clave_del_mejor", "segundos"]


def evaluate_genome(job):
    """Evalúa un genoma en varios episodios. Devuelve (fitness medio, métrica clave media).

    La métrica clave es la supervivencia de las presas (especie presa) o las
    capturas totales (especie depredador).
    """
    cfg, species, genome, seeds = job
    neural = NeuralController(layer_sizes(cfg, species), genome)
    if species == "presa":
        prey_c = neural
        pred_c = make_predator_controller(cfg["training"]["prey_opponent"], cfg)
        key = "prey_survival"
    else:
        prey_c = make_prey_controller(cfg["training"]["predator_opponent"], cfg)
        pred_c = neural
        key = "captures_total"
    fits, keys = [], []
    for s in seeds:
        m = run_episode(cfg, prey_c, pred_c, s)
        fits.append(fitness_for(species, m, cfg))
        keys.append(m[key])
    return float(np.mean(fits)), float(np.mean(keys))


class _Evaluator:
    """Evalúa varios genomas, en serie o en paralelo (el resultado es el mismo)."""

    def __init__(self, processes):
        self.pool = mp.get_context("spawn").Pool(processes) if processes > 1 else None

    def map(self, jobs):
        if self.pool is None:
            return [evaluate_genome(j) for j in jobs]
        return self.pool.map(evaluate_genome, jobs, chunksize=1)

    def close(self):
        if self.pool is not None:
            self.pool.close()
            self.pool.join()


def _git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else "sin-commit"
    except Exception:
        return "sin-git"


def train(cfg, species, scenario, run_dir, processes=1, log=print, init_population=None, desde=None):
    """Entrena una especie y guarda todo en run_dir. Devuelve el resumen (dict).

    init_population: población inicial (matriz genomas x parámetros) para continuar un
    entrenamiento previo (entrenamiento por etapas). Si es None, la población es aleatoria.
    """
    evo_cfg, tr = cfg["evolution"], cfg["training"]
    G, P, K = int(evo_cfg["generations"]), int(evo_cfg["population_size"]), int(evo_cfg["episodes_per_genome"])
    base_seed, offset = int(cfg["seeds"]["train_start"]), int(tr["validation_offset"])
    if G * K > offset:
        raise ValueError("generations * episodes_per_genome supera validation_offset: "
                         "las semillas de entrenamiento invadirían las de validación")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    net = Network(layer_sizes(cfg, species))
    rng = np.random.default_rng([int(cfg["seed"]), 2 if species == "presa" else 3])
    evo = Evolution(evo_cfg)
    if init_population is None:
        pop = np.stack([net.random_genome(rng) for _ in range(P)])
    else:
        init_population = np.asarray(init_population, dtype=float)
        if init_population.ndim != 2 or init_population.shape[1] != net.n_params or init_population.shape[0] < P:
            raise ValueError(f"La población inicial debe tener al menos {P} genomas de {net.n_params} parámetros; "
                             f"tiene forma {init_population.shape}")
        pop = init_population[:P].copy()
    np.save(run_dir / "population_gen0.npy", pop)
    with open(run_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump({**cfg, "_corrida": {"especie": species, "escenario": scenario,
                                            "procesos": processes}}, f, allow_unicode=True, sort_keys=False)

    key_name = "supervivencia de presas" if species == "presa" else "capturas"
    history_path = run_dir / "history.csv"
    with open(history_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(HISTORY_COLUMNS)

    evaluator = _Evaluator(processes)
    t0 = time.time()
    best_gen0, fit = None, None
    try:
        for g in range(G):
            seeds = [base_seed + g * K + j for j in range(K)]
            res = evaluator.map([(cfg, species, pop[i], seeds) for i in range(P)])
            fit = np.array([r[0] for r in res])
            key = np.array([r[1] for r in res])
            if g == 0:
                best_gen0 = pop[int(np.argmax(fit))].copy()
            elapsed = time.time() - t0
            row = [g + 1, fit.max(), fit.mean(), fit.std(), fit.min(), key.mean(),
                   key[int(np.argmax(fit))], round(elapsed, 1)]
            with open(history_path, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(row)
            eta = elapsed / (g + 1) * (G - g - 1)
            log(f"gen {g + 1:03d}/{G}  mejor {fit.max():.3f}  media {fit.mean():.3f}  "
                f"{key_name} {key.mean():.2f}  [{elapsed:.0f} s, faltan ~{eta / 60:.1f} min]")
            if g < G - 1:
                pop = evo.next_population(pop, fit, rng)

        # Validación final con semillas que nunca se usaron para entrenar.
        order = np.argsort(-fit, kind="stable")[: int(tr["validation_top_k"])]
        vseeds = [base_seed + offset + j for j in range(int(tr["validation_seeds"]))]
        val = evaluator.map([(cfg, species, pop[i], vseeds) for i in order])
        val_fit = np.array([v[0] for v in val])
        winner = int(order[int(np.argmax(val_fit))])
    finally:
        evaluator.close()

    best = pop[winner]
    np.save(run_dir / "best_genome.npy", best)
    np.save(run_dir / "best_gen0.npy", best_gen0)
    np.save(run_dir / "population_final.npy", pop)

    summary = {
        "especie": species,
        "escenario": scenario,
        "generaciones": G, "poblacion": P, "episodios_por_genoma": K,
        "oponente": tr["prey_opponent"] if species == "presa" else tr["predator_opponent"],
        "poblacion_inicial": str(desde) if desde else "aleatoria",
        "fitness_validacion_del_modelo_final": float(val_fit.max()),
        "fitness_validacion_de_los_finalistas": [float(v) for v in val_fit],
        "semillas_validacion": [vseeds[0], vseeds[-1]],
        "norma_cambio_de_pesos_vs_mejor_gen0": float(np.linalg.norm(best - best_gen0)),
        "fraccion_de_pesos_modificados": float(np.mean(np.abs(best - best_gen0) > 1e-12)),
        "n_parametros": int(net.n_params),
        "segundos_totales": round(time.time() - t0, 1),
        "episodios_simulados": G * P * K + len(order) * len(vseeds),
        "python": platform.python_version(), "numpy": np.__version__,
        "commit": _git_commit(),
    }
    with open(run_dir / "resumen.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary