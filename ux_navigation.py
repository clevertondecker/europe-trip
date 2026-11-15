"""UX 3.0: task-oriented navigation, with a non-breaking legacy route adapter.

Presentation only. The canonical TripPlan and the research catalog are unchanged.
Callbacks run *before* widgets render, so no widget state is mutated after its
instantiation. Legacy deep-links remain usable through an advanced expander.
"""
from __future__ import annotations

AREAS = ("Minha viagem", "Explorar", "Meu roteiro", "Orçamento")
SECTIONS = {
    "Minha viagem": ("Resumo", "Pendências", "Decisões"),
    "Explorar": ("Cidades-base", "Comparar", "Passeios", "Mapa"),
    "Meu roteiro": ("Visão geral", "Itália", "França", "Calendário", "Sugestões"),
    "Orçamento": ("Resumo financeiro", "Simulações", "Detalhamento"),
}
# Migration for bookmarks and callbacks from UX 3.0. Public task names stay stable.
TASK_ALIASES = {
    ("Minha viagem", "Pendências e fontes"): "Pendências",
    ("Explorar", "Comparar cidades"): "Comparar",
    ("Explorar", "Passeios e destinos"): "Passeios",
    ("Explorar", "Mais pesquisas"): "Cidades-base",
    ("Meu roteiro", "Visão do roteiro"): "Visão geral",
    ("Meu roteiro", "Meus passeios"): "França",
    ("Orçamento", "Visão financeira"): "Resumo financeiro",
    ("Orçamento", "Passeios e custos"): "Detalhamento",
}
DEFAULT_SECTION = {area: sections[0] for area, sections in SECTIONS.items()}
GUIDES = ("Explorar atrações", "Itália e Costa Amalfitana",
          "França e escapadas", "Transportes e custos",
          "Calendário de pesquisa", "Cronograma oficial")
RESEARCH_OPTIONS = ("Pesquisa ampliada", "França e escapadas",
                    "Transportes e custos", "Itália e Costa Amalfitana",
                    "Calendário de pesquisa", "Cronograma oficial")
SUGGESTION_OPTIONS = ("Descobrir", "Simular roteiros", "Guias especializados")
LEGACY_PAGES = ("Visão geral", "Mapa & destinos", "Comparar cidades",
                "Roteiro", "Orçamento", "Pesquisas & decisões")
LEGACY_ITINERARY = ("Visão geral", "Itália", "Meus passeios", "Explorar bases",
                    "Descobrir", "Orçamento", "Calendário",
                    "Simular roteiros", "Guias e pesquisas")

DESCRIPTIONS = {
    ("Minha viagem", "Resumo"): "O estado da viagem e os próximos passos.",
    ("Minha viagem", "Pendências"): "Pesquisas e decisões ainda por resolver.",
    ("Minha viagem", "Decisões"): "Escolhas registradas e evidências oficiais.",
    ("Explorar", "Cidades-base"): "Conheça cidades e suas pesquisas sem mudar o plano.",
    ("Explorar", "Comparar"): "Veja o custo e os destinos afetados ao trocar de base.",
    ("Explorar", "Passeios"): "Explore atrações e viagens próximas.",
    ("Explorar", "Mapa"): "Localize cidades e referências geográficas.",
    ("Meu roteiro", "Visão geral"): "Confira as etapas da viagem.",
    ("Meu roteiro", "Itália"): "Roma, Costa Amalfitana e lua de mel.",
    ("Meu roteiro", "França"): "Passeios escolhidos, França e deslocamentos.",
    ("Meu roteiro", "Calendário"): "Distribua atividades pelos dias.",
    ("Meu roteiro", "Sugestões"): "Descubra destinos ou simule melhorias.",
    ("Orçamento", "Resumo financeiro"): "Confira o teto e as principais categorias.",
    ("Orçamento", "Simulações"): "Teste hospedagem, duração, passeios e câmbio.",
    ("Orçamento", "Detalhamento"): "Consulte rubricas, limites e fontes.",
}


