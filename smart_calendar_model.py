"""UX 3.5: conditional, versioned smart calendar proposals.

Never writes to Streamlit, GitHub, Drive or an external booking service.
A chosen date means approved IN THE PLAN, not reserved with an operator.
A historical one-way train time is NOT evidence of a viable return.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo

from calendar_model import calendar_plan
from calendar_assignment_validation import validate_new_assignments
from itinerary_flow_model import selected_rows,ITALY_STAGE,FRANCE_STAGE
from planning_store import change_plan
from trip_plan_model import validate_plan
from attractions_model import route_for

DEFAULT_PREFERENCES={"timezone":"Europe/Paris","work_start":None,
                     "work_end":None,"allow_evenings":False}
MAX_OPTIONS=3


def validate_calendar_preferences(settings:dict|None)->dict:
    """Do not guess local work hours from the user's Brazil schedule."""
    values={**DEFAULT_PREFERENCES,**(settings or {})}
    if set(values)!=set(DEFAULT_PREFERENCES):
        raise ValueError("Preferência de calendário desconhecida")
    if not isinstance(values["timezone"],str):
        raise ValueError("Fuso do trabalho inválido")
    try:
        ZoneInfo(values["timezone"])
    except (ValueError,KeyError) as exc:
        raise ValueError("Fuso do trabalho desconhecido") from exc
    if type(values["allow_evenings"]) is not bool:
        raise ValueError("Preferência de noite inválida")
    for field in ("work_start","work_end"):
        val=values[field]
        if val is not None:
            try:
                normalized=datetime.strptime(val,"%H:%M").strftime("%H:%M")
            except (ValueError,TypeError) as exc:
                raise ValueError("Use HH:MM para o horário europeu") from exc
            if normalized!=val:
                raise ValueError("Horário deve usar HH:MM local")
    if (values["work_start"] is None)!=(values["work_end"] is None):
        raise ValueError("Preencha início e fim do expediente juntos")
    if (values["work_start"] is not None and
        values["work_start"]>=values["work_end"]):
        raise ValueError("Expediente local deve terminar depois de começar")
    # Evening plans still require opening hours AND verified last transport.
    # This model deliberately never auto-schedules them.
    return values


def availability_matrix(plan:dict,work_preferences:dict|None=None)->list[dict]:
    validate_plan(plan)
    settings=validate_calendar_preferences(work_preferences)
    days=calendar_plan(date.fromisoformat(plan["departure_date"]),
                       plan["total_days"],plan["italy_days"],
                       plan["vacation_days"],plan["setup_days"])
    italy_occupied={v["exact_date"]:v["destination_id"]
                   for v in plan.get("flexible_visits",[])
                   if v.get("stage")==ITALY_STAGE and v.get("exact_date")}
    french_occupied=plan.get("assignments",{})
    result=[]
    for row in days:
        occupied=(italy_occupied if row["stage"]==ITALY_STAGE
                  else french_occupied).get(row["date"])
        is_work="Trabalho remoto" in row["activity"]
        is_setup=row["activity"]=="Instalação"
        result.append({
            **row,"occupied_by":occupied,
            "workday":is_work,"setup":is_setup,
            "open_full_day":not occupied and not is_setup and not is_work,
            "date_status":("Aprovado no roteiro (não reservado)" if occupied
                           else "Dia de trabalho, período noturno a verificar" if is_work
                           else "Instalação, sem passeio de dia inteiro" if is_setup
                           else "Livre para planejamento"),
            "local_timezone":settings["timezone"],
            "booking_confirmed":False,
        })
    return result


def assess_day(plan:dict,visit:dict,day:str,evidence:dict|None=None,
               work_preferences:dict|None=None)->dict:
    days={r["date"]:r for r in availability_matrix(plan,work_preferences)}
    if day not in days:raise ValueError("Data fora da viagem")
    row=days[day]
    if row["stage"]!=visit["stage"]:
        return {"allowed":False,"reason":"A visita pertence a outra etapa"}
    if row["setup"] or row["workday"]:
        return {"allowed":False,"reason":(
            "Dia de instalação" if row["setup"] else
            "Trabalho remoto: não agendar passeio de dia inteiro")}
    if row["occupied_by"] not in (None,visit["id"]):
        return {"allowed":False,"reason":"Já existe passeio aprovado neste dia"}
    return {"allowed":True,"reason":"Dia livre na etapa, sujeito a horário e retorno",
            "conditional":True,"return_verified":False,
            "booking_confirmed":False}


