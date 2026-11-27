"""UX 3.0: task-oriented navigation, with a non-breaking legacy route adapter.

Presentation only. The canonical TripPlan and the research catalog are unchanged.
Callbacks run *before* widgets render, so no widget state is mutated after its
instantiation. Legacy deep-links remain usable through an advanced expander.
"""
from __future__ import annotations

AREAS = ("Minha viagem", "Explorar", "Meu roteiro", "Orçamento")
SECTIONS = {
    "Minha viagem": ("Resumo", "Pendências", "Decisões"),
    "Explorar": ("Cidades-base", "Comparar", "Passeios", "Mapa", "Cobertura dos dados"),
    "Meu roteiro": ("Meu planejamento", "Organizar viagem", "Melhorar meu roteiro"),
    "Orçamento": ("Resumo financeiro", "Simulações", "Detalhamento"),
}
# Migration for bookmarks and callbacks from UX 3.0. Public task names stay stable.
TASK_ALIASES = {
    ("Minha viagem", "Pendências e fontes"): "Pendências",
    ("Explorar", "Comparar cidades"): "Comparar",
    ("Explorar", "Passeios e destinos"): "Passeios",
    ("Explorar", "Mais pesquisas"): "Cidades-base",
    ("Meu roteiro", "Visão do roteiro"): "Meu planejamento",
    ("Meu roteiro", "Visão geral"): "Meu planejamento",
    ("Meu roteiro", "Meus passeios"): "Meu planejamento",
    ("Meu roteiro", "Itália"): "Melhorar meu roteiro",
    ("Meu roteiro", "França"): "Melhorar meu roteiro",
    ("Meu roteiro", "Calendário"): "Organizar viagem",
    ("Meu roteiro", "Sugestões"): "Melhorar meu roteiro",
    ("Orçamento", "Visão financeira"): "Resumo financeiro",
    ("Orçamento", "Passeios e custos"): "Detalhamento",
}
DEFAULT_SECTION = {area: sections[0] for area, sections in SECTIONS.items()}
GUIDES = ("Explorar atrações", "Itália e Costa Amalfitana",
          "França e escapadas", "Transportes e custos",
          "Calendário de pesquisa", "Cronograma oficial", "Estudos de cidades-base")
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
    ("Explorar", "Comparar"): "Investigue alternativas a partir dos destinos escolhidos.",
    ("Explorar", "Cobertura dos dados"): "Identifique lacunas de pesquisa sem alterar sua viagem.",
    ("Explorar", "Passeios"): "Explore atrações e viagens próximas.",
    ("Explorar", "Mapa"): "Localize cidades e referências geográficas.",
    ("Meu roteiro", "Meu planejamento"): "Escolha atrações e continue do ponto atual.",
    ("Meu roteiro", "Organizar viagem"): "Organize os passeios por período ou data.",
    ("Meu roteiro", "Melhorar meu roteiro"): "Pesquise e melhore o roteiro sem perder sua edição.",
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
        if section == "Cobertura dos dados":
            return "Cobertura dos dados", None, None, None
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
        return "Orçamento", None, None, None
    if section == "Meu planejamento":
        return "Roteiro", "Visão geral", None, None
    if section == "Organizar viagem":
        return ("Roteiro", "Calendário" if
                research=="Calendário completo" else "Visão geral",None,None)
    # Specialist resources are secondary choices, not separate main tabs.
    if suggestion=="Itália":
        return "Roteiro","Itália",None,None
    if suggestion=="Temporada europeia":
        return "Roteiro","Meus passeios",None,None
    if suggestion=="Consultor de passeios":
        return "Roteiro","Orçamento",None,None
    if suggestion=="Calendário completo":
        return "Roteiro","Calendário",None,None
    if suggestion=="Guias especializados":
        return "Roteiro","Guias e pesquisas",(guide_view if guide_view in GUIDES
                                               else GUIDES[0]),None
    return "Roteiro",(suggestion if suggestion in SUGGESTION_OPTIONS[:2]
                     else "Descobrir"),None,None


