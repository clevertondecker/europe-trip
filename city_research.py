"""Quality gates and evidence/provenance model for French base-city research.

Audit data is separate from editorial ranking data; it does not re-score cities.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

AUDIT_FILE = Path(__file__).resolve().parent / "data" / "city_research_audit_2026.json"
REQUIRED_FIELDS = ("id", "name", "historic_score", "historic_reference_rent_eur",
                   "alternative_logistics_rent_eur", "housing_samples_2026",
                   "eligible_2027_quotes", "audit_status", "completed_gates",
                   "pending_gates", "housing", "transport", "urban", "cost",
                   "source_urls", "risks")

def validate_audit(payload: dict[str, Any]) -> None:
    standards = payload["standards"]
    gate_ids = [x["id"] for x in standards]
    if len(gate_ids) < 8 or len(set(gate_ids)) != len(gate_ids):
        raise ValueError("Padrão de auditoria incompleto ou duplicado")
    if any(not s.get("label") or not s.get("gate") for s in standards):
        raise ValueError("Cada critério requer título e evidências mínimas")
    city_ids = set()
    for city in payload["cities"]:
        missing = set(REQUIRED_FIELDS) - set(city)
        if missing:
            raise ValueError(f"Cidade sem campos obrigatórios: {sorted(missing)}")
        if not city["id"] or city["id"] in city_ids:
            raise ValueError("Identificador de cidade duplicado ou vazio")
        city_ids.add(city["id"])
        if not 0 <= city["historic_score"] <= 5:
            raise ValueError("Nota editorial fora de 0 a 5")
        if not isinstance(city["source_urls"], list) or not city["source_urls"]:
            raise ValueError("Cidade sem fontes rastreáveis")
        if not all(isinstance(url, str) and url.startswith("https://") for url in city["source_urls"]):
            raise ValueError("URLs de fontes inválidas")
        completed = set(city["completed_gates"])
        pending = set(city["pending_gates"])
        if completed.intersection(pending) or completed.union(pending) != set(gate_ids):
            raise ValueError("Gates devem ser completos, sem omissões ou sobreposição")
        if city["eligible_2027_quotes"] < 3 and city["audit_status"] == "decision_ready":
            raise ValueError("Não classificar cidade pronta sem 3 ofertas elegíveis comprovadas")
        if city["audit_status"] == "decision_ready" and pending:
            raise ValueError("Não declarar cidade pronta com requisitos pendentes")
        if city["audit_status"] not in {"insufficient", "preliminary", "decision_ready"}:
            raise ValueError("Status de auditoria desconhecido")
        for key in ("housing", "transport", "urban", "cost", "risks"):
            if not city[key] or not all(str(item).strip() for item in city[key]):
                raise ValueError(f"Dados de {key} incompletos em {city['name']}")

def load_audit(path: Path = AUDIT_FILE) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_audit(payload)
    return payload

def city_readiness(city: dict[str, Any]) -> dict[str, Any]:
    total = len(city["completed_gates"]) + len(city["pending_gates"])
    completed = len(city["completed_gates"])
    return {"completed": completed, "total": total,
            "eligible_quotes": city["eligible_2027_quotes"],
            "decision_ready": city["audit_status"] == "decision_ready" and completed == total and city["eligible_2027_quotes"] >= 3}
