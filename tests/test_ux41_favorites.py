"""UX 4.1 favorites: common basket, missing data, persistence and trip isolation."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from base_research_expanded_model import load_research
from city_profiles_model import load_profiles
from city_research_packs_model import load_city_packs
from five_base_comparison_model import load_five_base_evidence
from ux41_favorites_model import (
    validate_favorites,set_favorites,comparative_matrix,comparison_insights,
    export_favorites,import_favorites
)
from trip_plan_model import new_plan
from attractions_model import load_attractions
from continuity_archive_model import make_archive,export_archive,import_archive

ROOT=Path(__file__).resolve().parents[1]


class FavoriteComparisonModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=load_research()
        cls.five=load_five_base_evidence()
        cls.profiles=load_profiles()
        cls.packs=load_city_packs()
        cls.dest=list(x["id"] for x in cls.five["common_destinations"])

    def test_up_to_three_and_deepcopy(self):
        a=["mulhouse","strasbourg","freiburg"]
        self.assertEqual(set_favorites([],a,self.study),a)
        with self.assertRaises(ValueError):
            validate_favorites(a+["trier"],self.study)
        with self.assertRaises(ValueError):
            validate_favorites(["mulhouse","mulhouse"],self.study)
        with self.assertRaises(ValueError):
            validate_favorites(["not-a-city"],self.study)
        with self.assertRaises(ValueError):
            validate_favorites(["strasbourg",24],self.study)

    def test_matrix_is_conservative_same_basket_no_score(self):
        plan=new_plan(); copy=deepcopy(plan)
        data=deepcopy(self.study)
        m=comparative_matrix(self.study,self.five,self.profiles,self.packs,
                             ["mulhouse","strasbourg","freiburg"],self.dest)
        self.assertEqual(len(m["cities"]),3)
        self.assertEqual(m["final_winner"],None)
        self.assertEqual(m["complete_budget"],None)
        self.assertEqual(m["cities"][0]["selected_destinations_count"],15)
        self.assertEqual(m["cities"][0]["documented_shared_basket"],6)
        self.assertEqual(m["cities"][1]["documented_shared_basket"],9)
        self.assertEqual(m["cities"][2]["documented_shared_basket"],0)
        self.assertEqual(m["cities"][2]["routes"][0]["status"],"not_researched")
        self.assertIsNone(m["cities"][2]["routes"][0]["duration_min_oneway"])
        self.assertTrue(all(not c["housing"]["available_2027_count"] for c in m["cities"]))
        self.assertTrue(all(not r["return_2027_verified"] for c in m["cities"]
                            for r in c["routes"]))
        self.assertTrue(comparison_insights(m))
        self.assertEqual(plan,copy)
        self.assertEqual(data,self.study)

    def test_selected_outings_same_for_all_and_lacunas_remain_unknown(self):
        m=comparative_matrix(self.study,self.five,self.profiles,self.packs,
                             ["trier","aachen"],["strasbourg","amsterdam"])
        for city in m["cities"]:
            self.assertEqual([r["destination_id"] for r in city["routes"]],
                             ["strasbourg","amsterdam"])
        self.assertIsNone(m["cities"][1]["routes"][0]["duration_min_oneway"])
        with self.assertRaises(ValueError):
            comparative_matrix(self.study,self.five,self.profiles,self.packs,
                               ["trier"],["not-real"])
        with self.assertRaises(ValueError):
            comparative_matrix(self.study,self.five,self.profiles,self.packs,
                               ["trier"],["paris","paris"])

    def test_portable_selection_and_schema_validation(self):
        cities=["mulhouse","strasbourg","freiburg"]
        raw=export_favorites(cities,self.study)
        self.assertEqual(import_favorites(raw,self.study),cities)
        with self.assertRaises(ValueError):
            import_favorites(b'{"city_ids":["fake"]}',self.study)

    def test_existing_private_archive_compatible_with_old_files(self):
        plan=new_plan();catalog=load_attractions()
        archive=make_archive(plan,catalog,city_favorites=["mulhouse","trier"])
        raw=export_archive(archive,catalog)
        self.assertEqual(import_archive(raw,catalog)["city_favorites"],
                         ["mulhouse","trier"])
        legacy=deepcopy(archive)
        legacy.pop("city_favorites")
        recovered=import_archive(__import__("json").dumps(legacy).encode(),catalog)
        self.assertEqual(recovered["city_favorites"],[])
        self.assertEqual(recovered["plan"],plan)


class FavoriteComparisonStreamlitTests(unittest.TestCase):
    def test_favorites_selection_and_no_plan_changes(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux42_city_activity").set_value("Comparar favoritas").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.multiselect(key="ux41_favorites_widget").set_value(
            ["mulhouse","strasbourg","freiburg"]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux41_favorites"],
                         ["mulhouse","strasbourg","freiburg"])
        app.button(key="ux41_open_strasbourg").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux40_selected_city"],"strasbourg")
        app.button(key="ux40_back_compare").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux41_favorites"],
                         ["mulhouse","strasbourg","freiburg"])
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(app.session_state["advisor_plan"]["revision"],
                         original["revision"])


if __name__=="__main__":
    unittest.main()
