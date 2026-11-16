"""Evaluación final (Fase 4): todas las condiciones en los escenarios A, B y C.

USA LAS SEMILLAS DE EVALUACIÓN FINAL (seeds.eval_start en adelante). Antes de
correrlo deben estar escritas las hipótesis (docs/hipotesis.md). Si hay que
corregir un error y repetirlo, se registra en la bitácora como cambio posterior.

Condiciones evaluadas:
- presas (contra el perseguidor y contra el interceptor): aleatoria, por reglas,
  red sin entrenar (5 redes aleatorias), red entrenada y, si se dan, red pequeña
  y red grande;
- depredadores (contra la presa por reglas): aleatorio, perseguidor, interceptor,
  red sin entrenar (5 redes aleatorias) y red entrenada;
- ecosistema exploratorio: red entrenada de presa contra red entrenada de depredador.

    python experiments/evaluar.py --presa-base models/presa_A_base --depre-etapa1 models/depre_A_etapa1 --depre-base models/depre_A_base --presa-pequena models/presa_A_pequena --presa-grande models/presa_A_grande
"""
import argparse
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from neuroeco.config import load_scenario
from neuroeco.evaluation import evaluate_jobs
from neuroeco.network import load_model
from neuroeco.training import _git_commit

N_SIN_ENTRENAR = 5


def _ruta(p):
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def _red(path, species, cfg):
    sizes, genome = load_model(_ruta(path), species, cfg)
    return {"tipo": "red", "sizes": sizes, "genome": genome}


def _redes_sin_entrenar(path, species, cfg):
    """Las primeras N redes de la población inicial aleatoria de una corrida."""
    sizes, _ = load_model(_ruta(path), species, cfg)
    pop = np.load(_ruta(path) / "population_gen0.npy")
    return [(str(k), {"tipo": "red", "sizes": sizes, "genome": pop[k]}) for k in range(N_SIN_ENTRENAR)]


def _ref(nombre):
    return {"tipo": "ref", "nombre": nombre}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presa-base", required=True)
    ap.add_argument("--depre-etapa1", required=True, help="corrida cuya población inicial aleatoria sirve de 'antes' del depredador")
    ap.add_argument("--depre-base", required=True)
    ap.add_argument("--presa-pequena", default=None)
    ap.add_argument("--presa-grande", default=None)
    ap.add_argument("--semillas", type=int, default=None, help="número de semillas de evaluación (por defecto seeds.eval_count)")
    ap.add_argument("--escenarios", default="ABC")
    ap.add_argument("--procesos", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--salida", default="results/fase4")
    args = ap.parse_args()

    base_cfg = load_scenario("A")
    n_seeds = args.semillas or int(base_cfg["seeds"]["eval_count"])
    first = int(base_cfg["seeds"]["eval_start"])
    seeds = list(range(first, first + n_seeds))
    print(f"Semillas de evaluación final: {seeds[0]} a {seeds[-1]} ({n_seeds} semillas)")

    # --- condiciones de presa
    prey_conditions = [
        ("aleatoria", [("", _ref("aleatorio"))]),
        ("reglas", [("", _ref("reglas"))]),
        ("red_sin_entrenar", _redes_sin_entrenar(args.presa_base, "presa", base_cfg)),
        ("red_entrenada", [("", _red(args.presa_base, "presa", base_cfg))]),
    ]
    if args.presa_pequena:
        prey_conditions.append(("red_pequena", [("", _red(args.presa_pequena, "presa", base_cfg))]))
    if args.presa_grande:
        prey_conditions.append(("red_grande", [("", _red(args.presa_grande, "presa", base_cfg))]))

    # --- condiciones de depredador
    pred_conditions = [
        ("aleatorio", [("", _ref("aleatorio"))]),
        ("perseguidor", [("", _ref("perseguidor"))]),
        ("interceptor", [("", _ref("interceptor"))]),
        ("red_sin_entrenar", _redes_sin_entrenar(args.depre_etapa1, "depredador", base_cfg)),
        ("red_entrenada", [("", _red(args.depre_base, "depredador", base_cfg))]),
    ]

    prey_trained = _red(args.presa_base, "presa", base_cfg)
    pred_trained = _red(args.depre_base, "depredador", base_cfg)

    jobs = []
    for esc in args.escenarios:
        cfg = load_scenario(esc)
        for opp in ("perseguidor", "interceptor"):
            for cond, variants in prey_conditions:
                for var, spec in variants:
                    for s in seeds:
                        meta = {"experimento": "presa", "escenario": esc, "condicion": cond,
                                "variante": var, "oponente": opp}
                        jobs.append((cfg, meta, spec, _ref(opp), s))
        for cond, variants in pred_conditions:
            for var, spec in variants:
                for s in seeds:
                    meta = {"experimento": "depredador", "escenario": esc, "condicion": cond,
                            "variante": var, "oponente": "reglas"}
                    jobs.append((cfg, meta, _ref("reglas"), spec, s))
        for s in seeds:
            meta = {"experimento": "ecosistema", "escenario": esc, "condicion": "red_vs_red",
                    "variante": "", "oponente": "red"}
            jobs.append((cfg, meta, prey_trained, pred_trained, s))

    print(f"{len(jobs)} episodios, {args.procesos} procesos")
    rows = evaluate_jobs(jobs, processes=args.procesos)

    out = _ruta(args.salida)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "episodios.csv", index=False)
    with open(out / "configuracion_evaluacion.json", "w", encoding="utf-8") as f:
        json.dump({"semillas": [seeds[0], seeds[-1]], "n_semillas": n_seeds, "escenarios": args.escenarios,
                   "modelos": {"presa_base": args.presa_base, "depre_etapa1": args.depre_etapa1,
                               "depre_base": args.depre_base, "presa_pequena": args.presa_pequena,
                               "presa_grande": args.presa_grande},
                   "redes_sin_entrenar_por_condicion": N_SIN_ENTRENAR,
                   "python": platform.python_version(), "numpy": np.__version__,
                   "commit": _git_commit()}, f, indent=2, ensure_ascii=False)
    print(f"\nListo. Episodios guardados en {out / 'episodios.csv'}")
    print("Siguiente paso: python experiments/analizar.py")


if __name__ == "__main__":
    main()