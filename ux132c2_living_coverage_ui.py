"""UX132C2: focused research gaps, not a second city profile or budget."""
import logging
from time import perf_counter
import streamlit as st

from ux132c2_living_coverage_model import (
    build_living_view, scope_rows, scope_counts, indicator_rows, compact_rows,
    PRIORITY, ALL,
)
from ux_widget_state import widget_state

_LOG = logging.getLogger(__name__)
UNKNOWN = "Não documentado"
COWORKING = {
    "compatible_2026": "Compatível na referência de 2026",
    "incompatible_2026": "Horário insuficiente na referência de 2026",
    "indeterminate": "Indeterminado",
}


def _load(research):
    started = perf_counter()
    view = build_living_view(research=research)
    _LOG.debug("UX132C2 living projection: %.3fs", perf_counter() - started)
    return view


def _ratio(n, d):
    return f"{n}/{d}" if d else "N/A (0/0)"


def _amount(value, unit):
    return UNKNOWN if value is None else f"{value:g} {unit}"


def _link(label, url):
    if isinstance(url, str) and url.startswith("https://"):
        st.link_button(label, url)
    else:
        st.caption(label + ": fonte específica não documentada.")


def _scope_note(view, rows):
    st.caption(f'{len(rows)} bases no recorte · {len(view["rows"])} bases auditadas no D-004. '
               "Recorte de pesquisa, não lista de finalistas oficiais. "
               "Outras cidades não foram avaliadas por este recorte.")


def render_living_summary(*, research=None):
    """Overview card body, with the default priority denominator explicitly named."""
    try:
        view = _load(research)
    except Exception:
        _LOG.exception("UX132C2 living summary unavailable")
        st.warning("Resumo de moradia e trabalho remoto indisponível.")
        return
    counts = scope_counts(view)
    n = counts["bases"]
    st.caption(f'{n} bases prioritárias · {len(view["rows"])} auditadas no D-004')
    cols = st.columns(2)
    for i, (label, key) in enumerate((
        ("Amostra de moradia", "with_historical_housing"),
        ("Clima pesquisado", "with_climate"),
        ("Coworking pesquisado", "with_coworking"),
        ("Três cotações de 2027", "with_three_verified_quotes"),
    )):
        cols[i % 2].metric(label, _ratio(counts[key], n))
    st.caption(f'Internet residencial confirmada para 2027: {_ratio(counts["with_residential_internet"], n)} · '
               f'Cesta local comparável: {_ratio(counts["with_local_basket"], n)}. '
               "Referências históricas não confirmam a estadia.")


def _render_indicators(counts):
    st.dataframe([{
        "Domínio": r["domain"], "Indicador": r["label"],
        "Bases com registro / total": _ratio(r["count"], r["total"]),
        "Cobertura": r["fraction"] * 100 if r["fraction"] is not None else None,
    } for r in indicator_rows(counts)], hide_index=True, width="stretch",
        column_config={"Cobertura": st.column_config.ProgressColumn(
            "Cobertura", min_value=0, max_value=100, format="%.1f%%")},
        key="ux132c2_indicators")
    st.caption("Cada indicador conta bases, não preços ou serviços. Zero registros não prova indisponibilidade. "
               "Academia e lavanderia: cobertura não medida por este inventário.")


def _render_housing(h):
    st.write(f'{h["summary"]["count"]} observações históricas no conjunto canônico · '
             f'{h["overview"]["available_for_56_to_60_nights_2027"]} cotações elegíveis para 2027 (meta: 3).')
    st.caption("Valores mensais históricos não são preço total da estadia; amostras de mercado e pacotes não são somadas.")
    st.write("Total de 2027: " + _amount(h["total_2027"], "EUR"))
    st.write("Caução de 2027: " + _amount(h["deposit_2027"], "EUR"))
    st.write("Contrato para 2027: " + ("Confirmado" if h["contract_2027_verified"] is True else "Não confirmado"))
    st.caption("Confirmar unidade privativa mobiliada para dois adultos, taxas, caução, contrato, internet e acesso à estação para 56–60 noites.")
    with st.expander("Amostras históricas e fontes de moradia"):
        if not h["historical_offers"]:
            st.info("Nenhuma amostra histórica catalogada.")
        else:
            st.dataframe([{
                "Referência": o.get("observed_title_or_address") or o["listing_ref"],
                "EUR/mês (histórico)": o.get("monthly_eur"),
                "Área (m²)": o.get("size_m2"),
                "Condições": o.get("utilities"),
                "Data": o.get("checked_at"),
                "Anúncio": o.get("listing_url"),
                "Catálogo (contexto)": o.get("catalogue_url"),
            } for o in h["historical_offers"]], hide_index=True, width="stretch",
                column_config={
                    "Anúncio": st.column_config.LinkColumn("Anúncio", display_text="Abrir anúncio"),
                    "Catálogo (contexto)": st.column_config.LinkColumn("Catálogo (contexto)", display_text="Abrir catálogo"),
                }, key="ux132c2_housing_offers")
            st.caption("Uma URL de catálogo não confirma o anúncio individual nem disponibilidade. "
                       "Data e condições correspondem a cada observação.")


