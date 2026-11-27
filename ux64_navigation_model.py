"""UX 6.4: public three-area navigation backed by the existing canonical router.

The legacy 4-area route IDs remain accepted for bookmarks and archives. Public
labels are a compatibility presentation, not a second persisted router.
"""
from __future__ import annotations

PUBLIC_AREAS=("Explorar","Planejar","Orçamento")
PUBLIC_TASKS={
    "Explorar":("Descobrir","Minha lista","Comparar bases","Cobertura dos dados","Mapa"),
    "Planejar":("Visão geral","Meus destinos","Organizar"),
    "Orçamento":("Visão financeira","Simulações"),
}
TARGETS={
    ("Explorar","Descobrir"):("Explorar","Passeios"),
    ("Explorar","Minha lista"):("Explorar","Passeios"),
    ("Explorar","Comparar bases"):("Explorar","Comparar"),
    ("Explorar","Cobertura dos dados"):("Explorar","Cobertura dos dados"),
    ("Explorar","Mapa"):("Explorar","Mapa"),
    ("Planejar","Visão geral"):("Minha viagem","Resumo"),
    ("Planejar","Meus destinos"):("Meu roteiro","Meu planejamento"),
    ("Planejar","Organizar"):("Meu roteiro","Organizar viagem"),
    ("Orçamento","Visão financeira"):("Orçamento","Resumo financeiro"),
    ("Orçamento","Simulações"):("Orçamento","Simulações"),
}


def public_area(legacy_area):
    return "Planejar" if legacy_area in ("Minha viagem","Meu roteiro") else (
        legacy_area if legacy_area in PUBLIC_AREAS else "Planejar")


def public_task(legacy_area, legacy_section, wishlist_view=None):
    if legacy_area=="Explorar":
        return ("Minha lista" if legacy_section=="Passeios"
                and wishlist_view=="Minha lista" else
                "Descobrir" if legacy_section=="Passeios" else
                "Mapa" if legacy_section=="Mapa" else
                "Cobertura dos dados" if legacy_section=="Cobertura dos dados" else "Comparar bases")
    if legacy_area=="Minha viagem":
        return "Visão geral"
    if legacy_area=="Meu roteiro":
        if legacy_section=="Melhorar meu roteiro":
            return None  # Secondary content is not the public destination editor.
        return "Organizar" if legacy_section=="Organizar viagem" else "Meus destinos"
    if legacy_area=="Orçamento":
        return "Simulações" if legacy_section=="Simulações" else "Visão financeira"
    return "Visão geral"


def select_public_task(state, area, task):
    if area not in PUBLIC_TASKS or task not in PUBLIC_TASKS[area]:
        raise ValueError("Área/atividade desconhecida")
    state["ux64_public_task"] = task
    from ux_navigation import set_task
    if (area=="Explorar" and task in ("Descobrir","Minha lista")
            and "ux502_discovery_filters" not in state):
        filters=dict(state.get("ux502_discovery_filters",{}))
        filters.update({key:state[key] for key in
                        ("ux501_country","ux501_categories","ux501_search","ux501_page")
                        if key in state})
        if filters:
            state["ux502_discovery_filters"]=filters
    target_area,target_section=TARGETS[(area,task)]
    previous=(state.get("ux_area"),state.get("ux_section"))
    set_task(state,target_area,target_section)
    if (area,task)==("Explorar","Comparar bases"):
        # Public task navigation starts at suggestions; REC03B/manual intents
        # deliberately override this *after* selecting the public task.
        state["rec03a_activity"]="Cidades sugeridas"
    # UX83: public navigation switches the focused *panel*, not the saved data.
    # Intent handoffs override this with their explicit build/review/organize.
    if area=="Planejar" and task=="Organizar":
        state["flow_journey_view"]="organize"
    elif area=="Planejar" and task=="Meus destinos" and previous==(
            "Meu roteiro","Organizar viagem"):
        state["flow_journey_view"]=None
    if (area,task)==("Explorar","Minha lista"):
        state["ux502_view"]="Minha lista"
    elif (area,task)==("Explorar","Descobrir"):
        state["ux502_view"]="Descobrir lugares"


def select_public_area(state, area):
    if area not in PUBLIC_AREAS:
        raise ValueError("Área desconhecida")
    preferred={"Explorar":"Descobrir","Planejar":"Visão geral",
               "Orçamento":"Visão financeira"}
    select_public_task(state,area,preferred[area])
