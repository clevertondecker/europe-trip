#!/usr/bin/env python3
"""Reproducible, read-only gap inventory using the app's canonical evidence adapter.

Do NOT infer door-to-door times, train connectivity, 2027 timetables or fares.
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path
from base_research_expanded_model import load_research
from base_explorer_model import load_exploration
from rail_evidence_unified_model import load_rail_evidence
from evidence_query_model import get_rail_evidence
from ux501_destination_discovery_model import build_destination_discovery
from dq30_mobility_evidence_model import load_mobility_pilot

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs"/"audits"/"2026-11-17-rail-attraction-gaps"


def write_csv(filename,records):
    if not records:
        raise ValueError("Empty audit table: "+filename)
    path=OUT/filename
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    research=load_research()
    discovery=build_destination_discovery()
    pilot=load_mobility_pilot()
    rail=load_rail_evidence()
    explorer=load_exploration()
    bases=research["cities"]
    destinations=discovery["destinations"]
    canonical=json.loads((ROOT/"data"/"attractions_2027.json").read_text(encoding="utf-8"))
    original={x["id"]:x for x in canonical["attractions"]}
    urban={x["attraction_id"]:x for x in pilot["attraction_access"]}
    OUT.mkdir(parents=True,exist_ok=True)

    attractions=[]
    for d in destinations:
        for a in d["attractions"]:
            base_a=original.get(a["id"],{})
            access=urban.get(a["id"],{})
            attractions.append({
                "attraction_id":a["id"],
                "attraction_name":a["name"],
                "destination_id":d["id"],
                "destination_name":d["name"],
                "source_kind":a["kind"],
                "tourism_source_url":a["source_url"],
                "public_access_address":access.get("public_access_point"),
                "urban_stop_if_researched":access.get("urban_stop"),
                "urban_mode_if_researched":access.get("urban_mode"),
                "station_to_attraction_minutes":access.get("walk_duration_min"),
                "attraction_coordinates_verified":base_a.get("coordinates") is not None,
                "visit_duration_editorial_minutes_not_travel":base_a.get("visit_minutes"),
                "missing_access":(
                    "arrival_station|walking_or_urban_transfer_minutes|"
                    "door_to_door_time|2027_access_conditions"
                )
            })
    rail_rows=[]
    base_rows=[]
    by_attraction=[]
    for base in bases:
        base_pairs=[]
        for d in destinations:
            ev=get_rail_evidence(base["id"],d["id"],rail=rail,exploration=explorer)
            observations=ev["observations"]
            times={o["minimum_oneway_min"] for o in observations
                   if type(o.get("minimum_oneway_min")) is int and
                   o["minimum_oneway_min"]>0}
            primary=next((o for o in observations
                          if o.get("source_url")==ev["source_url"] and
                          o.get("minimum_oneway_min")==ev["minimum_oneway_min"]),{})
            status=ev["status"]
            missing=["station_to_attraction_minutes",
                     "accommodation_to_station_minutes",
                     "2027_weekend_outbound","2027_weekend_return",
                     "2027_normal_fare"]
            if status=="local":
                missing.insert(0,"local_urban_access")
            elif status!="historical_time":
                missing.insert(0,"sourced_historical_train_duration")
            else:
                if ev["typical_oneway_min"] is None:
                    missing.append("typical_comparable_train_duration")
                if primary.get("transfers") is None:
                    missing.append("transfer_count")
            if len(times)>1:
                missing.append("reconcile_divergent_sources")
            row={
                "base_id":base["id"],"base_name":base["name"],
                "base_country":base["country"],"base_shortlist":base["shortlist"],
                "destination_id":d["id"],"destination_name":d["name"],
                "destination_country":d["country"],
                "attraction_count":d["attraction_count"],
                "rail_status":status,
                "historical_train_oneway_min":ev["minimum_oneway_min"],
                "historical_typical_oneway_min":ev["typical_oneway_min"],
                "transfers":primary.get("transfers"),
                "source_url":ev["source_url"],
                "source_date":ev["source_date"],
                "source_dataset":ev["source_dataset"],
                "observation_count":len(observations),
                "divergent_historical_times":len(times)>1,
                "weekend_return_2027_confirmed":False,
                "complete_door_to_door_minutes":None,
                "missing_fields":"|".join(missing)
            }
            rail_rows.append(row)
            base_pairs.append(row)
            for a in d["attractions"]:
                access=urban.get(a["id"],{})
                by_attraction.append({
                    "base_id":base["id"],"base_name":base["name"],
                    "destination_id":d["id"],"destination_name":d["name"],
                    "attraction_id":a["id"],"attraction_name":a["name"],
                    "rail_status":status,
                    "historical_station_to_station_oneway_min":
                        ev["minimum_oneway_min"],
                    "rail_source_url":ev["source_url"],
                    "attraction_access_reference_available":bool(access),
                    "verified_station_to_attraction_minutes":
                        access.get("walk_duration_min"),
                    "verified_base_to_attraction_total_minutes":None,
                    "missing_fields":(
                        "station_to_attraction_minutes|"
                        "accommodation_to_station_minutes|"
                        "2027_weekend_return|2027_normal_fare" +
                        ("|sourced_train_minutes" if status not in
                         ("historical_time","local") else "")
                    )
                })
        housing=base["housing_offers"]
        counter=Counter(x["rail_status"] for x in base_pairs)
        base_rows.append({
            "base_id":base["id"],"base_name":base["name"],
            "country":base["country"],"shortlist":base["shortlist"],
            "known_rail_times":counter["historical_time"],
            "partial_no_time":counter["partial"],
            "not_researched":counter["not_researched"],
            "local_access_pending":counter["local"],
            "historical_sources_divergent":sum(
                x["divergent_historical_times"] for x in base_pairs),
            "historical_rental_offers":len(housing),
            "verified_2027_short_stay_rentals":base["eligible_2027_quotes"],
            "rental_station_distance_verified":sum(
                x.get("near_station_verified") is True for x in housing)
        })
    assert len(bases)==30 and len(destinations)==46
    assert len(attractions)==sum(d["attraction_count"] for d in destinations)
    assert len(rail_rows)==1380
    assert len(by_attraction)==len(bases)*len(attractions)
    assert all(x["verified_base_to_attraction_total_minutes"] is None
               for x in by_attraction)

    write_csv("city_base_destination_matrix.csv",rail_rows)
    write_csv("city_base_summary.csv",base_rows)
    write_csv("attraction_access_gaps.csv",attractions)
    write_csv("city_base_attraction_matrix.csv",by_attraction)

    totals=Counter(x["rail_status"] for x in rail_rows)
    summary={
        "date":"2026-11-17",
        "scope":"Existing source registry and historical 2026 observations, no external route lookup",
        "city_bases":len(bases),
        "destinations":len(destinations),
        "distinct_attractions":len(attractions),
        "base_destination_pairs":len(rail_rows),
        "base_attraction_pairs":len(by_attraction),
        "rail_status_counts":dict(totals),
        "divergent_sources_pairs":sum(x["divergent_historical_times"] for x in rail_rows),
        "historical_typical_time_pairs":sum(
            x["historical_typical_oneway_min"] is not None for x in rail_rows),
        "historical_transfer_count_pairs":sum(x["transfers"] is not None for x in rail_rows),
        "canon_attractions_with_access_reference":sum(
            bool(x["public_access_address"]) for x in attractions),
        "canon_attractions_with_station_walk_minutes":sum(
            x["station_to_attraction_minutes"] is not None for x in attractions),
        "base_to_attraction_verified_total_minutes":0,
        "historic_rental_observations":sum(x["historical_rental_offers"] for x in base_rows),
        "rentals_verified_for_2027":sum(x["verified_2027_short_stay_rentals"] for x in base_rows),
        "complete_2027_weekend_returns":0,
        "secondary_note":"Musée Unterlinden, Colmar: 15-min station walk from museum source, but not a canonical catalog attraction.",
        "read_only":True
    }
    (OUT/"summary.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=[
        "# Mapeamento de lacunas de logística e atrações",
        "",
        "Auditoria do estado atual do catálogo (17/11/2026). "
        "Não houve consulta nova a operadores.",
        "",
        f"**{len(bases)} cidades-base × {len(destinations)} destinos = {len(rail_rows)} pares.**",
        f"**{len(attractions)} atrações distintas; {len(by_attraction)} combinações base × atração.**",
        "",
        "| Estado | Quantidade |",
        "|---|---:|",
        f"| Tempo histórico de ida cadastrado | {totals['historical_time']} |",
        f"| Pesquisa parcial sem tempo | {totals['partial']} |",
        f"| Sem pesquisa ferroviária cadastrada | {totals['not_researched']} |",
        f"| Deslocamento local, tempo desconhecido | {totals['local']} |",
        "",
        "A cobertura não significa qualidade logística. Nenhuma atração tem "
        "tempo porta a porta verificável desde uma cidade-base. "
        "Todos os retornos completos de 2027 continuam pendentes.",
        "",
        "## Situação por cidade-base",
        "",
        "| Base | Ida histórica | Parcial | Sem pesquisa | Local | Aluguéis históricos | Cotações 2027 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for b in base_rows:
        lines.append(
            f"| {b['base_name']} | {b['known_rail_times']} | {b['partial_no_time']} "
            f"| {b['not_researched']} | {b['local_access_pending']} "
            f"| {b['historical_rental_offers']} | "
            f"{b['verified_2027_short_stay_rentals']} |"
        )
    lines.extend([
        "",
        "## Dados exportados",
        "",
        "- city_base_destination_matrix.csv: todos os 1.380 pares; status, duração "
        "histórica e fonte, divergência, transferências e lacunas.",
        "- city_base_attraction_matrix.csv: todas as combinações de base e atração; "
        "tempo ferroviário só quando documentado, nunca tempo até a porta.",
        "- attraction_access_gaps.csv: todas as atrações, acesso urbano e fontes.",
        "- city_base_summary.csv: todas as 30 bases com indicadores de cobertura.",
        "- summary.json: estatísticas e proveniência da auditoria.",
        "",
        "## Limitações",
        "",
        "Tempo histórico de trem é estação a estação, não duração até museu ou "
        "monumento. Falta de evidência não prova inexistência de conexão. "
        "Os dados de 2026 não confirmam serviços, preços, horários, retorno "
        "ou aluguel para setembro–novembro de 2027. "
        "Nunca somar zero ou duração editorial de visita como deslocamento.",
        "",
        "A referência de 15 minutos até o Musée Unterlinden, em Colmar, "
        "é um caso isolado fora da lista canônica e não pode ser "
        "generalizada para as demais atrações.",
        "",
        "## Próxima pesquisa",
        "",
        "Priorizar as cidades-base que o usuário está comparando e a cesta de "
        "destinos marcados como desejados; procurar operadoras oficiais, "
        "serviços de retorno de sábado/domingo, destino ferroviário preciso, "
        "transporte urbano e acesso a cada atração. Sem ranking automático.",
        "",
    ])
    (OUT/"README.md").write_text("\n".join(lines),encoding="utf-8")
    print("COVERAGE_AUDIT="+json.dumps(summary,ensure_ascii=False))


if __name__=="__main__":
    main()