def from_legacy(page: str, itinerary: str | None = None,
                guide: str | None = None) -> tuple[str, str]:
    """Keep every old deep-link reachable after reducing itinerary tabs."""
    if page=="Visão geral":return "Minha viagem","Resumo"
    if page=="Pesquisas & decisões":return "Minha viagem","Pendências"
    if page=="Orçamento":return "Orçamento","Resumo financeiro"
    if page=="Mapa & destinos":return "Explorar","Mapa"
    if page=="Comparar cidades":return "Explorar","Comparar"
    if page=="Cobertura dos dados":return "Explorar","Cobertura dos dados"
    if itinerary in ("Visão geral","Meus passeios"):
        return "Meu roteiro","Meu planejamento"
    if itinerary=="Calendário":return "Meu roteiro","Organizar viagem"
    if itinerary in ("Itália","Descobrir","Simular roteiros"):
        return "Meu roteiro","Melhorar meu roteiro"
    if itinerary=="Explorar bases":return "Explorar","Cidades-base"
    if itinerary=="Orçamento":return "Meu roteiro","Melhorar meu roteiro"
    if itinerary=="Guias e pesquisas":
        if guide=="Explorar atrações" or guide is None:
            return "Explorar","Passeios"
        return "Meu roteiro","Melhorar meu roteiro"
    return "Meu roteiro","Meu planejamento"


