"""Streamlit rule-based travel advisor; explicit preview/approval and gated storage."""
from __future__ import annotations
import hashlib
import hmac
import json
from copy import deepcopy
from datetime import date
from decimal import Decimal
from html import escape
import streamlit as st
from attractions_model import load_attractions,load_base_routes,package_cost,excursions_overage_brl
from travel_advisor import assess_plan,recommendations,objective_weights
from travel_optimizer import propose_schedule
from trip_plan_model import new_plan,validate_plan,with_revision,apply_proposal
from trip_plan_repository import GitHubPlanRepository
from data_model import get_scenario
from unified_budget import resolve_french_budget,scenario_total

def _prepare_plan():
    if "advisor_plan" not in st.session_state:
        p=new_plan()
        p["packages"]=deepcopy(st.session_state.get("explore_packages",{}))
        p["assignments"]=deepcopy(st.session_state.get("explore_calendar",{}))
        p["base_city"]=st.session_state.get("explore_base","mulhouse")
        p["departure_date"]=str(st.session_state.get("itinerary_departure",date(2027,9,9)))
        p["total_days"]=st.session_state.get("itinerary_total_days",70)
        p["italy_days"]=st.session_state.get("itinerary_italy_days",10)
        p["vacation_days"]=st.session_state.get("itinerary_vacation_days",25)
        p["setup_days"]=st.session_state.get("itinerary_setup_days",4)
        try:validate_plan(p)
        except (ValueError,TypeError,KeyError):
            p=new_plan()
        st.session_state["advisor_plan"]=p
    return st.session_state["advisor_plan"]

def _owner_config():
    try:
        c=st.secrets.get("advisor_github",{})
        return {"token":c.get("token",""),"password_sha256":c.get("password_sha256","")}
    except Exception:
        return {"token":"","password_sha256":""}

def _secure_save(plan):
    cfg=_owner_config()
    if not cfg["token"] or not cfg["password_sha256"] or not st.session_state.get("advisor_owner_ok"):
        raise PermissionError("GitHub write unavailable without owner authentication")
    sha=st.session_state.get("advisor_github_sha")
    next_sha=GitHubPlanRepository(cfg["token"]).save(plan,sha)
    st.session_state["advisor_github_sha"]=next_sha

