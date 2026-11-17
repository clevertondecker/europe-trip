import unittest
from copy import deepcopy

from plan_read_models import legacy_plan_projection, read_plan_view, legacy_drift
from planning_store import create_from_legacy, sync_legacy_view, change_plan
from trip_plan_model import new_plan


class CanonicalProjectionTests(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan()
        self.plan["packages"]={"strasbourg":["strasbourg_cathedral"]}
        self.plan["preferences"]={"strasbourg_cathedral":"Quero visitar"}

    def test_legacy_projection_is_defensive_and_canonical(self):
        before=deepcopy(self.plan)
        projection=legacy_plan_projection(self.plan)
        self.assertEqual(projection["explore_packages"],self.plan["packages"])
        projection["explore_packages"]["strasbourg"].append("other")
        self.assertEqual(self.plan,before)

    def test_readonly_projection_separates_nested_objects(self):
        view=read_plan_view(self.plan)
        view["packages"]["strasbourg"].clear()
        view["preferences"].clear()
        self.assertEqual(self.plan["packages"]["strasbourg"],
                         ["strasbourg_cathedral"])
        self.assertTrue(self.plan["preferences"])

    def test_drift_is_diagnostic_never_a_write(self):
        stale={"explore_packages":{"stale":["bad"]},
               "unified_scenario":"60k"}
        before=deepcopy(stale)
        diff=legacy_drift(self.plan,stale)
        self.assertEqual(set(diff),{"explore_packages","unified_scenario"})
        self.assertEqual(stale,before)
        self.assertEqual(self.plan["budget_scenario"],"70k")

    def test_legacy_restore_and_compatibility_sync_still_work(self):
        legacy={"explore_base":"strasbourg","unified_scenario":"60k",
                "explore_packages":{},"explore_calendar":{}}
        restored=create_from_legacy(legacy)
        self.assertEqual(restored["base_city"],"strasbourg")
        self.assertEqual(restored["budget_scenario"],"60k")
        session={"other":"keep"}
        sync_legacy_view(self.plan,session)
        self.assertEqual(session["explore_packages"],self.plan["packages"])
        self.assertNotIn("explore_base",session)
        sync_legacy_view(self.plan,session,include_controls=True)
        self.assertEqual(session["explore_base"],self.plan["base_city"])
        self.assertEqual(session["other"],"keep")

    def test_revision_changes_only_via_plan_operations(self):
        before=deepcopy(self.plan)
        legacy_plan_projection(self.plan)
        read_plan_view(self.plan)
        self.assertEqual(self.plan,before)
        updated=change_plan(self.plan,{"budget_scenario":"60k"})
        self.assertEqual(updated["revision"],before["revision"]+1)
        self.assertEqual(self.plan,before)

    def test_legacy_restore_does_not_modify_original_backup(self):
        legacy={
            "explore_base":"metz","unified_scenario":"60k",
            "explore_packages":{"strasbourg":["strasbourg_cathedral"]},
            "explore_calendar":{"2027-09-24":"strasbourg"},
            "itinerary_total_days":70,"itinerary_italy_days":10,
            "itinerary_vacation_days":25,"itinerary_setup_days":4,
            "itinerary_departure":"2027-09-09",
        }
        original=deepcopy(legacy)
        restored=create_from_legacy(legacy)
        self.assertEqual(legacy,original)
        self.assertEqual(restored["base_city"],"metz")
        self.assertEqual(restored["packages"],legacy["explore_packages"])
        self.assertEqual(restored["assignments"],legacy["explore_calendar"])
        restored["packages"]["strasbourg"].append("mutated")
        self.assertEqual(legacy,original)

    def test_missing_legacy_keys_preserve_defaults_and_existing_controls(self):
        restored=create_from_legacy({})
        self.assertEqual(restored["budget_scenario"],"70k")
        self.assertEqual(restored["base_city"],"mulhouse")
        session={"explore_base":"strasbourg","unified_scenario":"60k"}
        sync_legacy_view(restored,session,include_controls=False)
        self.assertEqual(session["explore_base"],"strasbourg")
        self.assertEqual(session["unified_scenario"],"60k")
        self.assertEqual(session["explore_packages"],{})