def _render_daily(d):
    st.write("Restaurante para dois: " + _amount(d["restaurant_eur_two"], "EUR (histórico)"))
    p = d["urban_pass"] or {}
    st.write("Passe urbano: " + _amount(p.get("fare_eur_month_person"), "EUR/pessoa/mês (histórico)"))
    st.write("Cesta local completa comparável: " + _amount(d["comparable_local_basket_eur"], "EUR"))
    if d["local_grocery_basket_eur"] is not None:
        st.caption("Cesta parcial de supermercado: " + _amount(d["local_grocery_basket_eur"], "EUR") +
                   " · não equivale à cesta completa comparável.")
    with st.expander("Condições e fontes de vida cotidiana"):
        if d["restaurant_eur_two"] is not None:
            st.write(d["restaurant_basis"] or "Modalidade não documentada")
            st.caption("Data do pacote de pesquisa: " + str(d["restaurant_source_date"] or UNKNOWN))
            _link("Fonte do restaurante", d["restaurant_source_url"])
        if p:
            st.write(p.get("eligibility") or "Elegibilidade não informada")
            st.caption(str(p.get("price_period") or UNKNOWN))
            st.caption("Data do levantamento de mercado: " + str(d["urban_pass_source_date"] or UNKNOWN))
            if p.get("note"):
                st.caption(p["note"])
            _link("Fonte do passe urbano", p.get("source_url"))
        st.caption("Premissas compartilhadas do orçamento não são uma cesta de consumo específica da cidade.")


def _render_climate(d):
    climate = d["climate"] or {}
    months = climate.get("months_9_10_11")
    if months is None:
        st.write("Normais climáticas: não documentadas neste recorte.")
        return
    st.caption(f'Estação: {climate.get("station_name") or UNKNOWN} · '
               f'Período: {climate.get("normal_period") or UNKNOWN}.')
    st.dataframe([{
        "Mês": month, "Temperatura média (°C)": months.get(key, {}).get("tmean_c"),
        "Precipitação (mm)": months.get(key, {}).get("precip_mm"),
    } for key, month in (("9", "Setembro"), ("10", "Outubro"), ("11", "Novembro"))],
        hide_index=True, width="stretch", key="ux132c2_climate")
    with st.expander("Método e fonte do clima"):
        if climate.get("method"):
            st.caption(climate["method"])
        st.caption("Consulta: " + str(climate.get("observed_at") or UNKNOWN))
        _link("Fonte das normais", climate.get("source_url"))
    st.caption("Normais históricas da estação, não previsão meteorológica de 2027.")


