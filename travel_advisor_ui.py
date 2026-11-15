"""Streamlit rule-based travel advisor; explicit preview/approval and gated storage."""
from __future__ import annotations
import json
from copy import deepcopy
from datetime import date,datetime,timezone
from decimal import Decimal
from urllib.error import HTTPError
from html import escape
import streamlit as st
from attractions_model import load_attractions,load_base_routes,package_cost,excursions_overage_brl
from travel_advisor import assess_plan,recommendations,objective_weights
from travel_optimizer import propose_schedule
from trip_plan_model import new_plan,validate_plan,with_revision,apply_proposal
from trip_plan_repository import GitHubPlanRepository
from advisor_auth import is_verified_owner
from planning_store import create_from_legacy,change_plan,sync_legacy_view
from planning_session import active_plan,update_fields,accept_approved_plan
from planning_status import save_label,explain_storage_error,friendly_timestamp
from advisor_finance import advisor_projection
from discovery_ui import render_discovery
from my_outings_ui import render_my_outings
from active_preset import active_preset
from active_preset_ui import render_active_preset_summary
from outing_guide_model import build_outing_guide
from destination_labels import place_label
from advisor_presentation import present_risks,proposal_comparison,simple_next_step
from data_model import get_scenario
from unified_budget import resolve_french_budget,scenario_total

def _activate_loaded_plan(plan:dict,sha:str)->None:
    """Restore one saved plan into all related pages before widgets are drawn."""
    st.session_state["advisor_plan"]=deepcopy(plan)
    st.session_state["advisor_saved_snapshot"]=deepcopy(plan)
    st.session_state["advisor_github_sha"]=sha
    st.session_state["explore_packages"]=deepcopy(plan["packages"])
    st.session_state["explore_calendar"]=deepcopy(plan["assignments"])
    st.session_state["explore_base"]=plan["base_city"]
    st.session_state["unified_scenario"]=plan["budget_scenario"]
    st.session_state["itinerary_departure"]=date.fromisoformat(plan["departure_date"])
    for key,source in (("itinerary_total_days","total_days"),
                       ("itinerary_italy_days","italy_days"),
                       ("itinerary_vacation_days","vacation_days"),
                       ("itinerary_setup_days","setup_days")):
        st.session_state[key]=plan[source]
    for key in list(st.session_state):
        if key.startswith("explore_mark_"):
            del st.session_state[key]
    # Prevent Streamlit's old widget values from overwriting loaded fields.
    for key in ("advisor_base","advisor_profile","advisor_ceiling",
                "advisor_proposals","advisor_snapshot_preview"):
        st.session_state.pop(key,None)
    st.session_state["advisor_restore_notice"]=(
        f"Plano {plan['plan_id']} carregado do GitHub (revisão {plan['revision']})."
    )


def _recover_saved_plan()->None:
    """Only bootstrap an authenticated fresh session; never overwrite edits."""
    pending=st.session_state.pop("advisor_pending_restore",None)
    if pending is not None:
        _activate_loaded_plan(pending["plan"],pending["sha"])
        return
    if "advisor_plan" in st.session_state:
        return
    cfg=_owner_config()
    if not cfg["token"] or not _owner_signed_in(cfg):
        return
    try:
        repository=GitHubPlanRepository(cfg["token"])
        candidates=repository.recent_plans()
        st.session_state["advisor_saved_plans"]=candidates
        if candidates:
            plan,sha=repository.load(candidates[0]["plan_id"])
            _activate_loaded_plan(plan,sha)
    except (HTTPError,ValueError,TypeError,KeyError) as exc:
        # An API failure must never silently replace an already loaded plan.
        st.session_state["advisor_restore_error"]=_github_read_error(exc)


def _stage_plan_restore(plan:dict,sha:str)->None:
    """Call from a button; activation runs before controls on the next rerun."""
    st.session_state["advisor_pending_restore"]={"plan":plan,"sha":sha}
    st.rerun()


