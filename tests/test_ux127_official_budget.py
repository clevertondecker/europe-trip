"""Official projection regressions independent of simulated settings."""
import unittest
from copy import deepcopy
from data_model import load_data, calculate_scenario, get_scenario
from trip_plan_model import new_plan
from official_budget_model import (official_budget_projection, official_budget_for_plan,
                                   official_simulation_result)
from unified_budget import resolve_french_budget, scenario_total


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

    def test_simulation_starts_at_official_and_restores_without_mutation(self):
        costs = {"known_by_currency": {"EUR": 10000., "CHF": 100.},
                 "missing": ["unknown"]}
        snapshot = official_budget_projection(self.data, False, self.plan, costs)
        before = deepcopy((self.plan, snapshot))
        initial = official_simulation_result(snapshot)
        self.assertEqual(initial["total"], snapshot["total"])
        self.assertEqual(initial["margin"], snapshot["margin"])
        self.assertEqual(initial["new_components"]["dining"],
                         round(snapshot["french"]["amounts"]["dining"], 2))
        self.assertEqual(initial["deltas"]["dining"], 0.)
        changed = scenario_total(snapshot["scenario"], snapshot["french"],
                                 french_days=snapshot["french"]["french_days"],
                                 outings_weekly=2, outing_couple_eur=60,
                                 fx_brl_per_eur=6.3,
                                 excursions_delta_brl=snapshot["known_excursions_overage_brl"],
                                 flight_delta_brl=500, use_budget_dining=True)
        self.assertEqual(changed["total"], round(snapshot["total"] + 500, 2))
        self.assertEqual(official_simulation_result(snapshot), initial)
        self.assertEqual((self.plan, snapshot), before)

    def test_custom_restaurant_hypothesis_is_opt_in(self):
        official = official_budget_projection(self.data, False, self.plan, self.costs)
        args = dict(french_days=official["french"]["french_days"],
                    outings_weekly=0, outing_couple_eur=60, fx_brl_per_eur=6.3)
        same = scenario_total(official["scenario"], official["french"],
                              **args, use_budget_dining=True)
        changed = scenario_total(official["scenario"], official["french"], **args)
        self.assertEqual(same["total"], official["total"])
        self.assertEqual(same["deltas"]["dining"], 0.)
        self.assertEqual(changed["new_components"]["dining"], 0.)
        self.assertLess(changed["total"], same["total"])
