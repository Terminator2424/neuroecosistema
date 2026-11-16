"""Revisión de calidad de la Fase 2: desempeño de los agentes de referencia.

Usa semillas de DESARROLLO (las de entrenamiento, seeds.train_start en adelante),
nunca las de evaluación final. Sirve para comprobar que el mundo se comporta de
forma razonable y para calibrar parámetros antes de entrenar.

    python experiments/revisar_referencias.py
    python experiments/revisar_referencias.py --n 20
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from neuroeco.config import load_scenario
from neuroeco.controllers import make_predator_controller, make_prey_controller
from neuroeco.runner import run_episode

ENFRENTAMIENTOS = [
    ("aleatorio", "aleatorio"),
    ("reglas", "aleatorio"),
    ("reglas", "perseguidor"),
    ("reglas", "interceptor"),
    ("aleatorio", "perseguidor"),
    ("aleatorio", "interceptor"),
]
METRICAS = ["prey_survival", "prey_alive_final", "captures_total", "pred_alive_final",
            "pred_final_energy", "food_eaten_per_prey"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="número de semillas por condición")
    args = ap.parse_args()

    filas = []
    for esc in ("A", "B", "C"):
        cfg = load_scenario(esc)
        start = int(cfg["seeds"]["train_start"])
        for presa, depre in ENFRENTAMIENTOS:
            for s in range(start, start + args.n):
                m = run_episode(cfg, make_prey_controller(presa, cfg), make_predator_controller(depre, cfg), s)
                filas.append({"escenario": esc, "presa": presa, "depredador": depre, "semilla": s, **m})
            print(f"escenario {esc}: presa={presa}, depredador={depre} listo", flush=True)

    df = pd.DataFrame(filas)
    out = ROOT / "results" / "fase2_referencias.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False)

    resumen = df.groupby(["escenario", "presa", "depredador"])[METRICAS].agg(["mean", "std"]).round(2)
    pd.set_option("display.width", 250, "display.max_columns", None)
    print("\nMedia y desviación estándar por condición:\n")
    print(resumen.to_string())
    print(f"\nDatos por episodio guardados en {out}")


if __name__ == "__main__":
    main()