def route(area: str, section: str, *, research: str = "Pesquisa ampliada",
          suggestion: str = "Descobrir", france: str = "Meus passeios",
          city_view: str = "Visão da cidade",
          budget_view: str = "Simulação geral", guide_view: str = "Itália e Costa Amalfitana"
          ) -> tuple[str, str | None, str | None, str | None]:
    """Map the 15 task tabs into existing page modules."""
    section = TASK_ALIASES.get((area, section), section)
    if area not in SECTIONS or section not in SECTIONS[area]:
        raise ValueError("Área ou aba desconhecida")
    if area == "Minha viagem":
        return ("Visão geral" if section == "Resumo" else "Pesquisas & decisões",
                None, None, None)
    if area == "Explorar":
        if section == "Comparar":
            return "Comparar cidades", None, None, None
        if section == "Mapa":
            return "Mapa & destinos", None, None, None
        if section == "Passeios":
            return "Roteiro", "Guias e pesquisas", "Explorar atrações", None
        return ("Roteiro","Explorar bases",None,
                "Pesquisa ampliada" if city_view=="Pesquisa ampliada"
                else "Destinos próximos")
    if area == "Orçamento":
        if section == "Simulações" and budget_view == "Consultor de passeios":
            return "Roteiro", "Orçamento", None, None
        return "Orçamento", None, None, None
    if section == "Visão geral":
        return "Roteiro", "Visão geral", None, None
    if section == "Itália":
        return "Roteiro", "Itália", None, None
    if section == "França":
        if france in ("França e escapadas", "Transportes e custos"):
            return "Roteiro", "Guias e pesquisas", france, None
        return "Roteiro", "Meus passeios", None, None
    if section == "Calendário":
        return "Roteiro", "Calendário", None, None
    if suggestion=="Guias especializados":
        return "Roteiro", "Guias e pesquisas", (guide_view if guide_view in GUIDES
                                                 else GUIDES[0]), None
    return "Roteiro", (suggestion if suggestion in SUGGESTION_OPTIONS[:2]
                       else SUGGESTION_OPTIONS[0]), None, None


def from_legacy(page: str, itinerary: str | None = None,
                guide: str | None = None) -> tuple[str, str]:
    """Map old deep-links back into a visible UX 3.1 tab."""
    if page == "Visão geral":
        return "Minha viagem", "Resumo"
    if page == "Pesquisas & decisões":
        return "Minha viagem", "Pendências"
    if page == "Orçamento":
        return "Orçamento", "Resumo financeiro"
    if page == "Mapa & destinos":
        return "Explorar", "Mapa"
    if page == "Comparar cidades":
        return "Explorar", "Comparar"
    if itinerary == "Visão geral":
        return "Meu roteiro", "Visão geral"
    if itinerary == "Itália":
        return "Meu roteiro", "Itália"
    if itinerary == "Explorar bases":
        return "Explorar", "Cidades-base"
    if itinerary in ("Descobrir", "Simular roteiros"):
        return "Meu roteiro", "Sugestões"
    if itinerary == "Calendário":
        return "Meu roteiro", "Calendário"
    if itinerary == "Orçamento":
        return "Orçamento", "Detalhamento"
    if itinerary == "Guias e pesquisas":
        if guide in ("França e escapadas", "Transportes e custos"):
            return "Meu roteiro", "França"
        if guide == "Explorar atrações" or guide is None:
            return "Explorar", "Passeios"
        return "Meu roteiro", "Sugestões"
    return "Meu roteiro", "França"


def apply(state) -> tuple[str, str | None, str | None, str | None]:
    """Synchronize legacy keys BEFORE Streamlit instantiates corresponding widgets."""
    area = state.get("ux_area", AREAS[0])
    if area not in SECTIONS:
        area = AREAS[0]
        state["ux_area"] = area
    section = state.get("ux_section", DEFAULT_SECTION[area])
    section = TASK_ALIASES.get((area, section), section)
    state["ux_section"] = section
    if section not in SECTIONS[area]:
        section = DEFAULT_SECTION[area]
        state["ux_section"] = section
    research = state.get("ux_research", RESEARCH_OPTIONS[0])
    suggestion = state.get("ux_suggestion", SUGGESTION_OPTIONS[0])
    france = state.get("ux_france_view", "Meus passeios")
    city_view = state.get("ux_city_view","Visão da cidade")
    budget_view = state.get("ux_budget_view","Simulação geral")
    guide_view = state.get("ux_guide_view",GUIDES[0])
    target = route(area, section, research=research, suggestion=suggestion,
                   france=france,city_view=city_view,budget_view=budget_view,
                   guide_view=guide_view)
    page, itinerary, guide, base_mode = target
    state["main_navigation"] = page
    if itinerary is not None:
        state["itinerary_section"] = itinerary
    if guide is not None:
        state["guide_section"] = guide
    if base_mode == "Pesquisa ampliada":
        state["base_explorer_mode"] = "Pesquisa ampliada"
    elif base_mode is not None and "base_explorer_mode" not in state:
        state["base_explorer_mode"] = base_mode
    state["_ux_legacy_page"] = page
    state["_ux_legacy_itinerary"] = itinerary
    state["_ux_legacy_guide"] = guide
    return target


