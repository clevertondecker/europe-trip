"""Regression suite for continuous itinerary creation and old plan files."""
from copy import deepcopy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions
from itinerary_flow_model import (
    ITALY_STAGE,FRANCE_STAGE,UNASSIGNED,destinations,choice_counts,
    upsert_choice,remove_choice,selected_rows,is_selected,
    italy_starter_preview,adopt_italy_starter,
)
from planning_store import set_package,remove_package
from trip_plan_model import new_plan,validate_plan

ROOT=Path(__file__).resolve().parents[1]


class FlexibleVisitModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()

    def test_existing_schema_v1_backup_without_new_field_is_still_readable(self):
        old=new_plan()
        old.pop("flexible_visits")
        validate_plan(old)
        changed=upsert_choice(old,self.catalog,"italy_amalfi",
                              ["italy_amalfi__1"],"Durante a Costa Amalfitana")
        self.assertNotIn("flexible_visits",old)
        self.assertEqual(changed["schema_version"],1)
        self.assertEqual(changed["assignments"],{})
        self.assertEqual(changed["flexible_visits"][0]["period"],
                         "Durante a Costa Amalfitana")

    def test_italian_and_french_choices_use_one_plan_without_duplicating_costs(self):
        plan=new_plan()
        original=deepcopy(plan)
        plan=upsert_choice(plan,self.catalog,"italy_rome",
                           ["italy_rome__1","italy_rome__2"],"Durante Roma")
        self.assertEqual(plan["packages"],{})
        colmar=next(a["id"] for a in self.catalog["attractions"]
                    if a["destination_id"]=="colmar")
        plan=upsert_choice(plan,self.catalog,"colmar",
                           [colmar],"Primeiro fim de semana na França")
        self.assertEqual(plan["packages"]["colmar"],[colmar])
        self.assertEqual(plan["assignments"],{})
        self.assertEqual(choice_counts(plan,self.catalog)["destinations"],2)
        self.assertEqual(choice_counts(plan,self.catalog)["organized"],2)
        self.assertEqual(original["packages"],{})
        again=upsert_choice(plan,self.catalog,"colmar",
                            [colmar],"Primeiro fim de semana na França")
        self.assertEqual(again["revision"],plan["revision"])

    def test_legacy_editor_updates_and_removes_new_flexible_metadata(self):
        plan=new_plan()
        colmar=next(a["id"] for a in self.catalog["attractions"]
                    if a["destination_id"]=="colmar")
        another=next(a["id"] for a in self.catalog["attractions"]
                    if a["destination_id"]=="colmar" and a["id"]!=colmar)
        plan=upsert_choice(plan,self.catalog,"colmar",
                           [colmar],"Férias restantes")
        edited=set_package(plan,"colmar",[another])
        self.assertEqual(edited["packages"]["colmar"],[another])
        self.assertEqual(edited["flexible_visits"][0]["attractions"],[another])
        removed=remove_package(edited,"colmar")
        self.assertEqual(removed["packages"],{})
        self.assertEqual(removed["flexible_visits"],[])

    def test_italy_proposal_is_preview_only_until_approved(self):
        start=new_plan()
        preview=italy_starter_preview(start,self.catalog,"economy")
        self.assertEqual(len(preview["to_add"]),4)
        self.assertEqual(preview["snapshot"]["coast_base_proposed"],"salerno")
        self.assertEqual((preview["snapshot"]["rome_nights"],
                          preview["snapshot"]["coast_nights"],
                          preview["snapshot"]["naples_nights"]),(4,4,1))
        self.assertEqual(adopt_italy_starter(start,self.catalog,"economy"),start)
        applied=adopt_italy_starter(start,self.catalog,"economy",confirmed=True)
        self.assertEqual({x["destination_id"] for x in applied["flexible_visits"]},
                         {"italy_rome","italy_amalfi","italy_salerno","italy_naples"})
        self.assertEqual(len(applied["italy_proposal"]["days_detail"]),10)
        self.assertEqual(applied["italy_proposal"]["coast_base_proposed"],"salerno")
        self.assertEqual(applied["revision"],start["revision"]+1)
        self.assertEqual(applied["assignments"],{})
        self.assertEqual(applied["packages"],{})
        self.assertFalse(preview["reservations"])
        repeated=adopt_italy_starter(applied,self.catalog,"economy",confirmed=True)
        self.assertEqual(repeated["revision"],applied["revision"])
        switched=adopt_italy_starter(applied,self.catalog,"experience",confirmed=True)
        self.assertEqual(switched["italy_proposal"]["coast_base_proposed"],"minori")
        self.assertEqual(switched["italy_proposal"]["coast_nights"],5)
        self.assertEqual(switched["revision"],applied["revision"]+1)
        self.assertTrue({x["destination_id"] for x in applied["flexible_visits"]} <=
                        {x["destination_id"] for x in switched["flexible_visits"]})

    def test_exact_italy_day_is_independent_of_french_calendar(self):
        from itinerary_flow_model import schedule_italy_day,selected_rows
        plan=upsert_choice(new_plan(),self.catalog,"italy_amalfi",
                           ["italy_amalfi__1"],"Durante a Costa Amalfitana")
        scheduled=schedule_italy_day(plan,self.catalog,"italy_amalfi","2027-09-11")
        self.assertEqual(scheduled["assignments"],{})
        self.assertEqual(scheduled["flexible_visits"][0]["exact_date"],"2027-09-11")
        self.assertEqual(selected_rows(scheduled,self.catalog)[0]["exact_dates"],
                         ["2027-09-11"])
        with self.assertRaises(ValueError):
            schedule_italy_day(plan,self.catalog,"italy_amalfi","2027-10-12")
        unchanged=upsert_choice(scheduled,self.catalog,"italy_amalfi",
                                ["italy_amalfi__2"],"Durante a Costa Amalfitana")
        self.assertEqual(unchanged["flexible_visits"][0]["exact_date"],"2027-09-11")
        removed=schedule_italy_day(unchanged,self.catalog,"italy_amalfi",None)
        self.assertNotIn("exact_date",removed["flexible_visits"][0])

    def test_scenarios_reuse_same_italian_research_catalog(self):
        from italy_honeymoon_model import load_honeymoon,italy_itinerary_places
        from itinerary_flow_model import italian_catalog
        reference=load_honeymoon()
        self.assertEqual(italian_catalog(),italy_itinerary_places(reference))
        self.assertEqual(len(italian_catalog()),10)
        self.assertEqual({r["id"] for r in italian_catalog()},
                         {r["id"] for r in destinations(self.catalog)
                          if r["stage"]==ITALY_STAGE})
        snapshots={variant:italy_starter_preview(new_plan(),self.catalog,variant)
                   for variant in ("balanced","economy","experience")}
        self.assertEqual({x["snapshot"]["coast_base_proposed"]
                          for x in snapshots.values()},{"maiori","salerno","minori"})
        self.assertNotEqual(
            {x[0] for x in snapshots["balanced"]["to_add"]},
            {x[0] for x in snapshots["economy"]["to_add"]})

    def test_invalid_dates_duplicate_italy_and_other_stage_are_rejected(self):
        base=new_plan()
        for bad in (
            ["italy_amalfi__1","italy_amalfi__1"],
            ["colmar_fake"],
        ):
            with self.assertRaises(ValueError):
                upsert_choice(base,self.catalog,"italy_amalfi",bad,UNASSIGNED)
        with self.assertRaises(ValueError):
            upsert_choice(base,self.catalog,"italy_amalfi",
                          ["italy_amalfi__1"],"Primeiro fim de semana na França")


