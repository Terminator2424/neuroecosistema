"""Completa las columnas Resultado y ¿Se cumplió? de docs/hipotesis.md con los datos de
results/fase4/comparaciones.csv. No toca las hipótesis ni los criterios.

    python experiments/completar_hipotesis.py
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import pandas as pd


def coma(x, signo=False):
    s = f"{x:+.3f}" if signo else f"{x:.3f}"
    return s.replace(".", ",").replace("-", "−")


def p_txt(p):
    return "< ,001" if p < 0.001 else "= " + f"{p:.3f}".replace("0.", ",", 1)


def completar(ruta_md, ruta_csv):
    df = pd.read_csv(ruta_csv)
    lineas = Path(ruta_md).read_text(encoding="utf-8").split("\n")
    salida, hechas = [], 0
    for linea in lineas:
        if linea.startswith("| H") and not linea.startswith("| ID"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            hid = celdas[0]
            if len(celdas) == 8:
                if hid == "H4":
                    g = df[df["id"].str.startswith("H4-")]
                    n_ok = int((g["veredicto"] == "CUMPLE").sum())
                    celdas[6] = (f"{len(g)} pruebas; diferencias de {coma(g['diferencia'].min())} a "
                                 f"{coma(g['diferencia'].max())}; p ajustado máximo {p_txt(g['p_holm'].max())}")
                    celdas[7] = f"Sí ({n_ok} de {len(g)})" if n_ok == len(g) else f"Parcial ({n_ok} de {len(g)})"
                else:
                    r = df[df["id"] == hid]
                    if len(r) == 1:
                        r = r.iloc[0]
                        celdas[6] = (f"Diferencia {coma(r['diferencia'], True)} [IC 95 %: {coma(r['ic95_inf'])}; "
                                     f"{coma(r['ic95_sup'])}]; p ajustado {p_txt(r['p_holm'])}")
                        celdas[7] = "Sí" if r["veredicto"] == "CUMPLE" else "No"
                    else:
                        salida.append(linea)
                        continue
                linea = "| " + " | ".join(celdas) + " |"
                hechas += 1
        salida.append(linea)
    texto = "\n".join(salida)
    nota = "Resultados completados con experiments/completar_hipotesis.py a partir de results/fase4/comparaciones.csv. Las hipótesis y sus criterios no se modificaron."
    if nota not in texto:
        texto = texto.rstrip("\n") + f"\n\n{nota} Fecha: {date.today().isoformat()}.\n"
    Path(ruta_md).write_text(texto, encoding="utf-8")
    return hechas


def main():
    ruta_md = ROOT / "docs" / "hipotesis.md"
    ruta_csv = ROOT / "results" / "fase4" / "comparaciones.csv"
    if not ruta_csv.exists():
        sys.exit(f"No existe {ruta_csv}: primero corre experiments/analizar.py")
    n = completar(ruta_md, ruta_csv)
    print(f"Filas de hipótesis completadas: {n} de 10 (revisa docs/hipotesis.md)")


if __name__ == "__main__":
    main()