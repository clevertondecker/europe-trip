"""DQ3.0: read-only provenance validation for the 2026 mobility pilot.

Never infer walking routes, date-specific weekend feasibility, or 2027 fares.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
import json

DEFAULT = Path(__file__).resolve().parent / "data" / "dq30_mobility_pilot_2026_11.json"


def load_mobility_pilot(path: Path = DEFAULT) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_mobility_pilot(data)
    return deepcopy(data)


def validate_mobility_pilot(data: dict) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("Schema DQ3.0 incompatível")
    date.fromisoformat(data["checked_at"])
    if data.get("2027_return_verified") is not False:
        raise ValueError("Não inferir retorno de 2027")
    seen = set()
    for record in data["rail_service_observations"]:
        key = (record["origin_id"], record["destination_id"],
               record["observation_date"], record["departure_local"], record["service"])
        if key in seen:
            raise ValueError("Observação ferroviária duplicada")
        seen.add(key)
        date.fromisoformat(record["observation_date"])
        if not record["source_url"].startswith("https://"):
            raise ValueError("Observação sem fonte")
        if record["duration_min"] <= 0 or type(record["duration_min"]) is not int:
            raise ValueError("Duração ferroviária inválida")
        if record["return_verified"] or record["valid_for_2027"]:
            raise ValueError("Referência de 2026 não comprova retorno ou 2027")
        if record["last_mile_min"] is not None:
            raise ValueError("Última milha não pesquisada")
        fare = record["fare_from_eur_person_oneway"]
        if fare is not None and (fare <= 0 or record["fare_kind"] != "advertised_from_conditional"):
            raise ValueError("Tarifa 'desde' deve permanecer condicional")
    for record in data["operator_route_summaries"]:
        if not record["source_url"].startswith("https://"):
            raise ValueError("Resumo de rota sem fonte")
        if record["return_verified"] or record["valid_for_2027"]:
            raise ValueError("Resumo não comprova viagem futura")
        if record["last_mile_min"] is not None:
            raise ValueError("Resumo não comprova última milha")
        if (record["minimum_oneway_min"] is None and
                record["typical_oneway_min"] is None):
            raise ValueError("Resumo sem observação")
    for record in data["attraction_access"]:
        if not record["source_url"].startswith("https://") or not record["public_access_point"]:
            raise ValueError("Acesso sem fonte ou endereço")
        if record["coordinates"] is not None:
            raise ValueError("Coordenadas não pesquisadas no piloto")
        if record["walk_distance_m"] is not None or record["walk_duration_min"] is not None:
            raise ValueError("Caminhada sem roteamento autorizado")
    for record in data["access_reference_not_canonical_attraction"]:
        if record["attraction_id"] is not None:
            raise ValueError("Não inventar ID canônico para referência exploratória")


def access_by_attraction(data: dict, attraction_id: str) -> dict | None:
    """Read-only lookup of canonical-attraction references without geocoding."""
    row = next((r for r in data["attraction_access"]
                if r["attraction_id"] == attraction_id), None)
    return deepcopy(row) if row else None