class ItineraryFlowAppTests(unittest.TestCase):
    def test_add_amalfi_without_date_and_keep_it_after_navigating(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        before=at.session_state["advisor_plan"]["revision"]
        at.radio(key="ux_area").set_value("Meu roteiro").run()
        at.segmented_control(key="ux_section").set_value("Visão geral").run()
        at.button(key="flow_add_open_button").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        at.selectbox(key="flow_add_destination").set_value("italy_amalfi").run()
        at.multiselect(key="flow_pick_italy_amalfi").set_value(["italy_amalfi__1"]).run()
        at.selectbox(key="flow_period_italy_amalfi").set_value(
            "Durante a Costa Amalfitana").run()
        at.button(key="flow_add_confirm").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        plan=at.session_state["advisor_plan"]
        self.assertEqual(plan["revision"],before+1)
        self.assertEqual(plan["assignments"],{})
        self.assertEqual(plan["flexible_visits"][0]["destination_id"],"italy_amalfi")
        at.segmented_control(key="ux_section").set_value("Itália").run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        at.segmented_control(key="ux_section").set_value("Visão geral").run()
        self.assertEqual(at.session_state["advisor_plan"]["flexible_visits"][0]["period"],
                         "Durante a Costa Amalfitana")

    def test_italy_proposal_requires_two_separate_user_clicks(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        at.radio(key="ux_area").set_value("Meu roteiro").run()
        at.segmented_control(key="ux_section").set_value("Itália").run()
        before=deepcopy(at.session_state["advisor_plan"])
        at.button(key="italy_starter_open").click().run()
        self.assertEqual(at.session_state["advisor_plan"],before)
        at.button(key="italy_starter_confirm").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertTrue(is_selected(at.session_state["advisor_plan"],"italy_rome"))
        self.assertTrue(is_selected(at.session_state["advisor_plan"],"italy_amalfi"))


if __name__=="__main__":
    unittest.main()
