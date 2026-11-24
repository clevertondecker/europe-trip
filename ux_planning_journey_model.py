"""Read-only planning journey. No persisted progress or new planning authority."""
from __future__ import annotations

from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE, selected_rows, UNASSIGNED
from ux61_destination_board_model import (
    build_destination_board, board_metrics, organizer_wishlist_candidates,
)


def project_planning(plan, interests, discovery, catalog, *, private_saved=False, weekend_groups=None):
    board=build_destination_board(interests,plan,discovery,catalog,weekend_groups)
    counts=board_metrics(board)
    rows=selected_rows(plan,catalog)
    batches={stage:organizer_wishlist_candidates(interests,plan,discovery,catalog,stage)
             for stage in (ITALY_STAGE,FRANCE_STAGE)}
    eligible=sum(len(b["eligible"]) for b in batches.values())
    unsupported=batches[ITALY_STAGE]["unsupported"]
    by_id={r["id"]:r for r in board}
    pending=[r for r in rows if not by_id[r["id"]]["organized"]]
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
    # The full editor can still open an undated draft for independent saving.
    # The overview next action reflects useful travel work, not persistence.
    editor_next=action
    if action=="review" and pending:
        action="organize"
    stages={}
    for stage in (ITALY_STAGE,FRANCE_STAGE):
        stage_rows=[r for r in board if r["planned"] and r["stage"]==stage]
        stage_counts=board_metrics(stage_rows)
        stages[stage]={**stage_counts,
                       "days":plan["italy_days"] if stage==ITALY_STAGE else plan["total_days"]-plan["italy_days"],
                       "pending":stage_counts["planned"]-stage_counts["organized"],
                       "eligible":len(batches[stage]["eligible"]),
                       "groups":len({r["group_id"] for r in stage_rows if r["group_id"]})}
    next_stage=next((stage for stage in (ITALY_STAGE,FRANCE_STAGE)
                     if stages[stage]["eligible" if action=="build" else "pending"]),None) if action in ("build","organize") else None
    commitments=[]
    seen_groups=set()
    for row in board:
        if not row["planned"]:
            continue
        for day in row["individual_dates"]:
            commitments.append({"kind":"individual","name":row["name"],"stage":row["stage"],
                                "start":day,"end":day,"period":None})
        group_id=row["group_id"]
        if group_id and group_id not in seen_groups:
            seen_groups.add(group_id)
            if row["group_dates"] or row["group_period"]:
                dates=row["group_dates"]
                commitments.append({"kind":"group","name":row["group_name"],"stage":row["stage"],
                                    "start":dates[0] if dates else None,"end":dates[-1] if dates else None,
                                    "period":row["group_period"]})
    commitments.sort(key=lambda r:(r["start"] is None,r["start"] or "",r["name"]))
    return {"stages":stages,"next_stage":next_stage,"commitments":commitments,
            "editor_next":editor_next,
            "counts":counts,"rows":rows,"board":board,"batches":batches,"eligible_count":eligible,
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
