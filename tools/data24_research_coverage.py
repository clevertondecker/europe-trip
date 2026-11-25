"""Generate a deterministic, offline report and a complete source-traceable annex."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data24_audit_model import build_audit

REPORT = ROOT / "docs/audits/data24_research_coverage.md"
ANNEX = REPORT.with_suffix(".json")


def input_manifest(audit):
    """Fingerprint the actual public projection, not unrelated repository files.

    Source provenance and dates remain in the records. A content fingerprint
    intentionally stays unchanged when unrelated implementation code changes.
    """
    return {"audit_sha256": hashlib.sha256(json.dumps(
        audit, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()}


def coverage_line(name, c):
    rate = "N/A (0/0)" if c["fraction"] is None else f'{c["fraction"]:.1%}'
    return (f'| {name} | {c["total"]} | {c["historical"]} | {c["indicative"]} | '
            f'{c["local"]} | {c["missing"]} | {c["timed"]}/{c["eligible"]} · {rate} |')


def render_report(audit, manifest=None):
    a = audit["attractions"]["counts"]
    legacy = audit["legacy_summary"]
    pairs = audit["rail_pairs"]
    eligible = audit["rail_counts"]["eligible"]
    lines = [
        "# DATA24 — Cobertura documental de pesquisa",
        "",
        "Relatório gerado offline a partir dos dados públicos versionados. "
        "Não é ranking, cotação ou confirmação de viabilidade para 2027.",
        "",
        f"Versão do esquema: {audit['schema_version']}.",
        "",
        "## Universo ferroviário — pares dirigidos",
        "",
        f"{len(audit['base_ids'])} bases × {len(audit['destination_ids'])} destinos. "
        "Pares locais não entram no denominador de tempos; acesso urbano permanece pendente. "
        "Tempos históricos e indicativos não provam retorno.",
        "",
        "| Universo | Pares | Histórico | Indicativo | Local | Sem tempo | Cobertura |",
        "|---|---:|---:|---:|---:|---:|---:|",
        coverage_line("Global", audit["rail_counts"]),
        "",
        "### Por origem",
        "",
        "| Origem | Pares | Histórico | Indicativo | Local | Sem tempo | Cobertura |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(coverage_line(k, v) for k, v in sorted(audit["rail_by_base"].items()))
    lines.extend(["", "### Por destino", "",
                  "| Destino | Pares | Histórico | Indicativo | Local | Sem tempo | Cobertura |",
                  "|---|---:|---:|---:|---:|---:|---:|"])
    lines.extend(coverage_line(k, v) for k, v in sorted(audit["rail_by_destination"].items()))
    lines.extend(["", "### Evidências adicionais — denominador: pares não locais", ""])
    nonlocal_pairs = [p for p in pairs if p["category"] != "local"]
    for label, predicate in (
        ("Tempo típico histórico", lambda p: p["typical_min"] is not None),
        ("Tarifa de ida observada (não tarifa normal de 2027)", lambda p: bool(p["fare_observations"])),
        ("Transferências documentadas na observação principal", lambda p: p["transfers"] is not None),
        ("Variação histórica a reconciliar", lambda p: p["variation_status"] != "not_observed"),
        ("Contradição confirmada pelo contrato", lambda p: p["contradiction_confirmed"]),
        ("Retorno 2027 verificado", lambda p: p["return_2027_verified"]),
        ("Porta a porta completo", lambda p: p["full_door_to_door_min"] is not None),
    ):
        lines.append(f"- {label}: {sum(bool(predicate(p)) for p in nonlocal_pairs)}/{eligible}."
                     if eligible else f"- {label}: N/A (0/0).")
    lines.extend(["", "### Lacunas de tempo por origem (não implica ausência de conexão)", ""])
    for base in sorted(audit["base_ids"]):
        missing = [p["destination_id"] for p in pairs
                   if p["base_id"] == base and p["category"] == "no_time"]
        lines.append(f"- **{base}** ({len(missing)}): " + (", ".join(missing) or "nenhuma"))
    lines.extend(["", "## Destinos e atrações — universos distintos", "",
                  "| Indicador | Documentado | Denominador |", "|---|---:|---:|"])
    for label, key, denominator in (
        ("Destinos com atrações", "destinations_with_attractions", "destinations"),
        ("Destinos com foto atribuída", "destinations_with_attributed_photo", "destinations"),
        ("Atrações com descrição", "described", "attractions"),
        ("Atrações com duração editorial", "editorial_duration", "attractions"),
        ("Ingresso com preço e modalidade", "ticket_published", "attractions"),
        ("Ingresso não aplicável", "ticket_not_applicable", "attractions"),
        ("Ingresso desconhecido", "ticket_unknown", "attractions"),
        ("Atrações com foto própria atribuída", "attraction_photo_attributed", "attractions"),
        ("Atrações com acesso de estação documentado", "station_access_documented", "attractions"),
    ):
        lines.append(f"| {label} | {a[key]} | {a[denominator]} |")
    lines.extend(["", f"Aliases reconciliados (não atrações adicionais): {a['reconciled_aliases']}.",
                  "Fotos contextuais de destinos não contam como fotos de atrações. "
                  "Atribuição documentada não implica verificação online da imagem.",
                  "", "### Atrações por destino", "",
                  "| Destino | Atrações únicas | Foto contextual atribuída |",
                  "|---|---:|---|"])
    for d in sorted(audit["attractions"]["destinations"], key=lambda d: d["id"]):
        lines.append(f"| {d['id']} | {d['attractions']} | {'Sim' if d['photo_attributed'] else 'Não documentada'} |")
    lines.extend(["", "## Inventário histórico preservado — recorte original, não cobertura global",
                  "", f"{legacy['cities']} cidades; {legacy['shortlist']} finalistas no estudo histórico; "
                  f"{legacy['housing_documented']} com moradia pesquisada; "
                  f"{legacy['rail_documented']} com tempos na cesta original.",
                  "", "A cesta DQ31 é histórica, não a wishlist nem o recorte oficial D-004.",
                  "", "| Cidade | Amostra moradia | Tempos da cesta | Tarifas da cesta |",
                  "|---|---:|---:|---:|"])
    for r in audit["legacy_evidence"]:
        n = r["route_basket_total"]
        lines.append(f"| {r['id']} | {r['housing']['count']} | {r['route_basket_with_time']}/{n} | "
                     f"{r['route_basket_with_fare']}/{n} |")
    lines.extend(["", "## Anexo técnico e rastreabilidade", "",
                  "O anexo JSON gerado pela mesma execução mantém os registros completos: "
                  "pares, fontes, datas, observações e variações; atrações com IDs, aliases, "
                  "ingressos, fotos e acesso; evidências históricas por cidade, requisitos, "
                  "valores, unidades, limitações, moradia e DQ31 (todos os destinos da cesta).",
                  "", "Prioridades de pesquisa, sem ranking: completar tempos ausentes relevantes "
                  "à decisão; reconciliar variações; pesquisar retornos, tarifas equivalentes "
                  "e última milha; completar descrições, durações, ingressos e fotos. "
                  "DATA24C+D+E aprofundará o recorte D-004; esta seção histórica não o substitui.",
                  "", "## Reprodução", "",
                  "```sh", "python tools/data24_research_coverage.py",
                  "python tools/data24_research_coverage.py --check", "```", "",
                  "A execução grava o Markdown e o anexo JSON completo sob demanda. "
                  "--check verifica o Markdown versionado e o anexo histórico compacto; "
                  "--check-annex exige também o JSON completo gerado localmente. "
                  "O anexo completo não é necessário em um checkout limpo. "
                  "Nenhuma chamada de rede ou estado privado é necessário.", "",
                  "### Migração do painel anterior", "",
                  "| Campo anterior | Destino no anexo/relatório |", "|---|---|",
                  "| Matriz de evidências por cidade | legacy_evidence[].criteria e status |",
                  "| Moradia: contagem, mínimo, máximo, mediana | legacy_evidence[].housing |",
                  "| Cesta histórica: tempos, tarifas, países | legacy_evidence[].route_basket_* e international_countries_with_time |",
                  "| Requisitos, checks e scoring_gap | legacy_evidence[].criteria |",
                  "| Indicador, valor, unidade, observação, escopo, tipo, fonte e limite | legacy_evidence[].evidence |",
                  "| DQ31: ida, retorno, última milha e bloqueios | legacy_dq31.rows[].routes e missing |",
                  "| DQ32: atrações, aliases e cobertura | attractions e rail_counts (universo atual explícito) |",
                  "| Ficha Conhecer cidade | UX124, sem duplicar a ficha |",
                  "", "Evidências históricas consultáveis sem executar código: "
                  "[anexo histórico compacto](data24_legacy_evidence.json)."])

    return "\n".join(lines) + "\n"


def render_annex(audit, manifest=None):
    return json.dumps({"inputs": input_manifest(audit) if manifest is None else manifest, **audit}, ensure_ascii=False,
                      sort_keys=True, indent=2, allow_nan=False) + "\n"


def render_legacy_annex(audit):
    """Only migrated exclusive records; do not duplicate the global pair matrix."""
    return json.dumps({key: audit[key] for key in
                       ("schema_version", "legacy_summary", "legacy_evidence", "legacy_dq31",
                        "dq32_reconciled_aliases")},
                      ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verificar os artefatos versionados")
    parser.add_argument("--check-annex", action="store_true", help="Verificar também o anexo completo gerado localmente")
    parser.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args(argv)
    start = perf_counter()
    audit = build_audit()
    legacy_path = args.output.with_name("data24_legacy_evidence.json")
    files = {args.output: render_report(audit),
             legacy_path: render_legacy_annex(audit)}
    if not (args.check or args.check_annex) or args.check_annex:
        files[args.output.with_suffix(".json")] = render_annex(audit)
    if args.check or args.check_annex:
        stale = [str(p) for p, content in files.items()
                 if not p.is_file() or p.read_bytes() != content.encode("utf-8")]
        if stale:
            print("Desatualizado: " + ", ".join(stale), file=sys.stderr)
            return 1
    else:
        for p, content in files.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode("utf-8"))
    print(f"DATA24: {len(audit['rail_pairs'])} pares, "
          f"{audit['attractions']['counts']['attractions']} atrações; "
          f"uma projeção global; {perf_counter()-start:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
