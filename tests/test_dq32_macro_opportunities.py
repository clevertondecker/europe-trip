"""DQ 3.2 — tourism opportunity breadth is not trip feasibility."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_research_expanded_model import load_research
from base_scenario_model import base_options
from rail_evidence_unified_model import load_rail_evidence
from dq32_macro_opportunities_model import (
    load_macro_tourism,validate_macro_tourism,opportunity_overview,
)

ROOT=Path(__file__).resolve().parents[1]


class MacroOpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.macro=load_macro_tourism()
        cls.exploration=load_exploration()
        cls.research=load_research()
        cls.options=base_options()
        cls.rail=load_rail_evidence()

    def get(self,city):
        return opportunity_overview(city,macro=self.macro,catalog=self.catalog,
               exploration=self.exploration,research=self.research,
               options=self.options,rail=self.rail)

    def test_all_thirty_bases_are_available_without_reachability_gate(self):
        self.assertEqual(len(self.options),30)
        for city in self.options:
            with self.subTest(base=city["id"]):
                row=self.get(city["id"])
                self.assertGreaterEqual(row["registry_destinations"],30)
                self.assertIsNone(row["feasible_destinations_count"])
                self.assertIsNone(row["comparison_score"])
                self.assertTrue(row["read_only"])
                self.assertFalse(row["official_plan_modified"])
                self.assertEqual(len(row["destinations"]),row["registry_destinations"])

    def test_sourced_local_expansion_and_all_source_links(self):
        self.assertEqual(len(self.macro["attractions"]),30)
        self.assertGreaterEqual(len({x["city_id"] for x in self.macro["attractions"]}),23)
        for city in ("lille","dijon","trier","aachen","liege","offenburg",
                     "karlsruhe","reims","arras","besancon","selestat",
                     "saverne","namur","esch","saint_louis","belfort",
                     "thionville","baden_baden","saarbrucken","lorrach","kehl"):
            with self.subTest(city=city):
                row=self.get(city)
                self.assertGreater(row["known_local_attractions"],0)
                local=row["local_destinations"]
                self.assertEqual(len(local),1)
                self.assertTrue(all(x["source_url"].startswith("https://")
                                    for x in local[0]["attractions"]))

    def test_lille_keeps_existing_historical_trains_but_no_return(self):
        row=self.get("lille")
        self.assertGreater(row["rail_time_documented_count"],0)
        brussels=next(r for r in row["historical_rail_destinations"]
                      if r["destination_id"]=="brussels")
        self.assertGreater(brussels["minimum_train_oneway_min"],0)
        self.assertTrue(brussels["train_source_url"].startswith("https://"))
        self.assertFalse(brussels["weekend_return_verified"])
        self.assertFalse(brussels["reachable_confirmed"])
        self.assertIsNone(brussels["full_trip_cost_eur"])
        self.assertIsNone(brussels["walk_between_attractions_m"])

    def test_missing_time_is_unknown_not_impossible(self):
        city=self.get("freiburg")
        self.assertTrue(city["unresearched_destinations"])
        self.assertTrue(all(r["minimum_train_oneway_min"] is None and
                            r["reachable_confirmed"] is False
                            for r in city["unresearched_destinations"]))
        self.assertTrue(all(r["status"]=="unresearched_from_base"
                            for r in city["unresearched_destinations"]))

    def test_no_duplicate_luxembourg_identity(self):
        row=self.get("luxembourg_city")
        self.assertEqual(sum(x["destination_id"]=="luxembourg_city"
                             for x in row["destinations"]),1)
        local=row["local_destinations"][0]
        self.assertEqual(local["destination_id"],"luxembourg_city")
        self.assertIsNone(local["minimum_train_oneway_min"])
        self.assertFalse(local["reachable_confirmed"])

    def test_historical_catalog_and_plan_are_untouched(self):
        original=deepcopy(self.catalog)
        full=deepcopy(self.macro)
        result=self.get("arras")
        result["destinations"][0]["name"]="changed"
        self.assertEqual(self.catalog,original)
        self.assertEqual(self.macro,full)
        self.assertEqual(len(self.catalog["attractions"]),65)
        self.assertEqual(len(self.catalog["destinations"]),14)

    def test_duplicate_and_fabricated_fields_rejected(self):
        for mutation in ("duplicate","price","walk","invalid_url"):
            with self.subTest(mutation=mutation):
                sample=deepcopy(self.macro)
                if mutation=="duplicate":
                    sample["attractions"].append(deepcopy(sample["attractions"][0]))
                elif mutation=="price":
                    sample["attractions"][0]["ticket_eur"]=0
                elif mutation=="walk":
                    sample["attractions"][0]["walk_distance_m"]=500
                else:
                    sample["attractions"][0]["source_url"]="not-url"
                with self.assertRaises(ValueError):
                    validate_macro_tourism(sample)

    def test_unknown_base_rejected(self):
        with self.assertRaises(ValueError):
            self.get("not_in_30")


class MacroOpportunityUXTests(unittest.TestCase):
    def test_explore_alt_and_official_without_tripplan_edit(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        original=deepcopy(at.session_state["advisor_plan"])
        at.radio(key="ux_area").set_value("Explorar").run()
        at.segmented_control(key="ux_section").set_value("Passeios").run()
        at.selectbox(key="attractions_scenario_base").set_value("lille").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertTrue(any("Descoberta ampliada" in x.value for x in at.markdown))
        self.assertTrue(any("Atrações locais documentadas" == x.label for x in at.metric))
        at.selectbox(key="ux_dq32_opportunity_group").set_value(
            "Trem histórico documentado").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        at.selectbox(key="attractions_scenario_base").set_value("mulhouse").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["advisor_plan"],original)

    def test_comparison_panel_is_exploratory_and_plan_unchanged(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        before=deepcopy(at.session_state["advisor_plan"])
        at.radio(key="ux_area").set_value("Explorar").run()
        at.segmented_control(key="ux_section").set_value("Comparar").run()
        at.segmented_control(key="ux_compare_mode").set_value("Pesos das 30 cidades").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertTrue(any("Cobertura ampliada de oportunidades" in x.value
                            for x in at.markdown))
        self.assertEqual(at.session_state["advisor_plan"],before)


if __name__=="__main__":
    unittest.main()
