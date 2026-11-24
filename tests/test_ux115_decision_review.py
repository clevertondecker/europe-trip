"""UX115: sourced rail enrichment and concise single-base decision review."""
import unittest
from copy import deepcopy

from base_change_model import destination_catalog,known_route
from city_decision_model import compare_city_decisions
from city_decision_ui import contextual_impact_projection
from data_model import load_data
from rec03a_suggestions_ui import _review_destinations
from trip_plan_model import new_plan
from ux115_rail_gap_model import load_rail_gap_overlay,validate_rail_gap_overlay


class OperatorEvidenceTests(unittest.TestCase):
    EXPECTED={
        ("metz","basel"):137,
        ("metz","colmar"):87,
        ("metz","paris"):83,
        ("mulhouse","paris"):162,
        ("mulhouse","obernai"):69,
    }

    def test_new_times_are_source_checked_2026_oneway_only(self):
        data=load_rail_gap_overlay()
        self.assertFalse(data["confirmed_2027"])
        self.assertEqual(len(data["routes"]),len(self.EXPECTED))
        for key,minutes in self.EXPECTED.items():
            with self.subTest(pair=key):
                entry=next(x for x in data["routes"]
                           if (x["base_id"],x["destination_id"])==key)
                self.assertEqual(entry["fastest_train_oneway_min"],minutes)
                self.assertTrue(entry["source_url"].startswith(
                    "https://www.sncf-connect.com/train/"))
                self.assertIsNone(entry["fare_eur_person_oneway"])
                self.assertIsNone(entry["representative_minutes"])
                self.assertFalse(entry["return_verified_2027"])
                route=known_route(*key)
                self.assertEqual(route["minutes"],minutes)
                self.assertEqual(route["source"],entry["source_url"])
                self.assertFalse(route["return_verified"])

    def test_uncertain_interlaken_remains_unknown_and_not_synthesized(self):
        data=load_rail_gap_overlay()
        self.assertIn(("metz","interlaken"),
                      {(r["base_id"],r["destination_id"])
                       for r in data["research_gaps"]})
        self.assertIsNone(known_route("metz","interlaken")["minutes"])

    def test_invalid_or_duplicate_overlay_is_rejected(self):
        data=load_rail_gap_overlay()
        for mutation in (
            lambda p:p["routes"][0].update(fastest_train_oneway_min=0),
            lambda p:p["routes"].append(deepcopy(p["routes"][0])),
            lambda p:p["routes"][0].update(return_verified_2027=True),
            lambda p:p["routes"][0].update(fare_eur_person_oneway=20.0),
            lambda p:p["routes"][0].update(source_url="http://example.com"),
        ):
            with self.subTest(mutation=str(mutation)):
                changed=deepcopy(data)
                mutation(changed)
                with self.assertRaises(ValueError):
                    validate_rail_gap_overlay(changed)

    def test_obernai_available_to_review_not_automatically_in_trip(self):
        names=destination_catalog()
        self.assertEqual(names["obernai"],"Obernai")
        supported,unsupported=_review_destinations(
            ["paris","obernai","unknown_ux115"])
        self.assertEqual(supported,["paris","obernai"])
        self.assertEqual(unsupported,["unknown_ux115"])


class ContextualReviewProjectionTests(unittest.TestCase):
    def test_metz_to_mulhouse_honors_same_destinations_and_source_gaps(self):
        plan=new_plan()
        plan["base_city"]="metz"
        before=deepcopy(plan)
        destinations=["basel","colmar","interlaken","paris",
                      "strasbourg","obernai"]
        comparison=compare_city_decisions(
            plan,["mulhouse"],destinations,
            {"metz":None,"mulhouse":None},load_data(),False,60,6.3)
        view=contextual_impact_projection(comparison)
        self.assertEqual(view["candidate"],"mulhouse")
        self.assertEqual(view["total"],len(destinations))
        self.assertFalse(view["changes_official_plan"])
        self.assertFalse(view["housing_known"])
        self.assertIsNone(view["housing_delta_brl"])
        all_seen={name for rows in view["groups"].values()
                  for name in (row["name"] for row in rows)}
        self.assertEqual(all_seen,set(comparison["destination_names"].values()))
        by_name={row["name"]:row for rows in view["groups"].values() for row in rows}
        self.assertEqual(by_name["Paris"]["before"],83)
        self.assertEqual(by_name["Paris"]["after"],162)
        self.assertIn(by_name["Interlaken"],
                      view["groups"]["Não pesquisado"])
        self.assertIn(by_name["Obernai"],
                      view["groups"]["Não pesquisado"])
        self.assertEqual(plan,before)
        self.assertFalse(comparison["comparable_2027_totals"])

    def test_summary_never_calls_partial_coverage_a_winner(self):
        plan=new_plan()
        plan["base_city"]="metz"
        c=compare_city_decisions(
            plan,["mulhouse"],["interlaken","paris"],
            {},load_data(),False,60,6.3)
        view=contextual_impact_projection(c)
        self.assertEqual(view["comparable"],1)
        self.assertEqual(len(view["groups"]["Não pesquisado"]),1)
        self.assertFalse(view["changes_official_plan"])


if __name__=="__main__":
    unittest.main()
