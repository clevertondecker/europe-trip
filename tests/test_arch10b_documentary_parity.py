import unittest
import json
from copy import deepcopy
from five_base_comparison_model import load_five_base_evidence
from tools.arch10b_documentary_parity import documentary_rail_parity
from base_coverage_model import coverage_matrix


class DocumentaryParityTests(unittest.TestCase):
    def test_30_by_15_audit_without_mutation_or_false_equivalence(self):
        before=coverage_matrix("general")
        result=documentary_rail_parity()
        self.assertEqual(result["pairs"],450)
        # Source-backed 2026-11-17 audit baseline; changed data needs re-review.
        self.assertEqual(result["identical_pairs"],449)
        self.assertEqual(result["time_differences"],1)
        self.assertEqual(result["source_differences"],1)
        differing=[x for x in result["rows"] if not x["same_evidence"]]
        self.assertEqual([(x["base_id"],x["destination_id"]) for x in differing],
                         [("lille","luxembourg_city")])
        self.assertIsNone(differing[0]["legacy_documentary_minutes"])
        self.assertEqual(differing[0]["shared_display_minutes"],231)
        self.assertEqual(len(result["rows"]),450)
        self.assertEqual(result["pairs"],result["identical_pairs"]+
                         sum(not row["same_evidence"] for row in result["rows"]))
        self.assertEqual(result["time_differences"],
                         sum(not row["same_time"] for row in result["rows"]))
        self.assertEqual(result["source_differences"],
                         sum(not row["same_source"] for row in result["rows"]))
        audit={
            "pairs":result["pairs"],
            "time_differences":result["time_differences"],
            "source_differences":result["source_differences"],
            "identical_pairs":result["identical_pairs"],
            "safe_to_migrate_without_review":result["safe_to_migrate_without_review"],
            "examples":[
                {k:item[k] for k in ("base_id","destination_id",
                    "legacy_documentary_minutes","shared_display_minutes",
                    "legacy_documentary_source","shared_display_source")}
                for item in result["rows"] if not item["same_evidence"]
            ][:12],
        }
        print("ARCH10B_AUDIT_JSON="+json.dumps(audit,ensure_ascii=False))
        self.assertEqual(coverage_matrix("general"),before)
        self.assertFalse(result["documentary_model_modified"])
        self.assertTrue(all("difference_reason" in row for row in result["rows"]))

    def test_only_one_base_retains_same_15_denominator(self):
        result=documentary_rail_parity(cities=[{"id":"lille"}])
        self.assertEqual(result["pairs"],15)
        self.assertTrue(all(row["base_id"]=="lille" for row in result["rows"]))
        self.assertTrue(all(row["shared_observations_count"]>=0
                            for row in result["rows"]))

    def test_detects_source_and_time_disagreement_in_controlled_fixture(self):
        five=deepcopy(load_five_base_evidence())
        five["verified_time_routes"].append({
            "base_id":"lille","destination_id":"brussels",
            "fastest_train_oneway_min":999,
            "source_url":"https://example.org/controlled-documentary-fixture",
            "advertised_from_eur_person_oneway":None,
        })
        result=documentary_rail_parity(cities=[{"id":"lille"}],five=five)
        row=next(x for x in result["rows"] if x["destination_id"]=="brussels")
        self.assertEqual(row["legacy_documentary_minutes"],999)
        self.assertNotEqual(row["legacy_documentary_minutes"],
                            row["shared_display_minutes"])
        self.assertFalse(row["same_source"])
        self.assertFalse(result["safe_to_migrate_without_review"])
        self.assertGreaterEqual(result["time_differences"],1)
        self.assertGreaterEqual(result["source_differences"],1)
