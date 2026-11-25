"""Official projection regressions independent of simulated settings."""
import unittest
from copy import deepcopy
from data_model import load_data, calculate_scenario, get_scenario
from trip_plan_model import new_plan
from official_budget_model import official_budget_projection, official_budget_for_plan
from unified_budget import resolve_french_budget


class OfficialBudgetTests(unittest.TestCase):
    def setUp(self):
        self.data = load_data()
        self.plan = new_plan()
        self.costs = {"known_by_currency": {"EUR": 0., "CHF": 0.}, "missing": []}

    def test_empty_plan_matches_reference_and_does_not_mutate(self):
        before = deepcopy((self.data, self.plan, self.costs))
        for sid in ("60k", "70k"):
            plan = {**self.plan, "budget_scenario": sid}
            baseline = calculate_scenario(get_scenario(self.data, sid))
            result = official_budget_projection(self.data, False, plan, self.costs)
            self.assertEqual(result["total"], baseline["total"])
            self.assertEqual(result["margin"], baseline["balance"])
            self.assertEqual(result["known_excursions_overage_brl"], 0.)
            self.assertEqual(result, official_budget_for_plan(self.data, False, plan))
        self.assertEqual((self.data, self.plan, self.costs), before)

    def test_known_overage_only_and_missing_costs(self):
        baseline = official_budget_projection(self.data, False, self.plan, self.costs)
        costs = {"known_by_currency": {"EUR": 10000., "CHF": 100.},
                 "missing": ["unknown"]}
        result = official_budget_projection(self.data, False, self.plan, costs)
        allowance = resolve_french_budget(get_scenario(self.data, "70k"), False)["amounts"]["excursions"]
        expected = round(10000 * 6.3 + 100 * 7.1 - allowance, 2)
        self.assertEqual(result["known_excursions_overage_brl"], expected)
        self.assertEqual(result["total"], round(baseline["total"] + expected, 2))
        self.assertLess(result["margin"], 0)
        self.assertTrue(result["has_unknown_costs"])
        self.assertEqual(result["missing"], ("unknown",))

    def test_reference_duration_is_explicit(self):
        plan = {**self.plan, "total_days": 72}
        result = official_budget_projection(self.data, False, plan, self.costs)
        self.assertEqual(result["reference_days"], 70)
        self.assertEqual(result["planned_days"], 72)
        self.assertEqual(result["total"], get_scenario(self.data, "70k")["reported_total_brl"])
