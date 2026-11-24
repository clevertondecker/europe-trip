"""Read-only eligibility derived solely from the itinerary inventory."""
from __future__ import annotations
from destination_identity import canonical_destination_id, outing_destination_id

def eligibility_index(catalog):
    from itinerary_flow_model import destinations
    return {outing_destination_id(row["id"]): row for row in destinations(catalog)}

def itinerary_eligibility(destination_id, catalog, stage="França", *, index=None):
    from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE
    if stage not in (ITALY_STAGE, FRANCE_STAGE):
        raise ValueError("Etapa inválida")
    key = canonical_destination_id(destination_id)
    choice = (eligibility_index(catalog) if index is None else index).get(outing_destination_id(key))
    result = {"destination_id": key, "outing_id": choice["id"] if choice else None,
              "stage": choice["stage"] if choice else None}
    if choice is None:
        return {**result, "status": "research_only",
                "reason": "Atrações deste destino ainda não foram catalogadas para o roteiro. A inclusão ainda não é suportada pelo planejador."}
    if choice["stage"] != stage:
        return {**result, "status": "other_stage",
                "reason": "Este destino pertence à etapa " + choice["stage"] + " da viagem."}
    return {**result, "status": "eligible",
            "reason": "Você pode incluir este destino no roteiro sem definir datas ou atrações."}
