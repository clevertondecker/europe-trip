"""Second-round evidence for France city research, deliberately separate from booking quotes."""
from __future__ import annotations
import json
from pathlib import Path

FILE = Path(__file__).resolve().parent / "data" / "city_research_round2_2026.json"

def validate_round2(data: dict) -> None:
    cities = data["cities"]
    ids = [c["id"] for c in cities]
    if len(cities) < 4 or len(ids) != len(set(ids)):
        raise ValueError("Cidades de pesquisa ausentes ou repetidas")
    required = {"mulhouse", "strasbourg", "metz", "nancy"}
    if not required.issubset(ids):
        raise ValueError("Comparação incompleta")
    sources = data["common_sources"]
    if not all(str(x["url"]).startswith("https://") for x in sources):
        raise ValueError("Fonte inválida")
    for city in cities:
        if city["residential_rent_eur_sqm_month"] <= 0:
            raise ValueError("Referência de aluguel inválida")
        if city["restaurant_two_midrange_eur"] <= 0:
            raise ValueError("Referência de restaurante inválida")
        if not city["restaurant_source_url"].startswith("https://"):
            raise ValueError("Fonte de restaurante inválida")
        place = city["coworking"]
        if not all(k in place for k in
                   ("name", "price_eur", "price_basis", "source_url", "source_type",
                    "schedule", "verified_2027", "late_work_compatible", "note")):
            raise ValueError("Coworking incompleto")
        if place["verified_2027"] is not False or place["price_eur"] <= 0:
            raise ValueError("Preço exploratório confundido com cotação de 2027")
        if not place["source_url"].startswith("https://"):
            raise ValueError("Fonte coworking inválida")
    if "2027" not in data["study"]:
        raise ValueError("Escopo temporal não identificado")

def load_round2(path: Path = FILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_round2(data)
    return data
