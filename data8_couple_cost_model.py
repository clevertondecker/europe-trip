"""DATA 8.4: defensible couple cost planning, never a 2027 booking quote.

One intercity transport range per *destination outing*, not per attraction.
An explicit user-editable range is a scenario assumption, not a sourced fare.
Unknown ticket, food or transport remains unknown; zero must be justified.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite
from pathlib import Path
from urllib.parse import urlparse
import json

from data8_priority_tourism_model import load_priority_lot

DATA = Path(__file__).resolve().parent / "data" / "data8_cost_reference_2026_11.json"


def _nonnegative(v):
    return type(v) in (int,float) and isfinite(v) and v >= 0


def _https(value):
    p = urlparse(value or "")
    return p.scheme == "https" and bool(p.hostname)


def load_cost_addons(path=DATA):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    if (doc.get("schema_version") != 1 or
            doc.get("scope") != "historical_optional_activity_reference_only"):
        raise ValueError("cost source version mismatch")
    date.fromisoformat(doc["checked_at"])
    seen = set()
    for row in doc["optional_activities"]:
        key=(row.get("attraction_id"),row.get("activity_id"))
        if key in seen or not all(key):
            raise ValueError("activity duplicated or missing identity")
        seen.add(key)
        if (row.get("status") != "operator_published_historical" or
                row.get("valid_for_2027") is not False or
                not _https(row.get("source_url"))):
            raise ValueError("activity price needs source and historic status")
        date.fromisoformat(row["checked_at"])
        if (row.get("currency") != "EUR" or row.get("unit") not in
                ("adult","person","couple") or not _nonnegative(row.get("amount"))):
            raise ValueError("optional activity price invalid")
    return deepcopy(doc)


def _scenario_range(component, category):
    if component is None:
        return None
    if not isinstance(component, dict):
        raise ValueError(f"{category}: scenario must be explicitly supplied")
    a, b = component.get("min_eur"), component.get("max_eur")
    if (not _nonnegative(a) or not _nonnegative(b) or
            a > b or component.get("state") != "user_editorial_assumption" or
            not component.get("method")):
        raise ValueError(f"{category}: invalid range or method")
    return [float(a),float(b)]


SCOPES = {"external_visit", "general_entry", "optional_activity", "unknown"}


def _money(value):
    """Two-decimal monetary rounding, independently of binary float rounding."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def estimate_couple_excursion(attraction_ids, *, research=None, addons=None,
                              selected_addons=(), visit_scopes=None,
                              intercity_couple=None, local_couple=None,
                              dining_couple=None, eur_to_brl=None, travelers=2):
    """Cost only the explicitly selected scope for one destination and two adults.

    Absent visit_scopes defaults documented general entry to general_entry,
    but never silently converts exterior or unknown admission into a free ticket.
    Transport ranges cover return journeys for the *couple* only when the
    user supplies the explicit roundtrip_two_adults journey_scope marker.
    """
    research = research if research is not None else load_priority_lot()
    addons = addons if addons is not None else load_cost_addons()
    if type(travelers) is not int or travelers != 2:
        raise ValueError("this calculation is explicitly for two adults")
    if not attraction_ids or len(set(attraction_ids)) != len(attraction_ids):
        raise ValueError("select unique attraction IDs")
    if any(x not in research["by_id"] for x in attraction_ids):
        raise ValueError("unknown attraction")
    selected = [research["by_id"][aid] for aid in attraction_ids]
    destinations = {x["destination_id"] for x in selected}
    if len(destinations) != 1:
        raise ValueError("one outing per destination; never repeat the railway fare")
    if eur_to_brl is not None and (type(eur_to_brl) not in (int, float)
                                   or not isfinite(eur_to_brl) or eur_to_brl <= 0):
        raise ValueError("manual planning FX rate must be positive")
    if visit_scopes is not None and not isinstance(visit_scopes, dict):
        raise ValueError("visit scopes must be an attraction-to-scope mapping")
    visit_scopes = dict(visit_scopes or {})
    if set(visit_scopes) - set(attraction_ids):
        raise ValueError("scope supplied for an unselected attraction")

    addon_index = {a["activity_id"]: a for a in addons["optional_activities"]}
    if (len(set(selected_addons)) != len(selected_addons)
            or any(x not in addon_index for x in selected_addons)):
        raise ValueError("optional activities must be uniquely researched")
    for aid in selected_addons:
        if addon_index[aid]["attraction_id"] not in attraction_ids:
            raise ValueError("selected addon belongs to another attraction")

    resolved_scopes = {}
    amounts = []
    missing = []
    exterior = []
    detailed = []
    for r in selected:
        aid = r["attraction_id"]
        ticket = r["admission"]
        kind = ticket["state"]
        scope = visit_scopes.get(aid)
        if scope is None:
            scope = "general_entry" if kind in ("free_general_entry", "published_price") else "unknown"
        if scope not in SCOPES:
            raise ValueError("unsupported visit scope: " + str(scope))
        resolved_scopes[aid] = scope
        own_addons = [x for x in selected_addons if addon_index[x]["attraction_id"] == aid]

        if scope == "unknown":
            missing.append("escopo_visita:" + aid)
            detailed.append({"name": aid, "category": "unscoped_visit",
                             "known_eur": None, "status": kind,
                             "source_url": ticket.get("source_url")})
        elif scope == "external_visit":
            if (kind == "external_no_ticket"
                    and ticket.get("external_access_basis") == "documented_public_outdoor_area"
                    and ticket.get("source_url")):
                exterior.append(aid)
                detailed.append({"name": aid, "category": "external_visit_only",
                                 "known_eur": 0.0, "status": "documented_no_ticket_for_outdoor_scope",
                                 "source_url": ticket["source_url"]})
            else:
                missing.append("comprovacao_visita_externa:" + aid)
                detailed.append({"name": aid, "category": "external_visit_unproven",
                                 "known_eur": None, "status": kind,
                                 "source_url": ticket.get("source_url")})
        elif scope in ("general_entry", "optional_activity"):
            if kind in ("free_general_entry", "published_price"):
                if ticket.get("currency") != "EUR":
                    missing.append("moeda_ingresso:" + aid)
                else:
                    factor = travelers if ticket.get("unit") in ("person", "adult") else 1
                    amount = Decimal(str(ticket["amount"])) * factor
                    amounts.append(amount)
                    detailed.append({"name": aid, "category": "general_admission",
                                     "known_eur": _money(amount), "status": kind,
                                     "source_url": ticket.get("source_url")})
            else:
                missing.append("ingresso:" + aid)
        if scope == "optional_activity" and not own_addons:
            missing.append("atividade_opcional:" + aid)
        if own_addons and scope not in ("general_entry", "optional_activity"):
            raise ValueError("optional activity requires an admitted visit scope")

    for aid in selected_addons:
        opt = addon_index[aid]
        factor = travelers if opt["unit"] in ("person", "adult") else 1
        amount = Decimal(str(opt["amount"])) * factor
        amounts.append(amount)
        detailed.append({"name": aid, "category": "optional_activity",
                         "known_eur": _money(amount), "status": "published_historical",
                         "source_url": opt["source_url"]})

    components = {}
    for name, scenario in (
        ("intercity_couple", intercity_couple),
        ("local_couple", local_couple),
        ("dining_couple", dining_couple),
    ):
        values = _scenario_range(scenario, name)
        components[name] = values
        if values is None:
            missing.append(name)
        elif name != "dining_couple" and scenario.get("journey_scope") != "roundtrip_two_adults":
            missing.append("ida_volta_casal:" + name)

    reference_sum = sum(amounts, Decimal("0"))
    minimum = reference_sum + sum(Decimal(str(v[0])) for v in components.values() if v is not None)
    maximum = reference_sum + sum(Decimal(str(v[1])) for v in components.values() if v is not None)
    estimated_range = [_money(minimum), _money(maximum)]
    total_complete = not missing
    brl = ([_money(v * Decimal(str(eur_to_brl))) for v in (minimum, maximum)]
           if eur_to_brl is not None else None)
    return {
        "destination_id": selected[0]["destination_id"],
        "travelers": travelers, "attractions": list(attraction_ids),
        "visit_scopes": resolved_scopes,
        "known_general_and_optional_eur": _money(reference_sum),
        "known_reference_breakdown": detailed,
        "exterior_without_main_ticket": exterior,
        "user_assumption_components": components,
        "transport_scope": "roundtrip_for_two_adults",
        "partial_planning_range_eur": estimated_range,
        "full_scenario_range_eur": estimated_range if total_complete else None,
        "incomplete_estimate": not total_complete,
        "missing": sorted(set(missing)),
        "partial_planning_range_brl": brl,
        "full_scenario_range_brl": brl if total_complete else None,
        "fx_eur_to_brl": eur_to_brl,
        "fx_source": "user_assumption_not_live_fx" if eur_to_brl is not None else "unset",
        "fare_counted_once_per_destination": True,
        "valid_for_2027": False, "plan_mutated": False,
    }
