"""UX 5.1: readable route references and filter semantics (pure view projection)."""
import unittest
from nav_helpers import open_public
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from dq32_explorer_presentation import (
    format_travel_minutes, one_way_minutes, evidence_label,
    visible_destinations, table_rows,
)
from dq32_macro_opportunities_model import opportunity_overview

ROOT = Path(__file__).resolve().parents[1]


class DQ32PresentationTests(unittest.TestCase):
    def test_human_duration_format(self):
        for value, expected in ((18,"18 min"),(49,"49 min"),
                                (60,"1h00"),(90,"1h30"),(134,"2h14"),
                                (288,"4h48"),(414,"6h54"),(None,"A pesquisar")):
            with self.subTest(value=value):
                self.assertEqual(format_travel_minutes(value),expected)
        for bad in (-1,1.2,True,"100"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                format_travel_minutes(bad)

    def test_country_duration_and_order_filters_are_pure(self):
        src = [
            dict(destination_id="x",name="Rota longa",country="França",
                 attraction_count=1,minimum_train_oneway_min=280,
                 indicative_train_oneway_min=None,local=False),
            dict(destination_id="y",name="Rota curta",country="Bélgica",
                 attraction_count=4,minimum_train_oneway_min=None,
                 indicative_train_oneway_min=45,local=False),
            dict(destination_id="z",name="Sem pesquisa",country="França",
                 attraction_count=2,minimum_train_oneway_min=None,
                 indicative_train_oneway_min=None,local=False),
        ]
        prior=deepcopy(src)
        self.assertEqual([x["destination_id"] for x in
            visible_destinations(src,duration="Até 1h")],["y"])
        self.assertEqual([x["destination_id"] for x in
            visible_destinations(src,duration="Mais de 4h")],["x"])
        self.assertEqual([x["destination_id"] for x in
            visible_destinations(src,duration="Sem referência")],["z"])
        self.assertEqual([x["destination_id"] for x in
            visible_destinations(src,sort="Menor tempo")],["y","x","z"])
        self.assertEqual([x["destination_id"] for x in
            visible_destinations(src,sort="Mais atrações")],["y","z","x"])
        self.assertEqual(len(visible_destinations(src,countries=["França"])),2)
        self.assertEqual(src,prior)

    def test_source_and_readable_table_use_existing_domain_data(self):
        overview=opportunity_overview("mulhouse")
        rows=table_rows(overview["destinations"])
        self.assertEqual(len(rows),overview["registry_destinations"])
        formatted=[x for x in rows if x["Mínimo de ida (min)"] is not None]
        self.assertTrue(formatted)
        self.assertTrue(all(" min" in x["Tempo de ida"] or "h" in x["Tempo de ida"]
                            for x in formatted))
        self.assertTrue(all(x["Fonte"] and x["Fonte"].startswith("https://")
                            for x in formatted))
        self.assertEqual(overview["official_plan_modified"],False)

    def test_streamlit_table_and_filters_preserve_official_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        official=deepcopy(app.session_state["advisor_plan"])
        open_public(app,"Planejar","Visão geral")
        app.button(key="ux125b_home_base_outings").click().run()
        app.selectbox(key="attractions_scenario_base").set_value("lille").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.selectbox(key="ux_dq32_opportunity_group").set_value("Todos os destinos").run()
        frame=next(x.value for x in app.dataframe if "Tempo de ida" in x.value.columns)
        self.assertIn("País",frame.columns)
        self.assertIn("Evidência",frame.columns)
        self.assertIn("Mínimo de ida (min)",frame.columns)
        app.selectbox(key="ux_dq32_duration").set_value("Até 1h").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        app.selectbox(key="ux_dq32_duration").set_value("Todas").run()
        app.segmented_control(key="ux_dq32_view").set_value("Cartões").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)


if __name__=="__main__":
    unittest.main()
