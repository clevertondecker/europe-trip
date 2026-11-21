"""Read-only planning journey. No persisted progress or new planning authority."""
from __future__ import annotations

from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE, selected_rows, UNASSIGNED
from ux61_destination_board_model import (
    build_destination_board, board_metrics, organizer_wishlist_candidates,
)


def project_planning(plan, interests, discovery, catalog, *, private_saved=False):
    board=build_destination_board(interests,plan,discovery,catalog)
    counts=board_metrics(board)
    rows=selected_rows(plan,catalog)
    batches={stage:organizer_wishlist_candidates(interests,plan,discovery,catalog,stage)
             for stage in (ITALY_STAGE,FRANCE_STAGE)}
    eligible=sum(len(b["eligible"]) for b in batches.values())
    unsupported=batches[ITALY_STAGE]["unsupported"]
    pending=[r for r in rows if r["period"]==UNASSIGNED and not r["exact_dates"]]
    if eligible:
        action="build"
        phase="draft_with_pending" if rows else "eligible_wishes"
    elif rows:
        action="review"
        phase="draft_with_no_eligible_pending" if counts["wished"] else "draft_without_wishes"
    elif unsupported:
        action="exploratory"
        phase="exploratory_only"
    else:
        action="choose"
        phase="empty"
    return {"counts":counts,"rows":rows,"batches":batches,"eligible_count":eligible,
            "unsupported":unsupported,"pending":pending,"next":action,"phase":phase,
            "private_saved":bool(private_saved),
            "steps":[
                ("choose","Escolher destinos",f'{counts["wished"]} desejados'),
                ("build","Montar roteiro",f'{counts["planned"]} incluídos'),
                ("organize","Organizar visitas",f'{counts["organized"]} com período ou data'),
                ("review","Revisar e salvar","Salvo em espaço privado" if private_saved else "Rascunho a salvar"),
            ]}


def clear_planning_context(state):
    """Discard ephemeral planning UI state after a restore or identity change."""
    for key in list(state.keys()):
        if isinstance(key,str) and key.startswith("flow_journey_"):
            state.pop(key,None)
