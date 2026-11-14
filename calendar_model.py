"""Non-booked travel calendar derived from wedding, departure and holiday assumptions."""
from __future__ import annotations
from datetime import date,timedelta

WEDDING=date(2027,9,4)
def calendar_plan(departure: date, total_days: int, italy_days: int,
                  initial_vacation_days: int, setup_days: int) -> list[dict]:
    if departure <= WEDDING:
        raise ValueError("Partida deve ser depois do casamento")
    if not 50 <= total_days <= 100 or not 5 <= italy_days <= 20:
        raise ValueError("Duração fora da faixa planejada")
    if not italy_days < initial_vacation_days < total_days:
        raise ValueError("Férias iniciais devem incluir etapa italiana")
    if not 1 <= setup_days <= initial_vacation_days - italy_days:
        raise ValueError("Instalação excede férias na França")
    result=[]
    for index in range(total_days):
        day=departure+timedelta(days=index)
        if index < italy_days:
            stage,kind="Itália","Férias · Itália"
        elif index < italy_days+setup_days:
            stage,kind="França","Instalação"
        elif index < initial_vacation_days:
            stage,kind="França","Férias · excursões possíveis"
        elif day.weekday()>=5:
            stage,kind="França","Fim de semana · passeios"
        else:
            stage,kind="França","Trabalho remoto · noite livre a verificar"
        result.append({"day":index+1,"date":day.isoformat(),"weekday":day.strftime("%a"),
                       "stage":stage,"activity":kind,"confirmed":False})
    return result
