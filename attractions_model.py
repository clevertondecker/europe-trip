"""Adaptive attractions catalog, source-aware routes, and partial couple costs.

Prices are published historic observations, never complete 2027 travel quotes.
"""
from __future__ import annotations

import json
from datetime import date
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
ATTRACTIONS = ROOT / "data" / "attractions_2027.json"
ROUTES = ROOT / "data" / "base_destination_routes_2027.json"
VALID_TICKET_STATUS = {"operator_published", "unknown", "not_applicable"}
VALID_CURRENCIES = {"EUR", "CHF"}
VALID_BASES = {"mulhouse", "strasbourg", "metz", "nancy"}


def load_attractions(path: Path = ATTRACTIONS) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_attractions(data)
    return data


def load_base_routes(path: Path = ROUTES) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_routes(data)
    return data


def validate_attractions(data: dict) -> None:
    destinations = data["destinations"]
    ids = [d["id"] for d in destinations]
    if len(ids) != len(set(ids)) or not VALID_BASES.issubset(set(ids)):
        raise ValueError("Destino repetido ou cidade-base ausente")
    for dest in destinations:
        if not (-90 <= dest["lat"] <= 90 and -180 <= dest["lon"] <= 180):
            raise ValueError("Coordenadas de destino inválidas")
        if not dest["source_url"].startswith("https://"):
            raise ValueError("Destino sem fonte")
        if dest.get("photo") and not (
            dest["photo"]["url"].startswith("https://commons.wikimedia.org/")
            and dest["photo"]["source_page"].startswith("https://commons.wikimedia.org/")
            and dest["photo"]["author"] and dest["photo"]["license"]
        ):
            raise ValueError("Foto sem crédito/licença")
    seen = set()
    counts = defaultdict(int)
    for a in data["attractions"]:
        if a["id"] in seen or a["destination_id"] not in ids:
            raise ValueError("Atração duplicada ou destino inexistente")
        seen.add(a["id"])
        counts[a["destination_id"]] += 1
        if not a["source_urls"] or not all(str(x).startswith("https://") for x in a["source_urls"]):
            raise ValueError("Atração sem origem oficial")
        if not 10 <= a["visit_minutes"] <= 600 or a["visit_minutes_status"] != "editorial_assumption":
            raise ValueError("Duração de visita sem método")
        ticket = a["ticket"]
        if ticket["status"] not in VALID_TICKET_STATUS:
            raise ValueError("Ticket status inválido")
        if ticket["amount"] is None:
            if ticket["status"] == "operator_published":
                raise ValueError("Não pode declarar ingresso publicado sem preço")
        elif (ticket["amount"] < 0 or ticket["currency"] not in VALID_CURRENCIES or
              ticket["status"] != "operator_published"):
            raise ValueError("Preço ou moeda inválida")
    if any(counts[city] < 5 for city in VALID_BASES):
        raise ValueError("Menos de cinco atrações em uma cidade-base")


def validate_routes(data: dict) -> None:
    destinations = set(data["destinations"])
    rows = data["routes"]
    keys = {(r["base_id"], r["destination_id"]) for r in rows}
    if len(keys) != len(rows):
        raise ValueError("Rota duplicada")
    if keys != {(base, dest) for base in VALID_BASES for dest in destinations}:
        raise ValueError("Matriz base × destino incompleta")
    for row in rows:
        if row["fare_type"] == "discount_carte_fluo" and row["fare_eur_person_oneway"] is None:
            raise ValueError("Desconto sem valor")
        if row["fare_eur_person_oneway"] is not None and row["fare_eur_person_oneway"] < 0:
            raise ValueError("Tarifa negativa")
        if row["train_minutes_one_way"] is not None and row["minutes_scope"] != "station_to_station":
            raise ValueError("Minutos de trem não são porta a porta")
        if not row["source_url"].startswith("https://"):
            raise ValueError("Fonte de rota ausente")
        if row["eligible_2027"] is not False:
            raise ValueError("Tarifa histórica não vale como cotação 2027")


def route_for(routes: dict, base: str, dest: str) -> dict:
    for r in routes["routes"]:
        if r["base_id"] == base and r["destination_id"] == dest:
            return r
    raise ValueError("Rota ausente na matriz")


def line_of_sight_km(base: dict, destination: dict) -> float:
    """Haversine air distance only: never use it as rail/road distance."""
    a1, a2 = radians(base["lat"]), radians(destination["lat"])
    dl = radians(destination["lon"] - base["lon"])
    dp = a2-a1
    q = sin(dp/2)**2 + cos(a1)*cos(a2)*sin(dl/2)**2
    return round(6371 * 2 * atan2(sqrt(q), sqrt(1-q)), 1)


def places_for_base(attractions: dict, routes: dict, base: str) -> list[dict]:
    if base not in VALID_BASES:
        raise ValueError("Cidade-base inválida")
    names = {d["id"]:d for d in attractions["destinations"]}
    return [{
        "destination":d,
        "route":route_for(routes,base,d["id"]),
        "distance_straight_km":line_of_sight_km(names[base],d),
        "attractions_count":sum(a["destination_id"]==d["id"] for a in attractions["attractions"]),
    } for d in attractions["destinations"]]


