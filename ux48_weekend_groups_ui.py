"""Contextual weekend planning, using the existing private continuity sidecar."""
from datetime import date, timedelta
import streamlit as st
from ux48_weekend_groups_model import (
    empty_groups, validate_groups, create_group, update_group,
    remove_group, ungrouped_outings, available_weekends, eligible_weekends,
    set_rest_weekend, export_groups, import_groups, PERIODS,
)
from itinerary_flow_model import selected_rows, FRANCE_STAGE


def _state(plan, catalog):
    value = st.session_state.get("ux48_weekend_groups")
    if value is None:
        return empty_groups(plan)
    return validate_groups(value, plan, catalog)


def _save(value, message="Agrupamentos atualizados"):
    st.session_state["ux48_weekend_groups"] = value
    st.session_state["ux36_cloud_dirty"] = True
    st.session_state["ux48_weekend_message"] = message + (
        ". Alteração registrada nesta sessão. Salve uma cópia privada ou exporte "
        "um backup para preservar as alterações. Reservas continuam a confirmar.")


def _open_editor(plan_id, group=None, destinations=None, start=None):
    st.session_state["ux49_editor"] = {
        "plan_id": plan_id, "group_id": group["id"] if group else None,
        "name": group["name"] if group else "",
        "destinations": list(group["destinations"] if group else destinations or []),
        "period": group["period"] if group else PERIODS[0],
        "nights": group["nights"] if group else 0,
        "start": group["start_date"] if group else start,
        "notes": group["notes"] if group else "",
        "status": group["status"] if group else "estudo",
    }
    for key in list(st.session_state):
        if key.startswith("ux49_field_"):
            del st.session_state[key]


def _remember(field):
    st.session_state["ux49_editor"][field] = st.session_state["ux49_field_" + field]


def _date_label(value):
    return date.fromisoformat(value).strftime("%d/%m/%Y") if value else "Data a definir"


