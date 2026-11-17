"""UX 5.0.3 — fixed basket, historical provenance and UI navigation."""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests, set_interest
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux501_destination_discovery_model import build_destination_discovery
from base_research_expanded_model import load_research

ROOT = Path(__file__).resolve().parents[1]


def sample_wishes():
    d=empty_interests()
    for destination,priority in (
        ("bruges_be","interested"),("colmar","must_visit"),
        ("basel","must_visit"),("strasbourg","maybe"),("lille","discarded")):
        d=set_interest(d,destination,priority)
    return d


class DestinationBaseComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_destination_discovery()
        cls.research=load_research()

    def test_two_to_five_bases_reuse_same_priority_ordered_basket(self):
        wishes=sample_wishes()
        snapshot=deepcopy(wishes)
        for bases in (["mulhouse","strasbourg"],
                      ["mulhouse","strasbourg","lille"],
                      ["mulhouse","strasbourg","lille","metz","nancy"]):
            result=compare_wishlist_bases(wishes,bases,discovery=self.discovery,
                                           research=self.research,rail={"by_pair":{}},
                                           exploration={"routes":[]})
            expected=["colmar","basel","bruges_be","strasbourg"]
            self.assertEqual([x["id"] for x in result["destinations"]],expected)
            for base_id in bases:
                self.assertEqual([x["destination_id"] for x in result["rows"]
                                  if x["base_id"]==base_id],expected)
            self.assertEqual(result["discarded_count"],1)
            self.assertFalse(result["quality_ranking_available"])
            self.assertFalse(result["official_plan_modified"])
        self.assertEqual(wishes,snapshot)

    def test_visual_subset_does_not_modify_active_wishlist(self):
        original=sample_wishes()
        before=deepcopy(original)
        result=compare_wishlist_bases(
            original,["mulhouse","lille"],
            discovery=self.discovery,research=self.research,
            visible_destination_ids=["bruges_be","colmar"],
            rail={"by_pair":{}},exploration={"routes":[]})
        self.assertEqual([d["id"] for d in result["destinations"]],
                         ["colmar","bruges_be"])
        self.assertEqual(result["active_destination_count"],4)
        self.assertEqual(result["discarded_count"],1)
        self.assertEqual(len(result["rows"]),4)
        self.assertEqual(original,before)
        with self.assertRaises(ValueError):
            compare_wishlist_bases(
                original,["mulhouse","lille"],
                discovery=self.discovery,research=self.research,
                visible_destination_ids=["lille"],
                rail={"by_pair":{}},exploration={"routes":[]})

    def test_reject_invalid_base_count_and_duplicates(self):
        for bases in ([],["mulhouse"],["mulhouse"]*2,
                      ["mulhouse","unknown"],
                      ["mulhouse","strasbourg","metz","nancy","lille","basel"]):
            with self.subTest(bases=bases),self.assertRaises(ValueError):
                compare_wishlist_bases(empty_interests(),bases,
                                       discovery=self.discovery,research=self.research)

    def test_local_unknown_and_observation_provenance(self):
        doc=set_interest(empty_interests(),"strasbourg","must_visit")
        doc=set_interest(doc,"colmar","interested")
        def fake(origin,destination,**kwargs):
            if origin==destination:
                return {"status":"local","minimum_oneway_min":None,
                        "typical_oneway_min":None,"source_url":None,"source_date":None,
                        "source_dataset":None,"observations":[]}
            if (origin,destination)==("mulhouse","colmar"):
                return {"status":"historical_time","minimum_oneway_min":35,
                        "typical_oneway_min":48,"source_url":"https://example.org/rail",
                        "source_date":"2026-11-14","source_dataset":"sample",
                        "observations":[{"minimum_oneway_min":35,"source_url":"https://example.org/rail",
                                         "transfers":1},{"minimum_oneway_min":45,
                                         "source_url":"https://example.org/alternate"}]}
            return {"status":"not_researched","minimum_oneway_min":None,
                    "typical_oneway_min":None,"source_url":None,"source_date":None,
                    "source_dataset":None,"observations":[]}
        with patch("ux503_destination_base_comparison_model.get_rail_evidence",side_effect=fake):
            result=compare_wishlist_bases(doc,["strasbourg","mulhouse"],
                                          discovery=self.discovery,research=self.research,
                                          rail={},exploration={})
        local=next(r for r in result["rows"] if
                   r["base_id"]==r["destination_id"]=="strasbourg")
        timed=next(r for r in result["rows"] if
                   r["base_id"]=="mulhouse" and r["destination_id"]=="colmar")
        self.assertEqual(local["status"],"Local — acesso a verificar")
        self.assertIsNone(local["minimum_oneway_min"])
        self.assertEqual(timed["minimum_oneway_min"],35)
        self.assertEqual(timed["typical_oneway_min"],48)
        self.assertEqual(timed["source_date"],"2026-11-14")
        self.assertEqual(timed["transfers"],1)
        self.assertTrue(timed["divergent_sources"])
        self.assertFalse(timed["return_weekend_verified"])
        self.assertFalse(timed["local_access_verified"])

    def test_empty_discarded_and_priority_change(self):
        result=compare_wishlist_bases(empty_interests(),["mulhouse","lille"],
                                      discovery=self.discovery,research=self.research,
                                      rail={"by_pair":{}},exploration={"routes":[]})
        self.assertFalse(result["comparison_ready"])
        discarded=set_interest(empty_interests(),"colmar","discarded")
        d=compare_wishlist_bases(discarded,["mulhouse","lille"],
                                 discovery=self.discovery,research=self.research,
                                 rail={"by_pair":{}},exploration={"routes":[]})
        self.assertEqual(d["discarded_count"],1)
        self.assertEqual(d["destinations"],[])
        d2=set_interest(discarded,"colmar","must_visit")
        updated=compare_wishlist_bases(d2,["mulhouse","lille"],
                                        discovery=self.discovery,research=self.research,
                                        rail={"by_pair":{}},exploration={"routes":[]})
        self.assertEqual([x["id"] for x in updated["destinations"]],["colmar"])


