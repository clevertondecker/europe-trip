"""No fabricated totals, zero-filled gaps, budget mutations or double counting."""
import unittest
from copy import deepcopy
from ux44_finance_comparison_model import compare_city_costs,differences

class PartialFinanceTests(unittest.TestCase):
    def test_unknowns_stay_unknown_and_deposit_is_not_expense(self):
        assumptions={"mulhouse":{"housing":{"amount":"2600","basis":"manual_hypothesis"},
                                 "deposit":"1300"},
                     "strasbourg":{"housing":{"amount":"3100","basis":"manual_hypothesis"},
                                   "deposit":"1500"}}
        original=deepcopy(assumptions)
        matrix=compare_city_costs(assumptions,nights=60,travelers=2,eur_fx=6.3)
        self.assertEqual(matrix["cities"]["mulhouse"]["known_subtotal_eur"],2600)
        self.assertEqual(matrix["cities"]["mulhouse"]["deposit_cash_hold_eur"],1300)
        self.assertIsNone(matrix["cities"]["mulhouse"]["complete_cost_eur"])
        self.assertIn("outings",matrix["cities"]["mulhouse"]["missing_categories"])
        self.assertFalse(matrix["applied_to_official_budget"])
        self.assertEqual(assumptions,original)
        self.assertEqual(differences(matrix)[0]["category"],"housing")

    def test_zero_explicit_is_not_missing_but_blank_is(self):
        result=compare_city_costs({"a":{"fees":{"amount":"0","basis":"manual_hypothesis"}},
                                   "b":{}})
        self.assertIsNotNone(result["cities"]["a"]["categories"]["fees"])
        self.assertIsNone(result["cities"]["b"]["categories"]["fees"])

    def test_historical_requires_provenance(self):
        with self.assertRaises(ValueError):
            compare_city_costs({"a":{"housing":{"amount":1200,"basis":"historical_reference"}}})
        result=compare_city_costs({"a":{"housing":{"amount":1200,
                             "basis":"historical_reference",
                             "source_url":"https://example.org/observed"}}})
        self.assertTrue(result["comparison_is_partial"])

    def test_negative_nan_unknown_categories_rejected(self):
        for amount in ("-1","NaN","Infinity","not a price"):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    compare_city_costs({"a":{"housing":{"amount":amount,
                                     "basis":"manual_hypothesis"}}})
        with self.assertRaises(ValueError):
            compare_city_costs({"a":{"flights":{"amount":1,"basis":"manual_hypothesis"}}})

    def test_not_a_full_budget_even_with_all_categories(self):
        from ux44_finance_comparison_model import CATEGORIES
        entries={key:{"amount":100,"basis":"manual_hypothesis"} for key in CATEGORIES}
        result=compare_city_costs({"a":entries})
        self.assertEqual(result["cities"]["a"]["known_subtotal_eur"],700)
        self.assertIsNone(result["cities"]["a"]["complete_cost_eur"])
        self.assertFalse(result["applied_to_official_budget"])

if __name__=="__main__":
    unittest.main()
