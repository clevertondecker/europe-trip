"""REC01 contract tests using the real catalog and official rail loaders."""
from copy import deepcopy
import json
import unittest

from base_recommendation_evidence_model import build_recommendation_matrix, candidate_ids
from base_research_expanded_model import load_research
from data23_france_candidates_model import REQUIRED_IDS
from rail_reference_projection_model import decorate_comparison
from rec01_feasibility import run_assessment
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests, set_interest
from ux503_destination_base_comparison_model import compare_wishlist_bases


class SharedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery = build_exploration_discovery()
        cls.research = load_research(include_candidates=True)

    def test_dynamic_matrix_preserves_manual_cell_contract_and_inputs(self):
        wishes = set_interest(empty_interests(), "paris", "must_visit", self.discovery)
        wishes = set_interest(wishes, "colmar", "interested", self.discovery)
        original = deepcopy((wishes, self.research, self.discovery))
        plan = new_plan(base="metz")
        plan_before = deepcopy(plan)
        all_bases = candidate_ids(self.research)
        result = build_recommendation_matrix(
            wishes, ["paris", "colmar"], discovery=self.discovery, research=self.research)
        self.assertTrue(REQUIRED_IDS.issubset(result["comparison"]["base_ids"]))
        self.assertEqual(result["comparison"]["base_ids"], all_bases)
        self.assertEqual(result["evidence"]["total"], len(all_bases)*2)
        self.assertEqual(result["evidence"]["cells"][("le_mans", "paris")]["display_min"], 56)
        self.assertEqual(result["evidence"]["cells"][("le_mans", "paris")]["category"], "reference_only")
        self.assertFalse(result["evidence"]["cells"][("le_mans", "paris")]["weekend_return_known"])
        self.assertEqual(result["evidence"]["cells"][("colmar", "colmar")]["category"], "local")
        self.assertIsNone(result["evidence"]["cells"][("colmar", "colmar")]["display_min"])
        subset = ["metz", "le_mans", "colmar"]
        manual = compare_wishlist_bases(wishes, subset, discovery=self.discovery, research=self.research)
        expected = decorate_comparison(manual)
        for key, cell in expected["cells"].items():
            self.assertEqual(result["evidence"]["cells"][key], cell)
        with self.assertRaises(ValueError):
            compare_wishlist_bases(wishes, all_bases, discovery=self.discovery, research=self.research)
        self.assertEqual((wishes, self.research, self.discovery), original)
        self.assertEqual(plan, plan_before)
        self.assertFalse(result["official_plan_modified"])

    def test_scope_must_be_explicit_and_canonical(self):
        wishes = set_interest(empty_interests(), "paris", "interested", self.discovery)
        wishes = set_interest(wishes, "colmar", "discarded", self.discovery)
        for invalid in ([], ["paris", "paris"], ["colmar"], ["unknown"], ["PARIS"], "paris"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_recommendation_matrix(wishes, invalid, discovery=self.discovery, research=self.research)

    def test_invalid_duplicate_base_ids_rejected(self):
        data = deepcopy(self.research)
        data["cities"].append(deepcopy(data["cities"][0]))
        with self.assertRaises(ValueError):
            candidate_ids(data)

    def test_real_feasibility_scenarios_are_exhaustive(self):
        report = run_assessment()
        self.assertEqual(report["candidate_count"], len(self.research["cities"]))
        self.assertEqual(report["selectable_destination_count"], len(self.discovery["destinations"]))
        self.assertEqual(len(report["scenarios"]), 7)
        for name, row in [("overall", report["overall"]), *report["scenarios"].items()]:
            with self.subTest(scenario=name):
                self.assertEqual(row["bases"], report["candidate_count"])
                self.assertEqual(sum(row["categories"].values()), row["bases"]*row["destinations"])
                self.assertEqual(row["with_time"]+row["without_time"], row["bases"])
                self.assertEqual(list(row["thresholds"].values()), sorted(row["thresholds"].values(), reverse=True))
                self.assertLessEqual(len(row["complete_without_local"]), row["with_time"])
        # Report actual loader results in CI logs; counts are not frozen constants.
        print("REC01_FEASIBILITY " + json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
