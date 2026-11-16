"""UX3.8 compact researched-quote UI. No payments, reservations or ledger."""
from __future__ import annotations
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal

import streamlit as st
from quote_research_model import (
    CATEGORIES,CURRENCIES,UNITS,empty_collection,new_quote,validate_quote,
    upsert_quote,remove_quote,cloud_load,cloud_save,quote_difference,
    housing_budget_whatif
)
from private_continuity_store import StorageConflict,StorageUnavailable

LABELS={"housing":"Hospedagem","flight":"Passagem aérea",
        "intercity_train":"Trem intermunicipal","local_transport":"Transporte local",
        "outing":"Passeio","ticket":"Ingresso"}
UNIT_LABELS={"stay":"Estadia","person_oneway":"Pessoa · só ida",
             "person_roundtrip":"Pessoa · ida e volta",
             "couple_roundtrip":"Casal · ida e volta","person":"Pessoa",
             "couple":"Casal","night":"Noite","month":"Mês","visit":"Visita"}


def _store():
    from continuity_ui import _private_store
    store=_private_store()
    if store is None:return None
    store.key=store.key.removesuffix("current.json")+"ux38_quotes.json"
    return store


def _reload(store):
    collection,generation=cloud_load(store)
    st.session_state["ux38_quotes"]=collection
    st.session_state["ux38_generation"]=generation


def _persist(store,proposed):
    state=st.session_state
    generation=cloud_save(store,proposed,state.get("ux38_generation"))
    state["ux38_quotes"]=proposed
    state["ux38_generation"]=generation


def _availability():
    store=_store()
    if store is None:
        st.info("Entre com a conta Google do proprietário para guardar cotações na nuvem privada. "
                "Nenhum valor será publicado no GitHub.")
        return None,None
    state=st.session_state
    if st.button("Carregar / atualizar minhas cotações",key="ux38_load"):
        try:
            _reload(store)
            st.success("Cotações privadas carregadas.")
        except (ValueError,KeyError,TypeError,StorageConflict,StorageUnavailable):
            st.error("Não foi possível carregar. Seus dados desta sessão foram preservados.")
    return store,state.get("ux38_quotes")


