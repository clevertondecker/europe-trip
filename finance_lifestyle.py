"""Lifestyle budgeting: replace allocated French dining spend, never double count it."""
from __future__ import annotations
from dataclasses import dataclass

FRENCH_BUDGET = {
    "60k": {"rent": 9650, "groceries": 7785, "dining": 2895,
            "transport": 1029, "excursions": 2300, "french_days": 55},
    "70k": {"rent": 10937, "groceries": 8878, "dining": 4954,
            "transport": 1158, "excursions": 3500, "french_days": 60},
}
# Components originated in the historical Drive workbook, NOT real confirmed 2027 quotes.
SOURCE_URL = "https://drive.google.com/file/d/1_PgDDM-wPR5hlUyTRjdpxAwrnE0hhaqu/view"

def audit_subtotals() -> dict[str, dict]:
    return {
        key: {
            "french_subtotal": sum(record[k] for k in
                ("rent", "groceries", "dining", "transport", "excursions")),
            "dining_per_week_brl": record["dining"] / (record["french_days"] / 7),
        }
        for key, record in FRENCH_BUDGET.items()
    }

def lifestyle_outcome(
    scenario: dict, scenario_id: str, outings_per_week: float,
    outing_eur_couple: float, eur_brl: float,
    extra_excursions_brl: float = 0,
    extra_flights_brl: float = 0,
    extra_lodging_brl: float = 0,
) -> dict:
    """Compare a chosen dining lifestyle against the original dining allowance.

    The allocated dining allowance is ALREADY included in total. We replace it
    with simulated spending, then add only true overruns beyond other categories.
    Emergency reserve remains committed in the original total.
    """
    if scenario_id not in FRENCH_BUDGET:
        raise ValueError("Cenário de viagem inválido")
    values = (outings_per_week, outing_eur_couple, eur_brl,
              extra_excursions_brl, extra_flights_brl, extra_lodging_brl)
    if not all(isinstance(value, (int, float)) for value in values):
        raise ValueError("Valores devem ser numéricos")
    if any(value < 0 for value in values) or eur_brl <= 0:
        raise ValueError("Valores negativos ou câmbio zero são inválidos")
    if outings_per_week > 7:
        raise ValueError("Máximo de sete saídas por semana nesta simulação")
    french = FRENCH_BUDGET[scenario_id]
    weeks = french["french_days"] / 7
    total_outings = outings_per_week * weeks
    simulated_dining = round(total_outings * outing_eur_couple * eur_brl, 2)
    dining_delta = round(simulated_dining - french["dining"], 2)
    extras = round(extra_excursions_brl + extra_flights_brl + extra_lodging_brl, 2)
    total = round(scenario["reported_total_brl"] + dining_delta + extras, 2)
    remaining = round(scenario["cap_brl"] - total, 2)
    reserve = scenario["emergency_reserve_brl"]
    return {
        "weeks": weeks,
        "outings": round(total_outings, 1),
        "dining_allocated_brl": french["dining"],
        "dining_per_week_brl": round(french["dining"] / weeks, 2),
        "dining_simulated_brl": simulated_dining,
        "dining_delta_brl": dining_delta,
        "extra_brl": extras,
        "new_total_brl": total,
        "remaining_brl": remaining,
        "emergency_reserve_in_total_brl": reserve,
        "within_cap": remaining >= 0,
        "headroom_5pct_brl": round(scenario["cap_brl"] * 0.05, 2),
        "meets_headroom_5pct": remaining >= scenario["cap_brl"] * 0.05,
        "maximum_outings_at_spend":
            0 if outing_eur_couple == 0 else round(
                french["dining"] / (weeks * outing_eur_couple * eur_brl), 2),
    }
