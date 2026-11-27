"""UX132C2: focused research gaps, not a second city profile or budget."""
import logging
from time import perf_counter
import streamlit as st

from ux132c2_living_coverage_model import (
    build_living_view, scope_rows, scope_counts, indicator_rows, compact_rows,
    PRIORITY, ALL, scope_membership, complementary_coworking, documented_housing_counts,
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
    membership = scope_membership(view)
    audited = len(membership["priority_audited"])
    unaudited = membership["priority_unaudited"]
    additional = membership["additional_audited"]
    st.caption(f'{len(rows)} bases auditadas no recorte · {audited} prioritárias auditadas · '
               f'{len(additional)} adicionais do estudo histórico. '
               "Recorte de pesquisa, não lista de finalistas oficiais.")
    if unaudited:
        st.warning("Prioritárias ainda não auditadas: " + ", ".join(r["name"] for r in unaudited) +
                   ". Não entram nos denominadores; não representam cobertura zero.")


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
    _scope_note(view, scope_rows(view))
    st.markdown("**Requisitos para decidir em 2027**")
    cols = st.columns(2)
    cols[0].metric("Internet residencial confirmada", _ratio(counts["with_residential_internet"], n))
    cols[1].metric("Cesta local comparável", _ratio(counts["with_local_basket"], n))
    st.caption(f'Bases com contador de 3 ou mais cotações elegíveis declaradas: '
               f'{_ratio(counts["with_three_verified_quotes"], n)}. '
               "O contador histórico não confirma disponibilidade nem condições.")
    current = documented_housing_counts(scope_rows(view))
    st.caption("Bases com cotações individuais documentadas: " +
               _ratio(current["with_documented_quotes"], n) + " · sem confirmação independente.")
    st.markdown("**Referências históricas**")
    st.caption(f'Moradia: {_ratio(counts["with_historical_housing"], n)} · '
               f'Clima: {_ratio(counts["with_climate"], n)} · '
               f'Coworking: {_ratio(counts["with_coworking"], n)} bases.')


def _render_indicators(counts):
    historical_keys = {"with_historical_housing", "with_restaurant", "with_urban_pass",
                       "with_climate", "with_coworking"}
    rows = indicator_rows(counts)
    def table(entries, key):
        st.dataframe([{
            "Indicador": r["label"],
            "Bases / total auditado": _ratio(r["count"], r["total"]),
        } for r in entries], hide_index=True, width="stretch", key=key)
    st.markdown("#### Requisitos de pesquisa para a decisão")
    table([r for r in rows if r["key"] not in historical_keys], "ux132c2_requirements")
    st.caption("O contador declarado de cotações é um indicador legado, não comprovante individual de 2027.")
    with st.expander("Cobertura das referências históricas"):
        table([r for r in rows if r["key"] in historical_keys], "ux132c2_indicators")
        st.caption("Cada indicador conta bases auditadas. Zero registros não prova indisponibilidade. "
                   "Academia e lavanderia: cobertura não medida por este inventário.")


def _render_current_housing(observations):
    st.markdown("**Cotações individuais para 2027 — documentação**")
    if not observations:
        st.caption("Nenhuma observação individual registrada. Não significa indisponibilidade.")
        return
    st.write(f'{observations["documented"]} observações · '
             f'{observations["independently_verified"]} confirmadas independentemente.')
    st.caption("Documentação não garante disponibilidade atual nem confirma a contratação.")
    for group in observations["groups"]:
        st.write(f'{group["checkin"]} a {group["checkout"]} · {group["currency"]} · '
                 f'{group["complete_documentation"]}/{group["documented"]} com requisitos documentais completos.')
        for record in group["records"]:
            q, evaluation = record["quote"], record["evaluation"]
            st.markdown("**" + record["listing_id"] + "**")
            st.caption("Consulta: " + q["checked_at"] + " · dois adultos")
            st.write("Soma das despesas declaradas: " + _amount(evaluation["expense_total"], q["currency"]))
            st.write("Caução reembolsável declarada: " + _amount(evaluation["refundable_deposit_separate"], q["currency"]))
            st.caption("Contrato: " + (record["contract_terms"] or UNKNOWN))
            st.caption("Cancelamento: " + (record["cancellation_terms"] or UNKNOWN))
            st.caption("Requisitos pendentes ou negativos: " +
                       (", ".join(record["missing_requirements"]) or "Nenhum no registro declarado"))
            st.caption("Disponibilidade declarada: " + _evidence_state(q["available_on_dates"]) +
                       " · Internet declarada: " + _evidence_state(q["internet_verified"]))
            _link("Anúncio individual", q["source_url"])
            _link("Evidência documental", record["evidence_url"])


def _evidence_state(value):
    return "Sim" if value is True else "Não" if value is False else "Desconhecido"


def _render_housing(h):
    st.write(f'{h["summary"]["count"]} observações históricas no conjunto canônico · '
             f'{h["overview"]["available_for_56_to_60_nights_2027"]} cotações elegíveis declaradas no contador legado (meta: 3).')
    st.caption("Valores mensais históricos não são preço total da estadia; amostras de mercado e pacotes não são somadas. O contador não comprova condições individuais.")
    st.write("Total de 2027: " + _amount(h["total_2027"], "EUR"))
    st.write("Caução de 2027: " + _amount(h["deposit_2027"], "EUR"))
    st.write("Contrato para 2027: " + ("Confirmado" if h["contract_2027_verified"] is True else "Não confirmado"))
    st.caption("Confirmar unidade privativa mobiliada para dois adultos, taxas, caução, contrato, internet e acesso à estação para 56–60 noites.")
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
    if d["restaurant_eur_two"] is not None:
        st.write(d["restaurant_basis"] or "Modalidade não documentada")
        st.caption("Data geral do pacote de pesquisa: " + str(d["restaurant_source_date"] or UNKNOWN))
        _link("Fonte do restaurante", d["restaurant_source_url"])
    if p:
        st.write(p.get("eligibility") or "Elegibilidade não informada")
        st.caption(str(p.get("price_period") or UNKNOWN))
        st.caption("Data geral do levantamento de mercado: " + str(d["urban_pass_source_date"] or UNKNOWN))
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
             ("Confirmada" if w["residential_internet_2027"] is True else
              "Evidência negativa" if w["residential_internet_2027"] is False else "Não confirmada"))
    st.caption(f'{w["residential_internet_verified"]} observações com internet verificada no conjunto histórico; '
               "isso não confirma a conexão na estadia.")
    if coworking:
        st.write(_amount(coworking.get("price_eur"), "EUR"))
        st.caption(coworking.get("price_basis") or "Modalidade não informada")
        st.caption("Tipo de fonte: " + str(coworking.get("source_type") or UNKNOWN))
        st.write(coworking.get("schedule") or "Horário não documentado")
        st.caption("Data específica da observação: " + str(coworking.get("observed_at") or coworking.get("checked_at") or UNKNOWN))
        st.caption("Data geral do levantamento: " + str(w["coworking_source_date"] or UNKNOWN))
        if coworking.get("note"):
            st.caption(coworking["note"])
        _link("Fonte do coworking", coworking.get("source_url"))
    extra = complementary_coworking(w)
    if extra:
        st.caption("Referência complementar distinta; não substitui a observação principal do D-004.")
        p = extra
        st.write(p.get("name") or UNKNOWN)
        st.write(_amount(p.get("price_eur_2026"), "EUR (histórico)"))
        st.caption(p.get("price_basis") or "Modalidade não informada")
        st.caption("Tipo de fonte: " + str(p.get("source_type") or UNKNOWN))
        st.write(p.get("hours") or "Horário não documentado")
        st.caption(p.get("limitations") or "Condições não confirmadas")
        st.caption("Data específica: " + str(p.get("observed_at") or p.get("checked_at") or UNKNOWN))
        _link("Fonte complementar", p.get("source_url"))


