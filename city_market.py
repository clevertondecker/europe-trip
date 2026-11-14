"""Read and validate observed-market data, separate from 2027 quotes and 2026 editorial rankings."""
from __future__ import annotations
import json
from pathlib import Path
from statistics import median

DATA_FILE = Path(__file__).resolve().parent / "data" / "city_market_observations_2026.json"

def validate_market(data: dict) -> None:
    if not 55 <= data["planned_nights_min"] <= data["planned_nights_max"] <= 75:
        raise ValueError("Janela planejada inválida")
    if data["travelers"] != 2 or len(data["cities"]) != 4:
        raise ValueError("Escopo das cidades ou de viajantes inválido")
    ids = set()
    for city in data["cities"]:
        if city["id"] in ids:
            raise ValueError("Cidade duplicada")
        ids.add(city["id"])
        if len(city["offers"]) < 3 or len(city["rail"]) < 2:
            raise ValueError("Dados insuficientes de anúncios ou linhas de trem")
        if city["rental_quote_eligible_2027"] != 0:
            raise ValueError("Cotações reais requerem verificação separada")
        for offer in city["offers"]:
            if (offer["observed_eur_month"] <= 0 or offer["size_m2"] <= 0
                or offer["quote_for_2027"] or offer["total_stay_eur"] is not None
                or offer["contract_confirmed"] or offer["two_occupants_confirmed"]
                or offer["internet_verified"]):
                raise ValueError("Preço observado não pode ser convertido em cotação")
            if offer["source_url"] != city["housing_catalogue"] or not offer["source_url"].startswith("https://"):
                raise ValueError("Proveniência de anúncios ausente")
        pass_info = city["urban_pass"]
        if pass_info["fare_eur_month_person"] <= 0 or not pass_info["source_url"].startswith("https://"):
            raise ValueError("Passe local inválido")
        for route in city["rail"]:
            if route["train_minutes"] <= 0 or not route["source_url"].startswith("https://"):
                raise ValueError("Fonte ferroviária inválida")
            fare = route["discounted_eur_leg_person"]
            if fare is not None and fare <= 0:
                raise ValueError("Tarifa ferroviária inválida")
    if data["common_costs"]["city_specific"] is not False:
        raise ValueError("Cesta histórica compartilhada não deve virar diferencial de cidade")

def load_market(path: Path = DATA_FILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_market(data)
    return data

def observed_rent_summary(city: dict) -> dict:
    """Descriptive sample only, never total 60-night price or market average."""
    prices = sorted(float(o["observed_eur_month"]) for o in city["offers"])
    return {"sample_count": len(prices), "min_eur_month":prices[0],
            "max_eur_month":prices[-1], "sample_median_eur_month": median(prices)}

def example_train_couple_return(fare_eur_leg_person: float | None) -> float | None:
    """Conditional 2 travelers x 2 legs at advertised discounted per-leg tariff.

    No card ownership, dated fare, transfers or actual seats are implied.
    """
    return None if fare_eur_leg_person is None else round(fare_eur_leg_person * 4, 2)
