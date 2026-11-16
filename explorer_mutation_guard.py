"""P0: explorer mutation boundary. No simulation may write the canonical TripPlan."""
from __future__ import annotations

from planning_session import (
    active_plan, upsert_flexible_choice, remove_flexible_choice,
    update_interest, schedule_package, unschedule_package,
)
from itinerary_flow_model import UNASSIGNED


class SimulationWriteBlocked(PermissionError):
    pass


def can_edit(base: str, plan: dict, mode: str = "Oficial") -> bool:
    return base == plan["base_city"] and mode != "Simulação"


def _guard(base: str, mode: str) -> None:
    if not can_edit(base, active_plan(), mode):
        raise SimulationWriteBlocked(
            "Simulação: nenhuma alteração foi aplicada ao roteiro oficial."
        )


def save_outing(base: str, mode: str, destination: str, attractions: list[str]) -> None:
    _guard(base, mode)
    upsert_flexible_choice(destination, attractions, UNASSIGNED)


def remove_outing(base: str, mode: str, destination: str) -> None:
    _guard(base, mode)
    remove_flexible_choice(destination)


def change_interest(base: str, mode: str, attraction: str, value: str) -> None:
    _guard(base, mode)
    update_interest(attraction, value)


def schedule_outing(base: str, mode: str, day: str, destination: str) -> None:
    _guard(base, mode)
    schedule_package(day, destination)


def unschedule_outing(base: str, mode: str, day: str) -> None:
    _guard(base, mode)
    unschedule_package(day)
