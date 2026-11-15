"""UX 3.0: task-oriented navigation, with a non-breaking legacy route adapter.

Presentation only. The canonical TripPlan and the research catalog are unchanged.
Callbacks run *before* widgets render, so no widget state is mutated after its
instantiation. Legacy deep-links remain usable through an advanced expander.
"""
from __future__ import annotations

AREAS = ("Minha viagem", "Explorar", "Meu roteiro", "Orçamento")
SECTIONS = {
    "Minha viagem": ("Resumo", "Pendências e fontes"),
    "Explorar": ("Cidades-base", "Comparar cidades", "Passeios e destinos",
                 "Mapa", "Mais pesquisas"),
    "Meu roteiro": ("Visão do roteiro", "Itália", "Meus passeios",
                    "Calendário", "Sugestões"),
    "Orçamento": ("Visão financeira", "Passeios e custos"),
}
DEFAULT_SECTION = {area: sections[0] for area, sections in SECTIONS.items()}
GUIDES = ("Explorar atrações", "Itália e Costa Amalfitana",
          "França e escapadas", "Transportes e custos",
          "Calendário de pesquisa", "Cronograma oficial")
RESEARCH_OPTIONS = ("Pesquisa ampliada", "França e escapadas",
                    "Transportes e custos", "Itália e Costa Amalfitana",
                    "Calendário de pesquisa", "Cronograma oficial")
SUGGESTION_OPTIONS = ("Descobrir", "Simular roteiros")
LEGACY_PAGES = ("Visão geral", "Mapa & destinos", "Comparar cidades",
                "Roteiro", "Orçamento", "Pesquisas & decisões")
LEGACY_ITINERARY = ("Visão geral", "Itália", "Meus passeios", "Explorar bases",
                    "Descobrir", "Orçamento", "Calendário",
                    "Simular roteiros", "Guias e pesquisas")

DESCRIPTIONS = {
    ("Minha viagem", "Resumo"): "Visão da viagem e seu próximo passo.",
    ("Minha viagem", "Pendências e fontes"): "Acompanhe decisões, pesquisas e links oficiais.",
    ("Explorar", "Cidades-base"): "Investigue qualquer cidade-base sem mudar o roteiro.",
    ("Explorar", "Comparar cidades"): "Compare condições, custos e dados pesquisados.",
    ("Explorar", "Passeios e destinos"): "Descubra lugares e monte sua lista de atrações.",
    ("Explorar", "Mapa"): "Veja onde ficam os destinos e as etapas da viagem.",
    ("Explorar", "Mais pesquisas"): "Pesquisas detalhadas de transporte, França e cronograma.",
    ("Meu roteiro", "Visão do roteiro"): "Consulte as etapas da Itália ao retorno.",
    ("Meu roteiro", "Itália"): "Planeje a lua de mel na Itália e na Costa Amalfitana.",
    ("Meu roteiro", "Meus passeios"): "Organize os passeios selecionados.",
    ("Meu roteiro", "Calendário"): "Distribua atividades e verifique os dias disponíveis.",
    ("Meu roteiro", "Sugestões"): "Descubra destinos e simule melhorias do roteiro.",
    ("Orçamento", "Visão financeira"): "Compare os custos e ajuste as premissas da viagem.",
    ("Orçamento", "Passeios e custos"): "Detalhe a parcela de passeios do plano.",
}


def route(area: str, section: str, *, research: str = "Pesquisa ampliada",
          suggestion: str = "Descobrir") -> tuple[str, str | None, str | None, str | None]:
    """Return (legacy main page, itinerary area, guide, base-explorer mode)."""
    if area not in SECTIONS or section not in SECTIONS[area]:
        raise ValueError("Área ou tarefa de navegação desconhecida")
    if area == "Minha viagem":
        return ("Visão geral" if section == "Resumo" else "Pesquisas & decisões",
                None, None, None)
    if area == "Explorar":
        if section == "Comparar cidades":
            return "Comparar cidades", None, None, None
        if section == "Mapa":
            return "Mapa & destinos", None, None, None
        if section == "Cidades-base":
            return "Roteiro", "Explorar bases", None, "Destinos próximos"
        if section == "Passeios e destinos":
            return "Roteiro", "Guias e pesquisas", "Explorar atrações", None
        if research not in RESEARCH_OPTIONS:
            research = RESEARCH_OPTIONS[0]
        if research == "Pesquisa ampliada":
            return "Roteiro", "Explorar bases", None, "Pesquisa ampliada"
        return "Roteiro", "Guias e pesquisas", research, None
    if area == "Orçamento":
        return ("Orçamento", None, None, None) if section == "Visão financeira" else (
            "Roteiro", "Orçamento", None, None)
    if section == "Visão do roteiro":
        return "Roteiro", "Visão geral", None, None
    if section == "Itália":
        return "Roteiro", "Itália", None, None
    if section == "Meus passeios":
        return "Roteiro", "Meus passeios", None, None
    if section == "Calendário":
        return "Roteiro", "Calendário", None, None
    return "Roteiro", (suggestion if suggestion in SUGGESTION_OPTIONS
                       else SUGGESTION_OPTIONS[0]), None, None


def from_legacy(page: str, itinerary: str | None = None,
                guide: str | None = None) -> tuple[str, str]:
    """Migration/deep-link adapter: every old screen remains addressable."""
    simple = {
        "Visão geral": ("Minha viagem", "Resumo"),
        "Mapa & destinos": ("Explorar", "Mapa"),
        "Comparar cidades": ("Explorar", "Comparar cidades"),
        "Orçamento": ("Orçamento", "Visão financeira"),
        "Pesquisas & decisões": ("Minha viagem", "Pendências e fontes"),
    }
    if page in simple:
        return simple[page]
    mapping = {
        "Visão geral": ("Meu roteiro", "Visão do roteiro"),
        "Itália": ("Meu roteiro", "Itália"),
        "Meus passeios": ("Meu roteiro", "Meus passeios"),
        "Explorar bases": ("Explorar", "Cidades-base"),
        "Descobrir": ("Meu roteiro", "Sugestões"),
        "Simular roteiros": ("Meu roteiro", "Sugestões"),
        "Orçamento": ("Orçamento", "Passeios e custos"),
        "Calendário": ("Meu roteiro", "Calendário"),
        "Guias e pesquisas": ("Explorar", "Passeios e destinos")
             if guide in (None, "Explorar atrações") else ("Explorar", "Mais pesquisas"),
    }
    return mapping.get(itinerary or "Meus passeios",
                       ("Meu roteiro", "Meus passeios"))


def apply(state) -> tuple[str, str | None, str | None, str | None]:
    """Synchronize legacy keys BEFORE Streamlit instantiates corresponding widgets."""
    area = state.get("ux_area", AREAS[0])
    if area not in SECTIONS:
        area = AREAS[0]
        state["ux_area"] = area
    section = state.get("ux_section", DEFAULT_SECTION[area])
    if section not in SECTIONS[area]:
        section = DEFAULT_SECTION[area]
        state["ux_section"] = section
    research = state.get("ux_research", RESEARCH_OPTIONS[0])
    suggestion = state.get("ux_suggestion", SUGGESTION_OPTIONS[0])
    target = route(area, section, research=research, suggestion=suggestion)
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
    if itinerary == "Explorar bases" and state.get("base_explorer_mode") == "Pesquisa ampliada":
        state["ux_research"] = "Pesquisa ampliada"
        state["ux_section"] = "Mais pesquisas"
    apply(state)
