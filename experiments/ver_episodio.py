"""Abre el visor de la simulación (con consulta de decisiones y modo defensa).

Sin opciones usa las redes entrenadas si existen en models/ (presa_A_base y depre_A_base);
si no, usa los controladores de referencia. Dentro del visor se puede cambiar de controlador
con las teclas P (presa) y D (depredador).

Ejemplos:
    python experiments/ver_episodio.py
    python experiments/ver_episodio.py --escenario C --semilla 7
    python experiments/ver_episodio.py --presa reglas --depredador interceptor
    python experiments/ver_episodio.py --modelo-presa models/presa_A_grande
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from neuroeco.config import load_scenario
from neuroeco.controllers import (PREDATOR_CONTROLLERS, PREY_CONTROLLERS,
                                  make_predator_controller, make_prey_controller)
from neuroeco.network import load_neural_controller
from neuroeco.viewer import run_viewer

MODELOS_PRESA = [("red base", "models/presa_A_base"), ("red pequeña", "models/presa_A_pequena"),
                 ("red grande", "models/presa_A_grande")]
MODELOS_DEPREDADOR = [("red entrenada", "models/depre_A_base")]


def _ordenar(primero, opciones):
    """Pone primero la opción elegida y quita nombres repetidos."""
    vistos, salida = set(), []
    for nombre, ctrl in ([primero] if primero else []) + opciones:
        if nombre not in vistos:
            vistos.add(nombre)
            salida.append((nombre, ctrl))
    return salida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escenario", default="A", choices=["A", "B", "C"])
    ap.add_argument("--presa", default=None, choices=PREY_CONTROLLERS, help="controlador de referencia para empezar")
    ap.add_argument("--depredador", default=None, choices=PREDATOR_CONTROLLERS, help="controlador de referencia para empezar")
    ap.add_argument("--modelo-presa", default=None, help="carpeta o .npy de una presa entrenada para empezar")
    ap.add_argument("--modelo-depredador", default=None, help="carpeta o .npy de un depredador entrenado para empezar")
    ap.add_argument("--semilla", type=int, default=1000)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--max-frames", type=int, default=None, help="para pruebas sin ventana")
    ap.add_argument("--captura", default=None, help="ruta de una imagen para guardar el último cuadro")
    args = ap.parse_args()

    cfg = load_scenario(args.escenario)

    prey = [(n, load_neural_controller(ROOT / r, "presa", cfg)) for n, r in MODELOS_PRESA if (ROOT / r).exists()]
    prey += [("por reglas", make_prey_controller("reglas", cfg)), ("aleatoria", make_prey_controller("aleatorio", cfg))]
    pred = [(n, load_neural_controller(ROOT / r, "depredador", cfg)) for n, r in MODELOS_DEPREDADOR if (ROOT / r).exists()]
    pred += [("perseguidor", make_predator_controller("perseguidor", cfg)),
             ("interceptor", make_predator_controller("interceptor", cfg)),
             ("aleatorio", make_predator_controller("aleatorio", cfg))]

    primero_presa = primero_pred = None
    if args.modelo_presa:
        primero_presa = ("red elegida", load_neural_controller(args.modelo_presa, "presa", cfg))
    elif args.presa:
        primero_presa = ({"reglas": "por reglas", "aleatorio": "aleatoria"}[args.presa], make_prey_controller(args.presa, cfg))
    if args.modelo_depredador:
        primero_pred = ("red elegida", load_neural_controller(args.modelo_depredador, "depredador", cfg))
    elif args.depredador:
        primero_pred = (args.depredador, make_predator_controller(args.depredador, cfg))

    if primero_presa:
        prey = _ordenar(primero_presa, prey)
    if primero_pred:
        pred = [(n, c) for n, c in pred if n != primero_pred[0]]
        pred = _ordenar(primero_pred, pred)

    run_viewer(cfg, prey, pred, args.semilla, fps=args.fps, max_frames=args.max_frames, screenshot=args.captura,
               title=f"NeuroEcosistema - escenario {args.escenario}", scenario=args.escenario)


if __name__ == "__main__":
    main()