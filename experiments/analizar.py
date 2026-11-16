"""Análisis de la Fase 4: tablas, pruebas estadísticas y figuras a partir de results/fase4/episodios.csv.

Los criterios de cada hipótesis están definidos abajo en COMPARACIONES y coinciden
con docs/hipotesis.md. La columna "veredicto" aplica ese criterio de forma
automática; la interpretación (por qué pasó lo que pasó) es trabajo del informe.

    python experiments/analizar.py
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from neuroeco.estadistica import holm, mean_ci95, paired_comparison

LLAVES = ["experimento", "escenario", "oponente", "condicion", "semilla"]
ETIQUETAS = {
    "aleatoria": "aleatoria", "aleatorio": "aleatorio", "reglas": "por reglas",
    "perseguidor": "perseguidor", "interceptor": "interceptor",
    "red_sin_entrenar": "red sin\nentrenar", "red_entrenada": "red\nentrenada",
    "red_pequena": "red\npequeña", "red_grande": "red\ngrande", "red_vs_red": "red vs red",
}


# ------------------------------------------------------------------ reglas de decisión
def mejora(d_min, alfa):
    return lambda r: r["diferencia"] >= d_min and r["p_holm"] < alfa


def positiva(alfa):
    return lambda r: r["diferencia"] > 0 and r["p_holm"] < alfa


def no_supera():
    return lambda r: r["diferencia"] <= 0 or r["p_holm"] >= 0.05


def equivalencia(delta):
    return lambda r: r["ic95_inf"] >= -delta and r["ic95_sup"] <= delta


COMPARACIONES = []


def comp(hid, familia, tipo, exp, esc, opp, metrica, a, b, criterio, regla):
    COMPARACIONES.append(dict(id=hid, familia=familia, tipo=tipo, experimento=exp, escenario=esc,
                              oponente=opp, metrica=metrica, a=a, b=b, criterio=criterio, regla=regla))


# H1: antes y después del entrenamiento
comp("H1a", "H1", "confirmatoria", "presa", "A", "perseguidor", "fitness_presa", "red_entrenada", "red_sin_entrenar",
     "diferencia de fitness >= 0.20 y p ajustado < 0.01", mejora(0.20, 0.01))
comp("H1b", "H1", "confirmatoria", "depredador", "A", "reglas", "fitness_depredador", "red_entrenada", "red_sin_entrenar",
     "diferencia de fitness >= 0.20 y p ajustado < 0.01", mejora(0.20, 0.01))
# H2: arquitectura
comp("H2a", "H2", "confirmatoria", "presa", "A", "perseguidor", "fitness_presa", "red_grande", "red_entrenada",
     "la red grande no supera a la base (diferencia <= 0 o p ajustado >= 0.05)", no_supera())
comp("H2b", "H2", "confirmatoria", "presa", "A", "perseguidor", "fitness_presa", "red_pequena", "red_entrenada",
     "IC 95 % de la diferencia dentro de +-0.05", equivalencia(0.05))
# H3: red contra agentes de referencia
comp("H3a1", "H3", "confirmatoria", "presa", "A", "perseguidor", "fitness_presa", "red_entrenada", "reglas",
     "diferencia >= 0.05 y p ajustado < 0.05", mejora(0.05, 0.05))
comp("H3a2", "H3", "confirmatoria", "presa", "A", "perseguidor", "fitness_presa", "red_entrenada", "aleatoria",
     "diferencia >= 0.30 y p ajustado < 0.01", mejora(0.30, 0.01))
comp("H3b1", "H3", "confirmatoria", "depredador", "A", "reglas", "fitness_depredador", "red_entrenada", "aleatorio",
     "diferencia >= 0.30 y p ajustado < 0.01", mejora(0.30, 0.01))
comp("H3b2", "H3", "confirmatoria", "depredador", "A", "reglas", "fitness_depredador", "red_entrenada", "perseguidor",
     "equivalencia: IC 95 % de la diferencia dentro de +-0.08", equivalencia(0.08))
comp("H3b3", "H3", "confirmatoria", "depredador", "A", "reglas", "fitness_depredador", "red_entrenada", "interceptor",
     "diferencia > 0 y p ajustado < 0.05", positiva(0.05))
# H4: generalización (modelos entrenados solo en A)
for esc in "BC":
    comp(f"H4-presa-{esc}", "H4", "confirmatoria", "presa", esc, "perseguidor", "fitness_presa", "red_entrenada", "aleatoria",
         "diferencia > 0 y p ajustado < 0.05", positiva(0.05))
for esc in "ABC":
    comp(f"H4-presa-{esc}-int", "H4", "confirmatoria", "presa", esc, "interceptor", "fitness_presa", "red_entrenada", "aleatoria",
         "diferencia > 0 y p ajustado < 0.05 (oponente no visto en el entrenamiento)", positiva(0.05))
for esc in "BC":
    comp(f"H4-depre-{esc}", "H4", "confirmatoria", "depredador", esc, "reglas", "fitness_depredador", "red_entrenada", "aleatorio",
         "diferencia > 0 y p ajustado < 0.05", positiva(0.05))
# Exploratorias (sin hipótesis previa)
for esc in "ABC":
    for opp in ("perseguidor", "interceptor"):
        if not (esc == "A" and opp == "perseguidor"):
            comp(f"E-presa-reglas-{esc}-{opp[:4]}", "E", "exploratoria", "presa", esc, opp, "fitness_presa",
                 "red_entrenada", "reglas", "descriptivo", None)
for esc in "BC":
    for ref in ("perseguidor", "interceptor"):
        comp(f"E-depre-{ref[:4]}-{esc}", "E", "exploratoria", "depredador", esc, "reglas", "fitness_depredador",
             "red_entrenada", ref, "descriptivo", None)


# ------------------------------------------------------------------ datos
def cargar(salida):
    df = pd.read_csv(salida / "episodios.csv")
    num = [c for c in df.select_dtypes("number").columns if c != "semilla"]
    # Las redes sin entrenar son 5 por condición: se promedian por semilla.
    return df.groupby(LLAVES, as_index=False)[num].mean()


def serie(df, exp, esc, opp, cond, metrica):
    sub = df[(df.experimento == exp) & (df.escenario == esc) & (df.oponente == opp) & (df.condicion == cond)]
    if sub.empty:
        return None
    return sub.set_index("semilla")[metrica].sort_index()


def resumen_condiciones(df):
    filas = []
    metricas = ["fitness_presa", "fitness_depredador", "prey_survival", "prey_alive_final", "food_eaten_per_prey",
                "captures_total", "pred_alive_final", "pred_final_energy"]
    for (exp, esc, opp, cond), g in df.groupby(["experimento", "escenario", "oponente", "condicion"]):
        fila = {"experimento": exp, "escenario": esc, "oponente": opp, "condicion": cond, "n": len(g)}
        for m in metricas:
            media, lo, hi = mean_ci95(g[m].dropna().values) if g[m].notna().any() else (np.nan, np.nan, np.nan)
            fila[f"{m}_media"] = media
            fila[f"{m}_sd"] = g[m].std(ddof=1)
            fila[f"{m}_ic95_inf"], fila[f"{m}_ic95_sup"] = lo, hi
        filas.append(fila)
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ comparaciones
def ejecutar_comparaciones(df):
    filas = []
    for c in COMPARACIONES:
        sa = serie(df, c["experimento"], c["escenario"], c["oponente"], c["a"], c["metrica"])
        sb = serie(df, c["experimento"], c["escenario"], c["oponente"], c["b"], c["metrica"])
        fila = {k: c[k] for k in ("id", "familia", "tipo", "experimento", "escenario", "oponente", "metrica", "a", "b", "criterio")}
        if sa is None or sb is None:
            fila["estado"] = "faltan datos"
            filas.append(fila)
            continue
        fila.update(paired_comparison(sa.values, sb.reindex(sa.index).values))
        fila["estado"] = "ok"
        filas.append(fila)
    res = pd.DataFrame(filas)
    res["p_holm"] = np.nan
    for fam, idx in res[res.estado == "ok"].groupby("familia").groups.items():
        res.loc[idx, "p_holm"] = holm(res.loc[idx, "p_wilcoxon"].values)
    veredictos = []
    for i, c in enumerate(COMPARACIONES):
        r = res.iloc[i]
        if r["estado"] != "ok":
            veredictos.append("faltan datos")
        elif c["regla"] is None:
            veredictos.append("exploratoria")
        else:
            veredictos.append("CUMPLE" if c["regla"](r) else "NO CUMPLE")
    res["veredicto"] = veredictos
    return res


def escribir_md(res, salida):
    lineas = ["# Resultados de las hipótesis (generado por experiments/analizar.py)", "",
              "| ID | Comparación | Criterio | Diferencia [IC 95 %] | p de Wilcoxon (ajustado) | Veredicto |",
              "|----|-------------|----------|----------------------|--------------------------|-----------|"]
    for _, r in res[res.tipo == "confirmatoria"].iterrows():
        if r["estado"] != "ok":
            lineas.append(f"| {r['id']} | {r['a']} frente a {r['b']} ({r['escenario']}, {r['oponente']}) | {r['criterio']} | sin datos | | faltan datos |")
            continue
        lineas.append(f"| {r['id']} | {r['a']} frente a {r['b']} (escenario {r['escenario']}, oponente {r['oponente']}, {r['metrica']}) | "
                      f"{r['criterio']} | {r['diferencia']:.3f} [{r['ic95_inf']:.3f}; {r['ic95_sup']:.3f}] | "
                      f"{r['p_wilcoxon']:.2g} ({r['p_holm']:.2g}) | {r['veredicto']} |")
    (salida / "hipotesis_resultados.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ figuras
def fig_curvas(modelos, salida):
    existentes = [(n, ROOT / p) for n, p in modelos if (ROOT / p / "history.csv").exists()]
    if not existentes:
        return
    fig, axs = plt.subplots(1, len(existentes), figsize=(5 * len(existentes), 3.8), squeeze=False)
    for ax, (nombre, ruta) in zip(axs[0], existentes):
        h = pd.read_csv(ruta / "history.csv")
        ax.plot(h["generacion"], h["mejor"], label="mejor")
        ax.plot(h["generacion"], h["media"], label="media")
        ax.fill_between(h["generacion"], h["media"] - h["desviacion"], h["media"] + h["desviacion"], alpha=0.2)
        ax.set_title(nombre)
        ax.set_xlabel("generación")
        ax.set_ylabel("fitness")
        ax.legend()
    fig.tight_layout()
    fig.savefig(salida / "curvas_aprendizaje.png", dpi=150)
    plt.close(fig)


def fig_cajas(df, exp, opp, metrica, conds, titulo, archivo, salida, ylabel):
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for ax, esc in zip(axs, "ABC"):
        datos, etiquetas = [], []
        for cond in conds:
            s = serie(df, exp, esc, opp, cond, metrica)
            if s is not None:
                datos.append(s.dropna().values)
                etiquetas.append(ETIQUETAS.get(cond, cond))
        if datos:
            ax.boxplot(datos, showmeans=True)
            ax.set_xticks(range(1, len(etiquetas) + 1), etiquetas, fontsize=8)
        ax.set_title(f"Escenario {esc}")
        ax.grid(axis="y", alpha=0.3)
    axs[0].set_ylabel(ylabel)
    fig.suptitle(titulo)
    fig.tight_layout()
    fig.savefig(salida / archivo, dpi=150)
    plt.close(fig)


def fig_bosque(res, salida):
    r = res[(res.tipo == "confirmatoria") & (res.estado == "ok")].reset_index(drop=True)
    if r.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(r) + 1.5))
    y = np.arange(len(r))[::-1]
    ax.errorbar(r["diferencia"], y, xerr=[r["diferencia"] - r["ic95_inf"], r["ic95_sup"] - r["diferencia"]], fmt="o", capsize=3)
    ax.axvline(0, color="gray", lw=1)
    ax.set_yticks(y, [f"{i}  ({a} vs {b})" for i, a, b in zip(r["id"], r["a"], r["b"])], fontsize=7)
    ax.set_xlabel("diferencia de fitness (media pareada e IC 95 %)")
    fig.tight_layout()
    fig.savefig(salida / "diferencias_pareadas.png", dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="results/fase4")
    ap.add_argument("--presa-base", default="models/presa_A_base")
    ap.add_argument("--depre-etapa1", default="models/depre_A_etapa1")
    ap.add_argument("--depre-base", default="models/depre_A_base")
    args = ap.parse_args()
    salida = ROOT / args.salida

    df = cargar(salida)
    resumen = resumen_condiciones(df)
    resumen.to_csv(salida / "resumen_condiciones.csv", index=False)
    res = ejecutar_comparaciones(df)
    res.drop(columns=["criterio"]).to_csv(salida / "comparaciones.csv", index=False)
    escribir_md(res, salida)

    cols = ["id", "escenario", "oponente", "a", "b", "diferencia", "ic95_inf", "ic95_sup", "p_wilcoxon", "p_holm", "veredicto"]
    pd.set_option("display.width", 250, "display.max_columns", None, "display.max_colwidth", 30)
    print("\n=== Hipótesis confirmatorias ===\n")
    print(res[res.tipo == "confirmatoria"][cols].round(4).to_string(index=False))
    print("\n=== Comparaciones exploratorias (sin hipótesis previa) ===\n")
    print(res[res.tipo == "exploratoria"][cols].drop(columns=["veredicto"]).round(4).to_string(index=False))
    print("\n=== Media de fitness por condición ===\n")
    for exp, met in (("presa", "fitness_presa"), ("depredador", "fitness_depredador")):
        t = resumen[resumen.experimento == exp][["escenario", "oponente", "condicion", f"{met}_media", f"{met}_sd"]]
        print(f"[{exp}] {met}")
        print(t.round(3).to_string(index=False))
        print()

    prey_conds = ["aleatoria", "red_sin_entrenar", "reglas", "red_entrenada", "red_pequena", "red_grande"]
    pred_conds = ["aleatorio", "red_sin_entrenar", "interceptor", "perseguidor", "red_entrenada"]
    fig_curvas([("Presa (contra perseguidor)", args.presa_base), ("Depredador etapa 1 (contra presa aleatoria)", args.depre_etapa1),
                ("Depredador etapa 2 (contra presa por reglas)", args.depre_base)], salida)
    fig_cajas(df, "presa", "perseguidor", "fitness_presa", prey_conds, "Presas contra el perseguidor", "presa_fitness_perseguidor.png", salida, "fitness de la presa")
    fig_cajas(df, "presa", "interceptor", "fitness_presa", prey_conds, "Presas contra el interceptor (oponente no visto)", "presa_fitness_interceptor.png", salida, "fitness de la presa")
    fig_cajas(df, "depredador", "reglas", "fitness_depredador", pred_conds, "Depredadores contra la presa por reglas", "depredador_fitness.png", salida, "fitness del depredador")
    fig_cajas(df, "depredador", "reglas", "captures_total", pred_conds, "Capturas de los depredadores", "depredador_capturas.png", salida, "capturas por episodio")
    fig_bosque(res, salida)
    print(f"Tablas y figuras guardadas en {salida}")


if __name__ == "__main__":
    main()