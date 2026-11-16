"""UX 4.0 phase 1: practical research navigation, no data or TripPlan mutations."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest
from base_research_expanded_model import load_research
from five_base_comparison_model import BASE_IDS,load_five_base_evidence
from ux40_research_model import ACTIVITIES,five_base_cards,filter_candidates

ROOT=Path(__file__).resolve().parents[1]


class UX40ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_research()
        cls.five=load_five_base_evidence()

    def test_five_cards_are_derived_from_same_data_without_ranking(self):
        previous=deepcopy(self.data)
        cards=five_base_cards(self.data,self.five)
        self.assertEqual(tuple(x["id"] for x in cards),BASE_IDS)
        self.assertEqual(len(cards),5)
        self.assertEqual({x["id"]:x["with_station_times"] for x in cards},
                         {"offenburg":5,"trier":1,"mulhouse":6,
                          "strasbourg":10,"lille":6})
        self.assertTrue(all(x["housing_count"]==3 for x in cards))
        self.assertTrue(all(x["confirmed_2027_quotes"]==0 for x in cards))
        self.assertTrue(all("score" not in x for x in cards))
        self.assertEqual(self.data,previous)

    def test_30_candidates_and_combined_filters(self):
        self.assertEqual(len(filter_candidates(self.data)),30)
        finalists=filter_candidates(self.data,only_finalists=True)
        self.assertEqual(len(finalists),12)
        german=filter_candidates(self.data,country="Alemanha",only_finalists=True)
        self.assertEqual({x["id"] for x in german},
                         {"freiburg","offenburg","karlsruhe","trier","aachen"})
        exact=filter_candidates(self.data,country="Alemanha",
                                only_finalists=True,corridor="Estrasburgo–Floresta Negra")
        self.assertEqual([x["id"] for x in exact],["offenburg"])
        found=filter_candidates(self.data,evidence="Sem amostras de moradia")
        self.assertTrue(found)
        self.assertTrue(all(not c["housing_offers"] for c in found))


class UX40StreamlitTests(unittest.TestCase):
    def setUp(self):
        self.app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        self.assertFalse(self.app.exception,[e.message for e in self.app.exception])
        self.official=deepcopy(self.app.session_state["advisor_plan"])
        self.app.radio(key="ux_area").set_value("Explorar").run()
        self.app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.app.segmented_control(key="ux42_city_activity").set_value("Comparar favoritas").run()
        self.assertFalse(self.app.exception,[e.message for e in self.app.exception])

    def test_three_actions_and_five_cards_without_full_report_at_top(self):
        self.assertEqual(tuple(ACTIVITIES),("Comparar cidades","Explorar uma cidade",
                                            "Todas as candidatas"))
        self.assertEqual(self.app.session_state["ux42_city_activity"],"Comparar favoritas")
        self.assertTrue(any("Comparar favoritas" in x.value
                            for x in self.app.markdown))
        self.assertIn("ux40_open_offenburg",{b.key for b in self.app.button})
        self.assertIn("five_base_destinations",{x.key for x in self.app.multiselect})
        self.assertEqual(self.app.session_state["advisor_plan"],self.official)

    def test_open_offenburg_and_return_without_losing_context(self):
        self.app.button(key="ux40_open_offenburg").click().run()
        self.assertFalse(self.app.exception,[e.message for e in self.app.exception])
        self.assertEqual(self.app.session_state["ux42_city_activity"],"Explorar cidades")
        self.assertEqual(self.app.session_state["expanded_bases_detail_city"],"offenburg")
        self.app.button(key="ux40_back_compare").click().run()
        self.assertEqual(self.app.session_state["ux42_city_activity"],"Comparar favoritas")
        # Widget state is removed when its activity is hidden; durable state remains.
        self.assertEqual(self.app.session_state["ux40_selected_city"],"offenburg")
        self.app.segmented_control(key="ux42_city_activity").set_value(
            "Explorar cidades").run()
        self.assertEqual(self.app.session_state["expanded_bases_detail_city"],"offenburg")
        self.assertEqual(self.app.session_state["advisor_plan"],self.official)


    def test_same_fifteen_destinations_selection_is_restored(self):
        selected=[x.value for x in self.app.multiselect if x.key=="five_base_destinations"]
        self.assertTrue(selected)
        items=self.app.multiselect(key="five_base_destinations")
        items.set_value(["strasbourg","luxembourg_city"]).run()
        self.assertEqual(self.app.session_state["ux40_saved_five_destinations"],
                         ["strasbourg","luxembourg_city"])
        self.app.segmented_control(key="ux40_research_activity").set_value(
            "Explorar uma cidade").run()
        self.app.segmented_control(key="ux42_city_activity").set_value(
            "Comparar favoritas").run()
        self.assertEqual(self.app.session_state["five_base_destinations"],
                         ["strasbourg","luxembourg_city"])
        self.assertEqual(self.app.session_state["advisor_plan"],self.official)

    def test_country_corridor_and_finalist_filter_persist(self):
        self.app.segmented_control(key="ux42_city_activity").set_value("Explorar cidades").run()
        self.app.selectbox(key="expanded_bases_country_filter").set_value("Alemanha").run()
        self.app.checkbox(key="expanded_bases_only_shortlisted").check().run()
        self.assertFalse(self.app.exception,[e.message for e in self.app.exception])
        self.assertTrue(any("5 cidades encontradas" in x.value for x in self.app.caption))
        self.app.segmented_control(key="ux42_city_activity").set_value("Comparar favoritas").run()
        self.app.segmented_control(key="ux40_research_activity").set_value("Todas as candidatas").run()
        self.assertEqual(self.app.session_state["expanded_bases_country_filter"],"Alemanha")
        self.assertTrue(self.app.session_state["expanded_bases_only_shortlisted"])
        self.assertEqual(self.app.session_state["advisor_plan"],self.official)


if __name__=="__main__":
    unittest.main()
