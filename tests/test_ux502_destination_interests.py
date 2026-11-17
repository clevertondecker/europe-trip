"""UX 5.0.2 — destinations are not attractions or confirmed outings."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import (
    empty_interests, validate_interests, set_interest, remove_interest,
    reconcile_transient, selected_destinations_for_comparison,
    export_interests, import_interests,
)
from attractions_model import load_attractions
from continuity_archive_model import make_archive,export_archive,import_archive

ROOT=Path(__file__).resolve().parents[1]


class DestinationInterestsModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_destination_discovery()

    def test_priorities_order_immutable_and_removal(self):
        initial=empty_interests()
        a=set_interest(initial,"bruges_be","interested",self.discovery)
        a=set_interest(a,"colmar","must_visit",self.discovery)
        a=set_interest(a,"lille","discarded",self.discovery)
        a=set_interest(a,"basel","maybe",self.discovery)
        self.assertEqual(initial,empty_interests())
        self.assertEqual(selected_destinations_for_comparison(a,self.discovery),
                         ["colmar","bruges_be","basel"])
        self.assertEqual(set_interest(a,"colmar","must_visit",self.discovery),a)
        self.assertEqual(len(a["items"]),4)
        self.assertEqual(len(remove_interest(a,"lille",self.discovery)["items"]),3)

    def test_invalid_destination_duplicate_schema_and_attraction(self):
        with self.assertRaises(ValueError):
            set_interest(empty_interests(),"lux_bock","interested",self.discovery)
        with self.assertRaises(ValueError):
            set_interest(empty_interests(),"unknown","interested",self.discovery)
        bad=empty_interests()
        bad["items"]=[{"destination_id":"colmar","priority":"maybe"}]*2
        with self.assertRaises(ValueError):
            validate_interests(bad,self.discovery)
        bad["schema_version"]=99
        with self.assertRaises(ValueError):
            validate_interests(bad,self.discovery)

    def test_round_trip_and_transient_reconciliation(self):
        a=set_interest(empty_interests(),"colmar","must_visit",self.discovery)
        b=import_interests(export_interests(a,self.discovery),self.discovery)
        self.assertEqual(b,a)
        existing,missing=reconcile_transient(b,["colmar","bruges_be"],self.discovery)
        self.assertEqual(existing,a)
        self.assertEqual(missing,["bruges_be"])

    def test_legacy_archive_and_new_optional_field(self):
        from trip_plan_model import new_plan
        plan=new_plan()
        catalog=load_attractions()
        old=make_archive(plan,catalog)
        old.pop("destination_interests")
        legacy=import_archive(__import__("json").dumps(old).encode(),catalog)
        self.assertEqual(legacy["destination_interests"],empty_interests())
        new=set_interest(empty_interests(),"colmar","must_visit",self.discovery)
        doc=make_archive(plan,catalog,destination_interests=new)
        self.assertEqual(import_archive(export_archive(doc,catalog),catalog)["destination_interests"],new)


class DestinationInterestsAppTests(unittest.TestCase):
    def test_list_filter_priority_and_tripplan_isolation(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.radio(key="ux502_view").set_value("Minha lista").run()
        app.session_state["ux502_interests"]=set_interest(
            set_interest(empty_interests(),"colmar","must_visit"),
            "bruges_be","interested")
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(selected_destinations_for_comparison(
            app.session_state["ux502_interests"]),["colmar","bruges_be"])
        app.radio(key="ux502_view").set_value("Descobrir lugares").run()
        app.selectbox(key="ux501_country").set_value("Bélgica").run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(len(app.session_state["ux502_interests"]["items"]),2)


if __name__=="__main__":
    unittest.main()
