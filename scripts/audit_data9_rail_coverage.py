"""Export evidence-only coverage and priority backlog without changing source data.

Usage:
  python scripts/audit_data9_rail_coverage.py --output /tmp/data9-coverage
Outputs JSON (all pairs) and Markdown (top missing destinations / 30 bases).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rail_gap_coverage_audit_model import (
    build_rail_coverage_inventory, research_backlog, audit_summary,
    component_research_backlog, component_gap_summary,
)


def render_markdown(inventory):
    lines = [
        "# DATA 9.1 — Lacunas ferroviárias entre as bases e os destinos cadastrados",
        "",
        "**Snapshot de fontes:** pesquisa histórica até 18/11/2026; "
        "não comprova horários nem preços de 2027.",
        "",
        "| Indicador | Quantidade |",
        "|---|---:|",
    ]
    for label, key in (
        ("Cidades-base", "base_count"),("Destinos", "destination_count"),
        ("Pares possíveis", "total_pairs"),("Tempos históricos", "historical_pairs"),
        ("Referências indicativas", "indicative_pairs"),
        ("Deslocamentos locais", "local_pairs"),("Ainda sem tempo", "missing_pairs"),
    ):
        lines.append(f"| {label} | {inventory[key]} |")
    lines += [
        "", "## Destinos com maior número de origens sem tempo de ida",
        "", "| Destino | País | Bases sem tempo | Históricos | Indicativos |",
        "|---|---|---:|---:|---:|",
    ]
    for r in inventory["per_destination"]:
        lines.append(
            f'| {r["destination_name"]} | {r["country"]} | '
            f'{r["missing_bases"]} | {r["historical_bases"]} | '
            f'{r["indicative_bases"]} |')
    lines += [
        "", "## Pendências por cidade-base",
        "", "| Base | Histórico | Indicativo | Local | Sem tempo |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in inventory["per_base"]:
        lines.append(f'| {r["base_name"]} | {r["historical"]} | '
                     f'{r["indicative"]} | {r["local"]} | {r["missing"]} |')
    lines += [
        "", "## Priorização e contratos",
        "",
        "Para cada par ausente, pesquisar fontes oficiais e registrar origem, destino, "
        "estação, duração de ida, data da consulta e escopo da referência. "
        "Retorno de fim de semana, frequência, tarifa para dois adultos, "
        "última milha e viabilidade em 2027 devem permanecer como pendências "
        "independentes até documentação específica.",
        "",
        "A ausência de tempo **não significa** falta de conexão. Referências "
        "secundárias nunca são rotas de ida e volta verificadas.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("/tmp/data9-coverage"))
    args=parser.parse_args()
    result=build_rail_coverage_inventory()
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"inventory.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (args.output/"backlog.json").write_text(
        json.dumps(research_backlog(result),ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    all_components = component_research_backlog(result)
    components_summary = component_gap_summary(all_components)
    (args.output/"component_backlog.json").write_text(
        json.dumps(all_components,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    (args.output/"component_summary.json").write_text(
        json.dumps(components_summary,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    (args.output/"summary.md").write_text(
        render_markdown(result),encoding="utf-8")
    # Preserve the existing stdout contract consumed by tests and scripts.
    print(json.dumps(audit_summary(result),ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
