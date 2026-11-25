"""D-004 scope, provenance and non-mutation regression tests."""
import unittest
from copy import deepcopy
from data24_audit_model import build_audit
from data24_d004_audit_model import coworking_state, render_d004_section, scope_for_d004
from base_research_expanded_model import load_research, observed_housing
from data_model import load_data
from five_base_comparison_model import load_five_base_evidence


class D004AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = build_audit()
        cls.data = cls.audit["d004"]

    def test_scope_is_descriptive_and_does_not_assign_priority(self):
        scope = self.data["scope"]
        self.assertEqual(set(scope["named_candidates"]), {"mulhouse", "strasbourg", "metz", "nancy"})
        self.assertEqual(set(scope["five_base_study_ids"]), set(load_five_base_evidence()["base_ids"]))
        self.assertEqual(set(scope["descriptive_ids"]), set(scope["named_candidates"]) | set(scope["five_base_study_ids"]))
        self.assertIsNone(scope["official_finalist_ids"])
        self.assertIsNone(scope["priority_assignment"])
        self.assertEqual(len(scope["historical_shortlist_ids"]), 12)
        self.assertEqual(self.data["counts"]["bases"], len(scope["descriptive_ids"]))
        self.assertFalse(self.data["official_plan_modified"])

    def test_source_parity_and_unknown_values(self):
        cities = {c["id"]: c for c in load_research()["cities"]}
        for r in self.data["rows"]:
            h, w, d = r["housing"], r["remote_work"], r["daily_life"]
            self.assertEqual(h["summary"], observed_housing(cities[r["id"]]))
            self.assertEqual(h["historical_offers"], cities[r["id"]]["housing_offers"])
            self.assertIsNone(h["total_2027"])
            self.assertIsNone(h["deposit_2027"])
            self.assertEqual(r["rail"], self.audit["rail_by_base"][r["id"]])
            self.assertIsNone(r["decision_evidence"]["research_priority"])
            self.assertEqual(w["compatibility_2027"], "indeterminate")
            self.assertIsNone(w["residential_internet_2027"])
            if d["restaurant_eur_two"] is not None:
                self.assertTrue(d["restaurant_source_url"])
                self.assertTrue(d["restaurant_source_date"])
            if w["coworking"]:
                self.assertTrue(w["coworking"]["source_url"])
                self.assertTrue(w["coworking"]["price_basis"])
        self.assertFalse(self.data["shared_budget_context_not_local"]["city_specific"])

    def test_three_states_and_deterministic_rendering(self):
        self.assertEqual(coworking_state({"late_work_compatible": True}), "compatible_2026")
        self.assertEqual(coworking_state({"late_work_compatible": False}), "incompatible_2026")
        self.assertEqual(coworking_state({"late_work_compatible": None}), "indeterminate")
        self.assertEqual(coworking_state(None), "indeterminate")
        before = deepcopy(self.data)
        self.assertEqual(render_d004_section(self.data), render_d004_section(self.data))
        self.assertEqual(self.data, before)
        inputs = [load_data(), load_research(), load_five_base_evidence()]
        before_inputs = deepcopy(inputs)
        scope_for_d004(*inputs)
        self.assertEqual(inputs, before_inputs)
