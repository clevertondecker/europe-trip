"""Regression tests: plans remain discoverable when Streamlit generates a new ID."""
import unittest
from unittest.mock import patch
from trip_plan_model import new_plan
from trip_plan_repository import order_saved_plans
import travel_advisor_ui as ui


class RecoverSavedPlansTests(unittest.TestCase):
    def test_commit_sort_for_current_real_world_ids(self):
        ids=["trip-146f4b28cc46","trip-f86f1e779c9b"]
        commits=[
            {"commit":{"message":"Update travel plan trip-146f4b28cc46 r0",
                       "committer":{"date":"2026-11-15T04:29:44Z"}}},
            {"commit":{"message":"Update travel plan trip-f86f1e779c9b r2\n",
                       "committer":{"date":"2026-11-15T04:29:12Z"}}},
        ]
        result=order_saved_plans(ids,commits)
        self.assertEqual([x["plan_id"] for x in result],ids)
        self.assertEqual([x["revision"] for x in result],[0,2])
    def test_does_not_invent_ids_or_duplicate_same_plan(self):
        ids=["trip-aaaaaaaaaaaa","trip-bbbbbbbbbbbb"]
        commits=[
            {"commit":{"message":"Update travel plan trip-aaaaaaaaaaaa r2",
                       "committer":{"date":"2026-11-15T02:00:00Z"}}},
            {"commit":{"message":"Update travel plan trip-aaaaaaaaaaaa r1",
                       "committer":{"date":"2026-11-15T01:00:00Z"}}},
            {"commit":{"message":"Update travel plan trip-cccccccccccc r3",
                       "committer":{"date":"2026-11-15T03:00:00Z"}}},
        ]
        data=order_saved_plans(ids,commits)
        self.assertEqual([x["plan_id"] for x in data],
                         ["trip-aaaaaaaaaaaa","trip-bbbbbbbbbbbb"])
        self.assertEqual(data[0]["revision"],2)
    def test_empty_repository(self):
        self.assertEqual(order_saved_plans([],[]),[])
    def test_refresh_bootstraps_persisted_plan_and_explorer(self):
        stored=new_plan()
        stored["packages"]={"colmar":["colmar_venise"]}
        stored["assignments"]={"2027-09-24":"colmar"}
        latest=[{"plan_id":stored["plan_id"],"saved_at":"2026-11-15T04:30:00Z",
                 "revision":0}]
        class StubRepo:
            def __init__(self,token):self.token=token
            def recent_plans(self):return latest
            def load(self,plan_id):
                if plan_id!=stored["plan_id"]:raise AssertionError("Wrong ID")
                return stored,"github-blob-sha"
        with patch.object(ui.st,"session_state",{}), \
             patch.object(ui,"_owner_config",return_value={"token":"placeholder"}), \
             patch.object(ui,"_owner_signed_in",return_value=True), \
             patch.object(ui,"GitHubPlanRepository",StubRepo):
            ui._recover_saved_plan()
            state=ui.st.session_state
            self.assertEqual(state["advisor_plan"]["plan_id"],stored["plan_id"])
            self.assertEqual(state["advisor_github_sha"],"github-blob-sha")
            self.assertEqual(state["explore_packages"],stored["packages"])
            self.assertEqual(state["explore_calendar"],stored["assignments"])
            # Rerun must not replace or re-request the loaded plan.
            ui._recover_saved_plan()
            self.assertEqual(state["advisor_plan"]["plan_id"],stored["plan_id"])
    def test_no_authenticated_owner_means_no_remote_read(self):
        with patch.object(ui.st,"session_state",{}), \
             patch.object(ui,"_owner_config",return_value={"token":""}), \
             patch.object(ui,"_owner_signed_in",return_value=False):
            ui._recover_saved_plan()
            self.assertNotIn("advisor_plan",ui.st.session_state)

if __name__=="__main__":unittest.main()