def _render_detail(row):
    st.markdown(f'#### {row["name"]} — pesquisas pendentes')
    gaps = row["research_gaps"]
    st.markdown("**Necessário para comparar a escolha**")
    if gaps["decision_blockers"]:
        for gap in gaps["decision_blockers"]:
            st.write("• " + gap)
    else:
        st.caption("Nenhuma pendência nesta classificação.")
    if gaps["complementary"]:
        st.caption("Pesquisas complementares: " + " · ".join(gaps["complementary"]))
    st.caption("Lacunas ferroviárias estão em Transporte. Registros históricos não confirmam a estadia.")
    with st.expander("Moradia — registros e fontes"):
        _render_current_housing(row.get("housing_observations"))
        _render_housing(row["housing"])
    with st.expander("Vida cotidiana e custos"):
        _render_daily(row["daily_life"])
    with st.expander("Clima — normais históricas"):
        _render_climate(row["daily_life"])
    with st.expander("Trabalho remoto — registros e fontes"):
        _render_remote(row["remote_work"])


def render_living_coverage(*, research=None):
    try:
        view = _load(research)
    except Exception:
        _LOG.exception("UX132C2 living coverage unavailable")
        st.error("Não foi possível carregar a cobertura de moradia e trabalho. Seu roteiro permanece intacto.")
        return
    labels = {PRIORITY: f'Prioritárias auditadas ({len(scope_rows(view))})',
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
    current = documented_housing_counts(rows)
    st.caption("Cotações individuais documentadas: " + _ratio(current["with_documented_quotes"], len(rows)) +
               " bases · três com documentação completa para mesmas datas/moeda: " +
               _ratio(current["with_three_comparable_documented_quotes"], len(rows)) +
               " bases. Nenhuma confirmação independente por este inventário.")
    st.markdown("#### Evidências por cidade-base")
    st.dataframe([{
        "Cidade-base": r["name"],
        "Anúncios históricos": r["historical_offers"],
        "Contador legado de cotações": r["declared_quotes"],
        "Vida cotidiana": " · ".join(
            label + (": sim" if r[key] else ": pendente")
            for key, label in (("restaurant", "Restaurante"), ("urban_pass", "Passe"), ("local_basket", "Cesta"))),
        "Clima": "Registrado" if r["climate"] else "Pendente",
        "Trabalho remoto": ("Coworking: registro" if r["coworking"] else "Coworking: pendente") +
            (" · Internet 2027: confirmada" if r["internet_2027"] is True else
             " · Internet 2027: evidência negativa" if r["internet_2027"] is False else " · Internet 2027: não confirmada"),
    } for r in compact_rows(rows)], hide_index=True, width="stretch", key="ux132c2_bases")
    st.caption("Vida cotidiana: registros históricos ou cesta comparável. Trabalho remoto: pesquisa de coworking e confirmação residencial são distintos.")
    names = {r["id"]: r["name"] for r in rows}
    ident = st.selectbox("Cidade para detalhar", list(names), format_func=names.__getitem__,
                         **widget_state("ux132c2_base", next(iter(names)), lambda v: v in names))
    _render_detail(next(r for r in rows if r["id"] == ident))
