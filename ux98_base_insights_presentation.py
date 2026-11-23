"""Evidence-only pros and cautions for a REC02 candidate.

Presentation projection: never ranks cities, infers cost or mutates data.
Each message has a provenance code from the existing REC02 projection.
"""
from __future__ import annotations

from collections.abc import Mapping

ADVANTAGES = {
    "imperdiveis_identificados": "Há referências ou identificação local para todos os destinos imperdíveis.",
    "comparacao_condicional_disponivel": "Existem trajetos em comum que podem ser comparados, com ressalvas.",
    "menor_minimo_ponderado_no_mesmo_escopo_completo": (
        "Tempos mínimos de ida menores entre bases com o mesmo escopo documentado."
    ),
    "menor_minimo_ponderado_no_mesmo_subconjunto": (
        "Tempos mínimos de ida menores apenas no subconjunto comparável."
    ),
}
CAUTIONS = {
    "imperdiveis_com_evidencia_pendente": "Faltam referências para alguns destinos imperdíveis.",
    "acesso_local_a_verificar": "O acesso local e a última milha ainda precisam ser verificados.",
    "destinos_com_tempo_pendente": "Existem destinos sem tempo de deslocamento pesquisado.",
    "sem_tempo_ou_identificacao_local": "Ainda não há tempos ou acessos locais pesquisados.",
    "alternativa_individual_sem_grupo_completo": "Não há grupo equivalente para uma comparação completa.",
}
RETURN_CAUTION = ("Horários, retorno e custos de 2027 ainda não estão confirmados.")


def project_base_insights(candidate: Mapping) -> dict:
    """Return stable evidence-backed display items without extrapolating."""
    reasons = set(candidate.get("reasons") or [])
    must_visit=candidate.get("must_visit") or {}
    has_must_visit=bool(must_visit.get("known") or must_visit.get("local") or
                        must_visit.get("missing"))
    advantages = [
        {"code": code, "text": label}
        for code, label in ADVANTAGES.items()
        if code in reasons and (code!="imperdiveis_identificados" or has_must_visit)
    ]
    cautions = [
        {"code": code, "text": label}
        for code, label in CAUTIONS.items() if code in reasons
    ]
    if candidate.get("missing_destination_ids") and "destinos_com_tempo_pendente" not in reasons:
        cautions.append({"code": "missing_destination_ids",
                         "text": "Existem destinos sem tempo de deslocamento pesquisado."})
    if candidate.get("local_destination_ids") and "acesso_local_a_verificar" not in reasons:
        cautions.append({"code": "local_destination_ids",
                         "text": "Acesso urbano e última milha precisam ser verificados."})
    cautions.append({"code": "rec02_limitations", "text": RETURN_CAUTION})
    neutral=([{"code": "no_proven_advantage",
               "text": "Ainda não há vantagem comparativa comprovada para este escopo."}]
             if not advantages else [])
    return {"base_id": candidate["base_id"], "advantages": advantages,
            "neutral": neutral, "cautions": cautions}
