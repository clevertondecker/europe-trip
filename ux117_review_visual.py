"""Read-only UX117 presentation of the existing UX115 decision projection."""
from formatting import amount, REQUIRED, minutes, html_safe as _safe
from base_change_model import SIMILARITY_THRESHOLD_MINUTES
from ux_shared_ui_presentation import kpi_cards

def _duration(value):
    return minutes(value, missing="Sem tempo", nonpositive_as_zero=True, allow_zero=False)


def _signed(value):
    if value is None:
        return "—"
    return ("−" if value<0 else "+" if value>0 else "")+_duration(abs(value))

BASIS={"fastest_reference":"Mínimos de ida","representative":"Tempos típicos de ida"}

def comparable_subtotals(view):
    """One outbound per eligible destination; never mix methodology groups."""
    totals={}
    for row in view["rows"]:
        basis=row["comparison_basis"]
        if row["delta_minutes"] is None or basis not in BASIS:
            continue
        if row["status"] not in ("Melhorou","Piorou","Semelhante"):
            continue
        before,after=row["before"],row["after"]
        if before is None or after is None or before<=0 or after<=0:
            continue
        if after-before!=row["delta_minutes"]:
            raise ValueError("Inconsistent comparison delta")
        item=totals.setdefault(basis,{"before":0,"after":0,"count":0,"delta":0})
        item["before"]+=before
        item["after"]+=after
        item["count"]+=1
        item["delta"]+=row["delta_minutes"]
    return totals

def city_identity_html(city,role):
    return ('<div class="ux117-identity"><small>'+_safe(role)+'</small><strong>'
            +_safe(city["name"])+'</strong><span>'+_safe(city["country"])+'</span></div>')

def _cell(row,side):
    category=row[side+"_category"]
    value=row["before" if side=="official" else "after"]
    if category=="local":
        return '<span class="ux117-muted">Local · acesso a verificar</span>'
    if value is None:
        return '<span class="ux117-muted">Sem tempo</span>'
    qualifier=("Indicativo" if category=="reference_only" else "Histórico")
    if row[side+"_confidence"]=="low":
        qualifier+=" · baixa confiança"
    return '<strong>'+_safe(_duration(value))+'</strong><small>'+_safe(qualifier)+'</small>'

def impact_html(view):
    groups=view["groups"]
    pending=sum(len(groups[k]) for k in ("Não pesquisado","Local","Referência insuficiente"))
    metrics=[{"name":"Mais rápidos","value":len(groups["Melhorou"]),"icon":"↓"},
             {"name":"Mais lentos","value":len(groups["Piorou"]),"icon":"↑"},
             {"name":"Semelhantes","value":len(groups["Semelhante"]),"icon":"≈"},
             {"name":"A verificar","value":pending,"icon":"?"}]
    cards="".join(kpi_cards(metrics))
    common,total=view["comparable"],view["total"]
    percent=100*common/total if total else 0
    critical_late=sum(row["priority"]=="must_visit" for row in groups["Piorou"])
    critical_pending=sum(row["priority"]=="must_visit"
                         for status in ("Não pesquisado","Local","Referência insuficiente")
                         for row in groups[status])
    notices=[]
    if critical_late:
        notices.append("1 destino imperdível terá uma ida mais longa." if critical_late==1
                       else f"{critical_late} destinos imperdíveis terão idas mais longas.")
    if critical_pending:
        notices.append("1 destino imperdível ainda precisa de validação." if critical_pending==1
                       else f"{critical_pending} destinos imperdíveis ainda precisam de validação.")
    alert_html=('<p class="ux117-priority-note" role="note">'+_safe(" ".join(notices))+'</p>'
                if notices else "")
    body=[]
    kinds={"Melhorou":"gain","Piorou":"loss","Semelhante":"similar",
           "Não pesquisado":"pending","Local":"pending","Referência insuficiente":"pending"}
    for row in view["rows"]:
        status=row["status"]
        alert=row["priority"]=="must_visit" and status not in ("Melhorou","Semelhante")
        priority=('<small>'+_safe(row["priority_label"])+'</small>') if row["priority_label"] else ""
        if alert:
            priority+='<small class="ux117-critical">Atenção: imperdível</small>'
        note=BASIS.get(row["comparison_basis"],{"Local":"Acesso urbano pendente",
                    "Referência insuficiente":"Confiança insuficiente",
                    "Não pesquisado":"Sem par comparável"}.get(status,status))
        delta=_signed(row["delta_minutes"]) if row["delta_minutes"] is not None else "A verificar"
        body.append('<tr><th scope="row">'+_safe(row["name"])+priority+'</th><td>'+
                    _cell(row,"official")+'</td><td>'+_cell(row,"candidate")+
                    '</td><td><strong class="ux117-'+kinds[status]+'">'+_safe(delta)+
                    '</strong><small>'+_safe(status)+' · '+_safe(note)+'</small></td></tr>')
    return ('<section class="ux117-panel"><h3>Impacto nos seus passeios</h3>'
            '<div class="ux117-kpis">'+cards+'</div>'
            '<p class="ux117-coverage">'+str(common)+' de '+str(total)+' destinos comparáveis</p>'
            '<div class="ux117-track" role="progressbar" aria-label="Cobertura de comparação" '
            'aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+str(round(percent))+'">'
            '<span style="width:'+str(percent)+'%"></span></div>'
            '<p class="ux97-footnote">Diferenças inferiores a '+str(SIMILARITY_THRESHOLD_MINUTES)+
            ' minutos por trecho são consideradas semelhantes. A quantidade de melhorias '
            'não determina a melhor base.</p>'+alert_html+
            '<div class="ux97-scroll" role="region" tabindex="0" aria-label="Impacto da troca por destino">'
            '<table class="ux97-table ux117-table"><thead><tr><th scope="col">Destino</th>'
            '<th scope="col">'+_safe(view["official_name"])+'</th><th scope="col">'+
            _safe(view["candidate_name"])+'</th><th scope="col">Diferença</th></tr></thead><tbody>'+
            ''.join(body)+'</tbody></table></div>'
            '<p class="ux97-footnote">Referências de ida, não itinerários de 2027. '
            'Retorno, conexões reais e última milha a verificar. Sem tempo não significa inviável.</p></section>')

