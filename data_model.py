"""Pure data and calculation helpers for the Streamlit travel dashboard."""
from __future__ import annotations

from formatting import brl, REQUIRED

import json
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parent / "data" / "trip.json"
STATUS_LABEL = {"roteiro_proposto": "Roteiro proposto", "candidata": "Em avaliação", "opcional": "Passeio possível"}
STATUS_COLORS = {"roteiro_proposto": [26, 98, 110, 210], "candidata": [192, 130, 65, 210], "opcional": [105, 127, 151, 190]}


def load_data(path: Path = DATA_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def money_brl(value: float | int) -> str:
    return brl(value, decimals=2, missing=REQUIRED)


def select_places(places: list[dict], countries: list[str] | None = None, statuses: list[str] | None = None) -> list[dict]:
    return [p for p in places if (not countries or p["country"] in countries) and (not statuses or p["status"] in statuses)]


def calculate_scenario(scenario: dict, rent_increase_eur: float = 0, charged_months: int = 2, eur_brl: float = 6.3) -> dict:
    """Hypothetical rent delta; not a replacement for formula-based spreadsheet scenario modeling."""
    if charged_months < 0 or eur_brl <= 0 or rent_increase_eur < 0:
        raise ValueError("Valores negativos não são válidos nesta simulação")
    change_brl = round(rent_increase_eur * charged_months * eur_brl, 2)
    new_total = scenario["reported_total_brl"] + change_brl
    subtotal = sum(item["amount"] for item in scenario["components"])
    return {"base": scenario["reported_total_brl"], "delta": change_brl, "total": new_total,
            "balance": round(scenario["cap_brl"] - new_total, 2), "component_sum": subtotal,
            "rounding_difference": round(scenario["reported_total_brl"] - subtotal, 2)}


def get_scenario(data: dict, scenario_id: str) -> dict:
    return next(s for s in data["budget_scenarios"] if s["id"] == scenario_id)