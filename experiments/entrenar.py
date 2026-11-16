"""Entrena una especie (presa o depredador) por neuroevolución.

Ejemplos:
    python experiments/entrenar.py --especie presa --rapido
    python experiments/entrenar.py --especie depredador --oponente aleatorio --nombre depre_etapa1
    python experiments/entrenar.py --especie depredador --oponente reglas --desde models/depre_etapa1
    python experiments/entrenar.py --especie presa --generaciones 100 --poblacion 30 --episodios 3

Guarda todo en models/<nombre>/: best_genome.npy, history.csv, config.yaml, resumen.json.
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from neuroeco.config import load_scenario
from neuroeco.training import train


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--especie", required=True, choices=["presa", "depredador"])
    ap.add_argument("--escenario", default="A", choices=["A", "B", "C"])
    ap.add_argument("--generaciones", type=int, default=None)
    ap.add_argument("--poblacion", type=int, default=None)
    ap.add_argument("--episodios", type=int, default=None, help="episodios por genoma y generación")
    ap.add_argument("--procesos", type=int, default=max(1, (os.cpu_count() or 2) - 1),
                    help="procesos en paralelo (el resultado no depende de este número)")
    ap.add_argument("--oponente", default=None,
                    help="presa: perseguidor | interceptor | aleatorio; depredador: reglas | aleatorio")
    ap.add_argument("--desde", default=None,
                    help="carpeta de una corrida previa: se parte de su población final (entrenamiento por etapas)")
    ap.add_argument("--ocultas", default=None,
                    help="neuronas de las capas ocultas separadas por coma, por ejemplo 6,4 (cambia la arquitectura)")
    ap.add_argument("--semilla", type=int, default=None, help="semilla del algoritmo evolutivo")
    ap.add_argument("--nombre", default=None, help="nombre de la carpeta en models/")
    ap.add_argument("--rapido", action="store_true", help="corrida corta de prueba (8 generaciones, 12 genomas, 2 episodios)")
    args = ap.parse_args()

    cfg = load_scenario(args.escenario)
    evo = cfg["evolution"]
    if args.rapido:
        evo.update(generations=8, population_size=12, episodes_per_genome=2)
        cfg["training"].update(validation_top_k=3, validation_seeds=5)
    if args.generaciones is not None:
        evo["generations"] = args.generaciones
    if args.poblacion is not None:
        evo["population_size"] = args.poblacion
    if args.episodios is not None:
        evo["episodes_per_genome"] = args.episodios
    if args.ocultas is not None:
        cfg["network"]["prey_hidden" if args.especie == "presa" else "predator_hidden"] = [
            int(x) for x in args.ocultas.split(",")]
    if args.semilla is not None:
        cfg["seed"] = args.semilla
    if args.oponente is not None:
        cfg["training"]["prey_opponent" if args.especie == "presa" else "predator_opponent"] = args.oponente

    nombre = args.nombre or f"{args.especie}_{args.escenario}_{datetime.now():%Y%m%d_%H%M%S}"
    run_dir = ROOT / "models" / nombre
    print(f"Entrenando {args.especie} en el escenario {args.escenario} "
          f"({evo['generations']} generaciones, {evo['population_size']} genomas, "
          f"{evo['episodes_per_genome']} episodios, {args.procesos} procesos)")
    init = None
    if args.desde:
        origen = Path(args.desde)
        if not origen.is_absolute():
            origen = ROOT / origen
        init = np.load(origen / "population_final.npy")
        print(f"Población inicial tomada de {origen}")
    resumen = train(cfg, args.especie, args.escenario, run_dir, processes=args.procesos,
                    init_population=init, desde=args.desde)
    print(f"\nListo en {resumen['segundos_totales']} s. Modelo y registros en {run_dir}")
    print(f"Fitness de validación del modelo final: {resumen['fitness_validacion_del_modelo_final']:.3f}")


if __name__ == "__main__":
    main()