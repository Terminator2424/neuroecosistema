"""Visualiza un episodio con controladores de referencia.

Ejemplos:
    python experiments/ver_episodio.py
    python experiments/ver_episodio.py --escenario C --depredador interceptor --semilla 7
    python experiments/ver_episodio.py --modelo-presa models/presa_A_xxx --depredador perseguidor
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from neuroeco.config import load_scenario
from neuroeco.controllers import (PREDATOR_CONTROLLERS, PREY_CONTROLLERS,
                                  make_predator_controller, make_prey_controller)
from neuroeco.network import load_neural_controller
from neuroeco.viewer import run_viewer


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escenario", default="A", choices=["A", "B", "C"])
    ap.add_argument("--presa", default="reglas", choices=PREY_CONTROLLERS)
    ap.add_argument("--depredador", default="perseguidor", choices=PREDATOR_CONTROLLERS)
    ap.add_argument("--modelo-presa", default=None, help="carpeta o .npy de una presa entrenada (reemplaza --presa)")
    ap.add_argument("--modelo-depredador", default=None, help="carpeta o .npy de un depredador entrenado (reemplaza --depredador)")
    ap.add_argument("--semilla", type=int, default=1000)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--max-frames", type=int, default=None, help="para pruebas sin ventana")
    ap.add_argument("--captura", default=None, help="ruta de una imagen para guardar el último cuadro")
    args = ap.parse_args()

    cfg = load_scenario(args.escenario)
    if args.modelo_presa:
        prey_c, prey_name = load_neural_controller(args.modelo_presa, "presa", cfg), "red entrenada"
    else:
        prey_c, prey_name = make_prey_controller(args.presa, cfg), args.presa
    if args.modelo_depredador:
        pred_c, pred_name = load_neural_controller(args.modelo_depredador, "depredador", cfg), "red entrenada"
    else:
        pred_c, pred_name = make_predator_controller(args.depredador, cfg), args.depredador
    run_viewer(cfg, prey_c, pred_c, args.semilla, fps=args.fps, max_frames=args.max_frames,
               screenshot=args.captura,
               title=f"NeuroEcosistema - escenario {args.escenario} - presa: {prey_name} / depredador: {pred_name}")


if __name__ == "__main__":
    main()