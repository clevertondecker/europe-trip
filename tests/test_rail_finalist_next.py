"""Progressive shortlisted-rail research stays source-scoped and read-only."""
import unittest
from copy import deepcopy
from base_change_model import known_route,destination_impact
from attractions_model import load_base_routes
from base_explorer_model import load_exploration
from trip_plan_model import new_plan


class RailFinalistExpansionTests(unittest.TestCase):
    EXPECTED={
        ("nancy","luxembourg"):(91,106),
        ("nancy","brussels"):(211,244),
        ("metz","brussels"):(199,221),
        ("lille","luxembourg"):(231,278),
    }

    def test_four_new_official_sourced_observations(self):
        for (base,destination),(fast,typical) in self.EXPECTED.items():
            with self.subTest(base=base,destination=destination):
                row=known_route(base,destination)
                self.assertEqual(row["minutes"],fast)
                self.assertEqual(row["representative_minutes"],typical)
                self.assertIn("sncf-connect.com",row["source"])
                self.assertIsNone(row["fare"])
                self.assertFalse(row["return_verified"])
                self.assertGreaterEqual(typical,fast)

    def test_original_10_priority_routes_unchanged(self):
        for base in ("mulhouse","strasbourg"):
            for destination in ("luxembourg","interlaken","brussels","bruges_be","rotterdam"):
                row=known_route(base,destination)
                self.assertIsInstance(row["minutes"],int)
                self.assertFalse(row["return_verified"])

    def test_legacy_schema_and_exploratory_only(self):
        load_base_routes()
        exploration=load_exploration()
        self.assertEqual(exploration["schema_version"],1)

    def test_cross_base_comparison_never_updates_plan(self):
        plan=new_plan()
        old=deepcopy(plan)
        comparison=destination_impact(plan,"nancy",["luxembourg","brussels"])
        self.assertEqual(len(comparison),2)
        self.assertEqual(plan,old)
        self.assertIsNotNone(comparison[1]["official_minutes"])
        self.assertFalse(any("roundtrip_couple_eur" in item for item in comparison))

    def test_unresearched_remains_unknown(self):
        self.assertIsNone(known_route("nancy","unknown_test_destination")["minutes"])
        self.assertIsNone(known_route("metz","unknown_test_destination")["minutes"])


class RailFinalistAppTest(unittest.TestCase):
    def test_nancy_and_lille_research_visible_without_plan_change(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=110).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        previous=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        app.button(key="ux125b_open_base_studies").click().run()
        app.segmented_control(key="ux_compare_mode").set_value("Estudos de troca").run()
        app.multiselect(key="ux34_candidates").set_value(["nancy","lille"]).run()
        app.multiselect(key="ux34_destinations").set_value(["luxembourg","brussels"]).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],previous)
        displayed=" ".join(str(x.value) for x in app.dataframe)
        self.assertIn("Luxemburgo",displayed)
        self.assertIn("Bruxelas",displayed)


if __name__=="__main__":unittest.main()
