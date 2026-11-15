"""User-facing persistence labels; no technical IDs or false success states."""
from __future__ import annotations
from datetime import datetime,timezone
from planning_store import is_dirty

def save_label(current:dict,snapshot:dict|None,authenticated:bool)->tuple[str,str]:
    if not authenticated:return ("Backup disponível","Entre com Google para guardar online")
    if snapshot is None:return ("Ainda não salvo","Salve para continuar em outro dia")
    if is_dirty(current,snapshot):
        return ("Alterações não salvas","Seu planejamento mudou desde o último salvamento")
    return ("Planejamento salvo","Seu roteiro está guardado e poderá ser recuperado")

def explain_storage_error(exc:Exception)->str:
    from urllib.error import HTTPError,URLError
    if isinstance(exc,HTTPError):
        if exc.code in (401,403):return "O acesso ao salvamento foi recusado. Verifique as permissões da conta."
        if exc.code in (409,422):return "Seu planejamento foi alterado em outra sessão. Recarregue antes de salvar."
        if exc.code==404:return "Não foi possível encontrar esse planejamento. Selecione outro no Histórico."
        return "Serviço de salvamento indisponível. Seus dados continuam nesta sessão."
    if isinstance(exc,ValueError):return "Há um conflito ou dado inválido. Revise as alterações antes de salvar."
    if isinstance(exc,URLError):return "Sem conexão com o salvamento online. Tente novamente."
    return "Não foi possível salvar agora. Seus dados continuam nesta sessão."

def friendly_timestamp(value:str|None)->str:
    if not value:return "Data indisponível"
    try:
        moment=datetime.fromisoformat(value.replace("Z","+00:00"))
        return moment.astimezone(timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")
    except ValueError:return "Data indisponível"
