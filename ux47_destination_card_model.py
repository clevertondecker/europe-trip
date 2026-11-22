"""UX 4.7 presentation adapter for a chosen France-stage destination.

Read-only. Data comes from the existing TripPlan/catalog/rail guide; missing
costs and unverified return services must never become confirmed status.
"""
from __future__ import annotations
from outing_guide_model import build_outing_guide
from itinerary_flow_model import UNASSIGNED
from ux62_supplemental_outings import supplemental_destination

def destination_card_view(plan:dict,catalog:dict,routes:dict,row:dict)->dict:
    place=next((d for d in catalog["destinations"] if d["id"]==row["id"]),None)
    supplemental=False
    if place is None:
        # The planner explicitly supports validated supplemental choices.
        # They are not in catalog["destinations"] or the rail price matrix.
        place=supplemental_destination(row["id"])
        if place is None:
            raise ValueError("Destino não consta do catálogo de passeios")
        supplemental=True
    lookup={a["id"]:a["name"] for a in catalog["attractions"]
            if a["destination_id"]==row["id"]}
    if supplemental:
        lookup.update({a["id"]:a["name"] for a in place["attractions"]})
    picked=list(row["attractions"])
    # A supplemental destination may have saved attractions but has no
    # verified rail route/ticket price. Never pass it to the strict guide.
    if supplemental or not picked:
        # A confirmed destination without chosen attractions is a legitimate
        # UX77 plan state, not an excursion ready for pricing.
        # Do not invoke build_outing_guide: its 1..5-attraction contract is
        # intentionally strict and must remain unchanged.
        return {
            "id":row["id"],"name":place["name"],"country":place["country"],
            "photo":place.get("photo"),"attractions":[lookup.get(a,a) for a in picked],
            "attraction_count":len(picked),
            "period":row["period"] if row["period"]!=UNASSIGNED else None,
            "dates":list(row["exact_dates"]),
            "organized":bool(row["exact_dates"]) or row["period"]!=UNASSIGNED,
            "transport":("Rota suplementar não verificada; trajeto e retorno a pesquisar"
                         if supplemental else "Trajeto a pesquisar após escolher atrações"),
            "cost":"Custos ainda não calculados; nenhuma tarifa confirmada",
            "cost_complete":False,"reservation_confirmed":False,
            "data_basis":("Destino suplementar: tarifas, duração e transporte não verificados"
                          if supplemental else
                          "Destino escolhido, sem atrações nem reservas confirmadas"),
        }
    guide=build_outing_guide(plan,catalog,routes,row["id"],picked)
    route=guide["route"]
    minutes=guide["train_minutes_one_way"]
    if guide["local"]:
        transport="Passeio local · deslocamento urbano a verificar"
    elif minutes is None:
        transport="Tempo de transporte ainda não documentado"
    else:
        transport=(f"{minutes} min de trem por trecho (referência histórica)"
                   if minutes<60 else
                   f"{minutes//60}h{minutes%60:02d} de trem por trecho (referência histórica)")
    if not guide["local"] and not route["weekend_return_verified"]:
        transport+=" · retorno a confirmar"
    amounts=guide["known_cost"]
    known=[f"€ {amounts['EUR']:.2f}" if amounts["EUR"] else "",
           f"CHF {amounts['CHF']:.2f}" if amounts["CHF"] else ""]
    partial=" / ".join(x for x in known if x)
    cost=("Custo total ainda não confirmado"+
          (f" · parcial conhecido do casal: {partial}" if partial else ""))
    return {
        "id":row["id"],"name":place["name"],"country":place["country"],
        "photo":place.get("photo"),"attractions":[lookup.get(x,x) for x in picked],
        "attraction_count":len(picked),
        "period":row["period"] if row["period"]!=UNASSIGNED else None,
        "dates":list(row["exact_dates"]),"organized":bool(row["exact_dates"]) or
                    row["period"]!=UNASSIGNED,
        "transport":transport,"cost":cost,"cost_complete":False,
        "reservation_confirmed":False,
        "data_basis":"Histórico de 2026; sem disponibilidade ou reserva confirmada para 2027",
    }
