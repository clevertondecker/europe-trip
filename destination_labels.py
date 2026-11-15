"""Consistent, country-grounded destination labels throughout the travel planner.

Flags are visual cues only; place and country names remain readable text.
Unknown countries never receive an inferred flag.
"""
from __future__ import annotations

FLAGS={
    "França":"🇫🇷",
    "Alemanha":"🇩🇪",
    "Suíça":"🇨🇭",
    "Luxemburgo":"🇱🇺",
    "Itália":"🇮🇹",
    "Espanha":"🇪🇸",
    "Países Baixos":"🇳🇱",
    "Bélgica":"🇧🇪",
    "Áustria":"🇦🇹",
}

def country_flag(country:str|None)->str:
    return FLAGS.get(country or "","")

def place_label(name:str,country:str|None=None,*,show_country:bool=False)->str:
    flag=country_flag(country)
    label=(flag+" " if flag else "")+name
    return label+(" · "+country if show_country and country else "")

def destination_names(catalog:dict,*,show_country:bool=False)->dict[str,str]:
    return {d["id"]:place_label(d["name"],d.get("country"),show_country=show_country)
            for d in catalog["destinations"]}
