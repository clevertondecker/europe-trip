"""Read-only eligibility derived solely from the itinerary inventory."""
from __future__ import annotations

from destination_identity import canonical_destination_id

def itinerary_eligibility(destination_id, catalog, stage="França"):
    from itinerary_flow_model import destinations, ITALY_STAGE, FRANCE_STAGE
    if stage not in (ITALY_STAGE, FRANCE_STAGE):
        raise ValueError("Etapa inválida")
    key = canonical_destination_id(destination_id)
    # The Italian proposal uses a separate namespace.
    italy_key = {"rome": "italy_rome", "naples": "italy_naples"}.get(key, key)
    choice = next((row for row in destinations(catalog)
                   if canonical_destination_id(row["id"]) == key
                   or row["id"] == italy_key), None)
    if choice is None:
        return {"status": "research_only", "stage": None,
                "reason": "Atrações deste destino ainda não foram catalogadas para o roteiro."}
    if choice["stage"] != stage:
        return {"status": "other_stage", "stage": choice["stage"],
                "reason": "Este destino pertence à etapa " + choice["stage"] + " da viagem."}
    return {"status": "eligible", "stage": choice["stage"],
            "reason": "Você pode incluir este destino no roteiro sem definir datas ou atrações."}
