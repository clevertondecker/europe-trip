"""Travel-oriented Roteiro dashboard. Read-only view of the canonical TripPlan.

Historical fare estimates are partial, and the total budget already provisions
excursions. No mutation, booking, invented journey or 2027 quotation occurs here.
"""
from __future__ import annotations

from datetime import date, timedelta
from html import escape

import pydeck as pdk
import streamlit as st

from advisor_finance import advisor_projection
from attractions_model import load_attractions, load_base_routes, package_cost
from planning_store import summary
from planning_status import save_label
from active_preset import active_preset
from active_preset_ui import render_active_preset_summary


def dashboard_model(plan: dict, catalog: dict, routes: dict, trip_data: dict,
                    finance_live: bool, eurfx: float = 6.3, chffx: float = 7.1,
                    use_city_rent: bool = True) -> dict:
    """Prepare visible metrics without changing the authoritative itinerary."""
    stats = summary(plan)
    destinations = {item["id"]: item for item in catalog["destinations"]}
    attractions = {item["id"]: item for item in catalog["attractions"]}
    selected_ids = [a for group in plan["packages"].values() for a in group]
    costs = package_cost(catalog, routes, plan["base_city"], selected_ids)
    financial = advisor_projection(trip_data, finance_live, plan, costs,
                                   eurfx, chffx, use_city_rent)
    chosen = []
    for key, attraction_ids in plan["packages"].items():
        destination = destinations.get(key)
        if not destination:
            continue
        chosen.append({
            "id": key, "name": destination["name"], "country": destination["country"],
            "lat": destination["lat"], "lon": destination["lon"],
            "photo": destination.get("photo"),
            "attractions": [attractions[a]["name"] for a in attraction_ids if a in attractions],
            "dates": sorted(day for day, dest in plan["assignments"].items() if dest == key),
        })
    departure = date.fromisoformat(plan["departure_date"])
    return {
        "stats": stats, "destinations": chosen,
        "base": destinations[plan["base_city"]],
        "departure": departure.isoformat(),
        "return_candidate": (departure + timedelta(days=plan["total_days"]-1)).isoformat(),
        "projection": financial["result"],
        "known_billets_brl": financial["known_billets_brl"],
        "unknown_costs": len(costs["missing"]),
        "rent_reference": financial["rent_eur_month"],
        "fx": (eurfx, chffx),
        "allowance_brl": financial["budget_excursions_allowance_brl"],
    }


def _metric(label: str, value: str, note: str) -> None:
    st.markdown(
        "<div class='trip-dash-metric'><span>" + escape(label) +
        "</span><strong>" + escape(value) +
        "</strong><small>" + escape(note) + "</small></div>",
        unsafe_allow_html=True)


def _map(model: dict, suggested:dict | None = None, catalog:dict | None = None) -> None:
    base = model["base"]
    points = [{
        "name": base["name"] + " · base em estudo",
        "country": base["country"], "lat": base["lat"], "lon": base["lon"],
        "color": [42, 117, 108], "radius": 16,
    }]
    for item in model["destinations"]:
        if item["id"] != base["id"]:
            points.append({
                "name": item["name"] + " · passeio selecionado",
                "country": item["country"], "lat": item["lat"], "lon": item["lon"],
                "color": [30, 78, 111], "radius": 11,
            })
    if suggested is not None and catalog is not None:
        by_id={d["id"]:d for d in catalog["destinations"]}
        chosen_ids={item["id"] for item in model["destinations"]}
        for key in suggested["summary"]["packages"]:
            if key in chosen_ids or key==base["id"] or key not in by_id:
                continue
            item=by_id[key]
            points.append({"name":item["name"]+" · sugestão do perfil",
                           "country":item["country"],"lat":item["lat"],"lon":item["lon"],
                           "color":[196,130,61],"radius":11})
    layer = pdk.Layer(
        "ScatterplotLayer", data=points,
        get_position="[lon, lat]", get_fill_color="color",
        get_radius=11000, radius_min_pixels=7, radius_max_pixels=16,
        stroked=True, get_line_color=[255, 255, 255],
        line_width_min_pixels=2, pickable=True,
    )
    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(latitude=base["lat"], longitude=base["lon"],
                                         zoom=5.7 if len(points)>1 else 6.6),
        layers=[layer],
        tooltip={"html":"<b>{name}</b><br/>{country}",
                 "style":{"backgroundColor":"#163A4D","color":"white"}},
    )
    st.pydeck_chart(deck, height=340, width="stretch")


def _navigate(section: str) -> None:
    """Widget callbacks run before Streamlit re-instantiates segmented navigation."""
    st.session_state["itinerary_section"] = section


