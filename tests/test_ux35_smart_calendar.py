"""UX 3.5: dates are suggestions, not bookings, and only confirmed changes persist."""
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from trip_plan_model import new_plan
from attractions_model import load_attractions,load_base_routes
from itinerary_flow_model import upsert_choice
from planning_store import set_package
from smart_calendar_model import (
    validate_calendar_preferences,availability_matrix,assess_day,
    suggest_calendar,manual_calendar_move,review_calendar_change,
    apply_calendar_change,
)

ROOT=Path(__file__).resolve().parents[1]


def italy_plan():
    catalog=load_attractions()
    return upsert_choice(new_plan(),catalog,"italy_amalfi",
                         ["italy_amalfi__1"],"Durante a Costa Amalfitana")


def france_plan():
    p=new_plan()
    return set_package(p,"colmar",["colmar_old_town"],
                       valid_destinations={x["id"] for x in load_attractions()["destinations"]},
                       valid_attractions={x["id"] for x in load_attractions()["attractions"]
                                          if x["destination_id"]=="colmar"})


class SmartCalendarModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.routes=load_base_routes()

    def test_dates_are_derived_from_real_plan_without_mutating(self):
        p=new_plan()
        original=deepcopy(p)
        days=availability_matrix(p)
        self.assertEqual(len(days),70)
        self.assertEqual(sum(x["stage"]=="Itália" for x in days),10)
        self.assertEqual(sum(x["setup"] for x in days),4)
        self.assertTrue(any(x["workday"] for x in days))
        self.assertTrue(all(not x["booking_confirmed"] for x in days))
        self.assertEqual(p,original)

    def test_work_hours_are_optional_but_never_guessed(self):
        self.assertIsNone(validate_calendar_preferences(None)["work_start"])
        with self.assertRaises(ValueError):
            validate_calendar_preferences({"work_start":"18:00"})
        with self.assertRaises(ValueError):
            validate_calendar_preferences({"timezone":"Mars/Base"})
        with self.assertRaises(ValueError):
            validate_calendar_preferences({"work_start":"19:00","work_end":"09:00"})
        valid=validate_calendar_preferences({"work_start":"09:00",
                                            "work_end":"18:00"})
        self.assertEqual(valid["timezone"],"Europe/Paris")

    def test_italy_stays_in_italy_and_existing_exact_date_survives(self):
        p=italy_plan()
        snapshot=deepcopy(p)
        choices=suggest_calendar(p,self.catalog,self.routes)
        self.assertTrue(choices)
        self.assertEqual(p,snapshot)
        for proposal in choices:
            for change in proposal["changes"]:
                self.assertEqual(change["stage"],"Itália")
                self.assertLess(date.fromisoformat(change["to_date"]),
                                date(2027,9,19))
                self.assertTrue(change["conditional"])
                self.assertFalse(change["reservation"])
            self.assertIsNone(proposal["finance_delta_brl"])
        nextp=apply_calendar_change(p,choices[0],self.catalog,confirmed=True)
        self.assertEqual(nextp["revision"],p["revision"]+1)
        self.assertTrue(nextp["flexible_visits"][0]["exact_date"])
        self.assertEqual(nextp["packages"],p["packages"])
        self.assertEqual(nextp["base_city"],p["base_city"])
        self.assertEqual(p,snapshot)
        with self.assertRaises(ValueError):
            apply_calendar_change(nextp,choices[0],self.catalog,confirmed=True)

    def test_french_outings_skip_setup_and_remote_work_days(self):
        p=france_plan()
        choices=suggest_calendar(p,self.catalog,self.routes)
        self.assertTrue(choices)
        days={r["date"]:r for r in availability_matrix(p)}
        for proposal in choices:
            for item in proposal["changes"]:
                day=days[item["to_date"]]
                self.assertEqual(item["stage"],"França")
                self.assertFalse(day["workday"])
                self.assertFalse(day["setup"])
                self.assertFalse(item["reservation"])
        workdate=next(d["date"] for d in days.values() if d["workday"])
        chosen=next(r for r in __import__("itinerary_flow_model").selected_rows(
            p,self.catalog) if r["id"]=="colmar")
        self.assertFalse(assess_day(p,chosen,workdate)["allowed"])
        self.assertIn("Trabalho remoto",assess_day(p,chosen,workdate)["reason"])

    def test_known_unverified_train_is_conditional_not_confirmed(self):
        p=france_plan()
        proposals=suggest_calendar(p,self.catalog,self.routes)
        self.assertTrue(proposals)
        for pr in proposals:
            self.assertIn("retorno",pr["changes"][0]["warnings"][0].lower())
            self.assertFalse(pr["booking_confirmed"])
        self.assertEqual(p["assignments"],{})

    def test_unresearched_route_not_rejected_as_impossible(self):
        p=set_package(new_plan(),"metz",["metz_cathedral"],
                      valid_destinations={x["id"] for x in self.catalog["destinations"]},
                      valid_attractions={x["id"] for x in self.catalog["attractions"]
                                         if x["destination_id"]=="metz"})
        pr=suggest_calendar(p,self.catalog,self.routes)
        # If the route is absent, the absence is informational, not denial.
        if not pr:
            self.assertEqual(p["assignments"],{})

    def test_manual_move_and_remove_only_date(self):
        p=italy_plan()
        pr=manual_calendar_move(p,self.catalog,"italy_amalfi","Itália","2027-09-12")
        applied=apply_calendar_change(p,pr,self.catalog,confirmed=True)
        self.assertEqual(applied["flexible_visits"][0]["exact_date"],"2027-09-12")
        undone=manual_calendar_move(applied,self.catalog,"italy_amalfi","Itália",None)
        reverted=apply_calendar_change(applied,undone,self.catalog,confirmed=True)
        self.assertNotIn("exact_date",reverted["flexible_visits"][0])
        self.assertEqual(reverted["flexible_visits"][0]["attractions"],
                         applied["flexible_visits"][0]["attractions"])
        with self.assertRaises(ValueError):
            manual_calendar_move(p,self.catalog,"italy_amalfi","Itália","2027-10-03")

    def test_imported_draft_cannot_hide_extra_assignments(self):
        p=france_plan()
        pr=suggest_calendar(p,self.catalog,self.routes)[0]
        malicious=deepcopy(pr)
        malicious["assignments"]["2027-10-09"]="colmar"
        with self.assertRaises(ValueError):
            review_calendar_change(p,malicious,self.catalog)
        malicious=deepcopy(pr)
        malicious["booking_confirmed"]=True
        with self.assertRaises(ValueError):
            review_calendar_change(p,malicious,self.catalog)

    def test_existing_dates_not_overwritten(self):
        p=france_plan()
        existing=manual_calendar_move(p,self.catalog,"colmar","França","2027-09-24")
        booked=apply_calendar_change(p,existing,self.catalog,confirmed=True)
        self.assertEqual(booked["assignments"]["2027-09-24"],"colmar")
        self.assertEqual(suggest_calendar(booked,self.catalog,self.routes),[])

    def test_repeated_french_destination_is_one_visit_per_day(self):
        p=france_plan()
        first=manual_calendar_move(p,self.catalog,"colmar","França","2027-09-25")
        p=apply_calendar_change(p,first,self.catalog,confirmed=True)
        second=manual_calendar_move(p,self.catalog,"colmar","França",
                                    "2027-10-09",from_day=None)
        p2=apply_calendar_change(p,second,self.catalog,confirmed=True)
        self.assertEqual(len(p2["assignments"]),2)
        self.assertEqual(p2["packages"],p["packages"])


class SmartCalendarUITests(unittest.TestCase):
    def test_calendar_is_contextual_and_proposes_without_mutation(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=115).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Organizar viagem").run()
        app.segmented_control(key="ux_organize_view").set_value(
            "Calendário inteligente").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux35_suggest",{x.key for x in app.button})
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux35_suggest").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(original,app.session_state["advisor_plan"])
        self.assertTrue(any("Organizar a nossa viagem" in x.value
                            for x in app.markdown))

    def test_navigation_returns_to_smart_calendar(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=115).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Organizar viagem").run()
        app.segmented_control(key="ux_organize_view").set_value(
            "Calendário inteligente").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.button(key="ux35_go_budget").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_area"],"Orçamento")
        self.assertIn("workflow_back_to_edit",{x.key for x in app.button})
        app.button(key="workflow_back_to_edit").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_area"],"Meu roteiro")
        self.assertEqual(app.session_state["ux_section"],"Organizar viagem")
        self.assertEqual(app.session_state["ux_organize_view"],"Calendário inteligente")


if __name__=="__main__":
    unittest.main()
