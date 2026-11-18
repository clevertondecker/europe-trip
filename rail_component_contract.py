"""Read-only per-component research states; never a feasibility engine.

Only the outward city-level duration is queried by the parent DATA9 audit.
All other components default to not_evaluated. Optional overrides represent
already performed lookups, with provenance checked before they are admitted.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from urllib.parse import urlparse

STATES=frozenset({"documented","historical_only","indicative_reference",
    "editorial_estimate","not_evaluated","unknown_after_lookup",
    "not_applicable","incompatible"})
RAIL_COMPONENTS=(
    "outbound_rail_duration","outbound_departure_station","outbound_arrival_station",
    "dated_outbound_service_2027","outbound_transfers","return_rail_duration",
    "return_departure_station","return_arrival_station","return_service_calendar",
    "return_transfers","last_mile_outbound","last_mile_return","two_adults_fare",
)
LOCAL_COMPONENTS=("local_access_outbound","local_access_return",
                  "local_transport_two_adults_cost")
ATTRACTION_COMPONENTS=("attraction_opening_window",
                       "attraction_visit_duration_evidence")
ALL_COMPONENTS=RAIL_COMPONENTS+LOCAL_COMPONENTS+ATTRACTION_COMPONENTS
STATIONS={
    "outbound_departure_station":"outbound_departure_station_id",
    "outbound_arrival_station":"outbound_arrival_station_id",
    "return_departure_station":"return_departure_station_id",
    "return_arrival_station":"return_arrival_station_id",
}
DIRECTIONS={"last_mile_outbound":"arrival_station_to_attraction",
            "last_mile_return":"attraction_to_return_station"}
ALIASES={
    "last_mile_outbound":"last_mile_to_attraction",
    "last_mile_return":"last_mile_return_to_station",
    "outbound_transfers":"outbound_transfer_details",
    "return_transfers":"return_transfer_details",
    "return_service_calendar":"return_service_calendar",
    "return_rail_duration":"independent_return_service",
    "outbound_departure_station":"outbound_departure_station_identity",
    "outbound_arrival_station":"station_reconciliation",
    "return_departure_station":"return_departure_station_identity",
    "return_arrival_station":"return_arrival_station_identity",
    "dated_outbound_service_2027":"dated_outbound_service_2027",
    "two_adults_fare":"two_adults_fare",
    "attraction_opening_window":"attraction_opening_window",
    "attraction_visit_duration_evidence":"attraction_visit_duration_evidence",
    **{x:x for x in LOCAL_COMPONENTS},
}

def _https(value):
    if not isinstance(value,str): return False
    u=urlparse(value)
    return u.scheme=="https" and bool(u.hostname)

def _date(value):
    if not isinstance(value,str): raise ValueError("missing source date")
    return date.fromisoformat(value)

def _validate(component, supplied, *, base, dest, local):
    if component not in ALL_COMPONENTS or not isinstance(supplied,dict):
        raise ValueError("invalid component or observation")
    v=deepcopy(supplied)
    state=v.get("state")
    if state not in STATES: raise ValueError("invalid research state")
    if state=="not_applicable" and not (local and component in RAIL_COMPONENTS):
        raise ValueError("not_applicable is not proof of an available connection")
    if state in {"documented","historical_only","indicative_reference",
                 "unknown_after_lookup","incompatible"}:
        if not _https(v.get("source_url")) or not isinstance(v.get("source_dataset"),str) or not v["source_dataset"].strip():
            raise ValueError("claimed lookup/evidence needs source and dataset")
        _date(v.get("checked_at"))
    if state=="unknown_after_lookup":
        if (v.get("lookup_performed") is not True or v.get("lookup_outcome")!="no_match"
            or (v.get("lookup_base_id"),v.get("lookup_destination_id"),v.get("lookup_component"))!=(base,dest,component)):
            raise ValueError("unknown_after_lookup needs exact independently logged lookup")
    if state=="editorial_estimate":
        if not v.get("assumption") or v.get("valid_for_2027") is True:
            raise ValueError("editorial assumption is not an official result")
    if state=="incompatible" and (v.get("conflict_confirmed") is not True or not v.get("conflict_reason")):
        raise ValueError("station identity difference does not prove incompatibility")
    if state=="documented":
        if component in STATIONS and not v.get("station_id"):
            raise ValueError("documented station needs its own canonical station ID")
        if component in DIRECTIONS:
            if (v.get("direction")!=DIRECTIONS[component]
                or not v.get("from_id") or not v.get("to_id")
                or type(v.get("duration_min")) is not int or v["duration_min"]<=0):
                raise ValueError("last mile must have direction, endpoints and positive duration")
        if component=="return_rail_duration":
            if (not v.get("origin_station_id") or not v.get("destination_station_id")
                or type(v.get("duration_min")) is not int or v["duration_min"]<=0
                or _date(v.get("service_date")).year!=2027):
                raise ValueError("return leg needs independent dated stations and duration")
        if component in {"return_service_calendar","dated_outbound_service_2027"}:
            if _date(v.get("service_date")).year!=2027 or v.get("runs_on_date") is not True:
                raise ValueError("dated operating calendar required")
        if component in {"return_transfers","outbound_transfers"}:
            n=v.get("transfer_count")
            stations=v.get("transfer_station_ids")
            if (_date(v.get("service_date")).year!=2027 or type(n) is not int
                or n<0 or not isinstance(stations,list) or len(stations)!=n
                or any(not isinstance(x,str) or not x for x in stations)):
                raise ValueError("transfer details must match dated service")
        if component=="two_adults_fare":
            if (_date(v.get("fare_date")).year!=2027 or v.get("traveler_count")!=2
                or v.get("currency")!="EUR"
                or v.get("journey_scope") not in {"outbound_two_adults","return_two_adults","roundtrip_two_adults"}
                or type(v.get("amount_eur")) not in (int,float) or v["amount_eur"]<0):
                raise ValueError("fare must have traveler count, currency, date and journey scope")
        if component=="attraction_visit_duration_evidence":
            if type(v.get("duration_min")) is not int or v["duration_min"]<=0 or not v.get("visit_scope"):
                raise ValueError("visit needs explicit scope/duration")
        if component=="attraction_opening_window":
            if _date(v.get("service_date")).year!=2027 or not v.get("opens_at") or not v.get("closes_at"):
                raise ValueError("opening window must be dated")
    if v.get("valid_for_2027") is True and state!="documented":
        raise ValueError("historical/editorial references are not current availability")
    return v

def build_component_records(inventory, *, evidence_by_pair=None):
    """Compose already supplied source observations; never query or rank routes."""
    inputs={} if evidence_by_pair is None else evidence_by_pair
    if not isinstance(inputs,dict): raise ValueError("pair indexed evidence required")
    pairs=[]
    seen=set()
    for row in inventory["pairs"]:
        base,dest,cat=row["base_id"],row["destination_id"],row["category"]
        key=(base,dest)
        if key in seen: raise ValueError("duplicate pair")
        seen.add(key)
        if cat not in {"historical","indicative","missing","local"}:
            raise ValueError("unknown rail evidence category")
        local=cat=="local"
        duration=row.get("oneway_min")
        if local:
            if base!=dest or duration is not None: raise ValueError("local access is not a zero-minute train")
        elif base==dest or (cat=="missing" and duration is not None):
            raise ValueError("unresearched or local identity conflict")
        elif cat in {"historical","indicative"} and (type(duration) is not int or duration<=0):
            raise ValueError("documentary duration must be positive")
        if (row.get("return_2027_verified") is not False
            or row.get("door_to_door_2027_verified") is not False
            or row.get("fare_couple_2027_eur") is not None):
            raise ValueError("source inventory does not prove return or fare")
        states={c:{"state":("not_applicable" if
                    (local and c in RAIL_COMPONENTS) or
                    (not local and c in LOCAL_COMPONENTS)
                    else "not_evaluated")} for c in ALL_COMPONENTS}
        if cat in {"historical","indicative"} and _https(row.get("source_url")):
            states["outbound_rail_duration"]={
                "state":"historical_only" if cat=="historical" else "indicative_reference",
                "duration_min":duration,"source_url":row["source_url"],
                "source_dataset":"historical_rail_inventory",
                "checked_at":row.get("source_checked_at")}
        overrides=inputs.get(key,{})
        if not isinstance(overrides,dict): raise ValueError("component observations must be a mapping")
        if any(c not in ALL_COMPONENTS for c in overrides): raise ValueError("unknown component key")
        if local and any(c in RAIL_COMPONENTS for c in overrides):
            raise ValueError("no intercity train for same city")
        if not local and any(c in LOCAL_COMPONENTS for c in overrides):
            raise ValueError("use last-mile for nonlocal urban access")
        if "outbound_rail_duration" in overrides:
            raise ValueError("historical rail evidence precedence cannot be overridden")
        station_ids={field:None for field in STATIONS.values()}
        for component,value in overrides.items():
            validated=_validate(component,value,base=base,dest=dest,local=local)
            states[component]=validated
            if component in STATIONS and validated["state"]=="documented":
                station_ids[STATIONS[component]]=validated["station_id"]
        required=[]
        if local:
            required.extend(LOCAL_COMPONENTS)
        else:
            if cat=="missing":
                required.extend(("operator_route_page","published_oneway_duration"))
            if not row.get("source_url"):required.append("operator_route_page")
            if not row.get("source_checked_at"):required.append("source_date")
            required.extend(("station_reconciliation","dated_outbound_service_2027",
                "independent_return_service","two_adults_fare","last_mile_to_attraction",
                "last_mile_return_to_station","return_service_calendar",
                "outbound_transfer_details","return_transfer_details",
                "return_departure_station_identity","return_arrival_station_identity",
                "outbound_departure_station_identity"))
        required.extend(ATTRACTION_COMPONENTS)
        for c,v in overrides.items():
            alias=ALIASES.get(c)
            complete= c!="two_adults_fare" or v.get("journey_scope")=="roundtrip_two_adults"
            if v["state"]=="documented" and complete and alias in required:required.remove(alias)
        outwalk=states["last_mile_outbound"]
        retwalk=states["last_mile_return"]
        if outwalk["state"]=="documented" and station_ids["outbound_arrival_station_id"] and outwalk["from_id"]!=station_ids["outbound_arrival_station_id"]:
            required.append("outbound_last_mile_station_alignment")
        if retwalk["state"]=="documented" and station_ids["return_departure_station_id"] and retwalk["to_id"]!=station_ids["return_departure_station_id"]:
            required.append("return_last_mile_station_alignment")
        pairs.append({
            "base_id":base,"destination_id":dest,"base_name":row["base_name"],
            "destination_name":row["destination_name"],"category":cat,
            "known_outbound_oneway_min":duration,"source_url":row.get("source_url"),
            "component_states":states,"station_identities":station_ids,
            "research_required":list(dict.fromkeys(required)),
            "return_2027_verified":False,"confirmed_2027":False,
        })
    if len(pairs)!=inventory["total_pairs"] or set(inputs)-seen:
        raise ValueError("inventory incomplete or unknown pair in overrides")
    return pairs
