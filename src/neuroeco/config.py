"""Carga y combinación de configuraciones YAML."""
import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def merge_config(base, over):
    """Combina dos diccionarios de forma recursiva sin modificar los originales."""
    out = copy.deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_config(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(*paths):
    """Carga uno o más YAML en orden; los últimos sobrescriben a los primeros.

    Las rutas relativas se resuelven desde la raíz del proyecto.
    """
    cfg = {}
    for p in paths:
        p = Path(p)
        if not p.is_absolute():
            p = ROOT / p
        with open(p, encoding="utf-8") as f:
            cfg = merge_config(cfg, yaml.safe_load(f) or {})
    return cfg


def load_scenario(name="A"):
    """Configuración base más el escenario A, B o C."""
    return load_config("configs/base.yaml", f"configs/escenarios/{name.upper()}.yaml")