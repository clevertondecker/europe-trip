"""Historical monthly rents never satisfy the 2027 two-person decision gate."""
import unittest
from housing_short_stay_research_model import (
    housing_research_overview, evaluate_short_stay_quote, same_dates_housing_candidates,
)

QUOTE = {
    "base_id":"mulhouse",
    "checkin":"2027-09-10", "checkout":"2027-11-06",
    "source_url":"https://example.com/direct-unit-with-dated-availability",
    "checked_at":"2026-11-17", "currency":"EUR", "travelers":2,
    "private_entire_unit":True, "furnished":True,
    "short_stay_allowed":True, "available_on_dates":True,
    "internet_verified":True, "work_space_verified":True,
    "kitchen_verified":True, "laundry_verified":True,
    "station_access_verified":True, "mandatory_fees_verified":True,
    "rent_total":2200.0, "cleaning_fee":100.0, "service_fee":50.0,
    "mandatory_taxes":0.0, "utilities_total":0.0,
    "refundable_deposit":500.0,
}


class HousingShortStayTests(unittest.TestCase):
    def test_baseline_still_zero_bookable_quotes(self):
        result = housing_research_overview()
        self.assertEqual(result["base_count"], 30)
        self.assertEqual(result["historical_observation_count"], 35)
        self.assertEqual(result["verified_2027_quote_count"], 0)
        self.assertTrue(all(not x["decision_ready"] for x in result["bases"]))
        self.assertFalse(result["official_base_modified"])

    def test_full_quote_separates_expense_from_refundable_deposit(self):
        output = evaluate_short_stay_quote(QUOTE)
        self.assertEqual(output["nights"], 57)
        self.assertEqual(output["expense_total"], 2350.0)
        self.assertEqual(output["refundable_deposit_separate"], 500.0)
        self.assertEqual(output["upfront_cash_exposure"], 2850.0)
        self.assertTrue(output["decision_ready_for_dates"])
        self.assertTrue(output["requires_live_listing_recheck"])

    def test_missing_internet_or_fee_does_not_become_zero(self):
        lacking = evaluate_short_stay_quote({**QUOTE, "internet_verified":None,
                                            "service_fee":None})
        self.assertFalse(lacking["decision_ready_for_dates"])
        self.assertIsNone(lacking["expense_total"])
        self.assertIn("internet", lacking["research_missing"])
        self.assertIn("total_de_despesas_comprovado", lacking["research_missing"])

    def test_date_and_identity_gate(self):
        for q in (
            {**QUOTE, "checkin":"2027-09-04"},
            {**QUOTE, "checkout":"2027-09-30"},
            {**QUOTE, "travelers":1},
            {**QUOTE, "base_id":"maastricht"},
            {**QUOTE, "source_url":"http://example.com/listing"},
        ):
            with self.subTest(q=q), self.assertRaises(ValueError):
                evaluate_short_stay_quote(q)

    def test_housing_comparison_does_not_pick_winner(self):
        a = same_dates_housing_candidates([QUOTE, {**QUOTE, "base_id":"metz"}])
        self.assertTrue(a["same_dates_and_currency"])
        self.assertIsNone(a["recommended_base"])
        b = same_dates_housing_candidates([QUOTE, {**QUOTE, "checkin":"2027-09-12",
                                                      "checkout":"2027-11-08"}])
        self.assertFalse(b["same_dates_and_currency"])
        self.assertFalse(b["all_ready"])


if __name__ == "__main__":
    unittest.main()
