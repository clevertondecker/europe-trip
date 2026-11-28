"""Golden parity: original formatting implementations copied from pre-ARCH15B."""
import unittest
from importlib import import_module
from html import escape

VALUES = (0, 1, -1, 1234.56, -9876.125, 1000, None, float('nan'), True, 'text')
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
    ],
    "scenario_board_ui": [
        "def _currency(eur:float,chf:float)->str:\n    return f\"€ {eur:,.2f}  ·  CHF {chf:,.2f}\""
    ],
    "base_explorer_ui": [
        "def _format_eur(value:float)->str:\n    return \"€ \"+f\"{value:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")"
    ],
    "data_model": [
        "def money_brl(value: float | int) -> str:\n    return \"R$ \" + f\"{value:,.2f}\".replace(\",\", \"_\").replace(\".\", \",\").replace(\"_\", \".\")"
    ],
    "ux41_favorites_ui": [
        "def _currency(value):\n    return \"Não pesquisado\" if value is None else \"€ \"+f\"{value:,.0f}\".replace(\",\",\".\")"
    ],
    "dq21_comparison_ui": [
        "def _duration(minutes):\n    return \"Não documentado\" if minutes is None else f\"{minutes//60}h{minutes%60:02d}\""
    ],
    "rail_reference_projection_model": [
        "def format_minutes(value):\n    if value is None:\n        return \"não informado\"\n    if type(value) is not int or value < 1:\n        raise ValueError(\"duration invalid\")\n    return f\"{value // 60}h{value % 60:02d}\" if value >= 60 else f\"{value} min\""
    ],
    "ux96_comparison_visual_ui": [
        "def _safe(value) -> str:\n    return escape(str(value), quote=True)"
    ],
    "ux97_comparison_visual_ui": [
        "def _safe(value) -> str:\n    return escape(str(value),quote=True)"
    ],
    "ux99_base_cards_presentation": [
        "def _safe(value) -> str:\n    return escape(str(value), quote=True)"
    ],
    "ux100_base_card_photos": [
        "def _safe(value) -> str:\n    return escape(str(value), quote=True)"
    ],
    "ux_shared_ui_presentation": [
        "def _safe(value: object) -> str:\n    \"\"\"Escape text AND attribute data, including quotation marks.\"\"\"\n    return escape(str(value), quote=True)"
    ],
    "italy_honeymoon_ui": [
        "def _eur(value:float)->str:\n    return \"€ \"+f\"{value:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")"
    ],
    "five_base_comparison_ui": [
        "def _eur(v)->str:\n    return \"Não cotado\" if v is None else \"€ \"+f\"{v:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")"
    ],
    "ux124b_profile_presentation": [
        "def compact_money(value):\n    if value is None:\n        return \"Não pesquisado\"\n    text=f\"{value:,.2f}\".replace(\",\",\"_\").replace(\".\",\",\").replace(\"_\",\".\")\n    return \"€ \"+(text[:-3] if text.endswith(\",00\") else text)"
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
                if name in ("_duration", "format_minutes"):
                    args = [(v,) for v in (None, -1, -61, 0, 1, 59, 60, 61, 1.5, True, "text", float("nan"))]
                elif name == "_safe":
                    args = [(v,) for v in (None, 0, "<", ">", "&", "'", '"')]
                elif module_name in ("outing_guide_ui", "scenario_board_ui") and name == "_currency":
                    args = [(v, v) for v in VALUES]
                elif module_name == "ux124_city_profile_ui":
                    args = [(v, unit) for v in VALUES for unit in ("€", "CHF", "R$", "", None)]
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

    def test_inline_currency_expressions(self):
        from formatting import brl, REQUIRED
        for value in VALUES:
            for old, new in (
                (lambda value: "R$ "+f"{value:,.0f}".replace(",","."),
                 lambda value: brl(value, decimals=0, missing=REQUIRED)),
                (lambda value: "R$ "+f"{value:,.2f}",
                 lambda value: brl(value, decimals=2, missing=REQUIRED, decimal_comma=False)),
            ):
                def outcome(fn):
                    try:
                        return ("return", fn(value))
                    except Exception as exc:
                        return ("raise", type(exc))
                with self.subTest(value=value):
                    self.assertEqual(outcome(old), outcome(new))