def attraction_cost(ticket: dict, people: int = 2) -> float | None:
    if ticket["status"] == "not_applicable":
        return 0.0   # Outside/public-place visit; does not imply free interior activities.
    if ticket["amount"] is None:
        return None
    return round(ticket["amount"]*people,2)


def package_cost(attractions: dict, routes: dict, base: str,
                 chosen_attraction_ids: list[str], travelers: int = 2, *,
                 planned_destination_ids: list[str] | None = None) -> dict:
    """One round-trip intercity fare per destination, never per attraction."""
    if travelers < 1 or travelers > 20:
        raise ValueError("Número de viajantes inválido")
    if len(set(chosen_attraction_ids)) != len(chosen_attraction_ids):
        raise ValueError("Atração selecionada duas vezes")
    index = {a["id"]:a for a in attractions["attractions"]}
    from ux62_supplemental_outings import supplemental_attractions
    index.update({a["id"]:a for a in supplemental_attractions()})
    if not set(chosen_attraction_ids) <= set(index):
        raise ValueError("Atração não cadastrada")
    grouped = defaultdict(list)
    for key in chosen_attraction_ids:
        grouped[index[key]["destination_id"]].append(index[key])
    if planned_destination_ids is not None:
        from ux62_supplemental_outings import supplemental_allowed
        known = {d["id"] for d in attractions["destinations"]}
        for destination_id in planned_destination_ids:
            if destination_id not in known and supplemental_allowed(destination_id) is None:
                raise ValueError("Cidade planejada não cadastrada")
            grouped.setdefault(destination_id, [])
    amounts = {"EUR":0.0, "CHF":0.0}
    missing = []
    conditional = []
    breakdown = []
    for dest, items in grouped.items():
        try:
            route = route_for(routes,base,dest)
        except ValueError:
            route = None  # Newly researched city: no historical rail fare.
        if base == dest:
            missing.append(f"Transporte urbano em {dest}")
        elif route is None or route["fare_eur_person_oneway"] is None:
            missing.append(f"Transporte entre {base} e {dest}")
        else:
            # The return fare is only illustrative; the 2027 return is unconfirmed.
            price = round(route["fare_eur_person_oneway"]*travelers*2,2)
            amounts["EUR"] += price
            breakdown.append({"item":f"Transporte {base} ↔ {dest}", "currency":"EUR",
                              "known_eur":price, "condition":route["fare_type"]})
            if route["fare_type"]=="discount_carte_fluo":
                conditional.append(f"{base} ↔ {dest}: Carte Fluo não incluída")
        if not items:
            missing.append(f"Atividades a definir em {dest}")
        for item in items:
            price = attraction_cost(item["ticket"],travelers)
            if price is None:
                missing.append(f"Ingresso/atividade: {item['name']}")
            elif item["ticket"]["status"]=="operator_published":
                currency=item["ticket"]["currency"]
                amounts[currency] += price
                breakdown.append({"item":item["name"],"currency":currency,
                                  "known_eur":price,"condition":item["ticket"]["status"]})
    return {"known_by_currency":{k:round(v,2) for k,v in amounts.items()},
            "missing":sorted(set(missing)),
            "conditional":sorted(set(conditional)),
            "by_destination":{k:[a["id"] for a in v] for k,v in grouped.items()},
            "breakdown":breakdown,
            "complete":not missing and bool(grouped),
            "selected_count":len(chosen_attraction_ids)}


def approximate_feasibility(dest: dict, route: dict) -> str:
    """Unverified operational label, not a Sunday timetable check."""
    if dest["kind"] == "overnight":
        return "Pernoite recomendado investigar"
    if dest["id"] == route["base_id"]:
        return "Visita local, horário a verificar"
    if route["train_minutes_one_way"] is None:
        return "Viabilidade não comprovada"
    if route["train_minutes_one_way"] <= 70:
        return "Bate-volta candidato; volta a verificar"
    return "Dia inteiro candidato; volta a verificar"


def schedule_visit(days: list[dict], assignments: dict[str,str], day_iso: str,
                   destination_id: str, full_day: bool = True) -> dict[str,str]:
    selected = next((row for row in days if row["date"]==day_iso),None)
    if selected is None or selected["stage"] != "França":
        raise ValueError("Dia não pertence à etapa francesa")
    if day_iso in assignments:
        raise ValueError("Já existe um passeio neste dia")
    if selected["activity"] == "Instalação":
        raise ValueError("Dia reservado à instalação")
    if full_day and "Trabalho remoto" in selected["activity"]:
        raise ValueError("Passeio de dia inteiro conflita com trabalho remoto")
    return {**assignments,day_iso:destination_id}


def excursions_overage_brl(known_eur: float, known_chf: float,
                          euro_fx: float, chf_fx: float, allocated_brl: float) -> float:
    """Do not reduce excursion allowance using incomplete historical quotes.

    Only known amount beyond the existing allowance counts as extra, never double count.
    """
    values=(known_eur,known_chf,euro_fx,chf_fx,allocated_brl)
    if any(v<0 for v in values) or euro_fx==0 or chf_fx==0:
        raise ValueError("Conversão inválida")
    return round(max(0.0,known_eur*euro_fx+known_chf*chf_fx-allocated_brl),2)