def _visit_explanation(visit:dict,plan:dict,attractions:dict,routes:dict)->dict:
    if visit["stage"]==ITALY_STAGE:
        return {"eligible":True,"reason":"Férias italianas: 1 lugar por dia",
                "warning":"Horário, ingressos, transfer e reservas italianas não verificados",
                "source":None,"oneway_minutes":None}
    by_dest={d["id"]:d for d in attractions["destinations"]}
    dest=visit["id"]
    if dest not in by_dest:
        return {"eligible":False,"reason":"Destino sem cadastro de atrações",
                "warning":"Dados ausentes","source":None,"oneway_minutes":None}
    if by_dest[dest].get("kind")=="overnight":
        return {"eligible":False,"reason":"Roteiro com pernoite requer bloco próprio",
                "warning":"Pernoite e retorno a pesquisar","source":None,"oneway_minutes":None}
    route=route_for(routes,plan["base_city"],dest)
    local=dest==plan["base_city"]
    minutes=route.get("train_minutes_one_way")
    if not local and minutes is None:
        return {"eligible":False,"reason":"Tempo de deslocamento não pesquisado",
                "warning":"Ausência de dado não significa destino inviável",
                "source":route.get("source_url"),"oneway_minutes":None}
    durations={a["id"]:a["visit_minutes"] for a in attractions["attractions"]}
    total=sum(durations.get(a,0) for a in visit["attractions"])
    # Complete outing requires more than historic station time.  The 7-hour
    # limit is for museum/attraction time alone, not an accurate full-day sum.
    if total>420:
        return {"eligible":False,"reason":"Atrações somam mais de 7h",
                "warning":"Divida em dias ou reveja tempo de visita",
                "source":route.get("source_url"),"oneway_minutes":minutes}
    return {"eligible":True,
            "reason":"Férias ou fim de semana; ida histórica "
                     +(str(minutes)+" min entre estações" if minutes is not None
                       else "local com transporte a verificar"),
            "warning":"Sem retorno, última milha, abertura ou tarifas regulares verificadas para 2027",
            "source":route.get("source_url"),
            "oneway_minutes":minutes}


def _occupied_dates(plan:dict)->set[str]:
    return (set(plan.get("assignments",{}))|
            {v["exact_date"] for v in plan.get("flexible_visits",[])
             if v.get("stage")==ITALY_STAGE and v.get("exact_date")})


def _draft(plan:dict,assignments:dict,italy_dates:dict,changes:list,
           unresolved:list,variant:int)->dict:
    return {"proposal_id":f'{plan["plan_id"]}:r{plan["revision"]}:smart:{variant}',
            "plan_id":plan["plan_id"],"base_revision":plan["revision"],
            "base_city":plan["base_city"],
            "assignments":deepcopy(assignments),
            "italy_dates":deepcopy(italy_dates),
            "changes":deepcopy(changes),"unresolved":deepcopy(unresolved),
            "status":"draft_unapproved",
            "finance_delta_brl":None,
            "finance_note":"Sem tarifas regulares de volta/custos completos comparáveis; "
                           "a provisão existente não é cobrada novamente.",
            "booking_confirmed":False}


def suggest_calendar(plan:dict,catalog:dict,routes:dict,
                     preferences:dict|None=None,*,max_options:int=3)->list[dict]:
    """Suggestions never commit. Existing dated choices are untouched."""
    validate_plan(plan)
    validate_calendar_preferences(preferences)
    if type(max_options) is not int or not 1<=max_options<=MAX_OPTIONS:
        raise ValueError("Número de alternativas inválido")
    rows=selected_rows(plan,catalog)
    if not rows:return []
    days=availability_matrix(plan,preferences)
    jobs=[row for row in rows if not row["exact_dates"]]
    if not jobs:return []
    jobs.sort(key=lambda r:(r["stage"]!=ITALY_STAGE,r["name"]))
    proposals=[];signatures=set()
    for variant in range(max_options):
        assignments=deepcopy(plan.get("assignments",{}))
        italy_dates={v["destination_id"]:v["exact_date"] for v
                     in plan.get("flexible_visits",[])
                     if v.get("stage")==ITALY_STAGE and v.get("exact_date")}
        occupied=_occupied_dates(plan);changes=[];unresolved=[]
        for visit in jobs:
            insight=_visit_explanation(visit,plan,catalog,routes)
            if not insight["eligible"]:
                unresolved.append({"destination_id":visit["id"],
                                   "reason":insight["reason"]})
                continue
            options=[d for d in days if d["stage"]==visit["stage"]
                     and d["open_full_day"] and d["date"] not in occupied]
            if visit["stage"]==FRANCE_STAGE:
                prefer_vacation=insight["oneway_minutes"] is not None and insight["oneway_minutes"]>70
                options.sort(key=lambda d:(
                    0 if ("Férias" in d["activity"] if prefer_vacation
                          else "Fim de semana" in d["activity"]) else 1,
                    d["date"]))
            else:
                options.sort(key=lambda d:d["date"])
            if variant==1:options=list(reversed(options))
            if variant==2:options=options[1:]+options[:1] if len(options)>1 else options
            if not options:
                unresolved.append({"destination_id":visit["id"],
                                   "reason":"Sem data livre nesta etapa"})
                continue
            picked=options[0]["date"];occupied.add(picked)
            if visit["stage"]==ITALY_STAGE:italy_dates[visit["id"]]=picked
            else:assignments[picked]=visit["id"]
            changes.append({"destination_id":visit["id"],"stage":visit["stage"],
                            "from_date":None,"to_date":picked,
                            "reason":insight["reason"],
                            "warnings":[insight["warning"]],
                            "source":insight["source"],
                            "conditional":True,"reservation":False})
        if not changes:continue
        signature=tuple(sorted((x["destination_id"],x["to_date"]) for x in changes))
        if signature in signatures:continue
        signatures.add(signature)
        proposals.append(_draft(plan,assignments,italy_dates,changes,unresolved,
                                variant))
    return proposals


