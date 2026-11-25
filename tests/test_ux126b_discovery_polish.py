"""Regression tests for discovery polish; no change to UX126 eligibility."""
import ast
from pathlib import Path
import unittest

from ux501_destination_discovery_ui import _result_caption


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryPresentationTests(unittest.TestCase):
    def test_counter_includes_all_research_destinations(self):
        rows=[{"id":key} for key in ("r1","e1","r2","e2","o")]
        self.assertEqual(_result_caption(rows),"5 destinos")
        self.assertEqual(_result_caption(rows[:1]),"1 destino")
        self.assertEqual(_result_caption([]),"Nenhum destino")

    def test_portuguese_selection_and_json_upload_contract(self):
        violations = []
        for path in sorted(ROOT.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if not isinstance(node.func.value, ast.Name) or node.func.value.id != "st":
                    continue
                keywords = {k.arg: k.value for k in node.keywords}
                empty_select = node.func.attr == "selectbox" and (
                    isinstance(keywords.get("index"), ast.Constant) and keywords["index"].value is None)
                if node.func.attr == "multiselect" or empty_select:
                    if "placeholder" not in keywords:
                        violations.append(f"{path.name}:{node.lineno}: placeholder")
                if node.func.attr == "file_uploader":
                    types = keywords.get("type")
                    if isinstance(types, (ast.List, ast.Tuple)) and any(
                            isinstance(x, ast.Constant) and x.value == "json" for x in types.elts):
                        if "max_upload_size" not in keywords:
                            violations.append(f"{path.name}:{node.lineno}: upload limit")
                        if "Arquivo .json exportado por este app" not in path.read_text(encoding="utf-8"):
                            violations.append(f"{path.name}:{node.lineno}: upload caption")
        self.assertEqual(violations, [])

    def test_real_export_fits_upload_limit(self):
        from attractions_model import load_attractions
        from continuity_archive_model import make_archive, export_archive, MAX_FILE_BYTES
        from trip_plan_model import new_plan
        catalog = load_attractions()
        blob = export_archive(make_archive(new_plan(), catalog), catalog)
        self.assertGreater(len(blob), 0)
        self.assertLessEqual(len(blob), MAX_FILE_BYTES)
        self.assertLess(MAX_FILE_BYTES, 5 * 1024 * 1024)


class DiscoveryNavigationTests(unittest.TestCase):
    def test_same_cycle_page_and_navigation_state(self):
        from streamlit.testing.v1 import AppTest
        from trip01_supplemental_discovery import build_exploration_discovery
        from attractions_model import load_attractions
        from itinerary_eligibility import itinerary_eligibility, eligibility_index
        from copy import deepcopy
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        original = deepcopy(app.session_state["advisor_plan"])
        catalog = load_attractions()
        index = eligibility_index(catalog)
        all_rows = build_exploration_discovery()["destinations"]
        n = sum(itinerary_eligibility(x["id"], catalog, index=index)["status"] == "eligible"
                for x in all_rows)
        captions = lambda: [x.value for x in app.caption]
        pages = (len(all_rows) + 11) // 12
        self.assertIn(f"Página 1 de {pages}", captions())
        self.assertTrue(app.button(key="ux126b_previous_bottom").disabled)
        self.assertEqual(captions().count(f"Página 1 de {pages}"), 2)
        self.assertNotIn("ux126_eligibility_filter",{x.key for x in app.radio})
        app.button(key="ux126b_next_bottom").click().run()
        self.assertEqual(captions().count(f"Página 2 de {pages}"), 2)
        app.button(key="ux126b_next").click().run()
        self.assertIn(f"Página 3 de {pages}", captions())
        app.text_input(key="ux501_search").set_value("Lux").run()
        self.assertNotIn("ux126b_next", {b.key for b in app.button})
        self.assertNotIn("ux126b_previous", {b.key for b in app.button})
        self.assertNotIn("ux126b_next_bottom", {b.key for b in app.button})
        self.assertNotIn("ux126b_previous_bottom", {b.key for b in app.button})
        self.assertEqual(app.session_state["ux502_discovery_filters"]["ux501_page"], 1)
        app.selectbox(key="ux501_country").set_value("Luxemburgo").run()
        categories = app.multiselect(key="ux501_categories")
        if categories.options:
            categories.set_value([categories.options[0]]).run()
        expected = deepcopy(app.session_state["ux502_discovery_filters"])
        app.button(key="ux_sidebar_nav_2").click().run()
        # Simulate widget state left behind by a previously rendered view.
        app.session_state["ux501_search"] = "Aachen"
        app.session_state["ux126_eligibility_filter"] = "Todos"
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertNotIn("ux126_eligibility_filter",{x.key for x in app.radio})
        self.assertNotIn("ux126_eligibility_filter",app.session_state["ux502_discovery_filters"])
        self.assertEqual(app.text_input(key="ux501_search").value, "Lux")
        self.assertEqual(app.selectbox(key="ux501_country").value, "Luxemburgo")
        self.assertEqual(app.multiselect(key="ux501_categories").value, expected["ux501_categories"])
        self.assertEqual(app.session_state["ux502_discovery_filters"], expected)
        self.assertEqual(app.session_state["advisor_plan"], original)


class DiscoveryHandoffTests(unittest.TestCase):
    """Use the real navigation callbacks and discovery renderer in one session."""
    SCRIPT = """
import streamlit as st
from attractions_model import load_attractions
from planning_session import active_plan
from ux61_destination_board_ui import render_destination_board
from ux504_guided_journey_model import apply_navigation_request
from ux504_guided_journey_ui import request_step
from ux64_navigation_model import select_public_task
from ux501_destination_discovery_ui import render_independent_destination_discovery

apply_navigation_request(st.session_state)
if st.session_state.get("ux_section") == "Passeios":
    render_independent_destination_discovery()
else:
    render_destination_board(active_plan(), load_attractions())
    st.button("Jornada: Descobrir", key="guided", on_click=request_step, args=("discover",))
    st.button("Navegação: Descobrir", key="public", on_click=select_public_task,
              args=(st.session_state, "Explorar", "Descobrir"))
"""

    def _app(self):
        from streamlit.testing.v1 import AppTest
        from ux502_destination_interests_model import empty_interests, set_interest
        from trip01_supplemental_discovery import build_exploration_discovery
        app = AppTest.from_string(self.SCRIPT, default_timeout=120)
        app.session_state["ux_area"] = "Meu roteiro"
        app.session_state["ux_section"] = "Meu planejamento"
        app.session_state["ux502_view"] = "Descobrir lugares"
        app.session_state["ux502_interests"] = set_interest(
            empty_interests(), "colmar", "interested", build_exploration_discovery())
        app.session_state["ux502_discovery_filters"] = {
            "ux501_country": "Luxemburgo", "ux501_categories": [],
            "ux501_search": "Lux", "ux501_page": 1,
            "ux126_eligibility_filter": "Posso planejar agora",
        }
        app.run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        # Explicitly recreate stale widget keys even if Streamlit cleaned them.
        app.session_state["ux501_search"] = "Aachen"
        app.session_state["ux501_country"] = "Alemanha"
        app.session_state["ux126_eligibility_filter"] = "Todos"
        app.session_state["ux501_page"] = 3
        return app

    def test_ux61_target_overrides_stale_widgets_and_incompatible_filters(self):
        app = self._app()
        app.button(key="ux61_explore_colmar").click().run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(app.text_input(key="ux501_search").value, "Colmar")
        self.assertEqual(app.selectbox(key="ux501_country").value, "Todos os países")
        self.assertNotIn("ux126_eligibility_filter",{x.key for x in app.radio})
        self.assertNotIn("ux126_add_colmar",{b.key for b in app.button})
        self.assertTrue(any("Na minha lista" in x.value for x in app.caption))
        self.assertEqual(app.session_state["ux502_discovery_filters"]["ux501_page"], 1)

    def _assert_preserved(self, key):
        app = self._app()
        app.button(key=key).click().run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(app.text_input(key="ux501_search").value, "Lux")
        self.assertEqual(app.selectbox(key="ux501_country").value, "Luxemburgo")
        self.assertNotIn("ux126_eligibility_filter",{x.key for x in app.radio})
        self.assertNotIn("ux126_eligibility_filter",app.session_state["ux502_discovery_filters"])
        self.assertEqual(app.session_state["ux502_discovery_filters"]["ux501_page"], 1)

    def test_ux504_guided_handoff_preserves_snapshot(self):
        self._assert_preserved("guided")

    def test_ux64_public_navigation_preserves_snapshot(self):
        self._assert_preserved("public")