def apply(state) -> tuple[str, str | None, str | None, str | None]:
    """Synchronize legacy keys BEFORE Streamlit instantiates corresponding widgets."""
    area = state.get("ux_area", AREAS[0])
    from ux64_navigation_model import TARGETS
    proposed=state.get("ux_section")
    if (area,proposed) in TARGETS:
        area,proposed=TARGETS[(area,proposed)]
        state["ux_area"],state["ux_section"]=area,proposed
    if area not in SECTIONS:
        area = AREAS[0]
        state["ux_area"] = area
    section = state.get("ux_section", DEFAULT_SECTION[area])
    section = TASK_ALIASES.get((area, section), section)
    state["ux_section"] = section
    if section not in SECTIONS[area]:
        section = DEFAULT_SECTION[area]
        state["ux_section"] = section
    # Migrate the former nested coverage view once, before mounting widgets.
    old_view=state.get("ux112_active_view_shadow",state.get("ux112_active_view"))
    if old_view=="Cobertura dos dados":
        state["ux112_active_view_shadow"]="Explorar alternativas"
        state["ux112_active_view"]="Explorar alternativas"
        if (area,section)==("Explorar","Comparar"):
            section="Cobertura dos dados"
            state["ux_section"]=section
    focused=state.get("ux125b_focused_guide")
    if (area,section)==("Meu roteiro","Melhorar meu roteiro") and focused in ("Estudos de cidades-base","Explorar atrações"):
        # Keep route inputs durable when their widgets are intentionally unmounted.
        state["ux_improve_view"]="Guias especializados"
        state["ux_guide_view"]=focused
    else:
        state.pop("ux125b_focused_guide",None)
    # Remember a valid task independently of a deselected Streamlit widget.
    state["_ux_last_section"] = section
    research = ("Calendário completo" if state.get("ux_organize_view")=="Calendário completo"
                and (area,section)==("Meu roteiro","Organizar viagem")
                else state.get("ux_research",RESEARCH_OPTIONS[0]))
    suggestion = (state.get("ux_improve_view",SUGGESTION_OPTIONS[0])
                  if (area,section)==("Meu roteiro","Melhorar meu roteiro")
                  else state.get("ux_suggestion",SUGGESTION_OPTIONS[0]))
    france = state.get("ux_france_view", "Meus passeios")
    city_view = state.get("ux_city_view","Visão da cidade")
    guide_view = state.get("ux_guide_view",GUIDES[0])
    target = route(area, section, research=research, suggestion=suggestion,
                   france=france,city_view=city_view,
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
    if (state.get("ux_area"),state.get("ux_section"))==("Orçamento","Simulações") and state.get("ux_budget_view")=="Consultor de passeios":
        state.pop("ux_budget_view",None)
        state["ux_improve_view"]="Consultor de passeios"
        state["ux_area"],state["ux_section"]="Meu roteiro","Melhorar meu roteiro"
        return apply(state)
    if "ux_area" not in state:
        area, section = from_legacy(
            state.get("main_navigation", "Visão geral"),
            state.get("itinerary_section"), state.get("guide_section"))
        state["ux_area"], state["ux_section"] = area, section
        itinerary=state.get("itinerary_section")
        if itinerary=="Orçamento" and state.get("main_navigation")=="Roteiro":
            state["ux_improve_view"]="Consultor de passeios"
        elif itinerary=="Itália":
            state["ux_improve_view"]="Itália"
        elif itinerary=="Meus passeios":
            state["ux_improve_view"]="Temporada europeia"
        elif itinerary in ("Descobrir","Simular roteiros"):
            state["ux_improve_view"]=itinerary
        elif itinerary=="Calendário":
            state["ux_organize_view"]="Calendário completo"
    else:
        previous = state.get("_ux_legacy_page")
        request = state.get("main_navigation")
        if previous and request and request != previous:
            area, section = from_legacy(
                request, state.get("itinerary_section"), state.get("guide_section"))
            state["ux_area"], state["ux_section"] = area, section
            if request=="Roteiro" and state.get("itinerary_section")=="Orçamento":
                state["ux_improve_view"]="Consultor de passeios"
        elif (request == "Roteiro" and previous == "Roteiro"
              and state.get("_ux_legacy_itinerary") is not None
              and state.get("itinerary_section") != state["_ux_legacy_itinerary"]):
            itinerary = state.get("itinerary_section")
            area, section = from_legacy("Roteiro", itinerary,
                                        state.get("guide_section"))
            state["ux_area"], state["ux_section"] = area, section
            if itinerary=="Orçamento":
                state["ux_improve_view"]="Consultor de passeios"
            elif itinerary in SUGGESTION_OPTIONS:
                state["ux_suggestion"] = itinerary
            if itinerary == "Guias e pesquisas" and state.get("guide_section") in RESEARCH_OPTIONS:
                state["ux_research"] = state["guide_section"]
    return apply(state)


def set_area(state, area: str) -> None:
    state["ux_area"] = area
    state["ux_section"] = DEFAULT_SECTION[area]
    apply(state)


def set_task(state, area: str, section: str | None) -> None:
    # Clicking an already selected segmented option may emit None. Treat it
    # as a no-op instead of crashing or silently navigating elsewhere.
    if section is None:
        previous = state.get("_ux_last_section")
        section = previous if previous in SECTIONS[area] else DEFAULT_SECTION[area]
    section = TASK_ALIASES.get((area,section),section)
    if section not in SECTIONS[area]:
        raise ValueError("Tarefa de navegação inválida")
    state["ux_area"] = area
    state["ux_section"] = section
    section = TASK_ALIASES.get((area, section), section)
    if (area, section)==("Explorar", "Cidades-base"):
        state["ux42_city_activity"]="Explorar cidades"
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
    if page=="Roteiro" and itinerary == "Orçamento":
        state.pop("ux_budget_view",None)
        state["ux_improve_view"]="Consultor de passeios"
    if itinerary=="Itália":
        state["ux_improve_view"]="Itália"
    elif itinerary=="Meus passeios":
        state["ux_improve_view"]="Temporada europeia"
    elif itinerary=="Descobrir":
        state["ux_improve_view"]="Descobrir"
    elif itinerary=="Simular roteiros":
        state["ux_improve_view"]="Simular roteiros"
    elif itinerary=="Calendário":
        state["ux_organize_view"]="Calendário completo"
    if itinerary=="Guias e pesquisas" and guide not in ("Explorar atrações",None):
        state["ux_improve_view"]="Guias especializados"
    if itinerary == "Explorar bases" and state.get("base_explorer_mode") == "Pesquisa ampliada":
        state["ux_research"] = "Pesquisa ampliada"
        state["ux_section"] = "Cidades-base"
    apply(state)
