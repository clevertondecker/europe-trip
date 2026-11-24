"""UX119 foundation: one temporal projection and atomic sidecar consistency."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from attractions_model import load_attractions
from trip_plan_model import new_plan
from itinerary_flow_model import add_undated_choices, FRANCE_STAGE
from ux45_outing_contract import apply_outing
from ux48_weekend_groups_model import empty_groups, create_group, available_weekends
from ux61_destination_board_model import build_destination_board, board_metrics
from ux63_timeline_model import project_timeline, timeline_metrics
from ux_planning_journey_model import project_planning
from ux502_destination_interests_model import empty_interests
from trip01_supplemental_discovery import build_exploration_discovery


class PlanningFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.discovery=build_exploration_discovery()

    def setUp(self):
        self.plan=add_undated_choices(new_plan(),self.catalog,
            ["basel","colmar","interlaken","obernai","strasbourg"],FRANCE_STAGE)
        self.plan,_=apply_outing(self.plan,self.catalog,"colmar",[],
                                 "Férias restantes",confirmed=True)
        self.groups=empty_groups(self.plan)
        self.saturdays=[x["start"] for x in available_weekends(
            self.groups,self.plan,self.catalog) if x["status"]=="livre · não reservado"]
        from planning_store import add_assignment
        self.plan=add_assignment(self.plan,self.saturdays[-1],"strasbourg")

    def _check(self, groups, organized):
        before=deepcopy((self.plan,groups))
        wishes=empty_interests()
        board=build_destination_board(wishes,self.plan,self.discovery,self.catalog,groups)
        timeline=project_timeline(self.plan,self.catalog,groups)
        view=project_planning(self.plan,wishes,self.discovery,self.catalog,weekend_groups=groups)
        self.assertEqual(board_metrics(board)["organized"],organized)
        self.assertEqual(timeline_metrics(timeline)["organized"],organized)
        self.assertEqual(view["counts"]["organized"],organized)
        self.assertEqual(len(view["pending"]),5-organized)
        self.assertEqual(timeline_metrics(timeline)["dated"],1)
        self.assertEqual(board_metrics(board)["dated"],1)
        self.assertEqual((self.plan,groups),before)
        return {r["id"]:r for r in timeline}

    def test_metadata_only_visit_keeps_canonical_assignment(self):
        from itinerary_flow_model import selected_rows
        from planning_store import remove_assignment
        self.assertNotIn("strasbourg",self.plan["packages"])
        row=next(r for r in selected_rows(self.plan,self.catalog)
                 if r["id"]=="strasbourg")
        self.assertEqual(row["exact_dates"],[self.saturdays[-1]])
        self.assertEqual(row["attractions"],[])
        unscheduled=remove_assignment(self.plan,self.saturdays[-1])
        row=next(r for r in selected_rows(unscheduled,self.catalog)
                 if r["id"]=="strasbourg")
        self.assertEqual(row["exact_dates"],[])

    def test_group_interval_is_not_individual_date(self):
        self._check(self.groups,2)
        undated=create_group(self.groups,self.plan,self.catalog,name="Suíça",
            destinations=["basel","interlaken"])
        self._check(undated,2)
        period=create_group(self.groups,self.plan,self.catalog,name="Suíça",
            destinations=["basel","interlaken"],period="Férias restantes")
        self._check(period,4)
        dated=create_group(self.groups,self.plan,self.catalog,name="Suíça",
            destinations=["basel","interlaken"],start_date=self.saturdays[0],nights=1)
        rows=self._check(dated,4)
        for index,key in enumerate(["basel","interlaken"],1):
            self.assertEqual(rows[key]["dates"],[])
            self.assertIsNone(rows[key]["period"])
            self.assertEqual(rows[key]["group_dates"][0],self.saturdays[0])
            self.assertEqual(len(rows[key]["group_dates"]),2)
            self.assertEqual(rows[key]["group_sequence"],index)
            self.assertTrue(rows[key]["organized"])
            self.assertFalse(rows[key]["dated"])
        self.assertEqual(rows["strasbourg"]["dates"],[self.saturdays[-1]])

    def test_removal_reconciles_before_opening_organizer(self):
        import planning_session as session
        groups=create_group(self.groups,self.plan,self.catalog,name="Suíça",
            destinations=["basel","interlaken"],start_date=self.saturdays[0],notes="preservar")
        state={"advisor_plan":deepcopy(self.plan),"ux48_weekend_groups":groups}
        with patch.object(session.st,"session_state",state):
            session.delete_outing("basel",confirmed=True)
            updated=state["ux48_weekend_groups"]["groups"][0]
            self.assertEqual(updated["destinations"],["interlaken"])
            self.assertEqual(updated["start_date"],self.saturdays[0])
            self.assertEqual(updated["notes"],"preservar")
            self.assertTrue(state["ux36_cloud_dirty"])
            self.assertEqual(state["advisor_plan"]["assignments"],self.plan["assignments"])
            session.delete_outing("interlaken",confirmed=True)
            self.assertEqual(state["ux48_weekend_groups"]["groups"],[])

    def test_conflicting_new_assignment_has_no_partial_write(self):
        import planning_session as session
        groups=create_group(self.groups,self.plan,self.catalog,name="Suíça",
            destinations=["basel","interlaken"],start_date=self.saturdays[0])
        state={"advisor_plan":deepcopy(self.plan),"ux48_weekend_groups":groups}
        with patch.object(session.st,"session_state",state):
            with self.assertRaises(ValueError):
                session.schedule_package(self.saturdays[0],"obernai")
        self.assertEqual(state["advisor_plan"],self.plan)
        self.assertEqual(state["ux48_weekend_groups"],groups)
        self.assertFalse(state.get("ux36_cloud_dirty",False))

    def test_invalid_archive_does_not_repair_state_during_fingerprint(self):
        import continuity_ui as ui
        groups=create_group(self.groups,self.plan,self.catalog,name="Suíça",
            destinations=["basel","interlaken"])
        groups["groups"][0]["destinations"].append("orphan")
        state={"advisor_plan":deepcopy(self.plan),"ux48_weekend_groups":groups}
        before=deepcopy(state)
        with patch.object(ui.st,"session_state",state):
            with self.assertRaises(ValueError):
                ui._current_decisions_fingerprint(self.plan,self.catalog)
        self.assertEqual(state,before)
