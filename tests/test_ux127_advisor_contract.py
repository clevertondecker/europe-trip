"""Characterization of the existing advisor contract, before UX127 changes."""
import inspect
import unittest
from copy import deepcopy
from advisor_finance import advisor_projection
from unified_budget import LIVE_MATCH


class AdvisorContractTests(unittest.TestCase):
    def test_signature_and_live_fixture(self):
        self.assertEqual(list(inspect.signature(advisor_projection).parameters),
                         ["data", "source_live", "plan", "costs", "eur_fx",
                          "chf_fx", "use_city_rent", "cities"])
        amounts = dict(rent=6000, groceries=2000, dining=1000,
                       transport=500, excursions=1000)
        scenario = {"id": "70k", "days": 70, "reported_total_brl": 20000,
                    "cap_brl": 30000, "emergency_reserve_brl": 1000,
                    "components": [{"name": LIVE_MATCH[k], "amount": v}
                                   for k, v in amounts.items()]}
        data = {"budget_scenarios": [scenario]}
        plan = {"budget_scenario": "70k", "total_days": 70,
                "italy_days": 10, "base_city": "Metz"}
        costs = {"known_by_currency": {"EUR": 300, "CHF": 100},
                 "missing": ["unknown ticket"]}
        cities = {"cities": [{"name": "Metz", "reference_rent_eur": 700}]}
        before = deepcopy((data, plan, costs, cities))
        for use_city_rent, rent, total, margin, rent_delta in [
            (False, 6000, 26671.43, 3328.57, 0),
            (True, 8400, 29071.43, 928.57, 2400),
        ]:
            with self.subTest(use_city_rent=use_city_rent):
                snapshot = advisor_projection(data, True, plan, costs, 6., 7.,
                                              use_city_rent, cities)
                self.assertEqual(snapshot, {
                    "result": {"total": total, "margin": margin,
                               "status": "margem_condicional" if margin >= 1500 else "apertado",
                               "reserve_already_in_total": 1000,
                               "new_components": {"groceries": 2000., "transport": 500.,
                                                  "excursions": 2500., "dining": 6171.43,
                                                  "rent": rent},
                               "deltas": {"rent": rent_delta, "groceries": 0.,
                                          "dining": 5171.43, "transport": 0.,
                                          "excursions": 1500.},
                               "flight_delta": 0, "source": "drive",
                               "budget_fraction": round(total / 30000, 4), "days": 60},
                    "scenario": scenario,
                    "rent_eur_month": 700. if use_city_rent else None,
                    "city_rent_mode": "reference_2026" if use_city_rent else "budget_baseline",
                    "known_billets_brl": 2500., "budget_excursions_allowance_brl": 1000.,
                    "known_excursions_overage_brl": 1500.,
                    "has_unknown_costs": True, "profile_affects_price": False})
        self.assertEqual((data, plan, costs, cities), before)
