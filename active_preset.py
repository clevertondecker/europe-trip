"""One canonical source for the active, preselected itinerary across screens.

A profile preset is a preview until the traveler approves it. Reuse the same
profile builder that powers the budget and scenario comparison; never silently
mutate TripPlan or present historical costs as confirmed 2027 quotes.
"""
from __future__ import annotations

from travel_profile_scenarios import build_profile_scenarios
from predefined_budget_model import preset_budget_summary
from destination_labels import destination_names


def active_preset(plan:dict,catalog:dict,routes:dict,trip_data:dict,
                  live:bool,eurfx:float,chffx:float,use_city_rent:bool=True,
                  allow_overnight:bool=False)->dict:
    options=build_profile_scenarios(
        plan,catalog,routes,trip_data,live,eurfx,chffx,
        use_city_rent=use_city_rent,allow_overnight=allow_overnight)
    option=next(item for item in options if item["profile"]==plan["profile"])
    return {"option":option,
            "summary":preset_budget_summary(option,plan,eurfx,chffx)}


def preset_destination_names(summary:dict,catalog:dict)->list[str]:
    names=destination_names(catalog)
    return [names.get(key,key) for key in summary["packages"]]