def _edit_form(plan,previous=None):
    is_edit=previous is not None
    ident="edit" if is_edit else "new"
    french_start=date.fromisoformat(plan["departure_date"])+timedelta(days=plan["italy_days"])
    french_end=date.fromisoformat(plan["departure_date"])+timedelta(days=plan["total_days"])
    with st.form("ux38_form_"+ident):
        name=st.text_input("Descrição",value=previous["name"] if previous else "",
                           key="ux38_"+ident+"_name",max_chars=90)
        category=st.selectbox("Categoria",CATEGORIES,
                              format_func=lambda k:LABELS[k],
                              index=CATEGORIES.index(previous["category"]) if previous else 0,
                              key="ux38_"+ident+"_category")
        city=st.text_input("Cidade/destino (ID, opcional)",value=previous["city_id"] or "" if previous else plan["base_city"],
                           key="ux38_"+ident+"_city",max_chars=80)
        a,b,c=st.columns(3)
        money=a.text_input("Valor decimal",value=previous["amount"] if previous else "",
                           key="ux38_"+ident+"_amount",placeholder="2850.00")
        currency=b.selectbox("Moeda",CURRENCIES,
                             index=CURRENCIES.index(previous["currency"]) if previous else 1,
                             key="ux38_"+ident+"_currency")
        unit=c.selectbox("Unidade",UNITS,format_func=lambda v:UNIT_LABELS[v],
                         index=UNITS.index(previous["unit"]) if previous else 0,
                         key="ux38_"+ident+"_unit")
        q,t=st.columns(2)
        quantity=q.number_input("Quantidade de unidades",min_value=1,max_value=120,
                                value=previous["quantity"] if previous else 1,step=1,
                                key="ux38_"+ident+"_qty")
        travelers=t.number_input("Viajantes",min_value=1,max_value=10,
                                 value=previous["travelers"] if previous else 2,step=1,
                                 key="ux38_"+ident+"_trav")
        dated=st.checkbox("Vincular ao período",value=True if previous is None else previous["start_date"] is not None,
                          key="ux38_"+ident+"_dated")
        start=end=None
        if dated:
            x,y=st.columns(2)
            start=x.date_input("Início",value=date.fromisoformat(previous["start_date"]) if previous and previous["start_date"] else french_start,
                               key="ux38_"+ident+"_start")
            end=y.date_input("Fim (exclusivo)",value=date.fromisoformat(previous["end_date"]) if previous and previous["end_date"] else french_end,
                             key="ux38_"+ident+"_end")
        link=st.text_input("Fonte HTTPS (opcional)",value=previous["source_url"] or "" if previous else "",
                           key="ux38_"+ident+"_source")
        searched=st.date_input("Pesquisado em",value=date.fromisoformat(previous["researched_at"]) if previous else date.today(),
                                max_value=date.today(),key="ux38_"+ident+"_searched")
        notes=st.text_area("Observações",value=previous["notes"] if previous else "",
                           max_chars=700,key="ux38_"+ident+"_notes")
        fav=st.checkbox("Favorita para comparar (não é reserva)",
                        value=previous["favorite"] if previous else False,key="ux38_"+ident+"_fav")
        done=st.form_submit_button("Atualizar cotação" if is_edit else "Adicionar cotação privada")
    if not done:return None
    data={"name":name,"category":category,"city_id":city.strip() or None,
          "amount":money.strip(),"currency":currency,"unit":unit,
          "quantity":int(quantity),"travelers":int(travelers),
          "start_date":start.isoformat() if dated else None,
          "end_date":end.isoformat() if dated else None,
          "source_url":link.strip() or None,"researched_at":searched.isoformat(),
          "notes":notes,"favorite":fav}
    if is_edit:
        old=deepcopy(previous);old.update(data)
        return validate_quote(old)
    return new_quote(plan["plan_id"],**data)


def _rows(quotes):
    return [{"Cotação":q["name"],"Categoria":LABELS[q["category"]],
             "Cidade":q["city_id"] or "Não indicada",
             "Valor":q["amount"]+" "+q["currency"],
             "Unidade":UNIT_LABELS[q["unit"]],"Quantidade":q["quantity"],
             "Pesquisa":q["researched_at"],"Favorita":"Sim" if q["favorite"] else "Não"}
            for q in quotes]