def manual_calendar_move(plan:dict,catalog:dict,dest_id:str,stage:str,
                         day:str|None,*,from_day:str|None=None)->dict:
    """A proposed manual move, including a removal back to flexible period."""
    found=next((r for r in selected_rows(plan,catalog)
                if r["id"]==dest_id and r["stage"]==stage),None)
    if found is None:raise ValueError("Escolha uma visita existente no roteiro")
    old=found["exact_dates"]
    if stage==FRANCE_STAGE and len(old)>1 and from_day is None:
        raise ValueError("Indique a visita específica ao reagendar destino repetido")
    # An explicit empty origin means "add another visit". None means
    # "use the only existing visit" for backward compatibility.
    current=(None if from_day=="" else from_day if from_day is not None
             else (old[0] if old else None))
    if current and current not in old:
        raise ValueError("Data antiga não pertence a este destino")
    if day is not None:
        report=assess_day(plan,found,day)
        if not report["allowed"] and not (
            report["reason"]=="Já existe passeio aprovado neste dia" and day==current
        ):
            raise ValueError(report["reason"])
    assignments=deepcopy(plan.get("assignments",{}))
    italy_dates={v["destination_id"]:v["exact_date"] for v
                 in plan.get("flexible_visits",[])
                 if v.get("stage")==ITALY_STAGE and v.get("exact_date")}
    if stage==ITALY_STAGE:
        if day is None:italy_dates.pop(dest_id,None)
        else:italy_dates[dest_id]=day
    else:
        if current:assignments.pop(current,None)
        if day:assignments[day]=dest_id
    change={"destination_id":dest_id,"stage":stage,
            "from_date":current,"to_date":day,
            "reason":"Alteração manual solicitada pelo viajante",
            "warnings":["Data aprovada no roteiro; retorno, horários e reservas a confirmar"],
            "source":None,"conditional":True,"reservation":False}
    return _draft(plan,assignments,italy_dates,[change],[],0)


