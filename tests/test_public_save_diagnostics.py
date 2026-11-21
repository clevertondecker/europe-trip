"""Regression tests for safe, actionable public GitHub save errors."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from io import BytesIO

from planning_status import explain_storage_error
from trip_plan_model import new_plan
from trip_plan_repository import (
    GitHubPlanRepository, PlanConflictError, PlanValidationError,
)


class PublicSaveDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.repo = GitHubPlanRepository("test-token")
        self.plan = new_plan()

    def test_invalid_local_plan_is_diagnosed_without_remote_write(self):
        self.plan["base_city"] = "invalid_city"
        with patch.object(self.repo, "_request") as request:
            with self.assertRaisesRegex(PlanValidationError, "Base/perfil inválido"):
                self.repo.save(self.plan, None)
            request.assert_not_called()

    def test_public_safety_is_preserved_before_any_write(self):
        self.plan["private_email"] = "do-not-publish@example.com"
        with patch.object(self.repo, "_request") as request:
            with self.assertRaises(PlanValidationError):
                self.repo.save(self.plan, None)
            request.assert_not_called()

    def test_stale_sha_does_not_write(self):
        saved = dict(self.plan, revision=1)
        self.plan["revision"] = 2
        with patch.object(self.repo, "load", return_value=(saved, "remote-sha")):
            with patch.object(self.repo, "_request") as request:
                with self.assertRaises(PlanConflictError):
                    self.repo.save(self.plan, "stale-sha")
                request.assert_not_called()

    def test_non_increasing_revision_does_not_write(self):
        with patch.object(self.repo, "load", return_value=(self.plan.copy(), "sha")):
            with patch.object(self.repo, "_request") as request:
                with self.assertRaises(PlanConflictError):
                    self.repo.save(self.plan, "sha")
                request.assert_not_called()

    def test_concurrent_update_409_does_not_claim_success(self):
        self.plan["revision"] = 2
        old = dict(self.plan, revision=1)
        error = HTTPError("https://api.github.com/", 409, "Conflict", {}, BytesIO())
        with patch.object(self.repo, "load", return_value=(old, "correct-sha")):
            with patch.object(self.repo, "_request", side_effect=error) as request:
                with self.assertRaises(PlanConflictError):
                    self.repo.save(self.plan, "correct-sha")
                self.assertEqual(request.call_count, 1)

    def test_conflict_message_distinct_from_invalid_data(self):
        conflict = explain_storage_error(PlanConflictError("Revisão remota mudou"))
        invalid = explain_storage_error(PlanValidationError("Base/perfil inválido"))
        self.assertIn("Conflito de versões", conflict)
        self.assertIn("Dados do planejamento inválidos", invalid)
        self.assertIn("Base/perfil inválido", invalid)
        self.assertNotIn("dados inválidos", conflict.lower())

    def test_http_412_is_reported_as_conflict(self):
        exc = HTTPError("https://api.github.com/", 412, "Precondition Failed", {}, BytesIO())
        self.assertIn("conflito", explain_storage_error(exc).lower())

    def test_non_conflict_network_errors_are_not_mislabeled(self):
        exc = HTTPError("https://api.github.com/", 403, "Forbidden", {}, BytesIO())
        self.assertIn("acesso", explain_storage_error(exc).lower())
        self.assertNotIn("conflito", explain_storage_error(exc).lower())


if __name__ == "__main__":
    unittest.main()