def _prepare_plan():
    if "advisor_plan" not in st.session_state:
        try:
            p=create_from_legacy(st.session_state)
        except (ValueError,TypeError,KeyError):
            p=new_plan()
        st.session_state["advisor_plan"]=p
    return st.session_state["advisor_plan"]

def _owner_config():
    try:
        settings=st.secrets.get("advisor_github",{})
        auth=st.secrets.get("auth",{})
        google=auth.get("google",{}) if auth else {}
        return {"token":settings.get("token",""),
                "owner_email":settings.get("owner_email",""),
                "google_configured":bool(
                    auth.get("cookie_secret") and auth.get("redirect_uri") and
                    google.get("client_id") and google.get("client_secret"))}
    except Exception:
        return {"token":"","owner_email":"","google_configured":False}

def _owner_signed_in(cfg=None):
    cfg=_owner_config() if cfg is None else cfg
    if not cfg["google_configured"] or not cfg["owner_email"]:
        return False
    try:
        return is_verified_owner(st.user,cfg["owner_email"])
    except (AttributeError,KeyError,TypeError):
        return False

def _secure_save(plan):
    cfg=_owner_config()
    if not cfg["token"] or not _owner_signed_in(cfg):
        raise PermissionError("Only the verified OIDC owner may write to GitHub")
    if not st.session_state.get("advisor_public_repo_ack"):
        raise PermissionError("Owner must acknowledge public repository visibility")
    sha=st.session_state.get("advisor_github_sha")
    next_sha=GitHubPlanRepository(cfg["token"]).save(plan,sha)
    st.session_state["advisor_github_sha"]=next_sha
    st.session_state["advisor_saved_snapshot"]=deepcopy(plan)
    st.session_state["advisor_last_saved_at"]=datetime.now(timezone.utc).isoformat()

def _github_read_error(exc:Exception)->str:
    if isinstance(exc,HTTPError):
        if exc.code==404:
            return ("Este plano ainda não existe no GitHub. Primeiro clique em "
                    "'Gravar versão aprovada no GitHub'. Se já salvou outro, "
                    "abra 'Outros planos e histórico de revisões' para localizar o ID.")
        if exc.code in (401,403):
            return ("GitHub recusou o acesso (HTTP "+str(exc.code)+"). "
                    "Verifique a validade do token e sua permissão Contents.")
        return ("Erro do GitHub (HTTP "+str(exc.code)+"). "
                "Tente novamente e consulte os logs do Streamlit.")
    return ("Não foi possível carregar o plano ("+type(exc).__name__+
            "). Confira o ID, a conexão e os dados salvos.")


