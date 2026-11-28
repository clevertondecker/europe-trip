"""Documentary fare and dated schedule observations; never live availability or official costs."""
import json
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from weekend_return_validation_model import validate_service_leg, weekend_roundtrip_evidence

PATH = Path(__file__).resolve().parent / "data" / "rail_fare_observations_2027.json"
FIELDS = {"id", "outbound", "inbound", "checked_at", "source_url", "currency",
          "travelers", "total_minor", "mandatory_fees_included", "fare_class",
          "fare_conditions", "availability", "passenger_profile", "discount_eligibility",
          "ticket_structure", "checked_at_time", "refundability", "changeability"}

def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()

def _url(value):
    if not _text(value):
        return False
    try:
        p = urlparse(value)
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False

def _utc(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc)

def identity(leg):
    def service(row):
        values = tuple(row.get(k) for k in ("operator", "service_id", "arrival_service_id", "departure_service_id"))
        if any(v is not None and not _text(v) for v in values):
            raise ValueError("Identificador de serviço inválido")
        return values
    transfers = tuple((x["station_id"], _utc(x.get("arrival_at", x.get("arrival_local"))),
                       _utc(x.get("departure_at", x.get("departure_local"))), service(x))
                      for x in leg["transfer_legs"])
    return (leg["origin_id"], leg["destination_id"], leg["origin_station_id"],
            leg["destination_station_id"], _utc(leg["departure_at"]), _utc(leg["arrival_at"]),
            service(leg), transfers)

