"""Source-backed tourism research overlays, never a second attraction catalog."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from ux501_destination_discovery_model import build_destination_discovery

DATA = Path(__file__).resolve().parent / "data/tourism_visit_evidence_pilot_2026_11.json"


def _https(value):
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def load_visit_evidence(path=DATA, *, discovery=None):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1 or doc.get("scope") != (
        "historical_operator_read_only_2027_not_guaranteed"):
        raise ValueError("Escopo do overlay incompatível")
    date.fromisoformat(doc["checked_at"])
    discovery = discovery if discovery is not None else build_destination_discovery()
    lookup = {x["id"]: d["id"] for d in discovery["destinations"]
              for x in d["attractions"]}
    seen = set()
    for row in doc.get("entries", []):
        aid = row["attraction_id"]
        if aid in seen or aid not in lookup or lookup[aid] != row["destination_id"]:
            raise ValueError("Atração duplicada ou identidade de destino inválida")
        seen.add(aid)
        date.fromisoformat(row["checked_at"])
        if not (_https(row.get("source_url")) and
                _https(row.get("address_source_url"))):
            raise ValueError("Pesquisa sem fonte oficial URL HTTPS")
        if not row.get("experience_reason") or not row.get("address"):
            raise ValueError("Identidade/experiência insuficiente")
        if row.get("opening_state") != "verified_current_rule" or not row.get("opening_rule"):
            raise ValueError("Horário genérico não fundamentado")
        ticket = row["entry_ticket"]
        if ticket["status"] == "free_public_entry":
            if ticket.get("amount") != 0:
                raise ValueError("Ingresso externo gratuito exige valor zero")
        elif ticket["status"] == "unknown":
            if ticket.get("amount") is not None:
                raise ValueError("Ingresso não verificado não pode ter preço")
        else:
            raise ValueError("Estado do ingresso inválido")
        if row.get("additional_activity"):
            additional = row["additional_activity"]
            if (type(additional["amount"]) not in (int, float)
                    or additional["amount"] <= 0 or
                    not _https(additional["source_url"])):
                raise ValueError("Atividade adicional sem fonte/preço positivo")
            if additional.get("valid_for_2027") is not False:
                raise ValueError("Tarifa adicional futura não pesquisada")
        if (row.get("valid_for_2027") is not False or
                row.get("station_to_attraction_min") is not None or
                ticket.get("valid_for_2027") is not False):
            raise ValueError("Horários/tarifas atuais não garantem 2027/última milha")
    return deepcopy(doc)


def visit_decision_overview(*, discovery=None):
    data = load_visit_evidence(discovery=discovery)
    return {
        "entries": data["entries"], "pilot_count": len(data["entries"]),
        "2027_date_specific_opening_confirmed": 0,
        "door_to_door_verified": 0,
        "catalog_mutated": False, "wishlist_mutated": False,
    }
