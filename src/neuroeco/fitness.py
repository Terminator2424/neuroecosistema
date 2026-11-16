"""Funciones de fitness (qué se premia en cada especie).

Todas devuelven un valor en [0, 1] a partir de las métricas de un episodio.
Variantes (configs/base.yaml, sección fitness) para poder compararlas después:
- presa: "mixta" (supervivencia y comida) o "supervivencia";
- depredador: "mixta" (capturas y energía final) o "capturas".
"""


def fitness_prey(metrics, cfg):
    f = cfg["fitness"]
    survival = metrics["prey_survival"]
    if f["variant_prey"] == "supervivencia":
        return float(survival)
    food = min(metrics["food_eaten_per_prey"] / float(f["prey_food_ref"]), 1.0)
    return float(f["prey_weight_survival"] * survival + f["prey_weight_food"] * food)


def fitness_predator(metrics, cfg):
    f = cfg["fitness"]
    captures = min(metrics["captures_total"] / float(cfg["prey"]["initial"]), 1.0)
    if f["variant_predator"] == "capturas":
        return float(captures)
    return float(f["predator_weight_captures"] * captures
                 + f["predator_weight_energy"] * metrics["pred_final_energy"])


def fitness_for(species, metrics, cfg):
    if species == "presa":
        return fitness_prey(metrics, cfg)
    if species == "depredador":
        return fitness_predator(metrics, cfg)
    raise ValueError(f"Especie desconocida: {species}")