def _project_schedule_samples(samples):
    """Reuse the temporal/return contract without inventing passenger or fare claims."""
    if not isinstance(samples, list):
        raise ValueError("Amostras de horários inválidas")
    records, ids, seen = [], set(), set()
    leg_fields = {"origin_id", "destination_id", "origin_station_id",
                  "destination_station_id", "origin_station_label", "destination_station_label",
                  "departure_at", "arrival_at", "calendar_dates_verified", "transfer_count",
                  "transfer_legs", "source_url", "operator", "service_id",
                  "origin_timezone", "destination_timezone"}
    for raw in samples:
        if not isinstance(raw, dict) or set(raw) != {"id", "checked_at", "outbound", "inbound"}:
            raise ValueError("Horário datado não é cotação tarifária")
        if not _text(raw["id"]) or raw["id"] in ids:
            raise ValueError("Identidade de horário duplicada")
        checked = date.fromisoformat(raw["checked_at"])
        if checked.isoformat() != raw["checked_at"]:
            raise ValueError("Data de consulta inválida")
        legs = []
        for leg in (raw["outbound"], raw["inbound"]):
            if (not isinstance(leg, dict) or set(leg) != leg_fields
                    or not _url(leg["source_url"])
                    or any(not _text(leg[k]) for k in ("origin_station_label",
                           "destination_station_label", "operator", "service_id"))
                    or not all(leg[k].startswith("sncf_published:") for k in
                               ("origin_station_id", "destination_station_id"))):
                raise ValueError("Amostra de serviço sem proveniência ou rótulo de estação")
            normalized = validate_service_leg(leg)
            departure = datetime.fromisoformat(normalized["departure_at"])
            if (departure.year != 2026 or checked > departure.date()
                    or not normalized["calendar_date_applicable"]):
                raise ValueError("Amostra histórica sem data comprovada")
            legs.append(normalized)
        out, back = legs
        result = weekend_roundtrip_evidence(out, back)
        if (result["status"] != "documented_legs_only"
                or out["destination_station_id"] != back["origin_station_id"]
                or out["origin_station_id"] != back["destination_station_id"]
                or out["destination_station_label"] != back["origin_station_label"]
                or out["origin_station_label"] != back["destination_station_label"]):
            raise ValueError("Ida e retorno da amostra incompatíveis")
        key = (identity(out), identity(back), checked, out["source_url"], back["source_url"])
        if key in seen:
            raise ValueError("Amostra de horário duplicada")
        seen.add(key)
        ids.add(raw["id"])
        records.append({
            "id": raw["id"], "checked_at": raw["checked_at"], "outbound": out, "inbound": back,
            "outbound_duration_min": int((_utc(out["arrival_at"]) - _utc(out["departure_at"])).total_seconds() // 60),
            "inbound_duration_min": int((_utc(back["arrival_at"]) - _utc(back["departure_at"])).total_seconds() // 60),
            "gross_destination_minutes": int((_utc(back["departure_at"]) - _utc(out["arrival_at"])).total_seconds() // 60),
            "net_visit_minutes": None, "last_mile_verified": False,
            "station_identity_scope": "source_published_not_reconciled",
            "roundtrip_status": result["status"], "outing_feasible": False,
            "valid_for_2027": False,
        })
    return records


def project_rail_fares(payload):
    if not isinstance(payload, dict) or set(payload) not in ({"schema_version", "quotes"}, {"schema_version", "quotes", "schedule_samples"}) or type(payload["schema_version"]) is not int or payload["schema_version"] != 1 or not isinstance(payload["quotes"], list):
        raise ValueError("Contrato tarifário inválido")
    ids, identities, records = set(), {}, []
    for raw in payload["quotes"]:
        if not isinstance(raw, dict) or set(raw) != FIELDS:
            raise ValueError("Campos tarifários inválidos")
        q = deepcopy(raw)
        if not _text(q["id"]) or q["id"] in ids or not _url(q["source_url"]):
            raise ValueError("Identidade ou fonte inválida")
        if not _text(q["checked_at"]):
            raise ValueError("Data de consulta inválida")
        checked = date.fromisoformat(q["checked_at"])
        if checked.isoformat() != q["checked_at"]:
            raise ValueError("Data de consulta inválida")
        observed = q["checked_at_time"]
        if observed is not None:
            if not _text(observed):
                raise ValueError("Instante de consulta inválido")
            moment = datetime.fromisoformat(observed)
            if moment.utcoffset() is None or moment.date() != checked:
                raise ValueError("Instante de consulta exige offset e data correspondente")
            observed = moment.astimezone(timezone.utc)
        if q["passenger_profile"] != "two_adults":
            raise ValueError("Perfil deve ser dois adultos")
        for field in ("refundability", "changeability"):
            if q[field] not in (None, "allowed", "conditional", "not_allowed"):
                raise ValueError("Condição comercial inválida: " + field)
        if q["ticket_structure"] not in (None, "integrated", "separate"):
            raise ValueError("Estrutura de bilhete inválida")
        if q["discount_eligibility"] is not None and not _text(q["discount_eligibility"]):
            raise ValueError("Elegibilidade inválida")
        if q["currency"] not in ("EUR", "CHF", "GBP"):
            raise ValueError("Moeda não suportada")
        if type(q["travelers"]) is not int or q["travelers"] != 2:
            raise ValueError("Cotação deve representar duas pessoas")
        amount = q["total_minor"]
        if amount is not None and (type(amount) is not int or amount < 0):
            raise ValueError("Valor em unidades monetárias menores inválido")
        if q["availability"] not in ("documented_offer", "unavailable", "unknown"):
            raise ValueError("Estado de disponibilidade inválido")
        if q["availability"] != "documented_offer" and amount is not None:
            raise ValueError("Sem oferta documentada não há preço de oferta")
        if q["mandatory_fees_included"] is not None and type(q["mandatory_fees_included"]) is not bool:
            raise ValueError("Estado de taxas inválido")
        for field in ("fare_class", "fare_conditions"):
            if q[field] is not None and not _text(q[field]):
                raise ValueError("Condição tarifária inválida")
        legs = []
        for field in ("outbound", "inbound"):
            leg = q[field]
            if leg is None and field == "inbound":
                continue
            if not isinstance(leg, dict) or not _url(leg.get("source_url")):
                raise ValueError("Fonte de trecho inválida")
            normalized = validate_service_leg(leg)
            departure = datetime.fromisoformat(normalized["departure_at"])
            if (observed is None and checked > departure.date()) or (observed is not None and observed > departure.astimezone(timezone.utc)):
                raise ValueError("Consulta posterior à partida")
            legs.append(normalized)
        out = legs[0]
        back = legs[1] if len(legs) == 2 else None
        pair = weekend_roundtrip_evidence(out, back)
        if pair["status"] == "incompatible":
            raise ValueError("Ida e retorno incompatíveis")
        key = (tuple(identity(x) for x in legs), (observed if observed is not None else checked),
               q["source_url"].split("#", 1)[0], q["currency"], q["fare_class"],
               q["fare_conditions"], q["discount_eligibility"], q["ticket_structure"],
               q["refundability"], q["changeability"])
        claims = (amount, q["availability"], q["mandatory_fees_included"])
        if key in identities:
            raise ValueError("Observação duplicada" if identities[key] == claims
                             else "Observações conflitantes")
        ids.add(q["id"])
        identities[key] = claims
        complete = (q["availability"] == "documented_offer" and amount is not None
                    and q["mandatory_fees_included"] is True and q["fare_class"] is not None
                    and q["fare_conditions"] is not None and q["discount_eligibility"] is not None
                    and q["ticket_structure"] is not None and q["refundability"] is not None
                    and q["changeability"] is not None and all(x["calendar_date_applicable"] for x in legs))
        records.append({"quote": q, "outbound": out, "inbound": back,
                        "roundtrip_status": pair["status"], "complete_documentation": complete,
                        "scope": "roundtrip" if back else "oneway",
                        "return_temporally_coherent": back is not None,
                        "return_calendar_documented": bool(back and out["calendar_date_applicable"] and back["calendar_date_applicable"]),
                        "same_destination_station": out["destination_station_id"] == back["origin_station_id"] if back else None,
                        "same_base_station": out["origin_station_id"] == back["destination_station_id"] if back else None,
                        "outing_feasible": False,
                        "independently_verified": False, "valid_for_2027": False})
    schedules = _project_schedule_samples(payload.get("schedule_samples", []))
    return {"records": records, "documented": len(records),
            "schedule_samples": schedules, "dated_roundtrip_samples": len(schedules),
            "roundtrips": sum(x["inbound"] is not None for x in records),
            "complete_documentation": sum(x["complete_documentation"] for x in records),
            "complete_oneway": sum(x["complete_documentation"] and x["scope"] == "oneway" for x in records),
            "complete_roundtrip": sum(x["complete_documentation"] and x["scope"] == "roundtrip" for x in records),
            "independently_verified": 0}

def load_rail_fares(path=PATH):
    return project_rail_fares(json.loads(Path(path).read_text(encoding="utf-8")))
