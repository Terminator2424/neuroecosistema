"""Fase 5: ¿qué aprendieron las redes? Mide comportamientos en episodios de desarrollo.

Usa semillas de desarrollo (2000 en adelante), no las de evaluación final.

Mide tres cosas de las presas: qué tan rápido se mueven, cuánto tiempo pasan cerca de las
paredes y qué tan lejos se mantienen del depredador. Para comprobar las funciones:

    python experiments/analizar_comportamiento.py --verificar

Cuando las 3 pasen, corre el análisis completo:

    python experiments/analizar_comportamiento.py --n 10

Las trayectorias son arreglos de NumPy: pos tiene forma (T, n, 2) con T pasos, n agentes y
las coordenadas x, y; vivo tiene forma (T, n) con True si el agente estaba vivo en ese paso.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from neuroeco.config import load_scenario
from neuroeco.controllers import make_predator_controller, make_prey_controller
from neuroeco.network import load_neural_controller
from neuroeco.runner import run_episode


def grabar_episodio(cfg, prey_c, pred_c, seed):
    """Corre un episodio y guarda la trayectoria de cada paso.

    Devuelve un diccionario con prey_pos (T, n_presas, 2), prey_alive (T, n_presas),
    pred_pos (T, n_depredadores, 2) y pred_alive (T, n_depredadores).
    """
    hist = {"prey_pos": [], "prey_alive": [], "pred_pos": [], "pred_alive": []}

    def guardar(w):
        hist["prey_pos"].append(w.prey_pos.copy())
        hist["prey_alive"].append(w.prey_alive.copy())
        hist["pred_pos"].append(w.pred_pos.copy())
        hist["pred_alive"].append(w.pred_alive.copy())

    run_episode(cfg, prey_c, pred_c, seed, callback=guardar)
    return {k: np.array(v) for k, v in hist.items()}


def velocidad_media(pos, vivo):
    """Velocidad media (píxeles por paso) de los agentes.

    Cuenta solo los agentes que estaban vivos en el paso t y en el t+1 (un agente muerto
    no se mueve; su posición no cuenta).
    Cómo: np.diff(pos, axis=0) da el desplazamiento entre pasos; la distancia de cada
    desplazamiento es np.hypot(dx, dy); la máscara es vivo[1:] & vivo[:-1].
    Devuelve un float (o float('nan') si no hay datos).
    """
    d = np.diff(pos, axis=0)
    v = np.hypot(d[..., 0], d[..., 1])
    m = vivo[1:] & vivo[:-1]
    return float(v[m].mean()) if m.any() else float("nan")


def fraccion_cerca_de_paredes(pos, vivo, ancho, alto, margen=40):
    """Fracción de (agente, paso) vivos que están a menos de `margen` píxeles de una pared.

    Una posición está cerca de una pared si x < margen, x > ancho - margen, y < margen
    o y > alto - margen.
    Cómo: construye un arreglo booleano `cerca` con esas 4 condiciones unidas con |
    y promedia solo donde vivo es True: cerca[vivo].mean().
    """
    x, y = pos[..., 0], pos[..., 1]
    cerca = (x < margen) | (x > ancho - margen) | (y < margen) | (y > alto - margen)
    return float(cerca[vivo].mean()) if vivo.any() else float("nan")


def distancia_media_al_depredador(pos_presa, vivo_presa, pos_dep, vivo_dep):
    """Distancia media de las presas vivas al depredador vivo más cercano.

    En cada paso, para cada presa viva, toma la distancia al depredador VIVO más cercano.
    Los pasos en que no queda ningún depredador vivo no cuentan.
    Cómo: dif = pos_presa[:, :, None, :] - pos_dep[:, None, :, :] tiene forma (T, n, m, 2);
    con np.hypot sacas las distancias; pon np.inf donde el depredador no esté vivo
    (vivo_dep[:, None, :]); el más cercano es el mínimo sobre el eje 2; descarta los inf.
    """
    dif = pos_presa[:, :, None, :] - pos_dep[:, None, :, :]
    dist = np.hypot(dif[..., 0], dif[..., 1])
    dist = np.where(vivo_dep[:, None, :], dist, np.inf)
    cerca = dist.min(axis=2)
    ok = vivo_presa & np.isfinite(cerca)
    return float(cerca[ok].mean()) if ok.any() else float("nan")


def verificar():
    """Comprueba las 3 funciones con casos pequeños donde la respuesta se sabe."""
    fallos = []

    def caso(nombre, fn):
        try:
            fn()
            print(f"  [BIEN] {nombre}")
        except NotImplementedError:
            fallos.append(nombre)
            print(f"  [PENDIENTE] {nombre}")
        except AssertionError as e:
            fallos.append(nombre)
            print(f"  [MAL] {nombre}: {e}")

    def t1():
        pos = np.array([[[0, 0]], [[3, 0]], [[6, 0]], [[9, 0]]], float)
        assert abs(velocidad_media(pos, np.ones((4, 1), bool)) - 3.0) < 1e-9, "una presa a 3 px por paso debe dar 3.0"
        pos2 = np.array([[[0, 0]], [[3, 0]], [[100, 0]], [[200, 0]]], float)
        vivo2 = np.array([[1], [1], [0], [0]], bool)
        assert abs(velocidad_media(pos2, vivo2) - 3.0) < 1e-9, "después de morir no debe contar el movimiento"

    def t2():
        p = np.array([[[50, 50]], [[5, 50]], [[95, 50]], [[50, 50]]], float)
        r = fraccion_cerca_de_paredes(p, np.ones((4, 1), bool), 100, 100, margen=10)
        assert abs(r - 0.5) < 1e-9, f"2 de 4 pasos están cerca de una pared; diste {r}"
        r = fraccion_cerca_de_paredes(p, np.array([[1], [1], [0], [0]], bool), 100, 100, margen=10)
        assert abs(r - 0.5) < 1e-9, f"con la presa muerta en los pasos 3 y 4 solo cuentan los 2 primeros; diste {r}"

    def t3():
        pp = np.zeros((2, 1, 2))
        pd_ = np.array([[[3, 4], [100, 0]], [[3, 4], [100, 0]]], float)
        vd = np.array([[1, 1], [0, 1]], bool)
        r = distancia_media_al_depredador(pp, np.ones((2, 1), bool), pd_, vd)
        assert abs(r - 52.5) < 1e-9, f"paso 1: el más cercano está a 5; paso 2: el vivo más cercano está a 100; media 52.5; diste {r}"

    caso("velocidad_media", t1)
    caso("fraccion_cerca_de_paredes", t2)
    caso("distancia_media_al_depredador", t3)
    if fallos:
        print("\nTodavía hay funciones por arreglar.")
    else:
        print("\nTodo bien: ya puedes correr el análisis completo.")
    return not fallos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verificar", action="store_true", help="comprueba las funciones y termina")
    ap.add_argument("--n", type=int, default=10, help="semillas de desarrollo por condición")
    ap.add_argument("--inicio", type=int, default=2000)
    ap.add_argument("--escenario", default="A", choices=["A", "B", "C"])
    ap.add_argument("--oponente", default="perseguidor", choices=["perseguidor", "interceptor"])
    ap.add_argument("--presa-base", default="models/presa_A_base")
    ap.add_argument("--presa-pequena", default="models/presa_A_pequena")
    ap.add_argument("--presa-grande", default="models/presa_A_grande")
    args = ap.parse_args()

    if args.verificar:
        sys.exit(0 if verificar() else 1)

    cfg = load_scenario(args.escenario)
    pred_c = make_predator_controller(args.oponente, cfg)
    condiciones = [("aleatoria", make_prey_controller("aleatorio", cfg)),
                   ("reglas", make_prey_controller("reglas", cfg))]
    for nombre, ruta in (("red_entrenada", args.presa_base), ("red_pequena", args.presa_pequena),
                         ("red_grande", args.presa_grande)):
        if (ROOT / ruta).exists():
            condiciones.append((nombre, load_neural_controller(ROOT / ruta, "presa", cfg)))

    filas = []
    for nombre, prey_c in condiciones:
        for s in range(args.inicio, args.inicio + args.n):
            h = grabar_episodio(cfg, prey_c, pred_c, s)
            filas.append({
                "condicion": nombre, "semilla": s,
                "presas_vivas_al_final": int(h["prey_alive"][-1].sum()),
                "velocidad_media": velocidad_media(h["prey_pos"], h["prey_alive"]),
                "fraccion_cerca_de_paredes": fraccion_cerca_de_paredes(h["prey_pos"], h["prey_alive"], cfg["world"]["width"], cfg["world"]["height"]),
                "distancia_al_depredador": distancia_media_al_depredador(h["prey_pos"], h["prey_alive"], h["pred_pos"], h["pred_alive"]),
            })
        print(f"{nombre} listo", flush=True)

    df = pd.DataFrame(filas)
    salida = ROOT / "results" / "fase5"
    salida.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida / "comportamiento_presa.csv", index=False)
    resumen = df.groupby("condicion").agg(["mean", "std"]).drop(columns="semilla").round(2)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)
    print(f"\nComportamiento de las presas (escenario {args.escenario}, oponente {args.oponente}, semillas {args.inicio} a {args.inicio + args.n - 1}):\n")
    print(resumen.to_string())
    print(f"\nDatos por episodio en {salida / 'comportamiento_presa.csv'}")


if __name__ == "__main__":
    main()