def review_calendar_change(plan:dict,proposal:dict,catalog:dict)->dict:
    """Validate entire proposed change against current revision and selected rows."""
    validate_plan(plan)
    if (not isinstance(proposal,dict) or
        proposal.get("status")!="draft_unapproved" or
        proposal.get("plan_id")!=plan["plan_id"] or
        proposal.get("base_revision")!=plan["revision"] or
        proposal.get("base_city")!=plan["base_city"] or
        proposal.get("booking_confirmed") is not False):
        raise ValueError("Proposta desatualizada ou incompatível com o plano")
    changes=proposal.get("changes")
    assignments=proposal.get("assignments")
    italian=proposal.get("italy_dates")
    if (not isinstance(changes,list) or not changes or len(changes)>80 or
        not isinstance(assignments,dict) or not isinstance(italian,dict)):
        raise ValueError("Proposta com visitas inválidas")
    rows={r["id"]:r for r in selected_rows(plan,catalog)}
    for change in changes:
        dest=change.get("destination_id")
        if dest not in rows or change.get("stage")!=rows[dest]["stage"]:
            raise ValueError("Visita da proposta não pertence ao roteiro")
        old=change.get("from_date")
        if old is not None and old not in rows[dest]["exact_dates"]:
            raise ValueError("Data de origem diverge do plano")
        day=change.get("to_date")
        if day is not None:
            report=assess_day(plan,rows[dest],day)
            if not report["allowed"] and day!=old:
                raise ValueError(report["reason"])
    # A portable JSON draft is untrusted: the visible review must cover
    # *exactly* every persisted change, not a harmless-looking subset.
    expected_assignments=deepcopy(plan.get("assignments",{}))
    expected_italy={v["destination_id"]:v["exact_date"] for v
                    in plan.get("flexible_visits",[])
                    if v.get("stage")==ITALY_STAGE and v.get("exact_date")}
    seen_moves=set()
    for item in changes:
        dest=item["destination_id"]
        old=item.get("from_date");new=item.get("to_date")
        if (not isinstance(dest,str) or
            old is not None and not isinstance(old,str) or
            new is not None and not isinstance(new,str) or
            item.get("reservation") is not False):
            raise ValueError("Alteração de data inválida ou reserva indevida")
        unique=(item["stage"],dest,old,new)
        if unique in seen_moves:
            raise ValueError("Mudança duplicada no rascunho")
        seen_moves.add(unique)
        if item["stage"]==FRANCE_STAGE:
            if old:expected_assignments.pop(old,None)
            if new:
                if new in expected_assignments:
                    raise ValueError("Outro passeio já ocupa esta data")
                expected_assignments[new]=dest
        else:
            if old:expected_italy.pop(dest,None)
            if new:expected_italy[dest]=new
    if expected_assignments!=assignments or expected_italy!=italian:
        raise ValueError("O rascunho inclui datas que não apareceram na revisão")
    if any(not isinstance(d,str) or not isinstance(v,str) for d,v in assignments.items()):
        raise ValueError("Datas ou destinos inválidos")
    schedule={r["date"]:r for r in availability_matrix(plan)}
    italy_days={};legacy=set(plan.get("assignments",{}))
    for dest,day in italian.items():
        if dest not in rows or rows[dest]["stage"]!=ITALY_STAGE or day not in schedule:
            raise ValueError("Visita italiana inválida")
        if schedule[day]["stage"]!=ITALY_STAGE or day in italy_days:
            raise ValueError("Datas italianas duplicadas ou fora da etapa")
        italy_days[day]=dest
    if not set(plan["assignments"]).issubset(
        set(assignments)|{c.get("from_date") for c in changes}
    ):
        raise ValueError("Proposta remove data aprovada sem revisão")
    # Removing or replacing a France date must appear explicitly in changes.
    for day,dest in plan["assignments"].items():
        if assignments.get(day)!=dest and not any(
            c.get("stage")==FRANCE_STAGE and
            c.get("from_date")==day and c.get("destination_id")==dest
            for c in changes
        ):
            raise ValueError("Alteração de agenda sem revisão")
    candidate=deepcopy(plan)
    candidate["assignments"]=deepcopy(assignments)
    visits=deepcopy(plan.get("flexible_visits",[]))
    for row in visits:
        if row["stage"]!=ITALY_STAGE:continue
        row.pop("exact_date",None)
        if row["destination_id"] in italian:
            row["exact_date"]=italian[row["destination_id"]]
    candidate["flexible_visits"]=visits
    validate_new_assignments(candidate,assignments,
                             previously_approved=plan["assignments"])
    validate_plan(candidate)
    # Prevent an unrelated Italian date from disappearing.
    for original in plan.get("flexible_visits",[]):
        if original["stage"]!=ITALY_STAGE or not original.get("exact_date"):continue
        if (italian.get(original["destination_id"])!=original["exact_date"] and
            not any(c["destination_id"]==original["destination_id"] and
                    c["stage"]==ITALY_STAGE and
                    c.get("from_date")==original["exact_date"] for c in changes)):
            raise ValueError("Data italiana aprovada modificada sem revisão")
    return {"plan_id":plan["plan_id"],"base_revision":plan["revision"],
            "base_city":plan["base_city"],"changes":deepcopy(changes),
            "unresolved":deepcopy(proposal.get("unresolved",[])),
            "candidate":candidate,
            "finance_delta_brl":None,
            "booking_confirmed":False,
            "unchanged":["base oficial","atrações selecionadas","preferências",
                         "reservas externas","provisão financeira"]}


def apply_calendar_change(plan:dict,proposal:dict,catalog:dict,
                          *,confirmed:bool=False)->dict:
    if not confirmed:return deepcopy(plan)
    reviewed=review_calendar_change(plan,proposal,catalog)
    target=reviewed["candidate"]
    changes={field:target[field] for field in ("assignments","flexible_visits")
             if target[field]!=plan.get(field)}
    return change_plan(plan,changes) if changes else deepcopy(plan)
