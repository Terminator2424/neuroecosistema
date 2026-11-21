"""Completa las columnas Resultado y ¿Se cumplió? de docs/hipotesis.md con los datos de
results/fase4/comparaciones.csv. No toca las hipótesis ni los criterios.

    python experiments/completar_hipotesis.py
"""
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "hipotesis.md"
CSV_PATH = ROOT / "results" / "fase4" / "comparaciones.csv"
NOTA = ("Resultados completados con experiments/completar_hipotesis.py a partir de "
        "results/fase4/comparaciones.csv. Las hipótesis y sus criterios no se modificaron.")


def coma(x, signo=False):
    s = f"{x:+.3f}" if signo else f"{x:.3f}"
    return s.replace(".", ",").replace("-", "−")


def p_txt(p):
    return "< ,001" if p < 0.001 else "= " + f"{p:.3f}".replace("0.", ",", 1)


def completar_fila(celdas, df):
    """Rellena las dos últimas celdas de una fila de la tabla. Devuelve True si pudo."""
    hid = celdas[0]
    if hid == "H4":
        g = df[df["id"].str.startswith("H4-")]
        n_ok = int((g["veredicto"] == "CUMPLE").sum())
        celdas[6] = (f"{len(g)} pruebas; diferencias de {coma(g['diferencia'].min())} a "
                     f"{coma(g['diferencia'].max())}; p ajustado máximo {p_txt(g['p_holm'].max())}")
        celdas[7] = f"Sí ({n_ok} de {len(g)})" if n_ok == len(g) else f"Parcial ({n_ok} de {len(g)})"
        return True
    r = df[df["id"] == hid]
    if len(r) != 1:
        return False
    r = r.iloc[0]
    celdas[6] = (f"Diferencia {coma(r['diferencia'], True)} [IC 95 %: {coma(r['ic95_inf'])}; "
                 f"{coma(r['ic95_sup'])}]; p ajustado {p_txt(r['p_holm'])}")
    celdas[7] = "Sí" if r["veredicto"] == "CUMPLE" else "No"
    return True


def completar():
    df = pd.read_csv(CSV_PATH)
    salida, hechas = [], 0
    for linea in MD_PATH.read_text(encoding="utf-8").split("\n"):
        if linea.startswith("| H") and not linea.startswith("| ID"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if len(celdas) == 8 and completar_fila(celdas, df):
                linea = "| " + " | ".join(celdas) + " |"
                hechas += 1
        salida.append(linea)
    texto = "\n".join(salida)
    if NOTA not in texto:
        texto = texto.rstrip("\n") + f"\n\n{NOTA} Fecha: {date.today().isoformat()}.\n"
    MD_PATH.write_text(texto, encoding="utf-8")
    return hechas


def main():
    if not CSV_PATH.exists():
        sys.exit(f"No existe {CSV_PATH}: primero corre experiments/analizar.py")
    print(f"Filas de hipótesis completadas: {completar()} de 10 (revisa docs/hipotesis.md)")


if __name__ == "__main__":
    main()