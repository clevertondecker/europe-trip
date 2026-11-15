"""Fail closed before uploading a travel plan to the *public* GitHub branch.

This guard prevents accidental extra fields/secrets; it does not make a public
repository private, hide travel dates, or erase historical commits.
"""
from __future__ import annotations

import json
import re

PUBLIC_SCHEMA_V1_FIELDS=frozenset({
    "schema_version","plan_id","revision","base_city","departure_date",
    "total_days","italy_days","vacation_days","setup_days","budget_scenario",
    "profile","mandatory_destinations","excluded_destinations","packages",
    "assignments","preferences","accepted_recommendations",
    "rejected_recommendations","source_versions","flexible_visits",
})
EMAIL_PATTERN=re.compile(r"(?i)[\w.+%-]+@[\w.-]+\.[a-z]{2,}")


def ensure_public_plan_is_minimal(plan:dict)->None:
    """Never silently remove fields from a user's plan during serialization."""
    unexpected=set(plan)-PUBLIC_SCHEMA_V1_FIELDS
    if unexpected:
        raise ValueError("O plano contém campos extras não permitidos em GitHub público. "
                         "Exporte uma cópia local e remova dados pessoais antes de salvar.")
    serialized=json.dumps(plan,ensure_ascii=False)
    if EMAIL_PATTERN.search(serialized):
        raise ValueError("O plano contém endereço de e-mail; não é seguro gravá-lo "
                         "em um repositório público.")
