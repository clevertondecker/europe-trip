"""Budget screens: concrete preselected trip proposals without implicit approval.

Every financial card owns a real profile-specific set of destinations,
attractions, known fares, unknown components and tentative assignments.
"""
from __future__ import annotations

from decimal import Decimal


def preset_budget_summary(option:dict, plan:dict, eurfx:float, chffx:float)->dict:
    packages=option["proposal_packages"]
    approved=set(plan["packages"])
    known=option["known_cost_by_currency"]
    historical_brl=round(float(
        Decimal(str(known["EUR"]))*Decimal(str(eurfx))+
        Decimal(str(known["CHF"]))*Decimal(str(chffx))),2)
    finance=option["financial"]
    allowance=float(finance["budget_excursions_allowance_brl"])
    return {
        "profile":option["profile"],"label":option["label"],
        "packages":{d:list(ids) for d,ids in packages.items()},
        "new":sorted(set(packages)-approved),
        "approved":sorted(set(packages)&approved),
        "assignments":dict(option["preview_assignments"]),
        "unresolved":list(option["unresolved"]),
        "known_brl":historical_brl,
        "allowance_brl":allowance,
        "remaining_known_allowance_brl":max(0.0,round(allowance-historical_brl,2)),
        "overage_brl":float(finance["known_excursions_overage_brl"]),
        "global_total_brl":float(finance["result"]["total"]),
        "margin_brl":float(finance["result"]["margin"]),
        "missing":list(option["missing_costs"]),
        "budget_scenario":plan["budget_scenario"],
        "base_city":plan["base_city"],
    }


def validate_predefined_budget(plan:dict,option:dict)->None:
    """Reject stale and disallowed proposals before deliberate application."""
    from recommended_itineraries import approve_profile_scenario
    # Probe the domain approval without persisting, so review uses identical rules.
    approve_profile_scenario(plan,option,approved=True)