class DestinationBaseComparisonAppTests(unittest.TestCase):
    def test_wishlist_to_compare_and_back_does_not_mutate_tripplan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.session_state["ux502_interests"]=sample_wishes()
        app.radio(key="ux502_view").set_value("Minha lista").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.button(key="ux503_open_from_wishlist").click().run()
        self.assertEqual(app.session_state["ux_section"],"Comparar")
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(2 <= len(app.multiselect(key="ux503_bases").value) <= 5)
        app.button(key="ux503_back_to_wishes").click().run()
        self.assertEqual(app.session_state["ux_section"],"Passeios")
        self.assertEqual(app.session_state["ux502_interests"],sample_wishes())
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_base_switch_limits_and_remove_official(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        original=deepcopy(app.session_state["advisor_plan"])
        official=original["base_city"]
        app.session_state["ux502_interests"]=sample_wishes()
        app.run()
        app.multiselect(key="ux503_bases").set_value(["lille","metz"]).run()
        self.assertEqual(app.session_state["ux503_bases"],["lille","metz"])
        self.assertNotIn(official,app.session_state["ux503_bases"])
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        matrix=next(f.value for f in app.dataframe
                    if "Destino · prioridade" in f.value.columns)
        self.assertIn("Lille",matrix.columns)
        self.assertIn("Metz",matrix.columns)
        self.assertNotIn("Mulhouse",matrix.columns)
        app.multiselect(key="ux503_bases").set_value(["lille"]).run()
        self.assertTrue(any("duas e cinco" in str(w.value).lower() for w in app.warning))
        app.multiselect(key="ux503_bases").set_value([
            "mulhouse","strasbourg","lille","metz","nancy","basel"]).run()
        self.assertTrue(any("duas e cinco" in str(w.message).lower() for w in app.warning))
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_display_filter_and_priority_updates_matrix(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        original=deepcopy(app.session_state["advisor_plan"])
        wish=sample_wishes()
        app.session_state["ux502_interests"]=wish
        app.run()
        app.multiselect(key="ux503_visible_destinations").set_value(["bruges_be","colmar"]).run()
        matrix=next(f.value for f in app.dataframe
                    if "Destino · prioridade" in f.value.columns)
        self.assertEqual(len(matrix),2)
        self.assertIn("Colmar · Imperdível",list(matrix["Destino · prioridade"]))
        self.assertEqual(app.session_state["ux502_interests"],wish)
        revised=set_interest(wish,"bruges_be","must_visit")
        app.session_state["ux502_interests"]=revised
        app.run()
        matrix=next(f.value for f in app.dataframe
                    if "Destino · prioridade" in f.value.columns)
        self.assertIn("Bruges · Imperdível",list(matrix["Destino · prioridade"]))
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(app.session_state["ux502_interests"],revised)

    def test_compare_reflects_changed_priorities_and_favorites(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.session_state["ux41_favorites"]=["lille"]
        app.session_state["ux502_interests"]=sample_wishes()
        app.run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        changed=set_interest(sample_wishes(),"bruges_be","discarded")
        app.session_state["ux502_interests"]=changed
        app.run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["ux41_favorites"],["lille"])
        self.assertEqual(app.session_state["ux502_interests"],changed)
        self.assertEqual(app.session_state["advisor_plan"],original)


if __name__=="__main__":
    unittest.main()
