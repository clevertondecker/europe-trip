"""Validate *new* full-day France outings without rejecting legacy saved drafts.

The TripPlan schema v1 is kept unchanged. Existing persisted plans are readable;
invalid new proposals/assignments fail rather than silently changing them.
"""
from __future__ import annotations

from datetime import date

from calendar_model import calendar_plan


def validate_new_assignments(plan:dict, assignments:dict, *,
                             previously_approved:dict|None=None)->None:
    if not isinstance(assignments,dict):
        raise ValueError("Datas de passeios inválidas")
    schedule={row["date"]:row for row in calendar_plan(
        date.fromisoformat(plan["departure_date"]),plan["total_days"],
        plan["italy_days"],plan["vacation_days"],plan["setup_days"])}
    approved=previously_approved or {}
    for day,dest in assignments.items():
        if approved.get(day)==dest:
            continue  # Preserve load/edit compatibility with older saved plans.
        if not isinstance(day,str) or day not in schedule:
            raise ValueError("Passeio fora das datas da viagem")
        eligible = dest in plan["packages"] or any(
            v["destination_id"] == dest and v["stage"] == "França"
            for v in plan.get("flexible_visits", []))
        if not eligible:
            raise ValueError("Passeio agendado sem cidade incluída no roteiro")
        row=schedule[day]
        if (row["stage"]!="França" or row["activity"]=="Instalação" or
                "Trabalho remoto" in row["activity"]):
            raise ValueError("Passeio de dia inteiro conflita com trabalho, Itália ou instalação")
