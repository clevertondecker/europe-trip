"""Validate real-price provenance and read-only Italy honeymoon alternatives."""
import unittest
from tests.nav_helpers import open_support
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest
from italy_honeymoon_model import (
    load_honeymoon,preview_nights,ticket_sample,optional_comparison,manual_italy_cost,
)

ROOT=Path(__file__).resolve().parents[1]


class ItalyHoneymoonModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_honeymoon()
        cls.scenarios={s["id"]:s for s in cls.data["scenarios"]}

    def test_scenarios_have_ten_days_nine_nights_and_preserve_rome_and_coast(self):
        self.assertEqual(len(self.scenarios),3)
        for key,scenario in self.scenarios.items():
            with self.subTest(key=key):
                self.assertEqual(scenario["days"],10)
                self.assertEqual(scenario["nights"],9)
                self.assertEqual(scenario["rome_nights"],4)
                self.assertGreater(scenario["coast_nights"],0)
                self.assertEqual(len(scenario["days_detail"]),10)
                self.assertTrue(scenario["days_detail"][0][1]=="Roma")
                self.assertEqual(scenario["rome_nights"]+
                                 scenario["coast_nights"]+
                                 scenario["naples_nights"],9)
        self.assertEqual(self.scenarios["balanced"]["coast_base"],"maiori")
        self.assertEqual(self.scenarios["economy"]["naples_nights"],1)
        self.assertEqual(self.scenarios["experience"]["coast_base"],"minori")

    def test_tenth_night_is_extra_calendar_day_not_same_ten_days(self):
        initial=self.scenarios["balanced"]
        a=preview_nights(initial)
        b=preview_nights(initial,extra_night=True)
        self.assertEqual((a["nights"],a["calendar_days"]),(9,10))
        self.assertEqual((b["nights"],b["calendar_days"]),(10,11))
        self.assertTrue(b["requires_official_italy_days_change"])

    def test_ticket_samples_do_not_claim_entire_trip_or_double_roundtrip(self):
        a=ticket_sample(self.data,"balanced")
        b=ticket_sample(self.data,"economy")
        c=ticket_sample(self.data,"experience")
        self.assertAlmostEqual(a["known_sample_subtotal_eur"],257.8)
        self.assertAlmostEqual(b["known_sample_subtotal_eur"],215.8)
        self.assertAlmostEqual(c["known_sample_subtotal_eur"],197.8)
        self.assertFalse(a["is_complete_cost"])
        self.assertFalse(a["ticket_prices_valid_for_2027"])
        ids={x["id"]:x for x in a["items"]}
        self.assertEqual(ids["vatican_online"]["couple_sample_eur"],50)
        self.assertEqual(ids["pantheon"]["couple_sample_eur"],14)
        self.assertEqual(ids["rome_salerno"]["couple_sample_eur"],29.8)
        self.assertEqual(ids["maiori_positano_rt"]["couple_sample_eur"],60)
        with self.assertRaises(ValueError):
            ticket_sample(self.data,"not-a-scenario")
        with self.assertRaises(ValueError):
            ticket_sample(self.data,"balanced",0)

    def test_capri_and_pompeii_examples_separate_2026(self):
        data={i["id"]:i for i in optional_comparison(self.data)}
        self.assertEqual(data["capri_from_amalfi"]["known_ticket_reference_eur"],106)
        self.assertEqual(data["capri_from_maiori"]["known_ticket_reference_eur"],122)
        self.assertEqual(data["pompeii"]["known_ticket_reference_eur"],40)
        self.assertIn("30/09",data["capri_from_maiori"]["extra_needed"])
        self.assertTrue(all("extra_needed" in x for x in data.values()))

    def test_manual_money_requires_all_inputs_and_keeps_flights_outside(self):
        before=deepcopy(self.data)
        values=dict(rome_hotel_night=150,coast_hotel_night=130,
                    food_couple_per_day=75,extra_local_transport=150,
                    additional_admissions=0)
        p=manual_italy_cost(self.data,"balanced",values,6.3)
        self.assertEqual(p["status"],"complete_user_inputs_not_full_trip")
        self.assertAlmostEqual(p["illustrative_italy_total_eur"],2407.8)
        self.assertAlmostEqual(p["illustrative_italy_total_brl"],15169.14)
        self.assertTrue(p["flight_double_count_prevented"])
        self.assertTrue(p["global_budget_unchanged"])
        self.assertFalse(p["complete_2027_quote"])
        q=manual_italy_cost(self.data,"balanced",values,6.3,extra_night=True)
        self.assertAlmostEqual(q["illustrative_italy_total_eur"]-
                               p["illustrative_italy_total_eur"],205)
        self.assertTrue(q["extra_night_included"])
        missing=manual_italy_cost(self.data,"balanced",{},6.3)
        self.assertIsNone(missing["illustrative_italy_total_brl"])
        self.assertIn("coast_hotel_night",missing["missing_manual_inputs"])
        with self.assertRaises(ValueError):
            manual_italy_cost(self.data,"balanced",values,-6)
        with self.assertRaises(ValueError):
            manual_italy_cost(self.data,"balanced",
                              {**values,"coast_hotel_night":float("nan")},6)
        self.assertEqual(self.data,before)


class ItalyHoneymoonAppTests(unittest.TestCase):
    def test_italy_tab_is_visible_and_never_modifies_canonical_trip(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        initial=deepcopy(app.session_state["advisor_plan"])
        open_support(app,"Itália")
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("italy_honeymoon_variant",
                      {x.key for x in app.segmented_control})
        self.assertIn("italy_honeymoon_extra_night",
                      {x.key for x in app.checkbox})
        app.segmented_control(key="italy_honeymoon_variant").set_value(
            "Econômico e logístico").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.checkbox(key="italy_honeymoon_extra_night").check().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],initial)


if __name__=="__main__":
    unittest.main()
