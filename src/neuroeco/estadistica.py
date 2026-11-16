"""Herramientas estadísticas para comparar condiciones con las mismas semillas (datos pareados)."""
import numpy as np
from scipy import stats


def holm(pvalues):
    """Corrección de Holm-Bonferroni: devuelve los p ajustados en el orden original."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adjusted = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adjusted[idx] = min(running, 1.0)
    return adjusted


def mean_ci95(x):
    """Media y su intervalo de confianza del 95 % (distribución t)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean = float(x.mean())
    if n < 2:
        return mean, float("nan"), float("nan")
    half = stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n)
    return mean, float(mean - half), float(mean + half)


def paired_comparison(a, b):
    """Compara dos condiciones medidas en las mismas semillas (a menos b).

    Devuelve la diferencia media con su IC del 95 %, el tamaño del efecto
    (d_z de Cohen y correlación biserial por rangos) y el p de Wilcoxon pareado.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("Las dos condiciones deben tener el mismo número de semillas")
    d = a - b
    n = len(d)
    mean, lo, hi = mean_ci95(d)
    sd = float(d.std(ddof=1)) if n > 1 else float("nan")
    dz = mean / sd if sd and sd > 0 else float("nan")
    nonzero = d[d != 0]
    if len(nonzero) == 0:
        p, rb = 1.0, 0.0
    else:
        p = float(stats.wilcoxon(nonzero).pvalue)
        ranks = stats.rankdata(np.abs(nonzero))
        rb = float((ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / ranks.sum())
    return {"n": n, "media_a": float(a.mean()), "media_b": float(b.mean()),
            "diferencia": mean, "ic95_inf": lo, "ic95_sup": hi,
            "d_z": float(dz), "rango_biserial": rb, "p_wilcoxon": p}