def render_advisor(trip_data:dict,sync_sources:dict)->None:
    catalog=load_attractions();routes=load_base_routes()
    bydest={d["id"]:d for d in catalog["destinations"]}
    byattr={a["id"]:a for a in catalog["attractions"]}
    p=_prepare_plan()
    st.markdown("<div class='page-section'>Consultor automático · sem LLM</div>",unsafe_allow_html=True)
    st.caption("Análise determinística dos dados pesquisados. Sugestões não alteram reservas "
               "nem decisões do Drive. Tarifas históricas e retornos não verificados são sinalizados.")
    st.info("O consultor é uma ferramenta de apoio. Ele não consulta rotas em tempo real nem "
            "pode garantir disponibilidade ou preços de 2027.")
    a,b,c=st.columns(3,gap="medium")
    with a:
        base=st.selectbox("Base hipotética",["mulhouse","strasbourg","metz","nancy"],
                          index=["mulhouse","strasbourg","metz","nancy"].index(p["base_city"]),
                          key="advisor_base",format_func=lambda x:bydest[x]["name"])
    with b:
        profile=st.selectbox("Otimização",["balanced","economy","experience"],
            index=["balanced","economy","experience"].index(p["profile"]),
            key="advisor_profile",format_func=lambda x:{
              "balanced":"Equilibrado","economy":"Economizar","experience":"Aproveitar ao máximo"}[x])
    with c:
        ceiling=st.selectbox("Teto total do casal",["60k","70k"],
            index=["60k","70k"].index(p["budget_scenario"]),key="advisor_ceiling",
            format_func=lambda x:"R$ "+x[:-1]+" mil")
    if base!=p["base_city"] or profile!=p["profile"] or ceiling!=p["budget_scenario"]:
        p=with_revision(p,{"base_city":base,"profile":profile,"budget_scenario":ceiling})
        st.session_state["advisor_plan"]=p
        st.session_state.pop("advisor_proposals",None)
    st.caption("Pesos atuais (interesse / custo / conforto / agenda): "+
               " / ".join(str(x)+"%" for x in objective_weights(profile).values()))
    sync_packages=st.session_state.get("explore_packages",{})
    if sync_packages!=p["packages"]:
        st.warning("Sua lista de atrações da aba Explorar atrações está diferente da versão do consultor.")
        if st.button("Importar seleção atual para o consultor",key="advisor_import_selection"):
            p=with_revision(p,{"packages":deepcopy(sync_packages),
                                "assignments":{}})
            st.session_state["advisor_plan"]=p
            st.session_state.pop("advisor_proposals",None)
            st.rerun()
    names=[bydest[d]["name"] for d in p["packages"] if d in bydest]
    st.markdown("**Passeios selecionados:** "+(", ".join(names) if names else "Nenhum — adicione atrações na aba Explorar atrações"))
    st.caption(f"Plano {p['plan_id']} · revisão {p['revision']} · "
               "alterações ainda não gravadas no GitHub")

    # Financial baseline: the excursion budget is already included in the total.
    selected=[x for group in p["packages"].values() for x in group]
    cost=package_cost(catalog,routes,p["base_city"],selected)
    fxcol1,fxcol2=st.columns(2)
    with fxcol1: eurfx=st.number_input("R$/€ hipotético",4.,10.,6.3,.05,key="advisor_eurfx")
    with fxcol2: chffx=st.number_input("R$/CHF hipotético",4.,12.,7.1,.05,key="advisor_chffx")
    scenario=get_scenario(trip_data,p["budget_scenario"])
    french=resolve_french_budget(scenario,sync_sources["finance"]["status"]=="live")
    days= p["total_days"]-p["italy_days"]
    allocation=float(french["amounts"]["excursions"])*days/french["french_days"]
    overage=excursions_overage_brl(cost["known_by_currency"]["EUR"],
        cost["known_by_currency"]["CHF"],eurfx,chffx,allocation)
    result=scenario_total(scenario,french,french_days=days,
        outings_weekly=2,outing_couple_eur=60,fx_brl_per_eur=eurfx,
        excursions_delta_brl=overage)
    known_brl=float(Decimal(str(cost["known_by_currency"]["EUR"]))*Decimal(str(eurfx))+
                    Decimal(str(cost["known_by_currency"]["CHF"]))*Decimal(str(chffx)))
    metrics=[("Bilhetes conhecidos",f"R$ {known_brl:,.0f}","Subtotal incompleto; duas pessoas"),
             ("Custos faltantes",str(len(cost["missing"])),"Sem preço ou tarifa normal"),
             ("Projeção do cenário",f"R$ {result['total']:,.0f}","Orçamento integrado"),
             ("Margem até o teto",f"R$ {result['margin']:,.0f}","Reserva de emergência já incluída")]
    for col,(title,val,detail) in zip(st.columns(4),metrics):
        with col:
            st.metric(title,val,help=detail)
    if cost["missing"]:
        st.warning("Há gastos desconhecidos: não se pode afirmar que o roteiro está dentro do orçamento.")
    context={"margin":Decimal(str(result["margin"])),"cap":Decimal(str(scenario["cap_brl"]))}
    risks=assess_plan(p,catalog,routes,context)
    advice=recommendations(p,catalog,routes,risks)
    st.markdown("### Diagnóstico")
    if not risks:st.success("Nenhum alerta nas regras atuais; ainda exige conferência de dados 2027.")
    else:
        st.caption(f"{len(risks)} alertas fundamentados nos dados disponíveis")
        for index,r in enumerate(risks):
            with st.expander(f"{r['severity']} · {r['message']} — {r['affected']}",
                             expanded=index<2):
                st.write("**Ação sugerida:** "+r["resolution"])
                if r["source"]:st.markdown("[Ver evidência]("+r["source"]+")")
    if advice:
        st.markdown("### Recomendações para avaliar")
        for item in advice:
            with st.container(border=True):
                st.markdown("**"+item["title"]+"**")
                st.caption(item["reason"])
                st.caption("Sugestão explicativa — não remove passeios automaticamente")
    st.divider()
    st.markdown("### Otimizar calendário")
    st.caption("O otimizador só aloca passeios de duração compatível e com tempo de trem "
               "conhecido ou locais. Alpes e conexões não pesquisadas ficam pendentes, "
               "não são colocados arbitrariamente em um dia.")
    if st.button("Gerar propostas (sem alterar o roteiro)",key="advisor_generate",use_container_width=True):
        st.session_state["advisor_proposals"]=propose_schedule(p,catalog,routes,profile)
    props=st.session_state.get("advisor_proposals",[])
    for index,proposal in enumerate(props):
        if proposal["base_revision"]!=p["revision"]:
            st.warning("Proposta desatualizada após mudança no planejamento. Gere novamente.")
            break
        with st.container(border=True):
            st.markdown(f"**Proposta {index+1}: {len(proposal['placed'])} passeios distribuídos**")
            diff=[(day,dest) for day,dest in sorted(proposal["assignments"].items())
                  if p["assignments"].get(day)!=dest]
            if diff:
                st.dataframe([{"Data":day,"Passeio":bydest[dest]["name"]}
                              for day,dest in diff],hide_index=True,use_container_width=True)
            else:st.caption("Sem dias novos compatíveis.")
            if proposal["unresolved"]:
                st.warning(str(len(proposal["unresolved"]))+" pendências não agendadas: "+
                           "; ".join(x["destination"]+" — "+x["reason"]
                                     for x in proposal["unresolved"]))
            c1,c2=st.columns(2)
            with c1:
                if st.button("Aprovar esta proposta",key=f"advisor_accept_{index}",
                             disabled=not diff,use_container_width=True):
                    updated=apply_proposal(p,proposal,approved=True)
                    st.session_state["advisor_plan"]=updated
                    st.session_state["explore_calendar"]=deepcopy(updated["assignments"])
                    st.session_state.pop("advisor_proposals",None)
                    st.success("Roteiro atualizado localmente. Grave no GitHub separadamente.")
                    st.rerun()
            with c2:
                if st.button("Rejeitar",key=f"advisor_reject_{index}",use_container_width=True):
                    st.session_state["advisor_proposals"]=[x for x in props if x["proposal_id"]!=proposal["proposal_id"]]
                    st.rerun()

    st.divider()
    st.markdown("### Versão e salvamento")
    if p["assignments"]:
        st.caption("Datas aprovadas na versão local: "+
                   ", ".join(day+" "+bydest.get(dest,{"name":dest})["name"]
                             for day,dest in sorted(p["assignments"].items())))
    st.download_button("Exportar plano JSON",
                       data=json.dumps(p,ensure_ascii=False,indent=2),
                       file_name=p["plan_id"]+".json",mime="application/json",
                       use_container_width=True)
    uploaded=st.file_uploader("Restaurar um plano exportado",type=["json"],key="advisor_import_json")
    if uploaded is not None:
        if st.button("Validar e importar arquivo",key="advisor_import_confirm"):
            try:
                new=json.load(uploaded)
                validate_plan(new,set(byattr))
                if any(x not in bydest for x in new["packages"]):
                    raise ValueError("Destino inexistente")
                st.session_state["advisor_plan"]=new
                st.session_state["advisor_github_sha"]=None
                st.session_state.pop("advisor_proposals",None)
                st.success("Plano importado apenas nesta sessão.")
                st.rerun()
            except (ValueError,KeyError,TypeError) as exc:
                st.error("Arquivo de plano inválido: "+str(exc))
    cfg=_owner_config()
    ready=bool(cfg["token"] and cfg["password_sha256"])
    if not ready:
        st.info("Salvamento automático no GitHub desabilitado: configure token e hash "
                "de autenticação do proprietário nos Secrets. Exportação JSON disponível.")
    else:
        if not st.session_state.get("advisor_owner_ok"):
            password=st.text_input("Senha do proprietário para escrita no GitHub",type="password",key="advisor_pass")
            failures=st.session_state.get("advisor_failed_logins",0)
            if st.button("Autorizar gravação",disabled=failures>=5,key="advisor_login"):
                digest=hashlib.sha256(password.encode()).hexdigest()
                if hmac.compare_digest(digest,cfg["password_sha256"]):
                    st.session_state["advisor_owner_ok"]=True
                    st.session_state["advisor_failed_logins"]=0
                    st.rerun()
                else:
                    st.session_state["advisor_failed_logins"]=failures+1
                    st.error("Autenticação não autorizada.")
        else:
            col1,col2=st.columns(2)
            with col1:
                if st.button("Gravar versão aprovada no GitHub",key="advisor_save",use_container_width=True):
                    try:
                        _secure_save(p)
                        st.success("Plano salvo com revisão verificada no GitHub.")
                    except Exception as exc:
                        st.error("GitHub não confirmou a gravação: "+type(exc).__name__+
                                 ". Verifique permissões, conflito de SHA e autenticação.")
            with col2:
                if st.button("Carregar plano versionado do GitHub",key="advisor_load",use_container_width=True):
                    try:
                        loaded,sha=GitHubPlanRepository(cfg["token"]).load(p["plan_id"])
                        st.session_state["advisor_plan"]=loaded
                        st.session_state["advisor_github_sha"]=sha
                        st.session_state.pop("advisor_proposals",None)
                        st.rerun()
                    except Exception as exc:
                        st.error("GitHub não retornou o plano: "+type(exc).__name__)
            with st.expander("Outros planos e histórico de revisões"):
                plan_id=st.text_input("ID do plano salvo (trip-...)",key="advisor_plan_lookup",
                                      value=p["plan_id"])
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
                        st.session_state["advisor_plan"]=loaded
                        st.session_state["advisor_github_sha"]=sha
                        st.session_state.pop("advisor_proposals",None)
                        st.rerun()
                    except Exception as exc:
                        st.error("Plano indisponível: "+type(exc).__name__)
                if st.button("Exibir revisões",key="advisor_history"):
                    try:
                        st.session_state["advisor_history"]=GitHubPlanRepository(cfg["token"]).history(plan_id)
                    except Exception as exc:
                        st.error("Histórico indisponível: "+type(exc).__name__)
                history=st.session_state.get("advisor_history",[])
                if history:
                    selected=st.selectbox("Snapshot no GitHub",history,
                        format_func=lambda x:x["date"][:10]+" · "+x["message"],
                        key="advisor_snapshot_choice")
                    if st.button("Pré-visualizar snapshot histórico",key="advisor_snapshot"):
                        try:
                            historical=GitHubPlanRepository(cfg["token"]).load_at_commit(plan_id,selected["sha"])
                            st.session_state["advisor_snapshot_preview"]=historical
                        except Exception as exc:
                            st.error("Snapshot não acessível: "+type(exc).__name__)
                    preview=st.session_state.get("advisor_snapshot_preview")
                    if preview:
                        st.caption("Snapshot: revisão "+str(preview["revision"])+
                            " · "+str(len(preview["assignments"]))+" dias agendados")
                        if st.button("Restaurar snapshot como nova revisão local",key="advisor_restore"):
                            try:
                                if preview["plan_id"]!=p["plan_id"]:
                                    raise ValueError("Carregue o plano correspondente primeiro")
                                restored=with_revision(p,{
                                    "packages":deepcopy(preview["packages"]),
                                    "assignments":deepcopy(preview["assignments"])})
                                st.session_state["advisor_plan"]=restored
                                st.session_state.pop("advisor_proposals",None)
                                st.info("Restaurado na sessão. Grave a nova revisão separadamente.")
                                st.rerun()
                            except ValueError as exc:st.warning(str(exc))
    st.caption("Gravação no GitHub é opcional e exige configuração prévia. "
               "Para produção pública, preferir login OAuth/GitHub App e restrição por usuário. "
               "Sem autenticação, este painel não escreve em repositórios.")