def _editor(plan, catalog, groups, byid):
    draft = st.session_state.get("ux49_editor")
    if not draft or draft["plan_id"] != plan["plan_id"]:
        return
    group_id = draft["group_id"]
    if group_id and not any(g["id"] == group_id for g in groups["groups"]):
        st.warning("Este agrupamento foi removido. Escolha uma viagem para editar.")
        return
    used = {d for g in groups["groups"] if g["id"] != group_id for d in g["destinations"]}
    options = [d for d in byid if d not in used]
    remaining = [d for d in draft["destinations"] if d in options]
    if remaining != draft["destinations"]:
        draft["destinations"] = remaining
        st.session_state["ux49_field_destinations"] = remaining
        st.warning("Os passeios disponíveis mudaram. Revise a seleção antes de salvar.")
    with st.container(border=True):
        st.markdown("#### " + ("Editar viagem" if group_id else "Criar viagem"))
        # Draft values survive widget cleanup when navigating to other activities.
        for field, value in draft.items():
            if field not in ("plan_id", "group_id"):
                st.session_state.setdefault("ux49_field_" + field, value)
        st.text_input("Nome da viagem", key="ux49_field_name",
                      on_change=_remember, args=("name",), max_chars=100)
        selected = st.multiselect("Passeios na ordem desejada", options,
            format_func=lambda value: byid[value]["name"], max_selections=6,
            key="ux49_field_destinations", on_change=_remember, args=("destinations",))
        if len(selected) > 1:
            st.caption("Ordem atual: " + " → ".join(byid[d]["name"] for d in selected))
            moving = st.selectbox("Destino para reordenar", selected,
                                 format_func=lambda value: byid[value]["name"])
            for col, offset, label in zip(st.columns(2), (-1, 1),
                                         ("Mover para cima", "Mover para baixo")):
                index = selected.index(moving)
                if col.button(label, disabled=not 0 <= index + offset < len(selected)):
                    ordered = list(selected)
                    ordered[index], ordered[index + offset] = ordered[index + offset], ordered[index]
                    draft["destinations"] = ordered
                    del st.session_state["ux49_field_destinations"]
                    st.rerun()
        period = st.selectbox("Período flexível", PERIODS, key="ux49_field_period",
                              on_change=_remember, args=("period",))
        nights = st.number_input("Pernoites hipotéticos", min_value=0, max_value=3,
                                 key="ux49_field_nights", on_change=_remember, args=("nights",))
        st.caption("O agrupamento ocupa pelo menos sábado e domingo, mesmo sem pernoite. "
                   "Duas noites incluem segunda-feira; três incluem terça-feira. "
                   "Dias úteis exigem verificar sua disponibilidade para viajar.")
        candidates = eligible_weekends(groups, plan, catalog, destinations=selected,
                                       nights=nights, period=period, group_id=group_id)
        dates = [r["start"] for r in candidates if r["eligible"]]
        previous = draft["start"]
        invalid = previous is not None and previous not in dates
        choices = [None] + dates
        if invalid:
            choices.append(previous)
            reason = next((r["reason"] for r in candidates if r["start"] == previous),
                          "Data fora da temporada atual.")
            st.warning("A data escolhida ficou incompatível: " + str(reason) +
                       " Escolha outra data ou Data a definir para salvar.")
        # Keep a previous date visible, explicitly invalid, instead of silently dropping it.
        st.session_state["ux49_field_start"] = previous
        start = st.selectbox("Data opcional (sábado)", choices,
            format_func=lambda value: _date_label(value) + (
                " · incompatível" if value is not None and value not in dates else ""),
            key="ux49_field_start", on_change=_remember, args=("start",))
        if not dates:
            st.info("Nenhuma data compatível com essas escolhas. Você pode salvar com data a definir.")
        rejected = [r for r in candidates if not r["eligible"]]
        if rejected:
            with st.expander("Por que algumas datas estão indisponíveis?"):
                for row in rejected:
                    st.caption(_date_label(row["start"]) + " · " + row["reason"])
        st.text_area("Observações e pendências", max_chars=700, key="ux49_field_notes",
                     on_change=_remember, args=("notes",))
        st.selectbox("Estado do planejamento", ["estudo", "planejado"],
            format_func=lambda value: "Em estudo" if value == "estudo" else "Planejado · não reservado",
            key="ux49_field_status", on_change=_remember, args=("status",))
        st.caption("Transporte completo, retorno e hospedagem quando houver pernoite precisam ser verificados.")
        save, cancel = st.columns(2)
        if save.button("Salvar viagem", type="primary", disabled=not selected or (
                start is not None and start not in dates)):
            changes = dict(name=draft["name"].strip() or " + ".join(byid[d]["name"] for d in selected),
                           destinations=selected, period=period, nights=nights, start_date=start,
                           notes=draft["notes"], status=draft["status"])
            try:
                value = update_group(groups, plan, catalog, group_id, **changes) if group_id else create_group(
                    groups, plan, catalog, **changes)
                _save(value, "Viagem salva · " + changes["name"])
                del st.session_state["ux49_editor"]
                st.rerun()
            except (ValueError, TypeError) as exc:
                st.error(str(exc))
        if cancel.button("Fechar edição"):
            del st.session_state["ux49_editor"]
            st.rerun()


