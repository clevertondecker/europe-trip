"""DQ3.0 P2: provenance-aware, read-only access to attraction geography.

This is not a walking router. Missing walking geometry/distance stays unknown.
The canonical attraction catalog and DQ3.0 P1 historical pilot are unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from math import isfinite
from pathlib import Path
import json

DEFAULT = Path(__file__).resolve().parent / "data" / "dq30_walking_access_2026_11.json"
VALID_PRECISION = {"unknown", "attraction_point", "area_centroid", "entrance"}
VALID_DISTANCE_KINDS = {"walking_route", "straight_line", "rail_distance"}
VALID_MODES = {"walking", "rail", "public_transport"}
VALID_STATUS = {"operator_published_walk_duration", "pending_verified_pedestrian_route"}


def _geo(coordinates, precision, source_url, checked_at):
    if precision not in VALID_PRECISION:
        raise ValueError("Precisão geográfica inválida")
    if coordinates is None:
        if precision != "unknown" or source_url is not None:
            raise ValueError("Coordenadas desconhecidas exigem precisão e fonte nulas")
        return
    if not isinstance(coordinates, dict) or set(coordinates) != {"lat", "lon"}:
        raise ValueError("Coordenadas geográficas inválidas")
    lat, lon = coordinates["lat"], coordinates["lon"]
    if (type(lat) not in (int, float) or type(lon) not in (int, float)
            or not isfinite(lat) or not isfinite(lon)
            or not -90 <= lat <= 90 or not -180 <= lon <= 180):
        raise ValueError("Coordenadas fora dos limites")
    if precision == "unknown" or not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("Coordenada verificada exige precisão e fonte")
    date.fromisoformat(checked_at)


def validate_walking_access(data, catalog):
    if data.get("schema_version") != 1:
        raise ValueError("Schema geográfico incompatível")
    date.fromisoformat(data["checked_at"])
    destinations = data["destinations"]
    if len(destinations) != len(set(destinations)) or len(destinations) != 6:
        raise ValueError("P0 deve ter seis destinos únicos")
    catalog_items = {x["id"]: x for x in catalog["attractions"]}
    expected = {a["id"] for a in catalog["attractions"] if a["destination_id"] in destinations}
    stations = {}
    for station in data["stations"]:
        sid = station["id"]
        if sid in stations or station["destination_id"] not in destinations:
            raise ValueError("Estação duplicada ou fora do destino")
        _geo(station["coordinates"], "attraction_point",
             station["source_url"], station["checked_at"])
        if station["coordinate_precision"] != "station_point_not_entrance":
            raise ValueError("Estação não deve ser descrita como entrada verificada")
        stations[sid] = station
    if {x["destination_id"] for x in stations.values()} != set(destinations):
        raise ValueError("P0 sem estação representativa")
    indexed = {}
    for item in data["attractions"]:
        aid = item["attraction_id"]
        if aid in indexed or aid not in expected or item["destination_id"] != catalog_items[aid]["destination_id"]:
            raise ValueError("ID de atração desconhecido ou duplicado")
        _geo(item["coordinates"], item["coordinate_precision"],
             item["coordinate_source_url"], item["checked_at"])
        if item["entrance_verified"] and item["coordinate_precision"] != "entrance":
            raise ValueError("Centroide não pode ser entrada verificada")
        if item["station_id"] not in stations or stations[item["station_id"]]["destination_id"] != item["destination_id"]:
            raise ValueError("Estação não corresponde ao destino")
        if item["address"] is not None and (not item["address_source_url"] or
                                                not item["address_source_url"].startswith("https://")):
            raise ValueError("Endereço sem fonte")
        if item["walking_from_station_min"] is not None or item["walking_from_station_m"] is not None:
            raise ValueError("Duração de caminhada pertence a evidência de percurso")
        indexed[aid] = item
    if set(indexed) != expected:
        raise ValueError("Inventário das atrações P0 está incompleto")
    seen = set()
    for route in data["walking_routes"]:
        key = (route["origin_id"], route["destination_id"], route["mode"])
        if key in seen or route["origin_id"] not in stations or route["destination_id"] not in indexed:
            raise ValueError("Percurso duplicado ou com origem/destino inexistente")
        seen.add(key)
        if stations[route["origin_id"]]["destination_id"] != indexed[route["destination_id"]]["destination_id"]:
            raise ValueError("Percurso entre destinos incompatíveis")
        if route["mode"] not in VALID_MODES or route["distance_kind"] not in VALID_DISTANCE_KINDS:
            raise ValueError("Modal ou natureza da distância inválidos")
        if route["mode"] != "walking" or route["distance_kind"] != "walking_route":
            raise ValueError("Percurso pedestre não pode ser reclassificado")
        if route["status"] not in VALID_STATUS:
            raise ValueError("Status de evidência inválido")
        distance, minutes = route["distance_m"], route["duration_min"]
        if distance is not None and (type(distance) not in (int, float) or distance <= 0):
            raise ValueError("Distância caminhável inválida")
        if minutes is not None and (type(minutes) not in (int, float) or minutes < 0):
            raise ValueError("Tempo caminhável inválido")
        if distance is not None or minutes is not None:
            if (not route["source_url"] or not route["source_url"].startswith("https://")
                    or not route["method"] or not route["checked_at"]):
                raise ValueError("Distância ou tempo exige método, fonte e data")
            date.fromisoformat(route["checked_at"])
        if distance is not None and route["geometry_status"] != "verified_pedestrian_routing":
            raise ValueError("Distância pedestre exige geometria roteada")
        if route["status"] == "pending_verified_pedestrian_route" and (distance is not None or minutes is not None):
            raise ValueError("Percurso pendente não pode ter duração")
        if minutes is not None and route["status"] != "operator_published_walk_duration":
            raise ValueError("Tempo sem evidência direta")
    for seq in data["candidate_sequences"]:
        ids = seq["attraction_ids"]
        if (seq["destination_id"] not in destinations or not 2 <= len(ids) <= 10
                or len(ids) != len(set(ids)) or any(i not in indexed or indexed[i]["destination_id"] != seq["destination_id"] for i in ids)):
            raise ValueError("Sequência utiliza atrações incompatíveis")
        if seq["walking_geometry_verified"] or seq["inter_attraction_durations_min"] is not None:
            raise ValueError("Sequência hipotética não é um percurso verificado")


def load_walking_access(path=DEFAULT, catalog=None):
    from attractions_model import load_attractions
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_walking_access(content, catalog if catalog is not None else load_attractions())
    return deepcopy(content)


def attraction_access(attraction_id, *, evidence=None, catalog=None):
    """Single read-only access lookup across new geography and P1 legacy pilot."""
    from dq30_mobility_evidence_model import load_mobility_pilot, access_by_attraction
    source = evidence if evidence is not None else load_walking_access(catalog=catalog)
    row = next((x for x in source["attractions"] if x["attraction_id"] == attraction_id), None)
    if row is None:
        return None
    result = deepcopy(row)
    result["arrival_station"] = next(x for x in source["stations"] if x["id"] == row["station_id"])
    result["station_route"] = next((deepcopy(x) for x in source["walking_routes"] if x["destination_id"] == attraction_id and x["origin_id"] == row["station_id"]), None)
    legacy = access_by_attraction(load_mobility_pilot(), attraction_id)
    if legacy is not None:
        result["historical_access"] = legacy
    return result


def destination_access(destination_id, *, evidence=None):
    source = evidence if evidence is not None else load_walking_access()
    if destination_id not in source["destinations"]:
        return None
    return {"destination_id":destination_id,
            "attractions":[attraction_access(x["attraction_id"], evidence=source)
                           for x in source["attractions"] if x["destination_id"] == destination_id],
            "stations":deepcopy([x for x in source["stations"] if x["destination_id"] == destination_id]),
            "candidate_sequences":deepcopy([x for x in source["candidate_sequences"] if x["destination_id"] == destination_id])}
