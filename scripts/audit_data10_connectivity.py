"""DATA 10: export reproducible 30-base / 46-destination connectivity coverage.

No routes are synthesized, merged or inferred. No private plans are accessed.
Usage: python scripts/audit_data10_connectivity.py --output /tmp/data10-coverage
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from data10_connectivity_model import load_connectivity_references
from rail_gap_coverage_audit_model import build_rail_coverage_inventory

def build_report():
    inventory=build_rail_coverage_inventory()
    source=load_connectivity_references()
    by_base=[]
    for base in inventory["per_base"]:
        rows=[x for x in inventory["pairs"] if x["base_id"]==base["base_id"]]
        data10=sum(x.get("source_dataset")=="data10_connectivity_2026_11"
                   for x in rows)
        by_base.append({
            **base,
            "new_data10_references_shown":data10,
            "timed_or_reference_pairs":base["historical"]+base["indicative"],
        })
    by_dest=[]
    for d in inventory["per_destination"]:
        rows=[x for x in inventory["pairs"] if x["destination_id"]==d["destination_id"]]
        by_dest.append({
            **d,
            "new_data10_references_shown":sum(
                x.get("source_dataset")=="data10_connectivity_2026_11" for x in rows),
        })
    return {
        "scope":"data10_2026_connectivity_and_duration_not_schedules",
        "base_count":inventory["base_count"],
        "destination_count":inventory["destination_count"],
        "total_pairs":inventory["total_pairs"],
        "historical_pairs":inventory["historical_pairs"],
        "indicative_pairs":inventory["indicative_pairs"],
        "local_pairs":inventory["local_pairs"],
        "missing_pairs":inventory["missing_pairs"],
        "data10_sourced_records":len(source["records"]),
        "data10_new_references_shown":sum(
            x["new_data10_references_shown"] for x in by_base),
        "per_base":by_base,
        "per_destination":by_dest,
        "pairs":inventory["pairs"],
        "verified_2027_services":0,
        "synthetic_times":0,
        "user_plan_changed":False,
    }

def report_markdown(result):
    lines=[
        "# DATA 10 — Conexões e tempos aproximados entre bases e destinos",
        "",
        "**Consulta:** 18/11/2026. Mínimos publicados, não tempos típicos garantidos; "
        "nenhuma viagem de 2027 foi validada.",
        "",
        f'- Bases: **{result["base_count"]}**; destinos: **{result["destination_count"]}**; '
        f'pares dirigidos: **{result["total_pairs"]}**',
        f'- Registros DATA10 com fonte: **{result["data10_sourced_records"]}**; '
        f'novas células exibidas após precedência: **{result["data10_new_references_shown"]}**',
        f'- Históricos: **{result["historical_pairs"]}**; indicativos: '
        f'**{result["indicative_pairs"]}**; locais: **{result["local_pairs"]}**; '
        f'sem duração: **{result["missing_pairs"]}**',
        "",
        "## Cobertura das 30 cidades-base",
        "",
        "| Base | Histórico | Indicativo | DATA 10 aplicado | Sem duração |",
        "|---|---:|---:|---:|---:|",
    ]
    for x in result["per_base"]:
        lines.append(f'| {x["base_name"]} | {x["historical"]} | {x["indicative"]} | '
                     f'{x["new_data10_references_shown"]} | {x["missing"]} |')
    lines+=["","## Destinos com maior ausência de tempos", "",
            "| Destino | Bases sem duração | Novas referências DATA 10 |",
            "|---|---:|---:|"]
    for x in sorted(result["per_destination"],key=lambda z:(-z["missing_bases"],z["destination_id"])):
        lines.append(f'| {x["destination_name"]} | {x["missing_bases"]} | '
                     f'{x["new_data10_references_shown"]} |')
    lines+=["","## Interpretação e próximas pesquisas","",
            "- Uma rota ferroviária com duração publicada é **referência de conectividade**, "
            "não confirmação de trem na data da viagem.",
            "- O retorno não é inferido da ida; sentido inverso só aparece com fonte independente.",
            "- As fontes de operadoras prevalecem, e referências Trainline são secundárias.",
            "- Pares sem duração permanecem desconhecidos; isso não significa inacessíveis.",
            "- Para ampliar a cobertura, consultar fontes oficiais e adicionar apenas "
            "tempos positivos e citações individuais, sem estimar distância por mapa.",
            "- Quando houver interesse em bate-voltas, investigar depois horário, retorno, "
            "transferências, estação, última milha e bilhetes para duas pessoas.",
            ""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("/tmp/data10-coverage"))
    args=p.parse_args()
    report=build_report()
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"coverage.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (args.output/"coverage.md").write_text(report_markdown(report),encoding="utf-8")
    with (args.output/"unresearched_pairs.csv").open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=["base_id","base_name",
                        "destination_id","destination_name","category"])
        writer.writeheader()
        for row in report["pairs"]:
            if row["category"]=="missing":
                writer.writerow({k:row[k] for k in writer.fieldnames})
    print(json.dumps({k:report[k] for k in (
        "base_count","destination_count","total_pairs","historical_pairs",
        "indicative_pairs","local_pairs","missing_pairs","data10_sourced_records",
        "data10_new_references_shown")},sort_keys=True))

if __name__=="__main__":
    main()