def _render_remote(w):
    coworking = w["coworking"]
    st.write("Coworking: " + (coworking["name"] if coworking else UNKNOWN))
    st.write(COWORKING[w["compatibility_2026"]])
    st.write("Acesso no expediente de 2027: " +
             ("Compatível confirmado" if w["compatibility_2027"] == "compatible" else "Indeterminado"))
    st.write("Internet no imóvel para 2027: " +
             ("Confirmada" if w["residential_internet_2027"] is True else "Não confirmada"))
    st.caption(f'{w["residential_internet_verified"]} observações com internet verificada no conjunto histórico; '
               "isso não confirma a conexão na estadia.")
    if coworking:
        with st.expander("Modalidade, horários e fonte do coworking"):
            st.write(_amount(coworking.get("price_eur"), "EUR"))
            st.caption(coworking.get("price_basis") or "Modalidade não informada")
            st.write(coworking.get("schedule") or "Horário não documentado")
            st.caption("Data do levantamento: " + str(w["coworking_source_date"] or UNKNOWN))
            if coworking.get("note"):
                st.caption(coworking["note"])
            _link("Fonte do coworking", coworking.get("source_url"))
    elif w["pack_reference"]:
        st.caption("Há referência complementar de pacote, não equivalente à observação de coworking do D-004.")
        with st.expander("Referência complementar de coworking"):
            p = w["pack_reference"]
            st.write(p.get("name") or UNKNOWN)
            st.write(_amount(p.get("price_eur_2026"), "EUR (histórico)"))
            st.caption(p.get("price_basis") or "Modalidade não informada")
            st.caption(p.get("limitations") or "Condições não confirmadas")
            _link("Fonte complementar", p.get("source_url"))


def _render_detail(row):
    st.markdown(f'#### {row["name"]} — pesquisas pendentes')
    gaps = row["research_gaps"]
    for key, title in (
        ("decision_blockers", "Necessário para comparar a escolha"),
        ("complementary", "Pesquisas complementares"),
        ("sufficient_for_context_only", "Referências suficientes apenas para contexto"),
    ):
        st.markdown("**" + title + "**")
        st.write(" · ".join(gaps[key]) if gaps[key] else "Nenhuma pendência neste recorte")
    st.caption("Lacunas de viagem ferroviária estão na área Transporte; não duplicadas aqui.")
    with st.container(border=True):
        st.markdown("#### Moradia")
        _render_housing(row["housing"])
    with st.container(border=True):
        st.markdown("#### Vida cotidiana e custos")
        _render_daily(row["daily_life"])
    with st.container(border=True):
        st.markdown("#### Clima")
        _render_climate(row["daily_life"])
    with st.container(border=True):
        st.markdown("#### Trabalho remoto")
        _render_remote(row["remote_work"])


def render_living_coverage(*, research=None):
    try:
        view = _load(research)
    except Exception:
        _LOG.exception("UX132C2 living coverage unavailable")
        st.error("Não foi possível carregar a cobertura de moradia e trabalho. Seu roteiro permanece intacto.")
        return
    labels = {PRIORITY: f'Bases prioritárias ({len(scope_rows(view))})',
              ALL: f'Todas as bases auditadas ({len(view["rows"])})'}
    scope = st.selectbox("Recorte de pesquisa", list(labels), format_func=labels.__getitem__,
                         **widget_state("ux132c2_scope", PRIORITY, lambda v: v in labels))
    rows = scope_rows(view, scope)
    _scope_note(view, rows)
    st.info("Cobertura documental não é ranking de cidades nem confirmação de preços, contratos ou disponibilidade em 2027.")
    if not rows:
        st.info("Nenhuma base auditada neste recorte.")
        return
    _render_indicators(scope_counts(view, scope))
    st.markdown("#### Evidências por cidade-base")
    st.dataframe([{
        "Cidade-base": r["name"],
        "Anúncios históricos": r["historical_offers"],
        "Cotações 2027": f'{r["verified_quotes"]}/3',
        "Vida cotidiana": " · ".join(
            label + (": sim" if r[key] else ": pendente")
            for key, label in (("restaurant", "Restaurante"), ("urban_pass", "Passe"), ("local_basket", "Cesta"))),
        "Clima": "Registrado" if r["climate"] else "Pendente",
        "Trabalho remoto": ("Coworking: registro" if r["coworking"] else "Coworking: pendente") +
            (" · Internet 2027: confirmada" if r["internet_2027"] else " · Internet 2027: não confirmada"),
    } for r in compact_rows(rows)], hide_index=True, width="stretch", key="ux132c2_bases")
    st.caption("Vida cotidiana: registros históricos ou cesta comparável. Trabalho remoto: pesquisa de coworking e confirmação residencial são distintos.")
    names = {r["id"]: r["name"] for r in rows}
    ident = st.selectbox("Cidade para detalhar", list(names), format_func=names.__getitem__,
                         **widget_state("ux132c2_base", next(iter(names)), lambda v: v in names))
    _render_detail(next(r for r in rows if r["id"] == ident))
