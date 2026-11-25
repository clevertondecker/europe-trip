"""D-004 scope, provenance and non-mutation regression tests."""
import unittest
from copy import deepcopy
from data24_audit_model import build_audit
from data24_d004_audit_model import (D004_SNAPSHOT_CANDIDATES, coworking_state,
                                    render_d004_section, scope_for_d004,
                                    validate_scope_coverage, research_gaps)
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
        self.assertEqual(scope["named_candidates"], sorted(D004_SNAPSHOT_CANDIDATES))
        self.assertEqual(set(D004_SNAPSHOT_CANDIDATES), {"mulhouse", "strasbourg", "metz", "nancy"})
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

    def test_scope_does_not_parse_free_text(self):
        snapshot, research, five = load_data(), load_research(), load_five_base_evidence()
        decision = next(d for d in snapshot["decisions"] if d["id"] == "D-004")
        decision["note"] = "Metz saiu da avaliação. Colmar entrou."
        scope = scope_for_d004(snapshot, research, five)
        self.assertEqual(scope["named_candidates"], sorted(D004_SNAPSHOT_CANDIDATES))
        self.assertIsNone(scope["official_finalist_ids"])

    def test_missing_base_has_actionable_error(self):
        snapshot, research, five = load_data(), load_research(), load_five_base_evidence()
        five["base_ids"].append("not_registered")
        with self.assertRaisesRegex(ValueError, "pesquisa ampliada: not_registered"):
            scope_for_d004(snapshot, research, five)
        with self.assertRaisesRegex(ValueError, "cobertura ferroviária DATA24A: trier"):
            validate_scope_coverage(["trier"], {"cobertura ferroviária DATA24A": {}})

    def test_research_gaps_differ_and_do_not_rank(self):
        rows = {r["id"]: r for r in self.data["rows"]}
        self.assertIn("alternativa de coworking para expediente completo",
                      rows["mulhouse"]["research_gaps"]["decision_blockers"])
        self.assertIn("pesquisar coworking e condições de acesso",
                      rows["trier"]["research_gaps"]["decision_blockers"])
        self.assertIn("normais climáticas", rows["trier"]["research_gaps"]["complementary"])
        self.assertIn("normais climáticas", rows["mulhouse"]["research_gaps"]["sufficient_for_context_only"])
        for row in rows.values():
            self.assertEqual(row["research_gaps"], research_gaps(row))
            self.assertIsNone(row["decision_evidence"]["research_priority"])
        report = "\n".join(render_d004_section(self.data))
        self.assertIn("não versionado", report)
        self.assertIn("../../data/city_research_packs_2026_11.json", report)
