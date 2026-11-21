"""Legacy optional TripPlan fields remain valid in all settings read paths."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from trip_plan_model import new_plan, validate_plan
from planning_workflow_model import settings, preview_settings, approve_settings, compare_alternative
from travel_advisor import recommendations

OPTIONAL = ("preferences", "mandatory_destinations", "excluded_destinations")


class LegacyOptionalSettingsTests(unittest.TestCase):
    def setUp(self):
        self.plan = new_plan(base="metz")
        for name in OPTIONAL:
            self.plan.pop(name)
        validate_plan(self.plan)

    def test_settings_returns_independent_defaults_without_mutating_legacy_plan(self):
        original = deepcopy(self.plan)
        values = settings(self.plan)
        self.assertEqual(values["preferences"], {})
        self.assertEqual(values["mandatory_destinations"], [])
        self.assertEqual(values["excluded_destinations"], [])
        values["preferences"]["colmar"] = "Quero visitar"
        values["mandatory_destinations"].append("colmar")
        self.assertEqual(self.plan, original)

    def test_unrelated_change_does_not_invent_optional_fields(self):
        original = deepcopy(self.plan)
        preview = preview_settings(self.plan, {"total_days": 71})
        self.assertEqual(set(preview["changes"]), {"total_days"})
        self.assertEqual(preview["changes"]["total_days"]["current"], 70)
        self.assertEqual(self.plan, original)
        self.assertEqual(preview["proposed_plan"], {**original, "total_days": 71})
        confirmed = approve_settings(self.plan, preview, confirmed=True)
        self.assertEqual(confirmed["total_days"], 71)
        self.assertEqual(confirmed["revision"], self.plan["revision"] + 1)
        self.assertNotIn("preferences", confirmed)

    def test_explicit_empty_defaults_are_noop_in_preview(self):
        preview = preview_settings(self.plan, {
            "preferences": {}, "mandatory_destinations": [],
            "excluded_destinations": []})
        self.assertTrue(preview["same_choice"])
        self.assertEqual(preview["changes"], {})
        self.assertEqual(approve_settings(self.plan, preview, confirmed=True), self.plan)

    def test_optional_field_can_be_added_explicitly(self):
        review = preview_settings(self.plan, {
            "preferences": {"colmar": "Quero visitar"},
            "mandatory_destinations": ["colmar"]})
        self.assertEqual(review["changes"]["preferences"]["current"], {})
        self.assertEqual(review["changes"]["mandatory_destinations"]["current"], [])
        confirmed = approve_settings(self.plan, review, confirmed=True)
        self.assertEqual(confirmed["preferences"], {"colmar": "Quero visitar"})
        self.assertEqual(confirmed["mandatory_destinations"], ["colmar"])
        self.assertNotIn("excluded_destinations", confirmed)

    def test_explicitly_malformed_values_are_not_silently_replaced(self):
        for field, value in (("preferences", None),
                             ("preferences", {"colmar": "invalid"}),
                             ("mandatory_destinations", None),
                             ("excluded_destinations", "colmar")):
            with self.subTest(field=field, value=value):
                candidate = deepcopy(self.plan)
                candidate[field] = value
                with self.assertRaises(ValueError):
                    settings(candidate)
                with self.assertRaises((ValueError, TypeError)):
                    preview_settings(candidate, {"total_days": 71})

    def test_required_fields_still_fail_not_silently_defaulted(self):
        candidate = deepcopy(self.plan)
        del candidate["budget_scenario"]
        with self.assertRaises((KeyError, ValueError)):
            settings(candidate)

    def test_what_if_comparison_still_supports_legacy_plan(self):
        baseline = deepcopy(self.plan)
        comparison = compare_alternative(self.plan, {"base_city": "nancy"})
        self.assertEqual(comparison["differences"]["base_city"], ("metz", "nancy"))
        self.assertEqual(self.plan, baseline)

    @patch("travel_advisor.route_for", return_value={"train_minutes_one_way": 35})
    def test_recommendations_support_missing_excluded_destinations(self, route):
        risk = {"code": "OVERNIGHT", "affected": "travel", "severity": "WARNING",
                "message": "Pernoite", "resolution": "Ver alternativas", "source": ""}
        output = recommendations(self.plan, None, {}, [risk])
        self.assertTrue(any(row["id"] == "ALTERNATIVES:NEARBY" for row in output))


if __name__ == "__main__":
    unittest.main()
