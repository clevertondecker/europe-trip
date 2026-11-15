"""2026 supermarket/weekend samples and conservative 2027 reconciliation guards."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest
from attractions_model import load_attractions,load_base_routes
from data_model import load_data
from trip_plan_model import new_plan
from reconciled_trip_research import (
    load_extended_research,grocery_reference,day_of_outing,
    meal_observations,reconcile_researched_itinerary)
from research_cost_model import load_research

ROOT=Path(__file__).resolve().parents[1]


class WeekendPriceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.new=load_extended_research()
        self.old=load_research()
        self.catalog=load_attractions()
        self.routes=load_base_routes()
        self.data=load_data()
        self.plan=new_plan()
        self.colmar=[a["id"] for a in self.catalog["attractions"]
                     if a["destination_id"]=="colmar"][:2]

    def test_grocery_is_four_unit_prices_not_daily_budget(self):
        basket=grocery_reference(self.new)
        self.assertEqual(len(basket["rows"]),4)
        self.assertAlmostEqual(basket["sample_basket_eur"],6.49)
        self.assertTrue(basket["not_complete_food_basket"])
        self.assertTrue(basket["not_city_specific"])

    def test_weekend_menus_do_not_use_weekday_only_dishes(self):
        sunday=meal_observations("colmar","sun",self.old,self.new)
        self.assertTrue(sunday["items"])
        self.assertTrue(all(x["venue"]=="Savanna" for x in sunday["items"]))
        self.assertFalse(any(x["venue"]=="Le Zinc" for x in sunday["items"]))
        saturday=meal_observations("colmar","sat",self.old,self.new)
        self.assertTrue(any(x["venue"]=="Le Zinc" for x in saturday["items"]))
        self.assertTrue(any(x["venue"]=="Brasserie des Haras"
                            for x in meal_observations("strasbourg","sun",self.old,self.new)["items"]))
        self.assertEqual(meal_observations("metz","sun",self.old,self.new)["items"],[])
        self.assertEqual(meal_observations("colmar","undated",self.old,self.new)["items"],[])

    def test_sunday_itinerary_uses_menu_and_regular_train_but_no_double_count(self):
        self.plan["packages"]={"colmar":self.colmar}
        self.plan["assignments"]={"2027-10-10":"colmar"} # Sunday
        original=deepcopy(self.plan)
        preview=reconcile_researched_itinerary(
            self.plan,self.catalog,self.routes,self.data,False,6.3,7.1)
        self.assertEqual(preview["priced_count"],1)
        self.assertEqual(preview["total_count"],1)
        self.assertEqual(preview["outings"][0]["day"]["day"],"sun")
        self.assertAlmostEqual(preview["outings"][0]["normal_rail_couple_brl"],272.16)
        self.assertAlmostEqual(preview["outings"][0]["meal_couple_brl"],264.60)
        self.assertEqual(preview["indicated_increment_brl"],0)
        self.assertEqual(preview["partial_reference_projection_brl"],
                         preview["current_projected_brl"])
        self.assertFalse(preview["complete_2027_cost"])
        self.assertTrue(preview["does_not_change_official_budget"])
        self.assertEqual(original,self.plan)

    def test_without_date_or_without_regular_fare_global_preview_is_not_shown(self):
        self.plan["packages"]={"colmar":self.colmar}
        undated=reconcile_researched_itinerary(
            self.plan,self.catalog,self.routes,self.data,False,6.3,7.1)
        self.assertEqual(undated["priced_count"],0)
        self.assertIsNone(undated["partial_reference_projection_brl"])
        self.assertIn("colmar",undated["unpriced_destinations"])
        self.plan["base_city"]="strasbourg"
        self.plan["assignments"]={"2027-10-10":"colmar"}
        no_fare=reconcile_researched_itinerary(
            self.plan,self.catalog,self.routes,self.data,False,6.3,7.1)
        self.assertIsNone(no_fare["partial_reference_projection_brl"])
        self.assertIsNone(no_fare["outings"][0]["normal_rail_couple_brl"])
        self.assertNotIn("colmar",no_fare["unknown_admissions"])

    def test_profiles_change_example_not_official_trip(self):
        self.plan["packages"]={"colmar":self.colmar}
        self.plan["assignments"]={"2027-10-10":"colmar"}
        meal={}
        for p in ("economy","balanced","experience"):
            draft={**self.plan,"profile":p}
            result=reconcile_researched_itinerary(
                draft,self.catalog,self.routes,self.data,False,6.3,7.1)
            meal[p]=result["outings"][0]["meal_couple_brl"]
        self.assertLess(meal["economy"],meal["balanced"])
        self.assertLess(meal["balanced"],meal["experience"])
        self.assertEqual(self.plan["profile"],"balanced")
        self.assertEqual(self.plan["revision"],0)


class WeekendResearchUITests(unittest.TestCase):
    def test_my_outings_and_budget_show_new_research_panels(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        labels=[x.label for x in app.expander]
        self.assertTrue(any("Conciliação" in x for x in labels))
        self.assertTrue(any("Supermercado" in x for x in labels))
        app.segmented_control(key="itinerary_section").set_value("Orçamento").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Conciliar os três estilos" in x.label for x in app.expander))


if __name__=="__main__":
    unittest.main()