def render_advisor(trip_data:dict,sync_sources:dict,workspace_area:str='Meus passeios')->None:
    catalog=load_attractions();routes=load_base_routes()
    bydest={d["id"]:d for d in catalog["destinations"]}
    byattr={a["id"]:a for a in catalog["attractions"]}
    _recover_saved_plan()
    p=_prepare_plan()
    if "advisor_restore_notice" in st.session_state:
        st.success(st.session_state.pop("advisor_restore_notice"))
    if "advisor_restore_error" in st.session_state:
        st.warning("Não foi possível recuperar automaticamente o planejamento: "+
                   st.session_state.pop("advisor_restore_error"))
    st.markdown("<div class='page-section'>Workspace de planejamento</div>",unsafe_allow_html=True)
    st.caption("Meus passeios mostra seu roteiro atual. Simular roteiros é apenas uma proposta; nenhuma sugestão entra no plano sem aprovação.")
    st.caption("Valores e trajetos são referências históricas; não há reservas ou cotações confirmadas para 2027.")
    with st.expander("Configurações do planejamento",expanded=True):
        a,b,c=st.columns(3,gap="medium")
        with a:
            base=st.selectbox("Base hipotética",["mulhouse","strasbourg","metz","nancy"],
                              index=["mulhouse","strasbourg","metz","nancy"].index(p["base_city"]),
                              key="advisor_base",format_func=lambda x:place_label(bydest[x]["name"],bydest[x]["country"]))
        with b:
            profile=st.selectbox("Estilo de viagem",["balanced","economy","experience"],
                index=["balanced","economy","experience"].index(p["profile"]),
                key="advisor_profile",format_func=lambda x:{
                  "balanced":"Equilibrado","economy":"Econômico","experience":"Aproveitar ao máximo"}[x])
        with c:
            ceiling=st.selectbox("Teto total do casal",["60k","70k"],
                index=["60k","70k"].index(p["budget_scenario"]),key="advisor_ceiling",
                format_func=lambda x:"R$ "+x[:-1]+" mil")
        if base!=p["base_city"] or profile!=p["profile"] or ceiling!=p["budget_scenario"]:
            p=update_fields(base_city=base,profile=profile,budget_scenario=ceiling)
        with st.expander("Como o consultor toma decisões",expanded=False):
            st.caption("Prioridades (interesse / custo / conforto / agenda): "+
                       " / ".join(str(x)+"%" for x in objective_weights(profile).values())+
                       ". As sugestões são geradas por regras Python, sem LLM.")
    # One TripPlan is authoritative across attraction explorer, calendar and advisor.
    # This replaces the former manual "Importar seleção" step.
    st.session_state["explore_packages"]=deepcopy(p["packages"])
    st.session_state["explore_calendar"]=deepcopy(p["assignments"])
    names=[place_label(bydest[d]["name"],bydest[d]["country"]) for d in p["packages"] if d in bydest]
    if workspace_area != "Meus passeios":
        st.caption("Passeios escolhidos: "+(", ".join(names) if names else "Nenhum ainda"))
    saved_label,saved_hint=save_label(
        p,st.session_state.get("advisor_saved_snapshot"),
        _owner_signed_in())
    st.caption(f"**{saved_label}** · {saved_hint}")
    profile_name={"economy":"Econômico","balanced":"Equilibrado",
                  "experience":"Aproveitar ao máximo"}[p["profile"]]
    st.caption(f"**{place_label(bydest[p['base_city']]['name'],bydest[p['base_city']]['country'])} · {profile_name} · R$ {p['budget_scenario'][:-1]} mil · {len(p['packages'])} destinos · {saved_label}**")
    if st.session_state.get("advisor_last_saved_at"):
        st.caption("Último salvamento: "+
                   friendly_timestamp(st.session_state["advisor_last_saved_at"]))

    # Financial baseline: the excursion budget is already included in the total.
    selected=[x for group in p["packages"].values() for x in group]
    cost=package_cost(catalog,routes,p["base_city"],selected)
    with st.expander("Câmbio e aluguel (hipóteses)",expanded=False):
        fxcol1,fxcol2=st.columns(2)
        with fxcol1: eurfx=st.number_input("R$/€ hipotético",4.,10.,6.3,.05,key="advisor_eurfx")
        with fxcol2: chffx=st.number_input("R$/CHF hipotético",4.,12.,7.1,.05,key="advisor_chffx")
        st.caption("Ao alterar cidade-base, teto ou câmbio, a projeção abaixo é recalculada "
                   "na hora. Os valores de aluguel são referências históricas de 2026.")
        use_city_rent=st.checkbox(
            "Usar aluguel de referência da cidade escolhida (2026)",
            value=True,key="advisor_use_city_rent",
            help="Usa a referência mensal publicada em 2026 e substitui a verba de aluguel "
                 "já incluída na projeção; não é uma cotação para 2027. "
                 "Desmarque para usar a verba fixa do cenário.")
    financial=advisor_projection(
        trip_data,sync_sources["finance"]["status"]=="live",p,cost,
        eurfx,chffx,use_city_rent)
    scenario=financial["scenario"]
    result=financial["result"]
    known_brl=financial["known_billets_brl"]
    if financial["rent_eur_month"] is not None:
        st.caption(f"Referência de moradia em {bydest[p['base_city']]['name']}: "
                   f"€ {financial['rent_eur_month']:,.0f}/mês (pesquisa de 2026). "
                   "No orçamento, substitui a verba original de aluguel, sem duplicar.")
    else:
        st.caption("Moradia: verba geral do orçamento, sem ajuste por cidade-base. "
                   "Nesse modo a troca de cidade só altera custos dos passeios selecionados.")
    st.caption("Estilo de otimização: altera como o consultor prioriza sugestões, "
               "mas não inventa despesas ou economias. Para ver impacto financeiro real, "
               "escolha passeios ou ajuste as hipóteses do orçamento.")
    preset=(active_preset(p,catalog,routes,trip_data,
                          sync_sources["finance"]["status"]=="live",
                          eurfx,chffx,use_city_rent,
                          allow_overnight=st.session_state.get("advisor_discovery_overnight",False))
            if workspace_area in ("Meus passeios","Descobrir","Calendário") else None)
    if workspace_area == "Orçamento":
        st.caption("Os indicadores iniciais abaixo representam apenas seus passeios "
                   "confirmados. Os três roteiros prontos aparecem mais abaixo.")
        metrics=[("Bilhetes conhecidos",f"R$ {known_brl:,.0f}","Subtotal incompleto; duas pessoas"),
                 ("Custos faltantes",str(len(cost["missing"])),"Sem preço ou tarifa normal"),
                 ("Projeção do cenário",f"R$ {result['total']:,.0f}","Orçamento integrado"),
                 ("Margem até o teto",f"R$ {result['margin']:,.0f}","Reserva de emergência já incluída")]
        for col,(title,val,detail) in zip(st.columns(4),metrics):
            with col:
                st.metric(title,val,help=detail)
        if cost["missing"]:
            st.warning("Há gastos desconhecidos: não se pode afirmar que o roteiro está dentro do orçamento.")
        if result["margin"]<0:
            st.error(f"A projeção ultrapassa o teto em R$ {abs(result['margin']):,.0f}. "
                     "Isso considera o orçamento atual e não significa que os passeios "
                     "ainda não cotados estejam incluídos.")
    context={"margin":Decimal(str(result["margin"])),"cap":Decimal(str(scenario["cap_brl"]))}
    risks=assess_plan(p,catalog,routes,context)
    advice=recommendations(p,catalog,routes,risks)
    advice_cards=present_risks(risks,{k:v["name"] for k,v in bydest.items()})
    if workspace_area == "Calendário":
        st.markdown("### Sugestões para sua viagem")
        if preset is not None:
            render_active_preset_summary(preset,catalog,"calendar")
        st.caption(simple_next_step(p,advice_cards))
        if not advice_cards:
            st.success("Nenhum alerta nas regras atuais. Confirme horários e preços de 2027 antes de reservar.")
        else:
            important=advice_cards[:4]
            for item in important:
                with st.container(border=True):
                    icon_text={"Orçamento":"💰","Transporte":"🚆",
                               "Conforto":"🧳","Bilhetes":"🎟️"}.get(item["category"],"💡")
                    st.markdown(f"**{icon_text} {item['title']}**")
                    st.caption(item["destination"]+" · "+item["category"])
                    st.write(item["summary"])
                    st.markdown("**Sugestão:** "+item["suggestion"])
                    if item["confidence"]=="parcial":
                        st.caption("Análise parcial · preços ou horários ainda não confirmados")
                    with st.expander("Entenda os dados desta recomendação"):
                        st.write("Motivo registrado: "+next(
                            (r["message"] for r in risks
                             if item["id"]==r["code"]+":"+r["affected"]),item["summary"]))
                        if item["source"]:
                            st.markdown("[Consultar fonte]("+item["source"]+")")
                        st.caption("Não altera o roteiro sem sua aprovação.")
            if len(advice_cards)>len(important):
                with st.expander(f"Ver mais {len(advice_cards)-len(important)} recomendações"):
                    for item in advice_cards[len(important):]:
                        st.markdown(f"**{item['title']}** · {item['destination']}")
                        st.write(item["summary"]+" "+item["suggestion"])
                        if item["source"]:
                            st.markdown("[Fonte]("+item["source"]+")")
        st.divider()
    if workspace_area == "Meus passeios":
        with st.expander("Salvar planejamento, backups e histórico",expanded=False):
            st.markdown("### Salvamento e recuperação")
            st.caption("Suas escolhas ficam disponíveis ao voltar aqui após salvar.")
            if p["assignments"]:
                st.caption("Passeios no calendário: "+
                           ", ".join(day+" · "+bydest.get(dest,{"name":dest})["name"]
                                     for day,dest in sorted(p["assignments"].items())))
            with st.container(border=True):
                st.caption("Use o backup somente se quiser guardar uma cópia no seu computador "
                           "ou importar um arquivo de uma versão anterior.")
                st.download_button("Baixar backup",
                                   data=json.dumps(p,ensure_ascii=False,indent=2),
                                   file_name=p["plan_id"]+".json",mime="application/json",
                                   use_container_width=True,key="advisor_export_backup")
                uploaded=st.file_uploader("Importar backup salvo no computador",
                                          type=["json"],key="advisor_import_json")
                if uploaded is not None:
                    if st.button("Conferir e importar backup",key="advisor_import_confirm"):
                        try:
                            new=json.load(uploaded)
                            validate_plan(new,set(byattr))
                            if any(x not in bydest for x in new["packages"]):
                                raise ValueError("Destino inexistente")
                            st.session_state["advisor_plan"]=new
                            st.session_state["advisor_saved_snapshot"]=None
                            st.session_state["advisor_github_sha"]=None
                            sync_legacy_view(new,st.session_state)
                            st.session_state.pop("advisor_proposals",None)
                            st.success("Backup importado nesta sessão. Salve para guardar online.")
                            st.rerun()
                        except (ValueError,KeyError,TypeError) as exc:
                            st.error("Este arquivo não parece ser um planejamento válido: "+str(exc))
            cfg=_owner_config()
            ready=bool(cfg["token"] and cfg["owner_email"] and cfg["google_configured"])
            if not ready:
                st.info("Gravação no GitHub desativada: configure o OAuth Google e "
                        "advisor_github.token / advisor_github.owner_email nos "
                        "Streamlit Secrets. A exportação JSON funciona sem credenciais.")
            elif not _owner_signed_in(cfg):
                st.info("Para salvar o plano no GitHub, entre com a conta Google "
                        "autorizada. A visualização e a exportação continuam livres.")
                try:
                    logged_in=bool(st.user.get("is_logged_in",False))
                except (AttributeError,TypeError):
                    logged_in=False
                if logged_in:
                    st.warning("Esta conta Google não corresponde ao proprietário autorizado "
                               "ou a sessão de identidade expirou. Nenhum acesso de escrita concedido.")
                    st.button("Sair do Google",key="advisor_google_logout",on_click=st.logout)
                else:
                    st.button("Entrar com Google (proprietário)",
                              key="advisor_google_login",on_click=st.login,args=["google"])
            else:
                st.success("Proprietário autenticado pelo Google. "
                           "As gravações exigem confirmação explícita.")
                st.button("Encerrar sessão Google",key="advisor_google_signout",
                          on_click=st.logout)
                st.checkbox("Entendo que o repositório GitHub atual é PÚBLICO e que "
                            "planos salvos nele poderão ser vistos por outras pessoas. "
                            "Não incluí informações pessoais ou confidenciais.",
                            value=False,key="advisor_public_repo_ack")
                if st.session_state.get("advisor_public_repo_ack"):
                    st.checkbox("Salvar minhas alterações aprovadas automaticamente",
                                value=False,key="advisor_autosave_optin",
                                help="As escolhas serão gravadas após sua confirmação. "
                                     "Não salva propostas ainda em análise. "
                                     "O repositório atual é público.")
                if not st.session_state["advisor_public_repo_ack"]:
                    st.warning("A gravação só será habilitada após reconhecer a "
                               "visibilidade pública do repositório. "
                               "É mais seguro armazenar roteiros pessoais em repositório privado.")
                else:
                    col1,col2=st.columns(2)
                    with col1:
                        if st.button("Salvar planejamento",key="advisor_save",use_container_width=True,
                                     disabled=not (st.session_state.get("advisor_saved_snapshot") is None
                                                   or st.session_state["advisor_saved_snapshot"]!=p)):
                            try:
                                _secure_save(p)
                                st.session_state.pop("advisor_saved_plans",None)
                                st.success("Planejamento salvo! Você poderá continuar de onde parou.")
                            except Exception as exc:
                                if isinstance(exc,HTTPError) and exc.code in (401,403):
                                    st.error(explain_storage_error(exc))
                                elif isinstance(exc,ValueError):
                                    st.error(explain_storage_error(exc))
                                else:
                                    st.error(explain_storage_error(exc))
                    with col2:
                        if st.button("Reabrir planejamento salvo",key="advisor_load",use_container_width=True):
                            try:
                                repository=GitHubPlanRepository(cfg["token"])
                                available=repository.recent_plans()
                                if not available:
                                    st.info("Ainda não existem roteiros gravados no GitHub. "
                                            "Salve o primeiro com o botão da esquerda.")
                                else:
                                    ids={entry["plan_id"] for entry in available}
                                    target=(p["plan_id"] if p["plan_id"] in ids
                                            else available[0]["plan_id"])
                                    loaded,sha=repository.load(target)
                                    _stage_plan_restore(loaded,sha)
                            except Exception as exc:
                                st.error(_github_read_error(exc))
                    with st.container(border=True):
                        if st.button("Atualizar lista de planos salvos",key="advisor_refresh_saved"):
                            try:
                                st.session_state["advisor_saved_plans"]=GitHubPlanRepository(
                                    cfg["token"]).recent_plans()
                            except Exception as exc:
                                st.error("Falha ao consultar lista: "+_github_read_error(exc))
                        # No implicit GitHub list request on Streamlit reruns.
                        # Users explicitly refresh history when they need it.
                        recent=st.session_state.get("advisor_saved_plans",[])
                        if recent:
                            selected_plan=st.selectbox(
                                "Planejamentos salvos (mais recente primeiro)",
                                recent,key="advisor_saved_plan_choice",
                                format_func=lambda entry:
                                   (entry["plan_id"]+" · "+
                                    (entry["saved_at"][:16].replace("T"," ")+" UTC"
                                     if entry["saved_at"] else "data não disponível")+
                                    (" · revisão "+str(entry["revision"])
                                     if entry["revision"] is not None else "")))
                            if st.button("Abrir planejamento selecionado",key="advisor_load_selected",
                                         use_container_width=True):
                                try:
                                    loaded,sha=GitHubPlanRepository(cfg["token"]).load(
                                        selected_plan["plan_id"])
                                    _stage_plan_restore(loaded,sha)
                                except Exception as exc:
                                    st.error(_github_read_error(exc))
                        else:
                            st.info("Nenhum plano salvo foi localizado. Grave uma versão primeiro.")
                        plan_id=st.text_input("Ou informe o ID de um plano específico",
                            key="advisor_plan_lookup",value=p["plan_id"])
                        if st.button("Pesquisar planos no GitHub",key="advisor_list"):
                            try:
                                st.session_state["advisor_plan_ids"]=GitHubPlanRepository(cfg["token"]).list_plans()
                            except Exception as exc:
                                st.error("Falha ao listar: "+type(exc).__name__)
                        if st.session_state.get("advisor_plan_ids"):
                            st.caption("Planos: "+", ".join(st.session_state["advisor_plan_ids"][:20]))
                        if st.button("Carregar este ID",key="advisor_load_id"):
                            try:
                                loaded,sha=GitHubPlanRepository(cfg["token"]).load(plan_id)
                                _stage_plan_restore(loaded,sha)
                            except Exception as exc:
                                st.error(_github_read_error(exc))
                        if st.button("Exibir revisões",key="advisor_history"):
                            try:
                                st.session_state["advisor_history"]=GitHubPlanRepository(cfg["token"]).history(plan_id)
                            except Exception as exc:
                                st.error("Histórico indisponível: "+type(exc).__name__)
                        history=st.session_state.get("advisor_history",[])
                        if history:
                            selected=st.selectbox("Versão do planejamento",history,
                                format_func=lambda x:x["date"][:10]+" · "+x["message"],
                                key="advisor_snapshot_choice")
                            if st.button("Pré-visualizar versão anterior",key="advisor_snapshot"):
                                try:
                                    historical=GitHubPlanRepository(cfg["token"]).load_at_commit(plan_id,selected["sha"])
                                    st.session_state["advisor_snapshot_preview"]=historical
                                except Exception as exc:
                                    st.error("Snapshot não acessível: "+type(exc).__name__)
                            preview=st.session_state.get("advisor_snapshot_preview")
                            if preview:
                                st.caption("Essa versão possui "+str(len(preview["assignments"]))+
                                           " dias planejados. Confira antes de recuperá-la.")
                                if st.button("Recuperar esta versão (sem salvar ainda)",key="advisor_restore"):
                                    try:
                                        if preview["plan_id"]!=p["plan_id"]:
                                            raise ValueError("Carregue o plano correspondente primeiro")
                                        restored=with_revision(p,{
                                            "packages":deepcopy(preview["packages"]),
                                            "assignments":deepcopy(preview["assignments"])})
                                        st.session_state["advisor_plan"]=restored
                                        st.session_state.pop("advisor_proposals",None)
                                        st.info("Versão anterior recuperada nesta sessão. Clique em Salvar planejamento para confirmar.")
                                        st.rerun()
                                    except ValueError as exc:st.warning(str(exc))
            with st.container(border=True):
                st.caption("O planejamento fica versionado no GitHub. O repositório atual é público; "
                           "não inclua dados pessoais ou confidenciais.")
                st.caption("A gravação online exige autorização Google, token protegido no servidor "
                           "e confirmação do proprietário. Sem autenticação, somente backup local.")
    
    if workspace_area == "Meus passeios":
        applied=st.session_state.pop("budget_preset_applied",None)
        if applied:
            st.success("Roteiro "+applied+" adotado! Os passeios já aparecem abaixo. "
                       "Salve o planejamento para mantê-los em outros dispositivos.")
        render_my_outings(p,catalog,routes=routes,trip_data=trip_data,
                          finance_live=sync_sources["finance"]["status"]=="live",
                          eurfx=eurfx,chffx=chffx,use_city_rent=use_city_rent,
                          preset=preset)
    if workspace_area == "Descobrir" and preset is not None:
        render_active_preset_summary(preset,catalog,"discover")
    if workspace_area in ("Descobrir","Simular roteiros","Orçamento"):
        render_discovery(p,catalog,routes,trip_data,sync_sources,eurfx,chffx,use_city_rent,
                         view={"Descobrir":"discover","Simular roteiros":"board","Orçamento":"budget"}[workspace_area])
    if workspace_area == "Descobrir":
        st.caption("Depois de adicionar, veja o destino em Meus passeios para editar ou remover diretamente.")
    if workspace_area == "Calendário":
        st.markdown("### Organizar meus passeios")
        if p["packages"]:
            with st.expander("Ver deslocamentos e pendências dos passeios escolhidos"):
                for destination,ids in p["packages"].items():
                    guide=build_outing_guide(p,catalog,routes,destination,ids)
                    minutes=guide["train_minutes_one_way"]
                    st.markdown("**"+bydest[destination]["name"]+"** · saindo de "+
                                guide["base_name"])
                    st.caption((str(minutes)+" min de trem por trecho" if minutes is not None
                                else "Passeio local" if guide["local"]
                                else "Duração ferroviária não verificada")+
                               " · "+guide["feasibility"]+
                               " · "+str(len(guide["missing"]))+" verificações pendentes")
                st.caption("Horários e disponibilidade para 2027 ainda precisam de checagem.")
        st.caption("O otimizador só aloca passeios de duração compatível e com tempo de trem "
                   "conhecido ou locais. Alpes e conexões não pesquisadas ficam pendentes, "
                   "não são colocados arbitrariamente em um dia.")
        if not p["packages"]:
            st.info("Você ainda não escolheu passeios. Veja as recomendações acima e clique em "
                    "'Quero visitar' para começar; depois será possível organizar as datas.")
            st.session_state.pop("advisor_proposals",None)
        elif st.button("Encontrar uma organização melhor",key="advisor_generate",use_container_width=True):
            new_proposals=propose_schedule(p,catalog,routes,profile)
            st.session_state["advisor_proposals"]=new_proposals
            if not new_proposals:
                st.info("Seus passeios já estão organizados ou faltam informações de horários "
                        "para propor uma mudança segura.")
        props=st.session_state.get("advisor_proposals",[])
        for index,proposal in enumerate(props):
            if proposal["base_revision"]!=p["revision"]:
                st.warning("Proposta desatualizada após mudança no planejamento. Gere novamente.")
                break
            with st.container(border=True):
                comparison=proposal_comparison(p,proposal,cost)
                st.markdown(f"**Opção {index+1} · organizar {len(proposal['placed'])} passeios**")
                left,right=st.columns(2,gap="small")
                with left:st.metric("Dias já planejados",comparison["existing_count"])
                with right:st.metric("Dias com a sugestão",comparison["proposed_count"])
                st.caption(comparison["claim"])
                diff=[(item["date"],item["destination"]) for item in comparison["added"]]
                if diff:
                    st.markdown("**O que mudaria:**")
                    st.dataframe([{"Data":day,"Passeio":bydest[dest]["name"]}
                                  for day,dest in diff],hide_index=True,use_container_width=True)
                else:st.caption("Esta opção não muda o calendário atual.")
                if comparison["unresolved"]:
                    st.warning(str(comparison["unresolved_count"])+" passeio(s) ainda precisam de pesquisa: "+
                               "; ".join(x["destination"]+" — "+x["reason"]
                                         for x in comparison["unresolved"]))
                with st.expander("Como comparamos esta opção"):
                    score=proposal["score"]
                    st.caption(f"Pontuação relativa: {score['relative_score']:.1f}. "
                               f"Trem ida/volta conhecido: {score['known_roundtrip_train_minutes']} min. "
                               "Não inclui deslocamento porta a porta ou tarifa 2027.")
                c1,c2=st.columns(2)
                with c1:
                    if st.button("Aprovar esta proposta",key=f"advisor_accept_{index}",
                                 disabled=not diff,use_container_width=True):
                        updated=apply_proposal(p,proposal,approved=True)
                        accept_approved_plan(updated)
                        st.success("Sugestão aprovada! Seu planejamento tem alterações para salvar.")
                        st.rerun()
                with c2:
                    if st.button("Rejeitar",key=f"advisor_reject_{index}",use_container_width=True):
                        st.session_state["advisor_proposals"]=[x for x in props if x["proposal_id"]!=proposal["proposal_id"]]
                        st.rerun()
