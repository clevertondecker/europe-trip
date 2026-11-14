"""Europa 2027 — Streamlit travel + planning dashboard (read-only MVP)."""
from __future__ import annotations

from html import escape
from pathlib import Path

import pydeck as pdk
import streamlit as st

from data_model import STATUS_COLORS, STATUS_LABEL, calculate_scenario, get_scenario, load_data, money_brl, select_places
from drive_sync import load_live_updates, update_map_places

st.set_page_config(page_title="Nossa Europa 2027", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")
data = load_data()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live():
    # st.secrets does not exist locally until configured; never log secret contents.
    credentials = dict(st.secrets["gcp_service_account"])
    return load_live_updates(credentials)

sync_status = "snapshot"
sync_time = ""
sync_error = ""
sync_sources = {name: {"status": "snapshot"} for name in ("decisions", "tasks", "finance")}
sync_issues = []
try:
    if "gcp_service_account" in st.secrets:
        live = fetch_live()
        sync_time = live["synced_at"]
        sync_sources.update(live["source_status"])
        sync_issues = live["issues"]
        if sync_sources["decisions"]["status"] == "live":
            data["decisions"] = live["decisions"]
            data["places"] = update_map_places(data["places"], data["decisions"])
        if sync_sources["tasks"]["status"] == "live":
            data["tasks"] = live["tasks"]
        if sync_sources["finance"]["status"] == "live":
            data["budget_scenarios"] = live["budget_scenarios"]
            data["timeline"] = live["timeline"]
            data.update(live["trip_metadata"])
        if all(value["status"] == "live" for value in sync_sources.values()):
            sync_status = "live"
        elif any(value["status"] == "live" for value in sync_sources.values()):
            sync_status = "partial"
except Exception as exc:
    sync_error = type(exc).__name__


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
:root {--petrol:#163A4D;--green:#2E7668;--sand:#EEE7DB;--muted:#687A84;}
html, body, [class*="css"], [data-testid="stMarkdownContainer"]{font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"]{background: #F8F6F1;}
[data-testid="stSidebar"]{background:#F1ECE3;border-right:1px solid #E1D8CA;}
[data-testid="stMetricValue"]{font-size:1.7rem; color:#163A4D;}
[data-testid="stMetricLabel"]{color:#586F7B;}
h1,h2,h3{color:#163A4D !important;letter-spacing:-.025em;}
h1{font-family:'Playfair Display',serif !important;font-size:2.65rem !important;}
a{color:#286F69 !important;}
.block-container{padding-top:2rem;padding-bottom:3rem;max-width:1500px;}
.banner{background:linear-gradient(90deg,rgba(15,51,65,.94) 0%,rgba(15,51,65,.69) 55%,rgba(15,51,65,.3) 100%), url('https://upload.wikimedia.org/wikipedia/commons/4/4d/Maiori_Amalfi_coast.jpg') center 55% / cover;
  border-radius:22px; min-height:270px; display:flex;align-items:center;padding:42px; color:white;margin:5px 0 19px;}
.banner h2{color:white !important;font-family:'Playfair Display',serif;font-size:2.5rem;max-width:720px;line-height:1.2;margin:7px 0;}
.banner p{color:#ECF4F1;margin:0;}
.eyebrow{letter-spacing:.17em;font-size:.75rem;font-weight:700;color:#2E7668;text-transform:uppercase;}
.banner .eyebrow{color:#C4E1D5;}
.section-title{font-family:'Playfair Display',serif;font-size:1.55rem;color:#163A4D;margin:18px 0 10px;}
.note{background:#F1ECE3;border-left:3px solid #B98132;padding:11px 15px;border-radius:7px;color:#344E5A;font-size:.87rem;line-height:1.5;}
.hint{font-size:.84rem;color:#617582;}
.pill{display:inline-block;border-radius:99px;padding:4px 10px;font-size:.73rem;font-weight:700;}
.pill-main{background:#D5E9E1;color:#205F59;}
.pill-candidate{background:#FFF0D9;color:#93632B;}
.pill-possible{background:#E7ECF1;color:#476272;}
.timeline-step{border-left:3px solid #2E7668;padding:7px 15px 17px;margin-left:12px;}
.timeline-step small{color:#70838A;font-size:.8rem;}
.timeline-step b{color:#163A4D;font-size:1.06rem;}
.source-footer{font-size:.78rem;color:#60757E;border-top:1px solid #E3DED3;padding-top:14px;margin-top:24px;}
[data-testid="stDataFrame"]{border-radius:12px;}
</style>
""", unsafe_allow_html=True)


def link(label: str, key: str) -> None:
    url = data["sources"].get(key)
    if url:
        st.link_button(label, url, use_container_width=True)


def note(msg: str) -> None:
    st.markdown(f'<div class="note">{escape(msg)}</div>', unsafe_allow_html=True)


def overline(label: str) -> None:
    st.markdown(f'<div class="eyebrow">{escape(label)}</div>', unsafe_allow_html=True)


def section(text: str) -> None:
    st.markdown(f'<div class="section-title">{escape(text)}</div>', unsafe_allow_html=True)


def map_view(places: list[dict], height: int = 430) -> None:
    points = [dict(p, color=STATUS_COLORS[p["status"]], status_label=STATUS_LABEL[p["status"]]) for p in places]
    if not points:
        st.info("Nenhum destino corresponde aos filtros.")
        return
    scatter = pdk.Layer(
        "ScatterplotLayer", data=points, get_position="[lon, lat]", get_fill_color="color",
        get_radius=25000, radius_min_pixels=6, radius_max_pixels=15, stroked=True,
        get_line_color=[255, 255, 255], line_width_min_pixels=2, pickable=True,
    )
    label = pdk.Layer(
        "TextLayer", data=points, get_position="[lon, lat]", get_text="name",
        get_size=13, size_min_pixels=10, get_color=[27, 53, 64],
        get_pixel_offset=[0, 15], get_text_anchor="'middle'", pickable=True,
    )
    view = pdk.ViewState(latitude=45.3, longitude=10.1, zoom=4.0, min_zoom=2, max_zoom=14)
    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=view, layers=[scatter, label],
        tooltip={"html":"<b>{name}</b><br/>{country}<br/>{status_label}<br/>{role}",
                 "style":{"backgroundColor":"#163A4D","color":"white","fontFamily":"sans-serif"}},
    )
    st.pydeck_chart(deck, height=height, width="stretch")


def show_place(place: dict) -> None:
    role=escape(place["role"])
    st.markdown(f"**{escape(place['name'])} · {escape(place['country'])}**")
    st.caption(f"{STATUS_LABEL[place['status']]} · {role}")
    st.write(place["description"])
    st.write(f"**Duração:** {place['duration']}")
    url=data["sources"].get(place.get("source", ""))
    if url:
        st.link_button("Ver pesquisa ou decisão no Drive", url)


def mini_budget() -> None:
    selected = st.radio("Cenário", ["60k", "70k"], format_func=lambda x:"R$ 60 mil" if x=="60k" else "R$ 70 mil",
                        horizontal=True, key="summary_budget")
    scenario=get_scenario(data,selected)
    calc=calculate_scenario(scenario)
    st.metric("Total histórico simulado", money_brl(calc["base"]))
    st.progress(min(1.0, calc["base"]/scenario["cap_brl"]))
    st.caption(f"Limite {money_brl(scenario['cap_brl'])} · Margem {money_brl(calc['balance'])} · Reserva já incluída")
    if calc["balance"] < 1000:
        st.warning("Margem muito pequena. Não aprovar compras com estes valores sem novas cotações.")
    st.link_button("Abrir planilha original",data["sources"]["spreadsheet"],use_container_width=True)


def bottom_source() -> None:
    status_text = (f"Fontes do Drive verificadas às {escape(sync_time)} (UTC)." if sync_time
                   else f"Snapshot local de {escape(data['snapshot_date'])}.")
    details = " · ".join(f"{name}: {'Drive' if status['status'] == 'live' else 'snapshot'}" for name, status in sync_sources.items())
    st.markdown(f"<div class='source-footer'>{status_text} {escape(details)}. "
                "As finanças são estimativas, não preços cotados nem reservas. "
                "O mapa usa uma base geográfica de referência, não rotas contratadas.</div>", unsafe_allow_html=True)
    with st.expander("Fontes e documentação do projeto"):
        for title,key in [("Pasta do Drive","project_folder"),("Estado atual","decisions"),("Planilha financeira","spreadsheet"),
                           ("Markdown completo","knowledge"),("Pendências","tasks")]:
            st.markdown(f"- [{title}]({data['sources'][key]})")
        st.markdown(f"Crédito da fotografia: [{data['hero_image_credit']}]({data['hero_image_credit_url']}).")

with st.sidebar:
    st.markdown("### ✧ Nossa Europa 2027")
    st.caption("Lua de mel + temporada francesa")
    page = st.radio("Explorar", ["Visão geral", "Mapa & destinos", "Roteiro", "Orçamento", "Pesquisas & decisões"], label_visibility="collapsed")
    st.divider()
    st.caption("**ORIGEM DOS DADOS**")
    st.caption("Drive sincronizado" if sync_status == "live" else ("Drive parcialmente sincronizado" if sync_status == "partial" else "Snapshot de 14/11/2026"))
    for source_name, source_label in (("decisions", "Decisões"), ("tasks", "Pendências"), ("finance", "Financeiro e roteiro")):
        state = sync_sources[source_name]
        st.caption(f"{'✅' if state['status'] == 'live' else '⚪'} {source_label}: {state['status']}" + (f" · {state['modified_at'][:10]}" if state.get('modified_at') else ""))
    if st.button("Atualizar dados do Drive", use_container_width=True):
        fetch_live.clear()
        st.rerun()
    if sync_error:
        # Exception class only; never expose keys, tokens or raw API errors.
        st.warning("Sincronização indisponível; exibindo snapshot.")
        diagnosis = {
            "StreamlitSecretNotFoundError": "Secrets ausentes: configure [gcp_service_account] em Settings → Secrets.",
            "KeyError": "O campo [gcp_service_account] ou um campo obrigatório está ausente.",
            "ValueError": "Formato da credencial inválido. Confira especialmente os caracteres de nova linha na chave privada.",
            "MalformedError": "A chave privada não pôde ser interpretada.",
            "RefreshError": "O Google rejeitou a autenticação. Confira se a chave está ativa.",
        }.get(sync_error, "Verifique os logs do aplicativo no Streamlit Cloud.")
        st.error(f"Diagnóstico: {sync_error}. {diagnosis}")
    elif not any(state["status"] == "live" for state in sync_sources.values()):
        st.info("Nenhuma fonte sincronizada. Confira os Secrets e os avisos abaixo.")
    if sync_issues:
        with st.expander(f"Avisos de sincronização ({len(sync_issues)})"):
            for issue in sync_issues:
                st.warning(issue)
    st.link_button("Abrir pasta no Drive", data["sources"]["project_folder"], use_container_width=True)
    st.info("Painel em desenvolvimento. Nenhum voo, imóvel ou passeio foi reservado.")

if page == "Visão geral":
    overline("Painel de viagem · planejamento 2027")
    st.markdown('''<div class="banner"><div><div class="eyebrow">Itália → França</div>
      <h2>Do início da nossa lua de mel às semanas vivendo na Europa.</h2>
      <p>Uma viagem para explorar, viver e decidir com tranquilidade.</p></div></div>''',unsafe_allow_html=True)
    kpis=st.columns(4)
    for col,(lab,val) in zip(kpis,[("Casamento",data["wedding_date"]),("Permanência proposta",f"{data['duration_min_days']}–{data['duration_max_days']} dias"),
                                    ("Viajantes",f"{data['travelers']} pessoas"),("Tetos de orçamento","R$ 60k / 70k")]):
        with col: st.metric(lab,val)
    col1,col2=st.columns([1.7,1],gap="large")
    with col1:
        section("Nosso mapa")
        map_view([p for p in data["places"] if p["id"] in {"roma","maiori","napoles","mulhouse","strasbourg","interlaken","luxemburgo","freiburg"}],390)
        st.caption("Mapa de cidades de referência: mudanças de status refletem apenas decisões aprovadas no Drive; atrações e viagens não são reservas.")
    with col2:
        section("Orçamento em uma olhada")
        mini_budget()
        section("Próximas decisões")
        for d in data["decisions"]:
            if d["status"].casefold() in {"aberta", "não decidida", "nao decidida"}: st.markdown(f"**{d['title']}** — {d['note']}")
        st.caption("Ver as demais pendências na área de pesquisas.")
    section("Etapas da viagem")
    a,b,c=st.columns(3)
    for col,title,duration,details in [(a,"01 · Itália","~10 dias","Roma, praia e Costa Amalfitana"),
                                       (b,"02 · Instalação","3–5 dias","Chegada à base francesa"),
                                       (c,"03 · França","55–65 dias ao todo","Férias restantes + trabalho remoto")]:
        with col:
            with st.container(border=True):
                st.caption(title)
                st.markdown(f"### {duration}")
                st.write(details)
    note("As datas exatas, cidades, voos e apartamentos ainda serão definidos. As estimativas financeiras são históricas e têm folgas insuficientes para aprovar reservas.")

elif page == "Mapa & destinos":
    overline("Explorar nossa geografia")
    st.title("Mapa & destinos")
    st.caption("Catálogo geográfico do snapshot; uma cidade-base aprovada no D-004 muda de marcador automaticamente. As demais atrações não são lidas de rotas em tempo real.")
    st.write("Explore destinos propostos, cidades-base em avaliação e passeios possíveis. Use os filtros para montar sua visão.")
    statuses=st.multiselect("Situação", list(STATUS_LABEL.keys()), default=list(STATUS_LABEL.keys()),format_func=lambda x: STATUS_LABEL[x])
    countries=st.multiselect("Países", sorted(set(p["country"] for p in data["places"])),default=sorted(set(p["country"] for p in data["places"])))
    current=select_places(data["places"],countries,statuses)
    map_view(current, 520)
    st.caption("Cores: verde-petróleo = etapa proposta; âmbar = alternativa; azul-cinza = passeio possível. Não há rotas de deslocamento confirmadas.")
    if current:
        chosen=st.selectbox("Detalhes do destino",[p["id"] for p in current],format_func=lambda x:next(p["name"]+" · "+p["country"] for p in current if p["id"]==x))
        with st.container(border=True):show_place(next(p for p in current if p["id"]==chosen))

elif page == "Roteiro":
    overline("Etapas da viagem")
    st.title("Roteiro & calendário")
    note("Cronograma da aba 04 do Excel oficial." if sync_sources['finance']['status'] == 'live' else "Cronograma histórico do snapshot. Apenas o casamento é data fixa; não existem reservas confirmadas.")
    for entry in data["timeline"]:
        st.markdown(f"<div class='timeline-step'><small>{escape(entry['period'])} · {escape(entry['status'].upper())}</small>"
                    f"<br><b>{escape(entry['stage'])}</b><br>{escape(entry['details'])}</div>",unsafe_allow_html=True)
    section("Acompanhar decisões")
    link("Abrir decisões no Drive", "decisions")

elif page == "Orçamento":
    overline("Controle financeiro · dois viajantes")
    st.title("Orçamento & cenários")
    note("Valores calculados das premissas vigentes da aba 03 do Excel, conferidos com o cache da aba 02. São estimativas, não cotações. Reserva já incluída." if sync_sources['finance']['status'] == 'live' else "Números do snapshot histórico de 14/11/2026. Reserva já incluída. Não usar como tarifa real de 2027.")
    choice=st.radio("Cenário base",["60k","70k"],format_func=lambda x:"R$ 60 mil · ~65 dias" if x=="60k" else "R$ 70 mil · ~70 dias",horizontal=True)
    scenario=get_scenario(data,choice)
    c1,c2,c3=st.columns(3)
    baseline=calculate_scenario(scenario)
    c1.metric("Teto do casal",money_brl(scenario["cap_brl"]))
    c2.metric("Total histórico",money_brl(baseline["total"]))
    c3.metric("Folga simulada",money_brl(baseline["balance"]))
    section("Distribuição do orçamento histórico")
    st.bar_chart([{"Categoria": x["name"], "Valor (R$)": x["amount"]} for x in scenario["components"]], x="Categoria", y="Valor (R$)", horizontal=True, height=330)
    st.caption("Valores por categoria estão em reais. Reserva emergencial já está dentro do total.")
    if baseline["rounding_difference"]:
        st.info(f"A soma dos componentes difere {money_brl(abs(baseline['rounding_difference']))} do total histórico registrado. Trata-se de uma diferença a reconciliar com as fórmulas originais.")
    section("Simulação livre: aluguel mais caro")
    st.write("Teste um aumento hipotético no aluguel mensal, sem alterar a planilha nem afirmar que exista uma oferta nesse preço.")
    a,b,c=st.columns(3)
    with a: extra=a.slider("Aumento do aluguel (€/mês)",0,600,200,25)
    with b: months=b.number_input("Meses cobrados",min_value=1,max_value=4,value=2,step=1)
    with c: rate=c.number_input("Câmbio hipotético (R$/€)",min_value=4.0,max_value=10.0,value=6.30,step=0.05)
    res=calculate_scenario(scenario,extra,months,rate)
    aa,bb,cc=st.columns(3)
    aa.metric("Acréscimo simulado",money_brl(res["delta"]))
    bb.metric("Novo total hipotético",money_brl(res["total"]),delta=money_brl(res["delta"]),delta_color="inverse")
    cc.metric("Saldo até o teto",money_brl(res["balance"]))
    if res["balance"]<0:st.error("O cenário hipotético ultrapassa o teto. É necessário cortar despesas ou revisar a duração.")
    else:st.warning("O cenário permanece no teto, mas a margem ainda precisa de proteção e de cotações reais.")
    link("Abrir o modelo financeiro original", "spreadsheet")

elif page == "Pesquisas & decisões":
    overline("Registro do planejamento")
    st.title("Pesquisas, decisões e pendências")
    st.caption("Decisões e pendências: leitura atualizada do Drive (cache de até 5 min)." if sync_status == "live" else "Dados locais históricos; sincronização não configurada ou indisponível.")
    section("Decisões")
    for d in data["decisions"]:
        with st.expander(f"{d['id']} · {d['title']} · {d['status']}"):
            st.write(d["note"])
            st.markdown(f"[Fonte: decisões no Google Drive]({data['sources']['decisions']})")
    section("Fila de pesquisas")
    selected_priority=st.selectbox("Prioridade",["Todas","P0","P1","P2","P3"])
    for item in data["tasks"]:
        if selected_priority=="Todas" or item["priority"]==selected_priority:
            st.checkbox(f"{item['priority']} · {item['title']}",value=item.get("status") == "concluído",disabled=True)
    link("Abrir pendências no Drive", "tasks")
    section("Fontes principais")
    for text,key in [("Guia do projeto","guide"),("Estado atual","decisions"),("Padrão de evidências","evidence"),
                      ("Base completa Markdown","knowledge"),("Planilha de orçamento","spreadsheet")]:
        st.markdown(f"- [{text}]({data['sources'][key]})")

bottom_source()