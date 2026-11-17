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
# Legacy values remain accepted; new evidence types have distinct contracts.
VALID_STATUS = {
    "operator_published_walk_duration", "pending_verified_pedestrian_route",
    "official_published", "pedestrian_routed", "pending_verification",
}
OFFICIAL_STATUSES = {"operator_published_walk_duration", "official_published"}
PENDING_STATUSES = {"pending_verified_pedestrian_route", "pending_verification"}
PEDESTRIAN_PROFILES = {"pedestrian", "foot", "walking", "wheelchair"}


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


def _access_points(points, *, parent_id, kind):
    """Access points must be actual evidenced pedestrian entrances/exits."""
    if not isinstance(points, list):
        raise ValueError("Pontos de acesso precisam ser lista")
    indexed = {}
    for point in points:
        pid = point.get("id")
        if not isinstance(pid, str) or not pid or pid in indexed:
            raise ValueError("Ponto de acesso ausente ou duplicado")
        if point.get("parent_id") != parent_id or point.get("kind") not in (
                {"public_entrance", "public_exit"} if kind == "station"
                else {"public_entrance"}):
            raise ValueError("Tipo ou vínculo de acesso inválido")
        _geo(point.get("coordinates"), "entrance",
             point.get("source_url"), point.get("checked_at"))
        if point.get("coordinates") is None:
            raise ValueError("Ponto de acesso sem coordenada verificada")
        if point.get("verification_status") != "verified_public_access":
            raise ValueError("Acesso não comprovado")
        indexed[pid] = point
    return indexed


