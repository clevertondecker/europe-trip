"""DATA24 coverage invariants and exact parity with the existing rail projection."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from data24_coverage_model import coverage_counts, rail_coverage
from base_research_expanded_model import load_research
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests
from ux503_destination_base_comparison_model import build_wishlist_matrix, build_destination_matrix
from rail_reference_projection_model import decorate_comparison


class CoverageCountsTests(unittest.TestCase):
    def test_units_and_unknown(self):
        counts = coverage_counts(["historical", "reference_only", "local", "no_time"])
        self.assertEqual(counts, dict(total=4, eligible=3, timed=2,
                                      historical=1, indicative=1, local=1,
                                      missing=1, fraction=2/3))
        self.assertIsNone(coverage_counts([])["fraction"])
        self.assertIsNone(coverage_counts(["local"])["fraction"])
        self.assertEqual(coverage_counts(["no_time"])["fraction"], 0)
        with self.assertRaises(ValueError):
            coverage_counts(["unknown"])


class RailCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research = load_research(include_candidates=True)
        cls.discovery = build_exploration_discovery()
        before = deepcopy((cls.research, cls.discovery))
        with patch("data24_coverage_model.build_destination_matrix",
                   wraps=build_destination_matrix) as resolve:
            cls.coverage = rail_coverage(research=cls.research, discovery=cls.discovery)
        assert resolve.call_count == 1
        assert (cls.research, cls.discovery) == before

    def test_full_directed_universe(self):
        v = self.coverage
        bases = [c["id"] for c in self.research["cities"]]
        destinations = [d["id"] for d in self.discovery["destinations"]]
        self.assertEqual(v["base_ids"], bases)
        self.assertEqual(v["destination_ids"], destinations)
        self.assertEqual(set(v["pairs"]), {(b,d) for b in bases for d in destinations})
        self.assertEqual(v["global"]["total"], len(bases)*len(destinations))
        for name in ("total", "eligible", "timed", "historical", "indicative", "local", "missing"):
            self.assertEqual(v["global"][name], sum(c[name] for c in v["by_base"].values()))
        self.assertFalse(v["official_plan_modified"])

    def test_exact_cells_for_paris_in_all_bases(self):
        v = self.coverage
        self.assertIn("paris", v["destination_ids"])
        doc = empty_interests()
        doc["items"] = [{"destination_id": "paris", "priority": "interested"}]
        expected = decorate_comparison(build_wishlist_matrix(
            doc, v["base_ids"], discovery=self.discovery, research=self.research))["cells"]
        for key, cell in expected.items():
            self.assertEqual(v["pairs"][key]["cell"], cell)

    def test_audit_is_independent_of_wishlist_limit(self):
        with patch("ux502_destination_interests_model.LIMIT", 2):
            sample = {**self.discovery, "destinations": self.discovery["destinations"][:3]}
            v = rail_coverage(research=self.research, discovery=sample)
        self.assertEqual(v["global"]["total"], 3*len(v["base_ids"]))
        for key, pair in v["pairs"].items():
            self.assertEqual(pair["cell"], self.coverage["pairs"][key]["cell"])

    def test_public_contract_does_not_assign_wishlist_priority(self):
        base = self.coverage["base_ids"][0]
        result = build_destination_matrix([base], ["paris"],
                                          research=self.research, discovery=self.discovery)
        self.assertIsNone(result["rows"][0]["priority"])
        self.assertIsNone(result["destinations"][0]["priority_label"])
        self.assertEqual(result["active_destination_count"], 1)
        with self.assertRaises(ValueError):
            build_destination_matrix([base], ["paris", "paris"],
                                     research=self.research, discovery=self.discovery)
        empty = build_destination_matrix([base], [],
                                         research=self.research, discovery=self.discovery)
        self.assertFalse(empty["comparison_ready"])
        self.assertEqual(empty["rows"], [])
