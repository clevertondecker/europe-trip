"""Documentary fare observations; never live availability or official costs."""
import json
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from weekend_return_validation_model import validate_service_leg, weekend_roundtrip_evidence

PATH = Path(__file__).resolve().parent / "data" / "rail_fare_observations_2027.json"
FIELDS = {"id", "outbound", "inbound", "checked_at", "source_url", "currency",
          "travelers", "total_minor", "mandatory_fees_included", "fare_class",
          "fare_conditions", "availability"}

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

def project_rail_fares(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "quotes"} or type(payload["schema_version"]) is not int or payload["schema_version"] != 1 or not isinstance(payload["quotes"], list):
        raise ValueError("Contrato tarifário inválido")
    ids, identities, records = set(), set(), []
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
            if checked > departure.date():
                raise ValueError("Consulta posterior à partida")
            legs.append(normalized)
        out = legs[0]
        back = legs[1] if len(legs) == 2 else None
        pair = weekend_roundtrip_evidence(out, back)
        if pair["status"] == "incompatible":
            raise ValueError("Ida e retorno incompatíveis")
        def identity(leg):
            return (leg["origin_id"], leg["destination_id"], leg["origin_station_id"],
                    leg["destination_station_id"], datetime.fromisoformat(leg["departure_at"]).astimezone(timezone.utc),
                    datetime.fromisoformat(leg["arrival_at"]).astimezone(timezone.utc))
        key = (tuple(identity(x) for x in legs), q["checked_at"], q["source_url"].split("#", 1)[0],
               q["currency"], q["fare_class"], q["fare_conditions"])
        if key in identities:
            raise ValueError("Observação tarifária duplicada ou conflitante")
        ids.add(q["id"])
        identities.add(key)
        complete = (q["availability"] == "documented_offer" and amount is not None
                    and q["mandatory_fees_included"] is True and q["fare_class"] is not None
                    and q["fare_conditions"] is not None and all(x["calendar_date_applicable"] for x in legs))
        records.append({"quote": q, "outbound": out, "inbound": back,
                        "roundtrip_status": pair["status"], "complete_documentation": complete,
                        "independently_verified": False, "valid_for_2027": False})
    return {"records": records, "documented": len(records),
            "roundtrips": sum(x["inbound"] is not None for x in records),
            "complete_documentation": sum(x["complete_documentation"] for x in records),
            "independently_verified": 0}

def load_rail_fares(path=PATH):
    return project_rail_fares(json.loads(Path(path).read_text(encoding="utf-8")))
