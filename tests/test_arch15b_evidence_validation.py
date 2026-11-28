"""ARCH15B: verify shared URL rules against checked-in evidence before migration."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
from importlib import import_module

from evidence_validation import is_https_url

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    "rail_transfer_contract", "tourism_visit_evidence_model",
    "route_research_evidence_model", "ux506_decision_readiness_projection",
    "data8_couple_cost_model", "rail_component_contract",
    "data26a_housing_evidence_model", "ux132_research_coverage_model",
)

def _url_or_none(value):
    return value if is_https_url(value) else None

def _walk(value, location):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{location}[{index}]")
    elif isinstance(value, str) and value.strip().lower().startswith("https://"):
        yield location, value

class EvidenceUrlTests(unittest.TestCase):
    def test_contract(self):
        for value, expected in (
            ("https://a.b", True), ("http://a.b", False),
            ("https://:443/x", False), ("https://user@/x", False),
            (" https://a.b", False), ("https://a.b ", False),
            (None, False), (123, False), ("https://[", False),
        ):
            with self.subTest(value=value):
                self.assertEqual(is_https_url(value), expected)

    def test_checked_in_https_evidence(self):
        failures = []
        for path in sorted((ROOT / "data").rglob("*.json")):
            for location, value in _walk(json.loads(path.read_text(encoding="utf-8")), str(path.relative_to(ROOT))):
                if not is_https_url(value):
                    failures.append(f"{location}: {value!r}")
        self.assertFalse(failures, "\n".join(failures))

    def test_research_loaders_with_candidate_rule(self):
        with ExitStack() as stack:
            for name in MODULES:
                module = import_module(name)
                replacement = _url_or_none if name == "ux132_research_coverage_model" else is_https_url
                stack.enter_context(patch.object(module, "_https", replacement))
            from tools.validate_research_data import main
            main()
            from tourism_visit_evidence_model import load_visit_evidence
            from data8_couple_cost_model import load_cost_addons
            from data26a_housing_evidence_model import load_housing_observations
            from ux132_research_coverage_model import build_coverage_view
            for loader in (load_visit_evidence, load_cost_addons, load_housing_observations, build_coverage_view):
                with self.subTest(loader=loader.__name__):
                    loader()
