"""Golden parity: original formatting implementations copied from pre-ARCH15B."""
import unittest
from importlib import import_module
from html import escape

VALUES = (0, 1, -1, 1234.56, -9876.125, 1000, None)
def format_minutes(value):
    if value is None:
        return "não informado"
    if type(value) is not int or value < 1:
        raise ValueError("duration invalid")
    return f"{value // 60}h{value % 60:02d}" if value >= 60 else f"{value} min"

FIXTURES = {
    "base_research_expanded_ui": [
        "def _money(amount):\n    return \"Não pesquisado\" if amount is None else \"€ \"+f\"{amount:,.0f}\".replace(\",\",\".\")"
    ],
    "reconciled_trip_ui": [
        "def _money(value:float)->str:\n    return \"R$ \"+f\"{value:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")"
    ],
    "predefined_budget_ui": [
        "def _money(value:float)->str:\n    return \"R$ \"+f\"{value:,.0f}\".replace(\",\", \".\")"
    ],
    "itinerary_flow_ui": [
        "def _money(n:float)->str:\n    return \"R$ \"+f\"{n:,.0f}\".replace(\",\",\".\")"
    ],
    "outing_guide_ui": [
        "def _money(value:float)->str:\n    return \"R$ \"+f\"{value:,.0f}\".replace(\",\",\".\")",
        "def _currency(eur:float,chf:float)->str:\n    return f\"€ {eur:.2f} · CHF {chf:.2f}\""
    ],
    "ux117_review_visual": [
        "def _safe(value):\n    return escape(str(value),quote=True)",
        "def _duration(value):\n    if value is None:\n        return \"Sem tempo\"\n    return format_minutes(value) if value>0 else \"0 min\"",
        "def _money(value):\n    \"\"\"Preserve cent precision when present, using Portuguese separators.\"\"\"\n    formatted=f\"{abs(value):,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")\n    return formatted[:-3] if formatted.endswith(\",00\") else formatted"
    ],
    "scenario_comparison_ui": [
        "def money(value:float)->str:\n    return \"R$ \"+f\"{value:,.0f}\".replace(\",\",\".\")"
    ],
    "active_preset_ui": [
        "def money(value:float)->str:\n    return \"R$ \"+f\"{value:,.0f}\".replace(\",\",\".\")"
    ],
    "research_cost_ui": [
        "def money(v:float)->str:\n    return \"R$ \"+f\"{v:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")"
    ],
    "discovery_ui": [
        "def money(value):\n    return \"R$ \"+f\"{value:,.0f}\".replace(\",\",\".\")"
    ],
    "ux124_city_profile_ui": [
        "def money(value,unit=\"€\"):\n    return (\"Não pesquisado\" if value is None else\n            f\"{value:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")+\" \"+unit)"
    ],
    "city_decision_ui": [
        "def _currency(value:float|None)->str:\n    return \"Não calculável\" if value is None else (\n        \"R$ \"+f\"{value:,.0f}\".replace(\",\",\".\"))"
    ]
}

class FormattingParityTests(unittest.TestCase):
    def test_original_screen_outputs(self):
        for module_name, sources in FIXTURES.items():
            module = import_module(module_name)
            for source in sources:
                name = source.split("(")[0].split()[-1]
                namespace = {"escape": escape, "format_minutes": format_minutes}
                exec(source, namespace)
                old = namespace[name]
                new = getattr(module, name)
                if name == "_duration":
                    args = [(v,) for v in (None, -1, 0, 1, 59, 60, 61)]
                elif name == "_safe":
                    args = [(v,) for v in (None, 0, "<", ">", "&", "'", '"')]
                elif module_name == "outing_guide_ui" and name == "_currency":
                    args = [(v, v) for v in VALUES]
                elif module_name == "ux124_city_profile_ui":
                    args = [(v, unit) for v in VALUES for unit in ("€", "CHF", "R$")]
                else:
                    args = [(v,) for v in VALUES]
                def outcome(fn, arguments):
                    try:
                        return ("return", fn(*arguments))
                    except Exception as exc:
                        return ("raise", type(exc))
                for arguments in args:
                    with self.subTest(module=module_name, name=name, args=arguments):
                        self.assertEqual(outcome(old, arguments), outcome(new, arguments))
