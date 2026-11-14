"""Europa 2027 — Streamlit travel + planning dashboard (read-only MVP)."""
from __future__ import annotations

from html import escape
from pathlib import Path

import pydeck as pdk
import streamlit as st

from data_model import STATUS_COLORS, STATUS_LABEL, calculate_scenario, get_scenario, load_data, money_brl, select_places
from drive_sync import load_live_updates, update_map_places
from city_compare import get_preset, load_cities, normalized_weights, rank_cities

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

/* FASE 1: visual editorial para home, sem alterar lógica de dados. */
.home-hero{display:flex;align-items:center;min-height:300px;padding:clamp(26px,4vw,54px);
  overflow:hidden;border-radius:23px;margin:7px 0 22px;
  box-shadow:0 14px 37px rgba(19,53,64,.10);
  background:linear-gradient(90deg,rgba(12,42,56,.96),rgba(12,42,56,.83) 48%,rgba(12,42,56,.19)),
  url('https://upload.wikimedia.org/wikipedia/commons/4/4d/Maiori_Amalfi_coast.jpg') center 52%/cover;}
.home-hero__content{max-width:680px;}
.home-hero__eyebrow{color:#C8E1D8;font-size:.74rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;}
.home-hero h1{font-family:'Playfair Display',Georgia,serif !important;color:#fff !important;
  font-size:clamp(2rem,3.5vw,3.2rem) !important;line-height:1.14;letter-spacing:-.018em;margin:13px 0;}
.home-hero p{font-size:1rem;color:#E7F2F0;line-height:1.6;max-width:520px;margin-bottom:15px;}
.home-hero__chips{display:flex;flex-wrap:wrap;gap:8px;}
.home-hero__chips span{display:inline-block;color:#F4F8F6;background:rgba(18,48,60,.48);
  border:1px solid rgba(237,245,238,.28);border-radius:50px;padding:6px 11px;font-size:.77rem;font-weight:600;}
.home-kpi{background:#fff;border:1px solid #E4E0D8;border-radius:16px;
  min-height:122px;padding:17px 16px 15px;margin:0 0 6px;box-shadow:0 5px 18px rgba(30,56,58,.034);}
.home-kpi__label{font-size:.73rem;color:#67808A;letter-spacing:.08em;text-transform:uppercase;font-weight:700;}
.home-kpi__value{color:#163A4D;font-size:clamp(1.2rem,1.9vw,1.67rem);line-height:1.2;
  margin:10px 0 6px;font-weight:700;letter-spacing:-.032em;overflow-wrap:anywhere;}
.home-kpi__detail{font-size:.78rem;color:#677C82;line-height:1.45;}
.home-section-label{color:#2E7668;font-size:.73rem;font-weight:700;letter-spacing:.14em;
  text-transform:uppercase;margin:27px 0 5px;}
.home-section-title{color:#163A4D;font-family:'Playfair Display',Georgia,serif;
  font-size:clamp(1.6rem,2.5vw,2.2rem);letter-spacing:-.025em;margin:0 0 8px;}
.home-section-sub{color:#667B83;font-size:.9rem;line-height:1.6;margin-bottom:17px;}
.home-stage{min-height:165px;background:#fff;border:1px solid #E4E0D8;border-radius:16px;
  padding:19px 18px;box-shadow:0 5px 18px rgba(30,56,58,.032);margin-bottom:8px;border-top:3px solid #2E7668;}
.home-stage__no{color:#B98132;font-size:.72rem;font-weight:700;letter-spacing:.12em;}
.home-stage__name{color:#163A4D;font-family:'Playfair Display',Georgia,serif;
  font-size:1.3rem;font-weight:700;margin:9px 0 7px;}
.home-stage__desc{color:#637983;font-size:.84rem;line-height:1.58;}
.home-disclaimer{background:#F0EAE0;border:1px solid #E3D8C8;padding:14px 16px;
  border-radius:12px;color:#5E696D;font-size:.82rem;line-height:1.58;margin-top:10px;}
.home-decision{background:#fff;border:1px solid #E4E0D8;border-radius:14px;
  padding:17px 19px;margin-bottom:10px;min-height:114px;box-shadow:0 5px 18px rgba(30,56,58,.025);}
.home-decision strong{display:block;color:#163A4D;font-size:.98rem;}
.home-decision p{color:#677C82;font-size:.84rem;line-height:1.5;margin:10px 0 0;}
.sidebar-brand{padding:6px 0 10px;margin-bottom:12px;}
.sidebar-brand small{display:block;font-size:.65rem;letter-spacing:.18em;font-weight:700;color:#2E7668;}
.sidebar-brand strong{font-family:'Playfair Display',Georgia,serif;display:block;color:#163A4D;
  font-size:1.7rem;letter-spacing:-.03em;line-height:1.2;margin:8px 0 5px;}
.sidebar-brand span{font-size:.83rem;color:#607682;}
@media(max-width:980px){.home-hero{min-height:260px;padding:28px;}.home-hero h1{font-size:2.2rem !important;}}
@media(max-width:640px){.home-hero{min-height:250px;padding:24px 18px;border-radius:16px;}
  .home-hero h1{font-size:1.9rem !important;}.home-hero p{font-size:.9rem;}
  .home-kpi{min-height:102px;padding:15px;}.home-stage{min-height:0;}
  .block-container{padding-left:1rem;padding-right:1rem;}}

/* FASE 1B — modern travel app / minimal A+B approved by user */
:root {--ui-navy:#132B3D;--ui-blue:#168AC6;--ui-mint:#0B967E;--ui-bg:#F8FBFE;--ui-border:#E3EBF2;}
html,body,[class*="css"],[data-testid="stMarkdownContainer"]{font-family:'DM Sans',system-ui,sans-serif !important;}
[data-testid="stAppViewContainer"]{background:#FAFCFE !important;}
[data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E9EFF5 !important;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label{border-radius:10px;padding:8px 10px;margin:0 0 2px;transition:background .15s;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover{background:#EFF8FF;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked){background:#E5F4FF;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label p{color:#17354A !important;font-weight:600;}
[data-testid="stSidebar"] [data-testid="stInfo"]{background:#EDF7FC;border:1px solid #E0EBF3;color:#2C5870;}
.block-container{max-width:1520px;padding-top:1.25rem;padding-bottom:3rem;}
h1,h2,h3{font-family:'DM Sans',system-ui,sans-serif !important;color:#16364B !important;letter-spacing:-.035em;}
a{color:#1684B2 !important;}
.sidebar-brand{margin-bottom:14px;border-bottom:1px solid #E9EFF4;padding:4px 0 20px;}
.sidebar-brand small{color:#078F88;}
.sidebar-brand strong{font-family:'DM Sans',system-ui,sans-serif !important;font-size:1.55rem;font-weight:800;letter-spacing:-.045em;}
.sidebar-brand span{color:#647E91;}
.home-hero{min-height:272px;margin:8px 0 16px;padding:clamp(26px,3.7vw,55px);border-radius:20px;box-shadow:none;
  background:linear-gradient(90deg,rgba(7,47,71,.93) 0%,rgba(10,56,76,.76) 36%,rgba(8,65,82,.17) 78%),url('https://upload.wikimedia.org/wikipedia/commons/4/4d/Maiori_Amalfi_coast.jpg') center 48%/cover;}
.home-hero__content{max-width:740px;}
.home-hero__eyebrow{font-size:.70rem;letter-spacing:.17em;color:#D7F3F8;font-weight:800;}
.home-hero h1{font-family:'DM Sans',system-ui,sans-serif !important;font-size:clamp(2.1rem,3.35vw,3.2rem) !important;font-weight:800;line-height:1.1;letter-spacing:-.045em;margin:13px 0;}
.home-hero p{font-size:.96rem;line-height:1.52;max-width:570px;}
.home-hero__chips{gap:9px;}
.home-hero__chips span{background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.46);font-size:.75rem;padding:6px 10px;backdrop-filter:blur(4px);}
.home-kpi{position:relative;background:#F2F8FC;border:0;border-radius:15px;min-height:109px;padding:15px 18px;margin:0;box-shadow:none;}
.home-kpi--wedding{background:#FCF8F4;}
.home-kpi--departure{background:#EDF7FE;}
.home-kpi--duration{background:#EEF9F7;}
.home-kpi--budget{background:#EEF7FD;}
.home-kpi__label{letter-spacing:0;text-transform:none;color:#21475D;font-size:.78rem;font-weight:700;padding-left:38px;}
.home-kpi__icon{position:absolute;left:17px;top:17px;font-size:1.35rem;line-height:1;}
.home-kpi__value{font-size:clamp(1.05rem,1.65vw,1.58rem);color:#102C41;letter-spacing:-.04em;margin:8px 0 5px;overflow-wrap:normal;}
.home-kpi__detail{color:#637B8D;font-size:.77rem;}
.home-section-label{color:#168D82;margin:22px 0 6px;letter-spacing:.11em;}
.home-section-title{font-family:'DM Sans',system-ui,sans-serif;font-size:clamp(1.5rem,2.1vw,2rem);font-weight:800;letter-spacing:-.04em;margin:0 0 7px;}
.home-section-sub{color:#647F90;line-height:1.55;}
.home-overview-copy{padding:12px 2px 0;}
.home-overview-copy h2{font-family:'DM Sans',system-ui,sans-serif !important;font-size:clamp(1.38rem,1.85vw,1.8rem);font-weight:800;line-height:1.25;}
.home-overview-copy p{font-size:.87rem;color:#638093;line-height:1.65;}
.home-mini-budget{border:1px solid #E4ECF4;background:#FFF;padding:17px 19px;border-radius:17px;min-height:182px;box-shadow:0 5px 20px rgba(34,69,95,.035);}
.home-mini-budget__eyebrow{font-size:.76rem;color:#27475A;font-weight:700;}
.home-mini-budget__amount{font-size:clamp(1.3rem,2vw,1.9rem);color:#0B947D;font-weight:800;letter-spacing:-.045em;margin:14px 0 10px;}
.home-mini-budget__track{height:9px;background:#E7EDF2;border-radius:20px;overflow:hidden;margin:8px 0 11px;}
.home-mini-budget__fill{height:100%;background:#0B9E89;border-radius:20px;}
.home-mini-budget__foot{font-size:.77rem;color:#647C8B;}
.home-map-caption{font-size:.76rem;color:#617D8D;margin-top:5px;}
.home-decision{min-height:85px;padding:14px 16px;border-radius:13px;border:1px solid #E4ECF4;box-shadow:0 4px 15px rgba(32,65,85,.03);}
.home-decision strong{font-size:.89rem;font-weight:700;}
.home-decision p{font-size:.78rem;margin:7px 0 0;}
.home-stage{border:1px solid #E1E9F1;border-radius:17px;padding:0;overflow:hidden;min-height:0;box-shadow:0 5px 17px rgba(33,70,87,.045);border-top:0;}
.home-stage__image{height:112px;background-size:cover;background-position:center 48%;}
.home-stage__inside{padding:12px 16px 17px;}
.home-stage__no{font-size:.69rem;letter-spacing:.1em;color:#A76A20;}
.home-stage__name{font-family:'DM Sans',system-ui,sans-serif;font-weight:800;letter-spacing:-.03em;font-size:1.12rem;margin:6px 0 5px;}
.home-stage__desc{font-size:.79rem;color:#67808C;line-height:1.5;}
.home-disclaimer{background:#F2F7FB;border:1px solid #E0EAF1;border-radius:12px;color:#5B7481;}
.home-sync-pill{display:flex;align-items:center;gap:8px;background:#EEF9F6;border:1px solid #D7EAE4;padding:10px 12px;border-radius:11px;color:#136F60;font-size:.81rem;font-weight:700;margin:10px 0;}
@media(max-width:1050px){.home-hero{min-height:230px;}.home-kpi__label{padding-left:0;}.home-kpi__icon{position:static;display:block;margin-bottom:5px;}}
@media(max-width:640px){.block-container{padding:1rem !important;}.home-hero{padding:24px 19px;min-height:260px;border-radius:14px;}
.home-hero h1{font-size:2rem !important;}.home-stage__image{height:135px;}.home-kpi{min-height:95px;}
.home-overview-copy{padding:0 0 9px;}}


/* Remaining screens: shared light travel-app design system */
.page-eyebrow{font-size:.7rem;letter-spacing:.13em;font-weight:800;color:#0A9889;text-transform:uppercase;margin:10px 0 7px;}
.page-title{font-family:'DM Sans',system-ui,sans-serif;font-size:clamp(1.75rem,2.7vw,2.55rem);
  font-weight:800;color:#16364B;letter-spacing:-.045em;line-height:1.16;margin:0 0 9px;}
.page-subtitle{color:#647E90;font-size:.94rem;line-height:1.55;max-width:760px;margin:0 0 18px;}
.page-stat{background:#fff;border:1px solid #E3EBF2;border-radius:15px;padding:15px 17px;
  min-height:108px;box-shadow:0 4px 18px rgba(29,68,93,.028);margin-bottom:9px;}
.page-stat__label{font-size:.74rem;color:#698396;font-weight:700;}
.page-stat__value{font-size:clamp(1.18rem,1.8vw,1.7rem);font-weight:800;color:#15364B;margin:8px 0 4px;letter-spacing:-.04em;}
.page-stat__hint{font-size:.75rem;color:#6B8191;line-height:1.35;}
.page-stat--mint{background:#EDF9F6;border-color:#E1F1ED;}
.page-stat--blue{background:#EFF8FE;border-color:#E2F0FA;}
.page-stat--cream{background:#FCF8F3;border-color:#F4EBE1;}
.page-panel{background:#fff;border:1px solid #E2EBF2;border-radius:16px;padding:18px 20px;
  box-shadow:0 6px 18px rgba(23,59,80,.025);margin-bottom:12px;}
.page-panel__title{font-weight:800;color:#16364B;font-size:1rem;line-height:1.35;}
.page-panel__desc{color:#667E8C;font-size:.85rem;line-height:1.6;margin:9px 0 10px;}
.page-panel__meta{color:#758998;font-size:.75rem;}
.page-chip{display:inline-block;background:#EAF6FD;color:#1777A4;border-radius:99px;
  padding:5px 10px;font-size:.71rem;font-weight:800;letter-spacing:.015em;}
.page-chip--candidate{background:#FFF3E5;color:#966226;}
.page-chip--proposed{background:#E7F7F2;color:#157C6B;}
.page-chip--optional{background:#EDF1FA;color:#576F95;}
.page-section{color:#183D53;font-weight:800;font-size:1.21rem;letter-spacing:-.025em;margin:21px 0 12px;}
.page-timeline{display:flex;gap:16px;align-items:stretch;background:#fff;border:1px solid #E4ECF2;
  border-radius:15px;padding:16px 20px;margin:0 0 11px;box-shadow:0 4px 15px rgba(30,60,84,.02);}
.page-timeline__number{display:flex;align-items:center;justify-content:center;flex:0 0 36px;
  height:36px;border-radius:12px;background:#EAF7FB;color:#1486AC;font-weight:800;font-size:.85rem;}
.page-timeline__content{flex:1;min-width:0;}
.page-timeline__period{font-size:.72rem;font-weight:800;color:#178B82;letter-spacing:.055em;}
.page-timeline__stage{font-size:1.03rem;color:#15384E;font-weight:800;margin:4px 0;}
.page-timeline__desc{font-size:.85rem;color:#647E90;line-height:1.55;}
.page-task{background:#fff;border:1px solid #E4EBF1;border-radius:13px;display:flex;align-items:flex-start;
  gap:13px;padding:14px 15px;margin:0 0 9px;}
.page-task__tag{flex-shrink:0;padding:5px 9px;border-radius:8px;font-size:.73rem;font-weight:800;background:#EDF4FB;color:#305D8B;}
.page-task--p0 .page-task__tag{background:#FCEBED;color:#B94955;}
.page-task--p1 .page-task__tag{background:#FFF3E6;color:#A26B24;}
.page-task--p2 .page-task__tag{background:#EAF7FC;color:#2180A8;}
.page-task--p3 .page-task__tag{background:#EFF2F6;color:#6E8090;}
.page-task__body{flex:1;min-width:0;color:#2A4A5E;font-size:.86rem;line-height:1.55;}
.page-task__status{flex-shrink:0;color:#7A8E9A;font-size:.74rem;font-weight:700;}
.page-task--done .page-task__body{color:#748896;}
.page-budget-track{height:11px;background:#E4ECF0;border-radius:20px;overflow:hidden;margin:9px 0;}
.page-budget-track span{display:block;height:100%;background:linear-gradient(90deg,#18A596,#1C8BAC);border-radius:20px;}
.page-budget-row{display:flex;gap:12px;justify-content:space-between;align-items:center;
  border-bottom:1px solid #EAF0F4;padding:12px 0;font-size:.84rem;}
.page-budget-row:last-child{border:0;}
.page-budget-row__name{color:#557080;}
.page-budget-row__amount{color:#15384D;font-weight:800;white-space:nowrap;}
.page-alert{border-radius:12px;padding:13px 16px;font-size:.83rem;line-height:1.55;
  background:#FFF8EA;border:1px solid #F2E4C4;color:#856120;margin:9px 0 14px;}
.page-alert--neutral{background:#EFF7FC;border-color:#DBE9F2;color:#38657C;}
.page-filter-hint{color:#698294;font-size:.8rem;margin:2px 0 11px;}
/* Contrast fix for controls throughout the app, especially previously disabled task checkboxes */
[data-testid="stSelectbox"] [data-baseweb="select"],[data-testid="stMultiSelect"] [data-baseweb="select"]{
  color:#1E4258 !important;}
.stCheckbox label:has(input:disabled){opacity:1;}
[data-testid="stExpander"]{background:#fff;border:1px solid #E5EDF3;border-radius:13px;}
[data-testid="stMetricValue"]{color:#15374C;}
@media(max-width:700px){
 .page-panel{padding:15px 16px;}
 .page-task{gap:8px;padding:12px;}
 .page-task__status{font-size:.68rem;}
 .page-timeline{padding:13px;gap:10px;}
 .page-stat{min-height:92px;padding:13px;}
}


/* Evolução 1 — painel de comparação, reutilizando o design A+B existente */
.city-score{background:#fff;border:1px solid #E4EBF3;border-radius:18px;padding:20px;
  margin-bottom:12px;box-shadow:0 5px 20px rgba(24,65,90,.035);}
.city-score__top{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.city-score__rank{font-size:.7rem;color:#138D83;background:#EBF8F4;border-radius:9px;
  padding:6px 10px;font-weight:800;}
.city-score__name{color:#19394D;font-size:1.3rem;font-weight:800;margin:13px 0 4px;letter-spacing:-.04em;}
.city-score__number{font-size:1.7rem;font-weight:800;color:#168CB3;letter-spacing:-.045em;}
.city-score__bar{height:9px;background:#E5EDF4;border-radius:12px;overflow:hidden;margin:10px 0;}
.city-score__bar span{display:block;height:100%;background:#16A092;border-radius:12px;}
.city-score__detail{font-size:.8rem;color:#678195;line-height:1.55;}
.city-compare-caveat{border:1px solid #DCECF3;border-radius:13px;padding:13px 16px;
  background:#F0F8FC;font-size:.84rem;color:#36657C;line-height:1.55;margin:12px 0;}
.city-compare-source{font-size:.8rem;color:#627D8F;line-height:1.55;}

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


def map_view(places: list[dict], height: int = 430, show_labels: bool = True) -> None:
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
        initial_view_state=view, layers=[scatter, label] if show_labels else [scatter],
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

def navigate_page(destination: str) -> None:
    """Navigation from homepage controls, applied before the radio on rerun."""
    st.session_state["main_navigation"] = destination


with st.sidebar:
    st.markdown("""<div class='sidebar-brand'>
      <small>TRAVEL JOURNAL · 2027</small>
      <strong>✧ Nossa Europa</strong>
      <span>Lua de mel & temporada na França</span></div>""", unsafe_allow_html=True)
    page = st.radio("Explorar", ["Visão geral", "Mapa & destinos", "Comparar cidades", "Roteiro", "Orçamento", "Pesquisas & decisões"], label_visibility="collapsed", key="main_navigation", format_func=lambda name: {"Visão geral": "⌂  Visão geral", "Mapa & destinos": "▣  Mapa & destinos", "Comparar cidades": "▤  Comparar cidades", "Roteiro": "▦  Roteiro", "Orçamento": "◉  Orçamento", "Pesquisas & decisões": "☑  Pesquisas & decisões"}[name])
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
    st.markdown("""<div class="home-hero" role="region" aria-label="Apresentação da viagem">
      <div class="home-hero__content"><div class="home-hero__eyebrow">ITÁLIA → FRANÇA · 2027</div>
      <h1>Uma viagem para viver,<br>não só visitar.</h1>
      <p>Uma lua de mel entre cidades históricas, costa italiana e semanas vivendo como moradores na França.</p>
      <div class="home-hero__chips"><span>♡ Dois viajantes</span>
      <span>✧ Sem reservas confirmadas</span><span>◷ Longa temporada em estudo</span></div>
      </div></div>""", unsafe_allow_html=True)

    from datetime import date
    wedding = date.fromisoformat(data["wedding_date"])
    departure = date.fromisoformat(data["departure_candidate"])
    departure_label = departure.strftime("%d/%m/%Y") if departure > wedding else "A definir"
    cap_values = sorted({int(item["cap_brl"] / 1000) for item in data["budget_scenarios"]})
    cap_label = f"R$ {cap_values[0]} mil / R$ {cap_values[-1]} mil" if len(cap_values) > 1 else f"R$ {cap_values[0]} mil"
    cards = [
        ("Casamento", wedding.strftime("%d/%m/%Y"), "Data fixa do casal", "♡", "wedding"),
        ("Partida em estudo", departure_label, "Hipótese, sem bilhete emitido", "▦", "departure"),
        ("Permanência proposta", f"{data['duration_min_days']}–{data['duration_max_days']} dias", "Para dois viajantes", "✈", "duration"),
        ("Orçamento", cap_label, "Tetos de planejamento, não cotações", "◎", "budget"),
    ]
    for col, (label, value, detail, glyph, tone) in zip(st.columns(4, gap="small"), cards):
        with col:
            st.markdown(f"<div class='home-kpi home-kpi--{tone}'>"
                        f"<span class='home-kpi__icon' aria-hidden='true'>{glyph}</span>"
                        f"<div class='home-kpi__label'>{escape(label)}</div>"
                        f"<div class='home-kpi__value'>{escape(value)}</div>"
                        f"<div class='home-kpi__detail'>{escape(detail)}</div></div>",
                        unsafe_allow_html=True)

    overview_left, overview_map, overview_budget = st.columns([1.06, 1.42, 1.08], gap="medium")
    with overview_left:
        st.markdown("<div class='home-overview-copy'><div class='home-section-label'>VISÃO DA VIAGEM</div>"
                    "<h2>O que estamos construindo</h2>"
                    "<p>Destinos, orçamento e escolhas do casal em um só lugar. "
                    "Os pontos do mapa são referências, não reservas.</p></div>", unsafe_allow_html=True)
        st.button("Explorar destinos →", use_container_width=True,
                  on_click=navigate_page, args=("Mapa & destinos",), key="home_go_map")

    with overview_map:
        # The map displays real reference coordinates but no invented connecting route.
        map_view([p for p in data["places"] if p["id"] in {"roma", "maiori", "mulhouse", "strasbourg"}], 190)
        st.caption("Mapa de referência · cidades ainda em avaliação")

    with overview_budget:
        selected = st.radio("Cenário em estudo", ["60k", "70k"],
                            format_func=lambda x: f"R$ {x[:-1]} mil",
                            horizontal=True, key="home_budget_choice")
        scenario = get_scenario(data, selected)
        calc = calculate_scenario(scenario)
        used_pct = max(0, min(100, 100 * calc["total"] / scenario["cap_brl"]))
        st.markdown(
            "<div class='home-mini-budget'><div class='home-mini-budget__eyebrow'>◉ Resumo do orçamento</div>"
            f"<div class='home-mini-budget__amount'>{escape(money_brl(calc['total']))}</div>"
            f"<div class='home-mini-budget__track'><div class='home-mini-budget__fill' style='width:{used_pct:.1f}%'></div></div>"
            f"<div class='home-mini-budget__foot'>Margem: {escape(money_brl(calc['balance']))} · estimativa histórica</div></div>",
            unsafe_allow_html=True)
        st.button("Ver orçamento completo →", use_container_width=True,
                  on_click=navigate_page, args=("Orçamento",), key="home_go_budget")

    left, right = st.columns([2.3, 1], vertical_alignment="center")
    with left:
        st.markdown("<div class='home-section-label'>DECISÕES EM ABERTO</div>", unsafe_allow_html=True)
    with right:
        st.button("Ver todas as decisões →", use_container_width=True,
                  on_click=navigate_page, args=("Pesquisas & decisões",),
                  key="home_go_decisions")

    outstanding = [d for d in data["decisions"] if d["status"].casefold() in {"aberta", "não decidida", "nao decidida"}]
    if outstanding:
        for col, decision in zip(st.columns(min(3, len(outstanding)), gap="small"), outstanding[:3]):
            with col:
                detail = decision.get("note", "").strip()
                if not detail or detail.rstrip(".") == decision["title"].strip().rstrip("."):
                    detail = "Aguardando definição no Drive."
                st.markdown(
                    f"<div class='home-decision'><strong>{escape(decision['title'])}</strong>"
                    f"<p>{escape(detail)}</p></div>", unsafe_allow_html=True)
    else:
        st.caption("Nenhuma decisão pendente identificada no documento sincronizado.")

    st.markdown("<div class='home-section-label'>TRÊS MOMENTOS</div>", unsafe_allow_html=True)
    st.markdown("<div class='home-section-title'>Da lua de mel à vida francesa</div>", unsafe_allow_html=True)
    stages = [
        ("01 · NOSSA CHEGADA", "Itália",
         f"Cerca de {data['italy_days_approx']} dias entre Roma e uma base a escolher na Costa Amalfitana.",
         "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1000&auto=format&fit=crop&q=85", "Roteiro"),
        ("02 · NOSSA BASE", "Instalação",
         "Cerca de 3–5 dias para organizar moradia, internet e rotina na França.",
         "https://images.unsplash.com/photo-1449844908441-8829872d2607?w=1000&auto=format&fit=crop&q=85", "Roteiro"),
        ("03 · NOSSO COTIDIANO", "França",
         f"{data['france_days_estimate']} no total, incluindo férias e trabalho remoto.",
         "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1000&auto=format&fit=crop&q=85", "Roteiro"),
    ]
    for idx, (col, (number, title, description, photo, dest)) in enumerate(zip(st.columns(3, gap="medium"), stages)):
        with col:
            st.markdown(
                f"<div class='home-stage'><div class='home-stage__image' role='img' aria-label='Imagem ilustrativa: {escape(title)}' "
                f"style='background-image:url({photo})'></div>"
                f"<div class='home-stage__inside'><div class='home-stage__no'>{escape(number)}</div>"
                f"<div class='home-stage__name'>{escape(title)}</div>"
                f"<div class='home-stage__desc'>{escape(description)}</div></div></div>",
                unsafe_allow_html=True)
            st.button(f"Ver etapa: {title} →", key=f"home_stage_{idx}", use_container_width=True,
                      on_click=navigate_page, args=(dest,))

    st.markdown("<div class='home-disclaimer'>Planejamento em desenvolvimento: voos, imóveis e passeios ainda não reservados. "
                "As estimativas históricas não substituem cotações reais. Imagens ilustrativas: Wikimedia Commons e Unsplash.</div>",
                unsafe_allow_html=True)

elif page == "Mapa & destinos":
    st.markdown("<div class='page-eyebrow'>EXPLORAR · EUROPA 2027</div>"
                "<div class='page-title'>Mapa & destinos</div>"
                "<div class='page-subtitle'>Explore as cidades do planejamento, compare alternativas e "
                "acompanhe o que foi proposto ou ainda está em avaliação.</div>", unsafe_allow_html=True)
    countries_all = sorted(set(p["country"] for p in data["places"]))
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.markdown(f"<div class='page-stat page-stat--blue'><div class='page-stat__label'>Destinos mapeados</div>"
                    f"<div class='page-stat__value'>{len(data['places'])}</div>"
                    "<div class='page-stat__hint'>Referências geográficas</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='page-stat page-stat--mint'><div class='page-stat__label'>Países</div>"
                    f"<div class='page-stat__value'>{len(countries_all)}</div>"
                    "<div class='page-stat__hint'>Candidatos e passeios</div></div>", unsafe_allow_html=True)
    with c3:
        candidates = sum(p["status"] == "candidata" for p in data["places"])
        st.markdown(f"<div class='page-stat page-stat--cream'><div class='page-stat__label'>Alternativas em avaliação</div>"
                    f"<div class='page-stat__value'>{candidates}</div>"
                    "<div class='page-stat__hint'>Sem escolha definitiva</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='page-section'>Filtre os destinos</div>", unsafe_allow_html=True)
    a,b = st.columns([1,1], gap="medium")
    with a:
        countries = st.multiselect("Países", countries_all, default=countries_all, key="map_countries")
    with b:
        statuses = st.multiselect("Etapa de decisão", list(STATUS_LABEL.keys()),
                                  default=list(STATUS_LABEL.keys()), format_func=lambda key: STATUS_LABEL[key],
                                  key="map_statuses")
    current = select_places(data["places"], countries, statuses)
    st.markdown(f"<div class='page-filter-hint'>{len(current)} destinos encontrados · "
                "Os pontos não representam reservas, trajetos ou disponibilidade.</div>",
                unsafe_allow_html=True)
    map_view(current, 460, show_labels=False)
    st.caption("Passe o cursor sobre um ponto para ver o nome e a classificação. "
               "Os marcadores são referências geográficas, não rotas de transporte.")

    st.markdown("<div class='page-section'>Conheça as opções</div>", unsafe_allow_html=True)
    if current:
        for start_idx in range(0, len(current), 3):
            row = current[start_idx:start_idx+3]
            for column, place in zip(st.columns(3, gap="medium"), row):
                with column:
                    tone = {"roteiro_proposto":"proposed", "candidata":"candidate", "opcional":"optional"}.get(place["status"], "optional")
                    st.markdown(f"<div class='page-panel'>"
                                f"<span class='page-chip page-chip--{tone}'>{escape(STATUS_LABEL[place['status']])}</span>"
                                f"<div class='page-panel__title' style='margin-top:12px'>⌖ {escape(place['name'])}</div>"
                                f"<div class='page-panel__meta'>{escape(place['country'])} · {escape(place['role'])}</div>"
                                f"<p class='page-panel__desc'>{escape(place['description'])}</p>"
                                f"<div class='page-panel__meta'>Duração: {escape(place['duration'])}</div></div>",
                                unsafe_allow_html=True)
                    source_url = data["sources"].get(place.get("source", ""))
                    if source_url:
                        st.link_button("Consultar fonte", source_url, use_container_width=True)
    else:
        st.info("Nenhum destino corresponde aos filtros. Selecione mais países ou etapas.")
    st.markdown("<div class='page-alert page-alert--neutral'>"
                "Cidades e coordenadas vêm do catálogo histórico; a decisão sobre uma cidade-base francesa "
                "pode atualizar o status a partir do documento do Drive. Os demais pontos não são atualizados "
                "automaticamente por cotações ou reservas.</div>", unsafe_allow_html=True)

elif page == "Comparar cidades":
    city_data = load_cities()
    criteria_ids = [criterion["id"] for criterion in city_data["criteria"]]
    st.markdown("<div class='page-eyebrow'>FRANÇA · ESCOLHA DA CIDADE-BASE</div>"
                "<div class='page-title'>Onde vamos morar na França?</div>"
                "<div class='page-subtitle'>Compare quatro cidades com as notas históricas da planilha. "
                "Altere as prioridades para entender os trade-offs; nenhuma cidade foi aprovada ainda.</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='city-compare-caveat'>"
                "As notas (0–5) são avaliações editoriais históricas de novembro/2026, "
                "não indicadores oficiais de qualidade de vida. Aluguéis são envelopes de planejamento "
                "em €/mês, e não ofertas disponíveis para setembro–novembro/2027. "
                "A mudança dos pesos NÃO altera o Drive, a decisão D-004 nem o orçamento global.</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-section'>Personalize suas prioridades</div>", unsafe_allow_html=True)
    profile = st.selectbox("Perfil de comparação", city_data["presets"],
                           format_func=lambda item: item["label"], key="city_compare_profile",
                           help="Perfis transcritos da aba 12 PESOS CIDADES do Excel histórico.")
    profile_id = profile["id"]
    if st.session_state.get("_last_city_profile") != profile_id:
        for crit_id, value in get_preset(city_data, profile_id).items():
            st.session_state[f"city_weight_{crit_id}"] = int(value)
        st.session_state["_last_city_profile"] = profile_id
    cols = st.columns(3, gap="medium")
    weights = {}
    for idx, criterion in enumerate(city_data["criteria"]):
        with cols[idx % 3]:
            weights[criterion["id"]] = st.slider(
                criterion["label"], min_value=0, max_value=100, step=5,
                key=f"city_weight_{criterion['id']}",
                help=criterion["explanation"])
    total_weights = sum(weights.values())
    if total_weights == 0:
        st.warning("Escolha ao menos um critério com peso acima de zero para calcular o ranking.")
    else:
        actual_weights = normalized_weights(weights, criteria_ids)
        st.caption(f"Pesos inseridos: {total_weights}% no total. "
                   "Normalização automática para 100%: "
                   + " · ".join(f"{criterion['label']}: {actual_weights[criterion['id']]*100:.0f}%"
                                for criterion in city_data["criteria"]))
        ranking = rank_cities(city_data["cities"], weights, criteria_ids)
        st.markdown("<div class='page-section'>Ranking por suas preferências</div>",
                    unsafe_allow_html=True)
        for start in range(0, len(ranking), 2):
            for col, (pos, item) in zip(st.columns(2, gap="medium"),
                                         list(enumerate(ranking, 1))[start:start+2]):
                city = item["city"]
                with col:
                    percentage = min(100.0, max(0.0, item["score"] / 5.0 * 100.0))
                    st.markdown(
                        "<div class='city-score'>"
                        f"<div class='city-score__top'><span class='city-score__rank'>#{pos} · Ranking simulado</span>"
                        f"<span class='city-score__number'>{item['score']:.3f}/5</span></div>"
                        f"<div class='city-score__name'>{escape(city['name'])}</div>"
                        f"<div class='city-score__bar'><span style='width:{percentage:.2f}%'></span></div>"
                        f"<div class='city-score__detail'>{escape(city['summary'])}</div>"
                        f"<div class='city-score__detail' style='margin-top:10px'>"
                        f"Aluguel de referência histórica: <b>€ {city['reference_rent_eur']:,.0f}/mês</b> "
                        f"· Envelope € {city['range_eur'][0]:,.0f}–{city['range_eur'][1]:,.0f}/mês</div></div>",
                        unsafe_allow_html=True)
        st.markdown("<div class='page-section'>Notas por critério</div>",unsafe_allow_html=True)
        import pandas as pd
        table_rows = []
        for item in ranking:
            city = item["city"]
            table_rows.append({"Cidade": city["name"],"Score ponderado":round(item["score"],3),
                               "Ranking histórico":city["historic_score"],
                               "Aluguel ref. €/mês":city["reference_rent_eur"],
                               **{c["label"]:city["scores"][c["id"]] for c in city_data["criteria"]}})
        st.dataframe(pd.DataFrame(table_rows),use_container_width=True,hide_index=True,
                     column_config={"Score ponderado":st.column_config.NumberColumn(format="%.3f"),
                                    "Ranking histórico":st.column_config.NumberColumn(format="%.3f"),
                                    "Aluguel ref. €/mês":st.column_config.NumberColumn(format="€ %.0f")},
                     height=190)

        st.markdown("<div class='page-section'>Comparação lado a lado</div>",unsafe_allow_html=True)
        city_names = [city["name"] for city in city_data["cities"]]
        selected = st.multiselect("Selecione até duas cidades",city_names,
                                  default=["Mulhouse","Strasbourg"],max_selections=2,
                                  key="city_compare_pair")
        compare_index = {item["city"]["name"]:item for item in ranking}
        if not selected:
            st.info("Escolha uma ou duas cidades para ver os detalhes.")
        for col, city_name in zip(st.columns(2, gap="medium"),selected):
            city = compare_index[city_name]["city"]
            with col:
                st.markdown(
                    f"<div class='page-panel'><div class='page-panel__title'>{escape(city_name)}</div>"
                    f"<div class='page-panel__desc'>{escape(city['summary'])}</div>"
                    f"<div class='page-panel__meta'>Score atual: {compare_index[city_name]['score']:.3f}/5 "
                    f"· Referência histórica: € {city['reference_rent_eur']:,.0f}/mês</div></div>",
                    unsafe_allow_html=True)
                st.markdown("**Pontos favoráveis (históricos)**")
                for advantage in city["advantages"]:
                    st.markdown(f"- {advantage}")
                st.markdown("**Riscos e verificações**")
                for risk in city["risks"]:
                    st.markdown(f"- {risk}")
                with st.expander("Exemplos de anúncios pesquisados em 2026"):
                    st.caption("Links e preços históricos; não significam disponibilidade nem adequação contratual.")
                    for ad in city["sample_ads"]:
                        st.link_button(ad["label"], ad["url"], use_container_width=True)
    st.markdown("<div class='page-section'>Antes de escolher a cidade</div>",unsafe_allow_html=True)
    st.markdown("<div class='page-panel'>"
                "<div class='page-panel__title'>O que ainda precisa de confirmação</div>"
                "<div class='page-panel__desc'>Apartamentos mobiliados que aceitem 55–65 noites para duas pessoas; "
                "internet para home office; contrato aplicável; taxa total com contas, depósito e limpeza; "
                "custo de chegar da Itália e voltar ao Brasil; proximidade da estação e vida social."
                "</div></div>",unsafe_allow_html=True)
    source_url = city_data["source"]["url"]
    col1,col2=st.columns(2,gap="medium")
    with col1:
        st.link_button("Consultar matriz e pesos no Excel",source_url,use_container_width=True)
    with col2:
        st.link_button("Consultar decisão D-004 no Drive",data["sources"]["decisions"],use_container_width=True)
    st.caption("Fonte: abas 11, 12, 13 e 15 do Excel do projeto (novembro/2026). "
               "Notas de especialistas e preferências do planejamento, não dados objetivos atualizados.")

elif page == "Roteiro":
    st.markdown("<div class='page-eyebrow'>PLANEJAMENTO · ETAPAS DA VIAGEM</div>"
                "<div class='page-title'>Roteiro & calendário</div>"
                "<div class='page-subtitle'>Da lua de mel na Itália até a temporada francesa. "
                "As datas e durações, exceto o casamento, ainda são hipóteses de planejamento.</div>",
                unsafe_allow_html=True)
    finance_live = sync_sources["finance"]["status"] == "live"
    c1,c2,c3 = st.columns(3, gap="small")
    metrics = [
        ("Casamento", "04/09/2027", "Data fixa"),
        ("Duração prevista", f"{data['duration_min_days']}–{data['duration_max_days']} dias", "Estimativa para o casal"),
        ("Etapa italiana", f"~{data['italy_days_approx']} dias", "Roma e Costa Amalfitana"),
    ]
    for col, (label, value, hint) in zip((c1,c2,c3), metrics):
        with col:
            st.markdown(f"<div class='page-stat page-stat--blue'>"
                        f"<div class='page-stat__label'>{escape(label)}</div>"
                        f"<div class='page-stat__value'>{escape(value)}</div>"
                        f"<div class='page-stat__hint'>{escape(hint)}</div></div>", unsafe_allow_html=True)
    source_label = ("Cronograma sincronizado: aba 04 do Excel no Drive" if finance_live
                    else "Cronograma histórico do snapshot local — sincronização indisponível")
    st.markdown(f"<div class='page-alert page-alert--neutral'>◷ {escape(source_label)}. "
                "O roteiro é ilustrativo; não há passagens ou hospedagens emitidas.</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-section'>A jornada, etapa por etapa</div>", unsafe_allow_html=True)
    for index, entry in enumerate(data["timeline"], start=1):
        st.markdown(
            f"<div class='page-timeline'><div class='page-timeline__number'>{index:02d}</div>"
            "<div class='page-timeline__content'>"
            f"<div class='page-timeline__period'>{escape(entry['period'])} · {escape(entry['status'].upper())}</div>"
            f"<div class='page-timeline__stage'>{escape(entry['stage'])}</div>"
            f"<div class='page-timeline__desc'>{escape(entry['details'])}</div></div></div>",
            unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.link_button("Ver decisões no Drive",data["sources"]["decisions"],use_container_width=True)
    with c2:
        st.link_button("Abrir cronograma financeiro",data["sources"]["spreadsheet"],use_container_width=True)

elif page == "Orçamento":
    st.markdown("<div class='page-eyebrow'>PLANEJAMENTO FINANCEIRO · DOIS VIAJANTES</div>"
                "<div class='page-title'>Orçamento & cenários</div>"
                "<div class='page-subtitle'>Compare os dois limites da viagem completa, entenda os maiores "
                "custos e simule mudanças antes de tomar decisões.</div>", unsafe_allow_html=True)
    finance_live = sync_sources["finance"]["status"] == "live"
    st.markdown(
        "<div class='page-alert page-alert--neutral'>"
        + ("Valores recalculados a partir da aba 03 PREMISSAS do Excel sincronizado. "
           if finance_live else "Valores históricos do snapshot local; planilha não sincronizada. ")
        + "Os valores são estimativas para o casal, não ofertas confirmadas. "
        "A reserva emergencial já está incluída no total.</div>", unsafe_allow_html=True)
    choice=st.radio("Cenário base",["60k","70k"],
                    format_func=lambda x: "R$ 60 mil · ~65 dias" if x=="60k" else "R$ 70 mil · ~70 dias",
                    horizontal=True,key="budget_screen_scenario")
    scenario = get_scenario(data,choice)
    baseline = calculate_scenario(scenario)
    metrics = [
        ("Teto do casal",money_brl(scenario["cap_brl"]),"Limite de planejamento"),
        ("Total estimado",money_brl(baseline["total"]),"Inclui reserva emergencial"),
        ("Margem disponível",money_brl(baseline["balance"]),"Antes de cotações reais")
    ]
    for col, (label, value, hint) in zip(st.columns(3,gap="small"),metrics):
        with col:
            st.markdown(f"<div class='page-stat page-stat--mint'>"
                        f"<div class='page-stat__label'>{escape(label)}</div>"
                        f"<div class='page-stat__value'>{escape(value)}</div>"
                        f"<div class='page-stat__hint'>{escape(hint)}</div></div>",unsafe_allow_html=True)
    used_pct=max(0.0,min(100.0,baseline["total"]/scenario["cap_brl"]*100))
    st.markdown(f"<div class='page-panel'><div class='page-panel__title'>Utilização do orçamento · {used_pct:.1f}%</div>"
                f"<div class='page-budget-track'><span style='width:{used_pct:.1f}%'></span></div>"
                f"<div class='page-panel__meta'>Margem: {escape(money_brl(baseline['balance']))} · "
                "Valores em BRL · Dois viajantes</div></div>",unsafe_allow_html=True)
    if baseline["balance"]<1000:
        st.warning("Margem insuficiente para variações de câmbio e preços. Não aprovar reservas com base apenas nesta simulação.")
    if baseline["rounding_difference"]:
        st.info(f"A soma dos componentes difere {money_brl(abs(baseline['rounding_difference']))} "
                "do total calculado; revisar premissas antes de aprovar compras.")

    st.markdown("<div class='page-section'>Para onde vai o dinheiro?</div>",unsafe_allow_html=True)
    breakdown_chart,breakdown_list=st.columns([1.2,1],gap="large")
    with breakdown_chart:
        st.bar_chart([{"Categoria": x["name"],"Valor (R$)":x["amount"]} for x in scenario["components"]],
                     x="Categoria",y="Valor (R$)",horizontal=True,height=420)
        st.caption("Distribuição de custos estimados; não há despesas efetivamente contratadas.")
    with breakdown_list:
        for component in sorted(scenario["components"],key=lambda item:item["amount"],reverse=True):
            st.markdown(f"<div class='page-budget-row'><span class='page-budget-row__name'>{escape(component['name'])}</span>"
                        f"<span class='page-budget-row__amount'>{escape(money_brl(component['amount']))}</span></div>",
                        unsafe_allow_html=True)
    st.markdown("<div class='page-section'>Simulador de aluguel</div>",unsafe_allow_html=True)
    st.write("Teste aumentos hipotéticos do aluguel sem modificar a planilha original.")
    a,b,c=st.columns(3,gap="medium")
    with a:
        extra=st.slider("Aumento de aluguel (€/mês)",0,600,200,25,key="budget_rent_extra")
    with b:
        months=st.number_input("Meses cobrados",min_value=1,max_value=4,value=2,step=1,key="budget_months")
    with c:
        rate=st.number_input("Câmbio hipotético (R$/€)",min_value=4.0,max_value=10.0,value=6.30,step=0.05,key="budget_rate")
    simulation=calculate_scenario(scenario,extra,months,rate)
    figures=[
        ("Acréscimo hipotético",money_brl(simulation["delta"])),
        ("Novo custo total",money_brl(simulation["total"])),
        ("Saldo até o teto",money_brl(simulation["balance"]))
    ]
    for col,(label,value) in zip(st.columns(3,gap="small"),figures):
        with col:
            st.markdown(f"<div class='page-stat page-stat--blue'><div class='page-stat__label'>{escape(label)}</div>"
                        f"<div class='page-stat__value'>{escape(value)}</div>"
                        "<div class='page-stat__hint'>Não altera os documentos oficiais</div></div>",
                        unsafe_allow_html=True)
    if simulation["balance"]<0:
        st.error("Este cenário hipotético ultrapassa o teto escolhido.")
    else:
        st.info("O cenário está dentro do teto, mas precisa de folga e validação com cotações reais.")
    st.link_button("Abrir planilha financeira no Drive",data["sources"]["spreadsheet"],use_container_width=True)

elif page == "Pesquisas & decisões":
    st.markdown("<div class='page-eyebrow'>CENTRAL DE PLANEJAMENTO</div>"
                "<div class='page-title'>Pesquisas & decisões</div>"
                "<div class='page-subtitle'>Acompanhe o que foi decidido e quais investigações "
                "ainda precisam de atenção. O Google Drive continua como fonte oficial.</div>",unsafe_allow_html=True)
    tasks = data["tasks"]
    done = sum(t.get("status")=="concluído" for t in tasks)
    c1,c2,c3=st.columns(3,gap="small")
    summary=[
        ("Pesquisas registradas",str(len(tasks)),"Tarefas no planejamento"),
        ("Pendentes",str(len(tasks)-done),"Aguardando investigação"),
        ("Concluídas",str(done),"Registradas no Drive"),
    ]
    for col,(label,value,hint) in zip((c1,c2,c3),summary):
        with col:
            st.markdown(f"<div class='page-stat page-stat--blue'><div class='page-stat__label'>{escape(label)}</div>"
                        f"<div class='page-stat__value'>{escape(value)}</div>"
                        f"<div class='page-stat__hint'>{escape(hint)}</div></div>",unsafe_allow_html=True)
    st.markdown("<div class='page-alert page-alert--neutral'>"
                "Painel somente leitura: para registrar decisões ou concluir pendências, "
                "atualize o documento oficial no Drive. O app sincroniza essas mudanças.</div>",
                unsafe_allow_html=True)

    st.markdown("<div class='page-section'>Decisões registradas</div>",unsafe_allow_html=True)
    for decision in data["decisions"]:
        status=decision["status"]
        current_status=status.casefold()
        tone="proposed" if current_status.startswith(("vigente","aprovada","decidida")) else (
            "candidate" if current_status in {"aberta","não decidida","nao decidida"} else "optional")
        st.markdown(f"<div class='page-panel'>"
                    f"<span class='page-chip page-chip--{tone}'>{escape(status)}</span>"
                    f"<div class='page-panel__title' style='margin-top:9px'>{escape(decision['id'])} · {escape(decision['title'])}</div>"
                    f"<div class='page-panel__desc'>{escape(decision.get('note',''))}</div></div>",
                    unsafe_allow_html=True)
    st.link_button("Ver registro de decisões no Drive",data["sources"]["decisions"],use_container_width=True)

    st.markdown("<div class='page-section'>Fila de pesquisas</div>",unsafe_allow_html=True)
    priority_options=["Todas","P0","P1","P2","P3"]
    priority_titles={"P0":"Crítica","P1":"Alta","P2":"Média","P3":"Organização"}
    a,b=st.columns([1,1],gap="medium")
    with a:
        selected_priority=st.selectbox("Prioridade",priority_options,
                                       format_func=lambda p: p if p=="Todas" else f"{p} · {priority_titles[p]}",
                                       key="task_priority_filter")
    with b:
        status_filter=st.selectbox("Situação",["Todas","Pendentes","Concluídas"],key="task_status_filter")
    filtered=[item for item in tasks if (selected_priority=="Todas" or item["priority"]==selected_priority)
              and (status_filter=="Todas" or
                   (status_filter=="Pendentes" and item.get("status")!="concluído") or
                   (status_filter=="Concluídas" and item.get("status")=="concluído"))]
    st.markdown(f"<div class='page-filter-hint'>{len(filtered)} pesquisas encontradas · "
                "O status é controlado pelos documentos oficiais.</div>",unsafe_allow_html=True)
    if not filtered:
        st.info("Nenhuma pesquisa corresponde aos filtros selecionados.")
    for task in filtered:
        priority=task["priority"].lower()
        complete=task.get("status")=="concluído"
        st.markdown(
            f"<div class='page-task page-task--{priority}{' page-task--done' if complete else ''}'>"
            f"<div class='page-task__tag'>{escape(task['priority'])}</div>"
            f"<div class='page-task__body'>{escape(task['title'])}</div>"
            f"<div class='page-task__status'>{'✓ Concluída' if complete else '○ Pendente'}</div></div>",
            unsafe_allow_html=True)
    st.link_button("Abrir pendências no Drive",data["sources"]["tasks"],use_container_width=True)

    st.markdown("<div class='page-section'>Documentação e fontes</div>",unsafe_allow_html=True)
    source_items=[
        ("Guia de planejamento","guide"),("Estado atual e decisões","decisions"),
        ("Registro de pesquisas","evidence"),("Base de conhecimento","knowledge"),
        ("Modelo financeiro","spreadsheet")]
    for col,(label,key) in zip(st.columns(2,gap="small"),source_items[:2]):
        with col:
            st.link_button(label,data["sources"][key],use_container_width=True)
    for col,(label,key) in zip(st.columns(3,gap="small"),source_items[2:]):
        with col:
            st.link_button(label,data["sources"][key],use_container_width=True)

bottom_source()