def render_trip_dashboard(plan: dict, trip_data: dict, finance_live: bool,
                          saved_snapshot: dict | None, signed_in: bool,
                          eurfx: float = 6.3, chffx: float = 7.1,
                          use_city_rent: bool = True) -> None:
    """Read-only dashboard; go to Meus passeios to edit and approve changes."""
    catalog = load_attractions()
    routes = load_base_routes()
    model = dashboard_model(plan, catalog, routes, trip_data, finance_live,
                            eurfx, chffx, use_city_rent)
    suggested=active_preset(plan,catalog,routes,trip_data,finance_live,
                            eurfx,chffx,use_city_rent)
    stats = model["stats"]
    save_state, _ = save_label(plan, saved_snapshot, signed_in)
    st.markdown(
        "<div class='trip-dash-hero'><span>TRAVEL JOURNAL · 2027</span>"
        "<h2>Nosso roteiro, em um só lugar.</h2>"
        "<p>Lua de mel na Itália, uma temporada na França e os passeios "
        "que queremos viver juntos.</p>"
        "<div class='trip-dash-hero__chips'>"
        "<span>♡ 2 viajantes</span><span>✦ Itália → França</span>"
        "<span>◷ Ainda em planejamento</span></div></div>",
        unsafe_allow_html=True,
    )
    metrics = [
        ("Destinos escolhidos", str(stats["destinations"]), "Passeios aprovados no plano"),
        ("Atrações", str(stats["attractions"]), "Incluídas nos destinos"),
        ("Dias agendados", str(stats["scheduled_days"]), "Datas atribuídas"),
        ("Teto da viagem", "R$ " + stats["budget_scenario"][:-1] + " mil",
         "Orçamento do casal"),
    ]
    for col, item in zip(st.columns(4, gap="small"), metrics):
        with col:
            _metric(*item)
    st.caption("Base hipotética: " + model["base"]["name"] +
               " · Saída candidata: " + model["departure"] +
               " · Retorno estimado: " + model["return_candidate"] +
               " · " + save_state)

    st.markdown("### Roteiro inicial do perfil selecionado")
    render_active_preset_summary(suggested,catalog,"overview")
    st.button("Ver e adotar roteiro pré-definido →",key="dashboard_go_preset",
              on_click=_navigate,args=("Meus passeios",))
    st.caption("No mapa: passeios confirmados e sugestões ainda não aprovadas "
               "têm cores diferentes. Nenhuma proposta é salva automaticamente.")

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.markdown("### Nosso mapa")
        _map(model,suggested,catalog)
        st.caption("Pontos geográficos aproximados do catálogo; nenhuma rota, "
                   "passagem ou hospedagem foi reservada.")
    with right:
        st.markdown("### Orçamento integrado")
        budget = model["projection"]
        st.metric("Projeção para o casal", "R$ " + f"{budget['total']:,.0f}")
        margin = budget["margin"]
        st.metric("Margem até o teto", "R$ " + f"{margin:,.0f}")
        cap = budget["total"] + margin
        if cap > 0:
            st.progress(min(1.0, max(0.0, float(budget["total"]) / float(cap))))
        st.caption("Proporção da projeção em relação ao teto selecionado.")
        st.markdown("**Passagens e ingressos conhecidos:** R$ " +
                    f"{model['known_billets_brl']:,.0f}")
        st.caption("A verba de passeios já faz parte do orçamento; os valores "
                   "conhecidos não são somados novamente ao total.")
        if model["unknown_costs"]:
            st.warning(f"{model['unknown_costs']} componente(s) de custo ainda "
                       "sem cotação completa. A projeção não garante o teto.")
        st.caption("Câmbio hipotético: R$/€ " + str(model["fx"][0]) +
                   " · R$/CHF " + str(model["fx"][1]) +
                   ". Aluguel e bilhetes usam referências históricas.")
        if margin < 0:
            st.error("A projeção atual está acima do teto escolhido.")
        st.button("Ajustar orçamento →", key="dashboard_go_budget",
                  use_container_width=True,on_click=_navigate,args=("Orçamento",))

    st.markdown("### Lugares que escolhemos")
    if not model["destinations"]:
        st.info("Nenhum passeio confirmado. O roteiro pré-definido do perfil "
                "já aparece acima e pode ser adotado em Meus passeios.")
        st.button("Descobrir destinos →",key="dashboard_go_discover",
                  on_click=_navigate,args=("Descobrir",))
    else:
        cards = model["destinations"][:6]
        for index in range(0, len(cards), 3):
            for col, item in zip(st.columns(3, gap="medium"), cards[index:index+3]):
                with col:
                    with st.container(border=True):
                        photo = item["photo"]
                        if photo and photo.get("url"):
                            st.image(photo["url"], use_container_width=True)
                            st.caption("Foto: " + photo["author"] + " · " + photo["license"])
                        st.markdown("**" + item["name"] + " · " + item["country"] + "**")
                        count = len(item["attractions"])
                        st.caption(f"{count} atração(ões) · " +
                                   (", ".join(item["dates"]) if item["dates"]
                                    else "Data ainda não definida"))
                        if item["attractions"]:
                            st.write(" · ".join(item["attractions"][:2]))
        if len(model["destinations"]) > len(cards):
            st.caption(f"+ {len(model['destinations'])-len(cards)} destinos no planejamento")
        st.button("Editar meus passeios →",key="dashboard_go_outings",
                  use_container_width=True,on_click=_navigate,args=("Meus passeios",))
    st.caption("Informações do catálogo pesquisado em 2026. Disponibilidade, "
               "tarifas e condições de 2027 precisam de confirmação.")
