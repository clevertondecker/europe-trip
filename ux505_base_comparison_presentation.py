"""Read-only, presentation-only interpretations of UX 5.0.3 comparisons.

This module never decides which city-base is better; coverage is not a score.
"""
from __future__ import annotations


def comparison_overview(result: dict) -> dict:
    """Count every selected base × visible destination exactly once."""
    rows = result["rows"]
    documented = sum(row["minimum_oneway_min"] is not None for row in rows)
    local = sum(row["evidence_status"] == "local" for row in rows)
    missing = len(rows) - documented - local
    # Keep the distinction: no evidence != a demonstrated absent connection.
    return {"total": len(rows), "documented": documented, "missing": missing,
            "local": local,
            "description": (
                f"Das {len(rows)} combinações analisadas, {documented} possuem "
                "tempo histórico de ida pesquisado. "
                "Ainda não temos informações suficientes para concluir "
                "qual cidade-base oferece a melhor logística."
                if documented else
                f"Nenhuma das {len(rows)} combinações possui tempo histórico "
                "de ida pesquisado. Isso não significa ausência de conexão "
                "ferroviária. Ainda não podemos comparar com segurança."
            )}


def matrix_cell(row: dict) -> str:
    """Present known times without converting unknown or local travel to zero."""
    minimum = row["minimum_oneway_min"]
    if row["evidence_status"] == "local":
        value = "Local — acesso a verificar"
    elif minimum is not None:
        value = f"{minimum} min · ida histórica"
    elif row["observations"]:
        value = "Pesquisa parcial · tempo não identificado"
    else:
        value = "Tempo não pesquisado"
    if row["divergent_sources"]:
        value += " · tempos publicados diferentes"
    return value


def known_findings(result: dict) -> list[str]:
    """Describe known observations; never rank bases by documentary coverage."""
    if not result["rows"]:
        return ["Selecione destinos para visualizar as evidências disponíveis."]
    findings = []
    for summary in result["summaries"]:
        known = [row for row in result["rows"] if
                 row["base_id"] == summary["base_id"] and
                 row["minimum_oneway_min"] is not None]
        if known:
            # Rows retain the order and priority of the common wishlist basket.
            details = ", ".join(
                f'{row["destination_name"]} ({row["minimum_oneway_min"]} min)'
                for row in known
            )
            findings.append(
                f'{summary["base_name"]}: tempos históricos pesquisados '
                f'para {details}.'
            )
        else:
            findings.append(
                f'{summary["base_name"]}: ainda sem tempos históricos de ida '
                'para os destinos exibidos.'
            )
    findings.append(
        "Esses registros mostram o que já pesquisamos, não qual cidade-base "
        "tem a melhor logística. Faltam retornos, última milha e condições "
        "comparáveis para uma decisão segura."
    )
    return findings


def missing_research(result: dict) -> list[str]:
    """Consolidate recurring limitations without losing divergence/local flags."""
    rows = result["rows"]
    pending = []
    unknown = [r for r in rows if r["minimum_oneway_min"] is None
               and r["evidence_status"] != "local"]
    if unknown:
        pending.append(
            f"Pesquisar tempos históricos de ida para {len(unknown)} "
            "combinação(ões) de cidade-base e destino sem tempo cadastrado."
        )
    if any(r["evidence_status"] == "local" for r in rows):
        pending.append("Verificar transporte urbano e acesso local nos destinos "
                       "situados na própria cidade-base.")
    if any(r["divergent_sources"] for r in rows):
        pending.append("Conferir condições das observações com tempos publicados diferentes.")
    pending.extend([
        "Confirmar possibilidades de retorno nos fins de semana e última milha.",
        "Comparar moradia mobiliada, disponibilidade e custos em condições "
        "equivalentes para 2027.",
    ])
    return pending
