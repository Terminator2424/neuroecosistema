"""Evaluación de condiciones (controladores) en episodios con semillas fijas.

Una condición es un par (controlador de presa, controlador de depredador). Cada
controlador se describe con un diccionario sencillo, para poder enviarlo a otros
procesos:
    {"tipo": "ref", "nombre": "reglas"}                  controlador de referencia
    {"tipo": "red", "sizes": [6, 12, 8, 2], "genome": v}   red neuronal
"""
import multiprocessing as mp

from .controllers import make_predator_controller, make_prey_controller
from .fitness import fitness_predator, fitness_prey
from .network import NeuralController
from .runner import run_episode


def build_controller(spec, species, cfg):
    if spec["tipo"] == "ref":
        if species == "presa":
            return make_prey_controller(spec["nombre"], cfg)
        return make_predator_controller(spec["nombre"], cfg)
    if spec["tipo"] == "red":
        return NeuralController(spec["sizes"], spec["genome"])
    raise ValueError(f"Tipo de controlador desconocido: {spec['tipo']}")


def run_job(job):
    """Corre un episodio y devuelve una fila con los metadatos, las métricas y los fitness."""
    cfg, meta, prey_spec, pred_spec, seed = job
    metrics = run_episode(cfg, build_controller(prey_spec, "presa", cfg),
                          build_controller(pred_spec, "depredador", cfg), seed)
    return {**meta, "semilla": int(seed), **metrics,
            "fitness_presa": fitness_prey(metrics, cfg),
            "fitness_depredador": fitness_predator(metrics, cfg)}


def evaluate_jobs(jobs, processes=1, log=print):
    """Evalúa una lista de trabajos en serie o en paralelo; el orden y el resultado no cambian."""
    total = len(jobs)
    step = max(1, total // 20)
    rows = []

    def progress(i):
        if (i + 1) % step == 0 or i + 1 == total:
            log(f"  {i + 1}/{total} episodios")

    if processes <= 1:
        for i, job in enumerate(jobs):
            rows.append(run_job(job))
            progress(i)
    else:
        with mp.get_context("spawn").Pool(processes) as pool:
            for i, row in enumerate(pool.imap(run_job, jobs, chunksize=4)):
                rows.append(row)
                progress(i)
    return rows