def render_weekend_planner(plan, catalog):
    st.markdown("### Organizar viagens de fim de semana")
    st.caption("Reúna os passeios escolhidos em viagens. Datas e pernoites são hipóteses de planejamento.")
    try:
        groups = _state(plan, catalog)
    except (ValueError, KeyError, TypeError) as exc:
        st.error("Os agrupamentos precisam de revisão. Nenhuma decisão foi alterada: "+str(exc))
        return
    byid = {row["id"]: row for row in selected_rows(plan, catalog) if row["stage"] == FRANCE_STAGE}
    free = ungrouped_outings(groups, plan, catalog)
    slots = available_weekends(groups, plan, catalog)
    message = st.session_state.pop("ux48_weekend_message", None)
    if message:
        st.success(message)
    st.caption(f'{len(groups["groups"])} viagens · {len(free)} passeios não agrupados · '
               f'{sum(r["status"] == "livre · não reservado" for r in slots)} fins de semana livres · '
               f'{len(groups["rest_weekends"])} para descanso')
    st.markdown("#### Minhas viagens")
    if st.button("+ Criar viagem", disabled=not free):
        _open_editor(plan["plan_id"])
        st.rerun()
    if not groups["groups"]:
        st.info("Escolha passeios e crie sua primeira viagem de fim de semana.")
    for group in groups["groups"]:
        with st.container(border=True):
            st.markdown("**" + group["name"] + "**")
            st.write(" → ".join(byid[d]["name"] for d in group["destinations"]))
            status = "Em estudo" if group["status"] == "estudo" else "Planejado · não reservado"
            end = (date.fromisoformat(group["start_date"]) + timedelta(days=max(1, group["nights"]))).isoformat() if group["start_date"] else None
            dates = _date_label(group["start_date"])
            if end:
                dates += " até " + _date_label(end)
            st.caption(f'{status} · {dates} · {group["nights"]} pernoite(s) hipotético(s)')
            st.caption("Transporte e retorno a verificar" + (" · Hospedagem a verificar" if group["nights"] else ""))
            if st.button("Editar viagem / organizar data", key="ux49_edit_" + group["id"]):
                _open_editor(plan["plan_id"], group=group)
                st.rerun()
            with st.expander("Detalhes · " + group["name"]):
                st.caption("Base de referência: " + group["base_city"].capitalize() + " · " + group["period"])
                if group["notes"]:
                    st.write(group["notes"])
                if {"brussels", "bruges_be"}.issubset(group["destinations"]):
                    st.caption("Bruxelas ↔ Bruges: média histórica de 1h04. Verifique o trajeto completo e os horários de 2027.")
                    st.markdown("[Consultar SNCB](https://www.belgiantrain.be/en/travel-info/origin-destination/brussels-bruges)")
                if st.checkbox("Confirmar remoção do agrupamento", key="ux49_ack_" + group["id"]):
                    if st.button("Remover agrupamento", key="ux49_delete_" + group["id"]):
                        _save(remove_group(groups, plan, catalog, group["id"]), "Agrupamento removido; passeios preservados")
                        st.rerun()
    st.markdown("#### Passeios ainda não organizados")
    if free:
        selected = st.multiselect("Passeios para uma nova viagem", [r["id"] for r in free],
                                  format_func=lambda value: byid[value]["name"], max_selections=6)
        if st.button("Organizar passeios selecionados", disabled=not selected):
            _open_editor(plan["plan_id"], destinations=selected)
            st.rerun()
    else:
        st.caption("Todos os passeios escolhidos já estão agrupados." if byid else
                   "Adicione passeios em Meu planejamento para começar.")
    _editor(plan, catalog, groups, byid)
    st.markdown("#### Fins de semana da temporada")
    st.caption("Livre indica espaço no planejamento. Confira transporte e hospedagem antes de reservar.")
    for slot in slots:
        with st.container(border=True):
            st.markdown("**" + _date_label(slot["start"]) + " – " + _date_label(slot["end"]) + "**")
            group = next((g for g in groups["groups"] if g["start_date"] == slot["start"]), None)
            if group:
                st.write("Viagem com data · " + group["name"])
                if st.button("Abrir viagem", key="ux49_slot_edit_" + slot["start"]):
                    _open_editor(plan["plan_id"], group=group)
                    st.rerun()
            else:
                st.write(slot["status"].replace(" no TripPlan", ""))
            rest = slot["start"] in groups["rest_weekends"]
            if rest or slot["status"] == "livre · não reservado":
                if st.button("Desmarcar descanso" if rest else "Marcar descanso", key="ux49_rest_" + slot["start"]):
                    _save(set_rest_weekend(groups, plan, catalog, slot["start"], not rest),
                          "Descanso removido" if rest else "Fim de semana reservado para descanso")
                    st.rerun()
                if not rest and st.button("Criar viagem neste período", key="ux49_slot_create_" + slot["start"], disabled=not free):
                    _open_editor(plan["plan_id"], start=slot["start"])
                    st.rerun()
    st.divider()
    st.caption("**Persistência:** os agrupamentos integram o backup e o "
               "salvamento privado do planejamento, quando configurado. "
               "Não são publicados no GitHub nem incluídos no TripPlan. "
               "Sem armazenamento privado, exporte o backup antes de sair.")
    st.download_button("Exportar rascunho de fins de semana",
        data=export_groups(groups,plan,catalog),
        file_name="nossa-europa-fins-de-semana.json",
        mime="application/json",key="ux48_export_weekends")
    uploaded=st.file_uploader("Importar rascunho anterior (mesmo planejamento)",
        type=["json"],key="ux48_import_weekends")
    if uploaded and st.button("Validar e importar rascunho",key="ux48_confirm_import"):
        try:
            _save(import_groups(uploaded.getvalue().decode("utf-8"),plan,catalog))
            st.rerun()
        except (UnicodeDecodeError,ValueError,TypeError) as exc:
            st.error("Rascunho não importado: "+str(exc))
