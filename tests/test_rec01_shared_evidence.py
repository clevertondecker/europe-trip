"""REC01 contract tests using the real catalog and official rail loaders."""
from copy import deepcopy
import json
import unittest

from base_recommendation_evidence_model import build_recommendation_matrix, candidate_ids
from base_research_expanded_model import load_research
from data23_france_candidates_model import REQUIRED_IDS
from rail_reference_projection_model import decorate_comparison
from rec01_feasibility import run_assessment, SCENARIOS, DATA23_SCENARIOS
from rail_pair_projection_model import pair_projection_row
from ux503_destination_base_comparison_model import build_wishlist_matrix
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

    def test_single_base_and_observation_variation(self):
        wishes = set_interest(empty_interests(), "colmar", "must_visit", self.discovery)
        view = build_wishlist_matrix(wishes, ["strasbourg"], discovery=self.discovery)
        self.assertEqual(len(view["rows"]), 1)
        with self.assertRaises(ValueError):
            compare_wishlist_bases(wishes, ["strasbourg"], discovery=self.discovery)
        example = {"status": "historical_time", "minimum_oneway_min": 30,
                   "source_url": "https://example.org", "observations": [
                       {"minimum_oneway_min": 30, "evidence_date": "2026-11-10"},
                       {"minimum_oneway_min": 45, "evidence_date": "2026-11-11"}]}
        pair = pair_projection_row("strasbourg", "colmar", example)
        self.assertTrue(pair["divergent_sources"])
        self.assertEqual(pair["variation_status"], "multiple_dates")
        self.assertFalse(pair["contradiction_confirmed"])

    def test_candidate_pairs_with_explicit_catalog_fixtures(self):
        # Geneva may not yet be selectable; fixture exercises direction without
        # falsely claiming availability in the actual discovery catalog.
        discovery = deepcopy(self.discovery)
        known = {d["id"] for d in discovery["destinations"]}
        for key in ("saumur", "geneva", "saint_malo"):
            if key not in known:
                discovery["destinations"].append({"id": key, "name": key, "country": "Fixture"})
        wishes = empty_interests()
        for key in ("paris", "saumur", "geneva", "saint_malo", "colmar"):
            wishes = set_interest(wishes, key, "interested", discovery)
        all_view = build_recommendation_matrix(wishes, [x["destination_id"] for x in wishes["items"]],
                                                discovery=discovery)
        ids = ["angers", "annecy", "rennes", "le_mans", "strasbourg"]
        manual = decorate_comparison(compare_wishlist_bases(wishes, ids, discovery=discovery))
        for key, cell in manual["cells"].items():
            self.assertEqual(all_view["evidence"]["cells"][key], cell)
        for key in (("angers", "saumur"), ("annecy", "geneva"), ("rennes", "saint_malo")):
            self.assertEqual(manual["cells"][key]["category"], "reference_only")
            self.assertFalse(manual["cells"][key]["weekend_return_known"])

    def test_scope_must_be_explicit_and_canonical(self):
        wishes = set_interest(empty_interests(), "paris", "interested", self.discovery)
        wishes = set_interest(wishes, "colmar", "discarded", self.discovery)
        for invalid in ([], ["paris", "paris"], ["colmar"], ["unknown"], ["PARIS"], "paris"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_recommendation_matrix(wishes, invalid, discovery=self.discovery, research=self.research)

    def test_legacy_wishlist_aliases_resolve_before_explicit_scope(self):
        from recommendation_scope_model import confirm_scope
        wishes = set_interest(empty_interests(), "luxembourg_city", "interested", self.discovery)
        canonical = "luxembourg"
        self.assertEqual(wishes["items"][0]["destination_id"], canonical)
        confirmed = confirm_scope(wishes, [canonical], self.discovery)
        self.assertEqual(confirmed["destination_ids"], [canonical])
        matrix = build_recommendation_matrix(wishes, [canonical],
                                             discovery=self.discovery, research=self.research)
        self.assertEqual([d["id"] for d in matrix["comparison"]["destinations"]], [canonical])
        for invalid in (["luxembourg_city"], ["luxemburgo"], ["LUXEMBOURG"],
                        [" luxembourg "], [canonical, "luxembourg_city"]):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    confirm_scope(wishes, invalid, self.discovery)
                with self.assertRaises(ValueError):
                    build_recommendation_matrix(wishes, invalid, discovery=self.discovery,
                                                research=self.research)

    def test_invalid_duplicate_base_ids_rejected(self):
        data = deepcopy(self.research)
        data["cities"].append(deepcopy(data["cities"][0]))
        with self.assertRaises(ValueError):
            candidate_ids(data)

    def test_real_feasibility_scenarios_are_exhaustive(self):
        report = run_assessment()
        self.assertEqual(report["candidate_count"], len(self.research["cities"]))
        self.assertEqual(report["selectable_destination_count"], len(self.discovery["destinations"]))
        self.assertEqual(set(report["scenarios"]) | set(report["skipped_scenarios_missing_ids"]),
                         set(SCENARIOS) | set(DATA23_SCENARIOS))
        self.assertTrue(set(SCENARIOS) <= set(report["scenarios"]))
        for name, row in [("overall", report["overall"]), *report["scenarios"].items()]:
            with self.subTest(scenario=name):
                self.assertEqual(row["bases"], report["candidate_count"])
                self.assertEqual(sum(row["categories"].values()), row["bases"]*row["destinations"])
                self.assertEqual(row["with_time"]+row["without_time"], row["bases"])
                self.assertEqual(list(row["thresholds"].values()), sorted(row["thresholds"].values(), reverse=True))
                self.assertLessEqual(len(row["complete_without_local"]), row["with_time"])
        # Keep CI log summary compact; CLI emits full per-base coverage.
        for row in [report["overall"], *report["scenarios"].values()]:
            self.assertEqual(row["strict_complete_group_count"]+row["partial_evidence_count"]+
                             row["insufficient_evidence_count"], row["bases"])
            row.pop("coverage_by_base")
        print("REC01_FEASIBILITY " + json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
