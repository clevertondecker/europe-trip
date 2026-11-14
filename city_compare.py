"""Pure comparison functions for historical editorial French base-city scores."""
from __future__ import annotations
from pathlib import Path
import json
from math import isfinite
from typing import Any

DATA_PATH = Path(__file__).resolve().parent / "data" / "cities_france_2026.json"

def load_cities(path: Path = DATA_PATH) -> dict[str, Any]:
    content = json.loads(path.read_text(encoding="utf-8"))
    criteria = {item["id"] for item in content["criteria"]}
    if len(criteria) != 6 or len(content["cities"]) < 4:
        raise ValueError("Matriz de comparação histórica incompleta")
    for city in content["cities"]:
        if set(city["scores"]) != criteria or not all(0 <= float(x) <= 5 for x in city["scores"].values()):
            raise ValueError("Notas editoriais inválidas")
    return content

def normalized_weights(weights: dict[str, float], criteria: list[str]) -> dict[str, float]:
    """Normalize non-negative weights to a sum of 1; zero total is deliberately invalid."""
    if set(weights) != set(criteria):
        raise ValueError("Critérios e pesos devem corresponder")
    if not all(isfinite(float(v)) and float(v) >= 0 for v in weights.values()):
        raise ValueError("Pesos devem ser finitos e não negativos")
    total = sum(float(weights[key]) for key in criteria)
    if total <= 0:
        raise ValueError("Ao menos um critério precisa ter peso maior que zero")
    return {key: float(weights[key]) / total for key in criteria}

def score_city(city: dict[str, Any], weights: dict[str, float]) -> float:
    return sum(float(city["scores"][key]) * fraction for key, fraction in weights.items())

def rank_cities(cities: list[dict[str, Any]], weights: dict[str, float],
                criteria: list[str]) -> list[dict[str, Any]]:
    normalized = normalized_weights(weights, criteria)
    ranked = [
        {"city": dict(city), "score": score_city(city, normalized)}
        for city in cities
    ]
    return sorted(ranked, key=lambda row: (-row["score"], row["city"]["name"].casefold()))

def get_preset(data: dict[str, Any], preset_id: str) -> dict[str, float]:
    matches = [preset["weights"] for preset in data["presets"] if preset["id"] == preset_id]
    if len(matches) != 1:
        raise ValueError("Perfil não encontrado")
    return dict(matches[0])
