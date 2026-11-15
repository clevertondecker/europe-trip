"""Check city-base changes update discovered routes, fares and duration filters."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
from attractions_model import load_attractions,load_base_routes
from destination_recommender import recommend_destinations
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class RouteBaseDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_attractions()
        self.routes=load_base_routes()

    def test_route_prices_and_minutes_are_specific_to_base(self):
        values={}
        for base in ("mulhouse","strasbourg","metz","nancy"):
            plan=new_plan(base=base)
            recs=recommend_destinations(plan,self.catalog,self.routes,
                profile="balanced",max_travel_minutes=300,limit=100,
                include_unverified_routes=True)
            values[base]={r["destination_id"]:r for r in recs}
        self.assertEqual(values["mulhouse"]["colmar"]["train_minutes_one_way"],18)
        self.assertEqual(values["strasbourg"]["colmar"]["train_minutes_one_way"],32)
        self.assertEqual(values["mulhouse"]["colmar"]["fare_eur_person_oneway"],5.4)
        self.assertEqual(values["strasbourg"]["colmar"]["fare_eur_person_oneway"],7.9)
        self.assertIsNone(values["metz"]["colmar"]["train_minutes_one_way"])
        self.assertIsNone(values["nancy"]["colmar"]["fare_eur_person_oneway"])

    def test_unknown_routes_excluded_from_verified_duration_filter(self):
        plan=new_plan(base="metz")
        filtered=recommend_destinations(plan,self.catalog,self.routes,
            profile="balanced",max_travel_minutes=70,limit=100,
            include_unverified_routes=False)
        self.assertTrue(all(x["train_minutes_one_way"] is not None
                            or x["destination_id"]==plan["base_city"]
                            for x in filtered))
        self.assertNotIn("colmar",{x["destination_id"] for x in filtered})
        expanded=recommend_destinations(plan,self.catalog,self.routes,
            profile="balanced",max_travel_minutes=70,limit=100,
            include_unverified_routes=True)
        self.assertIn("colmar",{x["destination_id"] for x in expanded})

    def test_ui_switching_base_recomputes_visible_fares(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Descobrir").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        text=" ".join(x.value for x in list(app.caption)+list(app.info))
        self.assertIn("Cidade-base",text)
        self.assertIn("Mulhouse",text)
        self.assertIn("€ 5.40",text)
        app.selectbox(key="advisor_base").set_value("strasbourg").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"strasbourg")
        text=" ".join(x.value for x in list(app.caption)+list(app.info))
        self.assertIn("Strasbourg",text)
        self.assertIn("€ 7.90",text)
        app.selectbox(key="advisor_base").set_value("metz").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn("advisor_discover_add_colmar",{b.key for b in app.button})
        app.checkbox(key="advisor_discovery_unverified").check().run()
        self.assertIn("advisor_discover_add_colmar",{b.key for b in app.button})


if __name__=="__main__":unittest.main()
