"""Calibración del mundo (Fase 2b): ¿el entorno deja margen para aprender?

Los criterios K1 a K9 se redactaron durante la exploración (semillas 1000 a 1009),
y aquí se validan con semillas distintas (por defecto 2000 en adelante): los
parámetros no se ajustaron mirando estas semillas. Los umbrales son juicios de
diseño y están escritos abajo para que se puedan discutir. Las semillas de
evaluación final (seeds.eval_start) no se tocan.

    python experiments/calibrar_mundo.py
    python experiments/calibrar_mundo.py --n 30 --inicio 3000
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

# (escenario, presa, depredador)
PARES = [
    ("A", "reglas", "aleatorio"),
    ("A", "reglas", "perseguidor"),
    ("A", "reglas", "interceptor"),
    ("A", "aleatorio", "perseguidor"),
    ("B", "reglas", "aleatorio"),
    ("B", "reglas", "perseguidor"),
    ("C", "reglas", "perseguidor"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="semillas por condición")
    ap.add_argument("--inicio", type=int, default=2000, help="primera semilla de desarrollo")
    args = ap.parse_args()

    filas = []
    for esc, presa, depre in PARES:
        cfg = load_scenario(esc)
        for s in range(args.inicio, args.inicio + args.n):
            m = run_episode(cfg, make_prey_controller(presa, cfg), make_predator_controller(depre, cfg), s)
            filas.append({"escenario": esc, "presa": presa, "depredador": depre, "semilla": s, **m})
        print(f"{esc} {presa} vs {depre} listo", flush=True)
    df = pd.DataFrame(filas)
    out = ROOT / "results" / "fase2b_calibracion.csv"
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False)

    n_prey = load_scenario("A")["prey"]["initial"]
    n_pred = load_scenario("A")["predators"]["initial"]

    def v(esc, presa, depre, col):
        return float(df[(df.escenario == esc) & (df.presa == presa) & (df.depredador == depre)][col].mean())

    a_np_alive = v("A", "reglas", "aleatorio", "prey_alive_final") / n_prey
    b_np_alive = v("B", "reglas", "aleatorio", "prey_alive_final") / n_prey
    a_surv = v("A", "reglas", "perseguidor", "prey_survival")
    a_caps = v("A", "reglas", "perseguidor", "captures_per_pred")
    a_pred_alive = v("A", "reglas", "perseguidor", "pred_alive_final") / n_pred
    a_rand_surv = v("A", "aleatorio", "perseguidor", "prey_survival")
    a_caps_total = v("A", "reglas", "perseguidor", "captures_total")
    a_caps_rand = v("A", "reglas", "aleatorio", "captures_total")
    b_surv = v("B", "reglas", "perseguidor", "prey_survival")
    c_surv = v("C", "reglas", "perseguidor", "prey_survival")
    c_alive = v("C", "reglas", "perseguidor", "prey_alive_final")

    criterios = [
        ("K1", "A tiene alimento suficiente: sin depredación efectiva sobreviven al menos 85 % de las presas",
         a_np_alive, a_np_alive >= 0.85),
        ("K2", "B es escasez real sin ser extinción: sobreviven entre 25 % y 60 % y como mucho 60 % de lo de A",
         b_np_alive, 0.25 <= b_np_alive <= 0.60 and b_np_alive <= 0.6 * a_np_alive),
        ("K3", "A deja margen a las presas: supervivencia con referencia entre 0.45 y 0.75",
         a_surv, 0.45 <= a_surv <= 0.75),
        ("K4", "A deja margen a los depredadores: entre 3 y 10 capturas por depredador",
         a_caps, 3.0 <= a_caps <= 10.0),
        ("K5", "En A no se extinguen los depredadores: al menos 30 % sigue vivo al final",
         a_pred_alive, a_pred_alive >= 0.30),
        ("K6", "Una presa aleatoria sobrevive al menos 0.20 menos que una por reglas",
         a_surv - a_rand_surv, (a_surv - a_rand_surv) >= 0.20),
        ("K7", "El depredador por reglas captura al menos 5 veces más que el aleatorio",
         a_caps_total / max(a_caps_rand, 1.0), a_caps_total >= 5.0 * max(a_caps_rand, 1.0)),
        ("K8", "C aumenta la presión sin aniquilar: supervivencia al menos 0.20 menor que A y quedan 1.5 presas o más",
         a_surv - c_surv, (a_surv - c_surv) >= 0.20 and c_alive >= 1.5),
        ("K9", "B con depredadores es más duro que A",
         a_surv - b_surv, b_surv < a_surv),
    ]

    print("\nCriterios de calibración (semillas %d a %d):\n" % (args.inicio, args.inicio + args.n - 1))
    for cid, texto, valor, ok in criterios:
        print(f"{cid} [{'CUMPLE' if ok else 'NO CUMPLE'}] valor = {valor:6.2f}  {texto}")
    print(f"\n{sum(1 for c in criterios if c[3])} de {len(criterios)} criterios cumplidos. Datos en {out}")


if __name__ == "__main__":
    main()