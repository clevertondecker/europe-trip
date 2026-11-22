"""TRIP01: scenario fixtures are non-authoritative, bounded and catalog-aware."""
import json
import unittest
from datetime import date
from pathlib import Path
from copy import deepcopy

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/trip01_exploratory_scenarios_2027.json"


class EditorialScenarioFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(DATA.read_text(encoding="utf-8"))
        cls.itinerary=json.loads((ROOT/"data/itinerary_options_2027.json").read_text(encoding="utf-8"))

    def test_dates_and_lengths_are_proposals_not_bookings(self):
        doc=self.doc
        self.assertEqual(doc["schema_version"],"trip01-exploratory-1.0")
        self.assertEqual(doc["status"],"unapproved_research_fixture")
        self.assertFalse(doc["authoritative_plan_mutation"])
        self.assertEqual(doc["travelers"],2)
        self.assertLess(date.fromisoformat(doc["wedding"]),date.fromisoformat(doc["candidate_arrival"]))
        start=date.fromisoformat(doc["candidate_arrival"])
        end=date.fromisoformat(doc["candidate_departure"])
        self.assertEqual((end-start).days,doc["italy_nights"]+doc["france_nights"])
        self.assertIsNone(doc["budget_brl"]["verified_total"])
        self.assertEqual(len(doc["scenarios"]),3)
        self.assertTrue(all(item["budget_total_brl"] is None for item in doc["scenarios"]))

    def test_all_italian_bases_are_known_and_outings_do_not_infer_eligibility(self):
        from trip_plan_model import BASES,new_plan
        place_ids={p["id"] for p in self.itinerary["places"]}
        all_ids=set()
        for item in self.doc["scenarios"]:
            self.assertNotIn(item["id"],all_ids)
            all_ids.add(item["id"])
            self.assertIn(item["france_base_id"],BASES)
            self.assertEqual(sum(b["nights"] for b in item["italy_bases"]),self.doc["italy_nights"])
            self.assertTrue(all(b["place_id"] in place_ids for b in item["italy_bases"]))
            self.assertEqual(item["france_after_work"],[item["france_base_id"]])
            self.assertIsNone(item["budget_total_brl"])
            self.assertEqual(item["confidence"],"editorial_candidates_only")
        missing=set().union(*(set(x["italy_candidates"])-place_ids for x in self.doc["scenarios"]))
        self.assertEqual(missing,{"pompeii","sorrento"})
        self.assertEqual(self.doc["scenarios"][2]["noncanonical_italy_candidates"],sorted(missing))
        # Loading proposals does not call any plan service or select a base.
        plan=new_plan()
        before=deepcopy(plan)
        self.assertEqual(plan,before)

    def test_french_candidates_have_catalog_or_research_identity(self):
        from trip01_supplemental_discovery import build_exploration_discovery
        from base_research_expanded_model import load_research
        known={x["id"] for x in build_exploration_discovery()["destinations"]}
        known|={x["id"] for x in load_research(include_candidates=True)["cities"]}
        known|={p["id"] for p in self.itinerary["places"]}
        for case in self.doc["scenarios"]:
            for field in ("france_after_work","france_weekend_candidates","france_vacation_candidates"):
                picks=case[field]
                self.assertEqual(len(picks),len(set(picks)),(case["id"],field))
                for city in picks:
                    self.assertIn(city,known,(case["id"],field,city))

    def test_fixture_is_not_deserialized_as_tripplan(self):
        from trip_plan_model import validate_plan
        with self.assertRaises((ValueError,KeyError,TypeError)):
            validate_plan(self.doc)


if __name__=="__main__":
    unittest.main()
