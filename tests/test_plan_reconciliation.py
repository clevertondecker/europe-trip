"""Regression tests for safe reconciliation of locally restored travel plans."""
import copy
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from plan_reconciliation import compare_plans, plan_digest, prepare_reconciled_plan
from trip_plan_model import new_plan
from trip_plan_repository import GitHubPlanRepository, PlanConflictError


class PlanReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.local = new_plan()
        self.remote = copy.deepcopy(self.local)

    def test_equal_plans_are_read_only_and_report_no_difference(self):
        before = copy.deepcopy(self.local)
        result = compare_plans(self.local, self.remote)
        self.assertEqual(result["difference_count"], 0)
        self.assertEqual(self.local, before)
        self.assertEqual(self.remote, before)

    def test_nested_outings_and_dates_are_visible(self):
        self.local["packages"] = {"colmar": ["colmar_venise"]}
        self.remote["packages"] = {"colmar": ["colmar_tanners"]}
        self.local["assignments"] = {"2027-09-13": "colmar"}
        self.remote["assignments"] = {"2027-09-14": "colmar"}
        result = compare_plans(self.local, self.remote)
        paths = {item["field"] for item in result["different_fields"]}
        self.assertIn("packages.colmar", paths)
        self.assertIn("assignments.2027-09-13", paths)
        self.assertIn("assignments.2027-09-14", paths)

    def test_local_draft_and_remote_are_preserved_during_rebase(self):
        self.local["revision"] = 1
        self.local["profile"] = "experience"
        self.remote["revision"] = 4
        original_local = copy.deepcopy(self.local)
        original_remote = copy.deepcopy(self.remote)
        result = prepare_reconciled_plan(self.local, self.remote)
        self.assertEqual(result["revision"], 5)
        self.assertEqual(result["profile"], "experience")
        self.assertEqual(self.local, original_local)
        self.assertEqual(self.remote, original_remote)

    def test_same_revision_still_advances_after_approval(self):
        self.local["revision"] = self.remote["revision"] = 7
        self.assertEqual(prepare_reconciled_plan(self.local, self.remote)["revision"], 8)

    def test_different_plan_ids_are_not_reconciled(self):
        other = new_plan()
        with self.assertRaisesRegex(ValueError, "IDs diferentes"):
            compare_plans(self.local, other)
        with self.assertRaises(ValueError):
            prepare_reconciled_plan(self.local, other)

    def test_digest_detects_edits_after_preview(self):
        prior = plan_digest(self.local)
        self.local["preferences"] = {"colmar_venise": "Quero visitar"}
        self.assertNotEqual(prior, plan_digest(self.local))

    def test_remote_sha_is_always_rechecked_before_put(self):
        repo = GitHubPlanRepository("test-token")
        self.local["revision"] = 4
        self.remote["revision"] = 2
        candidate = prepare_reconciled_plan(self.local, self.remote)
        with patch.object(repo, "load", return_value=(self.remote, "newer-sha")):
            with patch.object(repo, "_request") as request:
                with self.assertRaises(PlanConflictError):
                    repo.save(candidate, "preview-sha")
                request.assert_not_called()

    def test_mid_write_conflict_does_not_report_success(self):
        repo = GitHubPlanRepository("test-token")
        self.remote["revision"] = 3
        candidate = prepare_reconciled_plan(self.local, self.remote)
        err = HTTPError("https://api.github.com/", 409, "Conflict", {}, BytesIO())
        with patch.object(repo, "load", return_value=(self.remote, "preview-sha")):
            with patch.object(repo, "_request", side_effect=err):
                with self.assertRaises(PlanConflictError):
                    repo.save(candidate, "preview-sha")

    def test_preview_caps_number_and_length_of_differences(self):
        self.local["preferences"] = {f"item_{i}": "Quero visitar" for i in range(120)}
        summary = compare_plans(self.local, self.remote)
        self.assertGreater(summary["difference_count"], 100)
        self.assertEqual(len(summary["different_fields"]), 100)


if __name__ == "__main__":
    unittest.main()