def render_quotes_details(plan:dict)->None:
    st.markdown("### Cotações para comparar")
    st.caption("Pesquisas manuais, não pagamentos, reservas ou preços garantidos. "
               "Sua previsão oficial e o roteiro não serão alterados.")
    store,data=_availability()
    if store is None:return
    if data is None:
        st.caption("Carregue a coleção privada para começar, sem alterar a previsão.")
        return
    quotes=[q for q in data["quotes"] if q["plan_id"]==plan["plan_id"]]
    if quotes:st.dataframe(_rows(quotes),hide_index=True,width="stretch")
    else:st.info("Ainda não há cotações neste planejamento.")
    with st.expander("Adicionar cotação",expanded=not quotes):
        try:
            fresh=_edit_form(plan)
            if fresh is not None:
                _persist(store,upsert_quote(data,fresh))
                st.success("Cotação salva no espaço privado.")
                st.rerun()
        except StorageConflict:
            st.error("Conflito: outra sessão gravou. Atualize a coleção antes de tentar novamente.")
        except (ValueError,TypeError,KeyError,StorageUnavailable):
            st.error("Cotação não salva. Confira os campos ou baixe um backup antes de fechar.")
    if not quotes:return
    by_id={q["id"]:q for q in quotes}
    chosen=st.selectbox("Gerenciar cotação",list(by_id),
                        format_func=lambda v:by_id[v]["name"],key="ux38_chosen")
    selected=by_id[chosen]
    with st.expander("Editar cotação"):
        try:
            edited=_edit_form(plan,selected)
            if edited is not None:
                _persist(store,upsert_quote(data,edited))
                st.success("Cotação atualizada na nuvem.")
                st.rerun()
        except StorageConflict:
            st.error("Conflito de revisão. Atualize e confira as alterações.")
        except (ValueError,TypeError,KeyError,StorageUnavailable):
            st.error("Não foi possível confirmar essa edição.")
    with st.expander("Excluir cotação"):
        ack=st.checkbox("Confirmo a exclusão desta pesquisa",key="ux38_delete_ack")
        if st.button("Excluir cotação",disabled=not ack,key="ux38_delete"):
            try:
                _persist(store,remove_quote(data,chosen))
                st.success("Cotação excluída da coleção privada.")
                st.rerun()
            except StorageConflict:
                st.error("Conflito: atualize antes de excluir.")
            except (ValueError,TypeError,KeyError,StorageUnavailable):
                st.error("Exclusão não confirmada.")
    st.markdown("**Comparar alternativas equivalentes**")
    peers=[q for q in quotes if q["id"]!=selected["id"]]
    from quote_research_model import comparable_quotes
    peers=[q for q in peers if comparable_quotes(selected,q)]
    if peers:
        other=st.selectbox("Comparar com",list(range(len(peers))),
                           format_func=lambda i:peers[i]["name"],key="ux38_compare")
        diff=quote_difference(selected,peers[other])
        st.caption("Diferença entre valores pesquisados, com mesmo destino, período, "
                   "moeda, unidade e número de viajantes: "+str(diff)+" "+selected["currency"]+
                   ". Não é economia confirmada.")
    else:
        st.caption("Nenhuma outra cotação com escopo equivalente. "
                   "Não comparar períodos, moedas ou tipos de tarifa diferentes.")


def render_quotes_summary(data:dict,plan:dict,finance_live:bool)->None:
    st.markdown("#### Minhas cotações pesquisadas")
    state=st.session_state
    collection=state.get("ux38_quotes")
    if collection is None:
        st.caption("Para consultar suas cotações, abra **Orçamento → Detalhamento** e carregue "
                   "os estudos privados. Nada é adicionado automaticamente ao orçamento.")
        return
    quotes=[q for q in collection["quotes"] if q["plan_id"]==plan["plan_id"]]
    if not quotes:
        st.caption("Nenhuma cotação registrada. Seu orçamento continua como referência.")
        return
    st.caption(str(len(quotes))+" cotações registradas neste planejamento. "
               "Valores abaixo são hipóteses, não alterações no orçamento oficial.")
    from data_model import get_scenario
    from unified_budget import resolve_french_budget
    scenario=get_scenario(data,plan["budget_scenario"])
    french=resolve_french_budget(scenario,finance_live)
    housing=Decimal(str(french["amounts"]["rent"]))
    st.caption("Provisão de moradia da França: R$ "+str(housing.quantize(Decimal("0.01")))+
               " · fonte "+french["source"])
    fx=st.number_input("Câmbio hipotético R$/EUR para comparar hospedagem",
                       min_value=0.1,max_value=20.0,value=6.30,step=0.1,
                       key="ux38_fx_simulation")
    for quote in quotes:
        if quote["category"]!="housing":continue
        result=housing_budget_whatif(quote,plan,housing,
                                   fx_brl_per_unit=str(fx) if quote["currency"]=="EUR" else None)
        if quote["currency"]=="CHF":
            st.caption(quote["name"]+": CHF exige câmbio próprio explícito; sem diferença calculada.")
        elif result["delta_brl"] is None:
            st.caption(quote["name"]+": "+result["reason"]+".")
        else:
            st.caption(quote["name"]+": diferença **hipotética** de R$ "+result["delta_brl"]+
                       " em relação à provisão de moradia. Não somada ao orçamento.")
    st.caption("Para trem, voo e passeios, as provisões podem cobrir outros itens. "
               "Não calculamos diferenças sem escopo e unidade equivalentes.")