def _walking_route(route, stations, attractions, station_access, attraction_access):
    status = route["status"]
    if status not in VALID_STATUS:
        raise ValueError("Status de evidência inválido")
    if route["mode"] != "walking" or route["distance_kind"] != "walking_route":
        raise ValueError("Trecho ferroviário/linha reta não é caminhada")
    distance, minutes = route["distance_m"], route["duration_min"]
    if distance is not None and (type(distance) not in (int, float)
            or not isfinite(distance) or distance <= 0):
        raise ValueError("Distância caminhável inválida")
    if minutes is not None and (type(minutes) not in (int, float)
            or not isfinite(minutes) or minutes <= 0):
        raise ValueError("Duração caminhável inválida")
    measured = distance is not None or minutes is not None
    source = route.get("source_url")
    method = route.get("method")
    checked = route.get("checked_at")
    if measured:
        if not isinstance(source, str) or not source.startswith("https://") or not method:
            raise ValueError("Evidência de caminhada exige fonte e método")
        date.fromisoformat(checked)
    if status in PENDING_STATUSES:
        if measured or route.get("geometry_status") == "verified_pedestrian_routing":
            raise ValueError("Rota pendente não pode possuir resultados")
        return
    if not measured:
        raise ValueError("Evidência confirmada não pode ser vazia")
    if status in OFFICIAL_STATUSES:
        if method != "official_tourism_access_statement" and method != "official_published_access":
            raise ValueError("Tempo oficial exige método de publicação oficial")
        if route.get("geometry_status") == "verified_pedestrian_routing":
            raise ValueError("Geometria roteada deve usar evidência de motor pedestre")
        if route.get("engine") is not None:
            raise ValueError("Publicação oficial não pode mascarar motor de rotas")
        return
    # A pedestrian engine result requires real PUBLIC access coordinates on
    # both ends, never a station centroid or a generic attraction point.
    if route.get("geometry_status") != "verified_pedestrian_routing":
        raise ValueError("Motor pedestre exige geometria validada")
    if not isinstance(route.get("engine"), str) or not route["engine"].strip():
        raise ValueError("Motor de roteamento não identificado")
    if route.get("profile") not in PEDESTRIAN_PROFILES or route.get("method") != "pedestrian_routing_engine":
        raise ValueError("Perfil ou método pedestre inválido")
    origin_access = route.get("origin_access_id")
    destination_access = route.get("destination_access_id")
    if origin_access not in station_access.get(route["origin_id"], {}):
        raise ValueError("Entrada/saída pública da estação não verificada")
    if destination_access not in attraction_access.get(route["destination_id"], {}):
        raise ValueError("Entrada da atração não verificada")
    if not isinstance(route.get("geometry_source_url"), str) or not route["geometry_source_url"].startswith("https://"):
        raise ValueError("Sem referência auditável à geometria do percurso")
    if not isinstance(route.get("engine_version"), str) or not route["engine_version"].strip():
        raise ValueError("Versão do motor pedestre ausente")
    if not isinstance(route.get("routing_observed_at"), str):
        raise ValueError("Data do roteamento ausente")
    date.fromisoformat(route["routing_observed_at"])
    if route.get("coordinate_conflict_unresolved") is True or stations[route["origin_id"]].get("coordinate_conflict_unresolved", False):
        raise ValueError("Conflito de localização não resolvido")


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
    station_access = {}
    for station in data["stations"]:
        sid = station["id"]
        if sid in stations or station["destination_id"] not in destinations:
            raise ValueError("Estação duplicada ou fora do destino")
        _geo(station["coordinates"], "attraction_point",
             station["source_url"], station["checked_at"])
        if station["coordinate_precision"] != "station_point_not_entrance":
            raise ValueError("Estação não deve ser descrita como entrada verificada")
        if not isinstance(station.get("coordinate_conflict_unresolved", False), bool):
            raise ValueError("Marcador de conflito inválido")
        reconciliation = station.get("coordinate_reconciliation")
        if reconciliation is not None:
            if (reconciliation.get("status") != "representative_station_location_reconciled_only"
                    or len(reconciliation.get("sources", [])) < 2
                    or not all(isinstance(u,str) and u.startswith("https://")
                               for u in reconciliation["sources"])
                    or not reconciliation.get("reason")
                    or station.get("coordinate_conflict_unresolved", False)):
                raise ValueError("Conciliação da posição de estação sem proveniência")
            date.fromisoformat(reconciliation["checked_at"])
        if station.get("pedestrian_routing_ready", False) and not station.get("pedestrian_access_points"):
            raise ValueError("Estação sem saída pública não pode estar pronta para roteamento")
        station_access[sid] = _access_points(
            station.get("pedestrian_access_points", []),
            parent_id=sid, kind="station")
        if station.get("coordinate_conflict_unresolved", False) and station_access[sid]:
            raise ValueError("Resolver conflito geográfico antes de validar acessos")
        stations[sid] = station
    if {x["destination_id"] for x in stations.values()} != set(destinations):
        raise ValueError("P0 sem estação representativa")
    indexed = {}
    attraction_access_points = {}
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
        attraction_access_points[aid] = _access_points(
            item.get("pedestrian_access_points", []),
            parent_id=aid, kind="attraction")
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
        _walking_route(route, stations, indexed,
                       station_access, attraction_access_points)
    # Distances for official complete itineraries are not distances between
    # any two of their individual highlights.
    seen_itineraries = set()
    for itinerary in data.get("published_walking_itineraries", []):
        ident=itinerary.get("id")
        if not isinstance(ident,str) or not ident or ident in seen_itineraries:
            raise ValueError("Roteiro pedestre duplicado ou sem ID")
        seen_itineraries.add(ident)
        start=itinerary.get("origin_id")
        end=itinerary.get("end_station_id")
        if start not in stations or end not in stations:
            raise ValueError("Roteiro oficial sem estação canônica")
        if (stations[start]["destination_id"] != itinerary.get("destination_id")
                or stations[end]["destination_id"] != itinerary.get("destination_id")):
            raise ValueError("Roteiro oficial em destino incompatível")
        if (itinerary.get("status") != "official_published"
                or itinerary.get("method") != "official_tourism_walking_itinerary"
                or itinerary.get("mode") != "walking"
                or itinerary.get("distance_kind") != "walking_route"
                or itinerary.get("route_scope") != "entire_loop_not_individual_segments"
                or itinerary.get("geometry_status") != "official_tourism_route_map_link"):
            raise ValueError("Roteiro total não pode ser disfarçado de trecho")
        if (type(itinerary.get("distance_m")) not in (int,float)
                or not isfinite(itinerary["distance_m"]) or itinerary["distance_m"] <= 0
                or itinerary.get("duration_min") is not None):
            raise ValueError("Distância total publicada ou duração inválida")
        if not isinstance(itinerary.get("source_url"),str) or not itinerary["source_url"].startswith("https://"):
            raise ValueError("Roteiro oficial sem fonte")
        date.fromisoformat(itinerary["checked_at"])
        ids=itinerary.get("included_attraction_ids",[])
        if not ids or len(ids)!=len(set(ids)) or any(
                x not in indexed or indexed[x]["destination_id"]!=itinerary["destination_id"]
                for x in ids):
            raise ValueError("Destaques do roteiro inexistentes ou incompatíveis")

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