def bootstrap(state) -> tuple[str, str | None, str | None, str | None]:
    """Recover old bookmarks and internally-set legacy navigation requests."""
    if "ux_area" not in state:
        area, section = from_legacy(
            state.get("main_navigation", "Visão geral"),
            state.get("itinerary_section"), state.get("guide_section"))
        state["ux_area"], state["ux_section"] = area, section
    else:
        previous = state.get("_ux_legacy_page")
        request = state.get("main_navigation")
        if previous and request and request != previous:
            area, section = from_legacy(
                request, state.get("itinerary_section"), state.get("guide_section"))
            state["ux_area"], state["ux_section"] = area, section
        elif (request == "Roteiro" and previous == "Roteiro"
              and state.get("_ux_legacy_itinerary") is not None
              and state.get("itinerary_section") != state["_ux_legacy_itinerary"]):
            itinerary = state.get("itinerary_section")
            area, section = from_legacy("Roteiro", itinerary,
                                        state.get("guide_section"))
            state["ux_area"], state["ux_section"] = area, section
            if itinerary in SUGGESTION_OPTIONS:
                state["ux_suggestion"] = itinerary
            if itinerary == "Guias e pesquisas" and state.get("guide_section") in RESEARCH_OPTIONS:
                state["ux_research"] = state["guide_section"]
    return apply(state)


def set_area(state, area: str) -> None:
    state["ux_area"] = area
    state["ux_section"] = DEFAULT_SECTION[area]
    apply(state)


def set_task(state, area: str, section: str) -> None:
    if section not in SECTIONS[area]:
        raise ValueError("Tarefa de navegação inválida")
    state["ux_area"] = area
    state["ux_section"] = section
    section = TASK_ALIASES.get((area, section), section)
    if (area, section)==("Explorar", "Cidades-base"):
        state["base_explorer_mode"]="Destinos próximos"
    apply(state)


def set_from_legacy(state, page: str,
                    itinerary: str | None = None,
                    guide: str | None = None) -> None:
    area, section = from_legacy(page, itinerary, guide)
    state["ux_area"], state["ux_section"] = area, section
    if itinerary in SUGGESTION_OPTIONS:
        state["ux_suggestion"] = itinerary
    if itinerary == "Guias e pesquisas" and guide in RESEARCH_OPTIONS:
        state["ux_research"] = guide
    if itinerary == "Guias e pesquisas" and guide in GUIDES and guide not in ("Explorar atrações","França e escapadas","Transportes e custos"):
        state["ux_suggestion"]="Guias especializados"
        state["ux_guide_view"]=guide
    if itinerary == "Guias e pesquisas" and guide in ("França e escapadas", "Transportes e custos"):
        state["ux_france_view"] = guide
    if itinerary == "Meus passeios":
        state["ux_france_view"] = "Meus passeios"
    if itinerary == "Explorar bases":
        state["ux_city_view"]=("Pesquisa ampliada" if
            state.get("base_explorer_mode")=="Pesquisa ampliada"
            else "Visão da cidade")
    if itinerary == "Orçamento":
        state["ux_budget_view"]="Consultor de passeios"
    if itinerary == "Explorar bases" and state.get("base_explorer_mode") == "Pesquisa ampliada":
        state["ux_research"] = "Pesquisa ampliada"
        state["ux_section"] = "Cidades-base"
    apply(state)