def subtotals_html(view):
    totals=comparable_subtotals(view)
    if not totals:
        return ""
    sections=[]
    for basis,item in totals.items():
        scale=max(item["before"],item["after"])
        bars=[]
        for name,key in ((view["official_name"],"before"),(view["candidate_name"],"after")):
            value=item[key]
            bars.append('<div class="ux117-bar-row"><span>'+_safe(name)+'</span>'
                        '<div class="ux117-track"><span class="ux117-bar-'+key+'" style="width:'+
                        str(100*value/scale)+'%"></span></div><strong>'+_safe(_duration(value))+'</strong></div>')
        delta=item["delta"]
        description=(_duration(abs(delta))+(" a menos" if delta<0 else " a mais")
                     if delta else "Mesmo tempo acumulado")
        sections.append('<div class="ux117-subtotal"><h4>'+BASIS[basis]+' · '+str(item["count"])+
                        ' destinos</h4>'+''.join(bars)+'<strong class="ux117-delta">'+
                        _safe(description)+' na soma de ida · '+str(item["count"])+
                        '/'+str(view["total"])+' destinos</strong></div>')
    return ('<section class="ux117-panel"><h3>Impacto acumulado</h3>'+''.join(sections)+
            '<p class="ux97-footnote">Uma ida por destino comparável em cada grupo. '
            'Não inclui retornos, frequência, custos ou última milha. Não é uma economia garantida.</p></section>')

def _money(value):
    return amount(value, decimals=2, missing=REQUIRED, absolute=True, trim_zeros=True)


def housing_html(comparison,view):
    rents=comparison["rents_eur_month"]
    cards=[]
    for city,name in ((comparison["official_base"],view["official_name"]),
                      (view["candidate"],view["candidate_name"])):
        rent=rents.get(city)
        value="Não cotado" if rent is None else "€ "+_money(rent)+"/mês"
        cards.append('<div class="ux117-rent"><small>'+_safe(name)+'</small><strong>'+_safe(value)+'</strong></div>')
    if view["housing_known"]:
        delta=view["housing_delta_brl"]
        summary="Variação hipotética da moradia: "+("−" if delta<0 else "+" if delta>0 else "")+"R$ "+_money(delta)
    else:
        summary="Informe dois aluguéis para comparar. Ausência de cotação não é custo zero."
    return ('<section class="ux117-panel"><div class="ux117-rents">'+''.join(cards)+
            '</div><p class="ux117-coverage">'+_safe(summary)+'</p><p class="ux97-footnote">'+
            _safe(str(comparison["french_days"])+" dias · câmbio hipotético R$ "+f'{comparison["eur_fx"]:.2f}'.replace(".",",")+"/€")+
            '. Somente moradia; não é o custo total da viagem.</p></section>')
