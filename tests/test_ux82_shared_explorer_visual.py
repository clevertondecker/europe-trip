"""UX82: Explorer's public tasks share the same UX81 visual language."""
from pathlib import Path
from copy import deepcopy
import unittest
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


class ExplorerDesignConsistencyTests(unittest.TestCase):
    def test_all_four_tasks_consume_shared_components(self):
        discovery=(ROOT/"ux501_destination_discovery_ui.py").read_text()
        wishlist=(ROOT/"ux502_destination_interests_ui.py").read_text()
        comparison=(ROOT/"rec03a_suggestions_ui.py").read_text()
        app=(ROOT/"app.py").read_text()
        for name,code in (("Descobrir",discovery),("Minha lista",wishlist),
                          ("Comparar bases",comparison),("Mapa",app)):
            with self.subTest(task=name):
                self.assertIn("page_header(",code)
        # Discovery intentionally uses a gallery, not the obsolete catalog KPI panel.
        self.assertNotIn("kpi_cards(",discovery)
        self.assertNotIn("kpi_cards(",wishlist)
        self.assertIn("render_inline_comparison(",comparison)
        self.assertNotIn("kpi_cards(",comparison)
        self.assertIn("next_action(",wishlist)
        self.assertIn('variant="compact"',app)

    def test_discovery_and_wishlist_use_one_header_each_without_losing_state(self):
        script="""
import streamlit as st
from ux501_destination_discovery_ui import render_independent_destination_discovery
render_independent_destination_discovery()
"""
        app=AppTest.from_string(script,default_timeout=120)
        app.session_state["ux502_view"]="Descobrir lugares"
        app.run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(sum("ui-page-header" in m.value for m in app.markdown),1)
        initial=deepcopy(app.session_state["ux502_interests"])
        app.radio(key="ux502_view").set_value("Minha lista").run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(sum("ui-page-header" in m.value for m in app.markdown),1)
        self.assertEqual(app.session_state["ux502_interests"],initial)
        self.assertFalse(any("Indicadores do catálogo de desejos" in e.label for e in app.expander))
        self.assertTrue(any("destino(s) desejados" in x.value for x in app.caption))

    def test_visual_changes_do_not_introduce_a_second_router_or_persistence(self):
        from ux64_navigation_model import TARGETS,PUBLIC_TASKS
        self.assertEqual(PUBLIC_TASKS["Explorar"],
                         ("Descobrir","Minha lista","Comparar bases","Cobertura dos dados","Mapa"))
        self.assertEqual(TARGETS[("Explorar","Mapa")],("Explorar","Mapa"))
        self.assertEqual(TARGETS[("Explorar","Cobertura dos dados")],("Explorar","Cobertura dos dados"))
        from ux_navigation import route, LEGACY_PAGES
        self.assertEqual(route(*TARGETS[("Explorar","Cobertura dos dados")])[0],"Cobertura dos dados")
        self.assertIn("Cobertura dos dados",LEGACY_PAGES)
        code=(ROOT/"ux87_inline_base_comparison_ui.py").read_text()
        self.assertIn('compare_wishlist_bases(',code)
        self.assertIn('visible_destination_ids=list(scope["destination_ids"])',code)
        self.assertFalse((ROOT/"ux503_destination_base_comparison_ui.py").exists())
        self.assertNotIn('update_fields(',code)


if __name__=="__main__":
    unittest.main()
