"""Regression tests for discovery polish; no change to UX126 eligibility."""
import ast
from pathlib import Path
import unittest

from ux501_destination_discovery_ui import _ordered_matches, _result_caption


ROOT = Path(__file__).resolve().parents[1]


class DiscoveryPresentationTests(unittest.TestCase):
    def test_stable_partition_and_counter(self):
        rows = [{"id": key} for key in ("r1", "e1", "r2", "e2", "o")]
        statuses = dict(zip(("r1", "e1", "r2", "e2", "o"),
                            ("research_only", "eligible", "research_only", "eligible", "other_stage")))
        eligibility = {k: {"status": v} for k, v in statuses.items()}
        self.assertEqual([x["id"] for x in _ordered_matches(rows, eligibility, "Todos")],
                         ["e1", "e2", "r1", "r2", "o"])
        eligible = _ordered_matches(rows, eligibility, "Posso planejar agora")
        self.assertEqual(eligible, [rows[1], rows[3]])
        for items, expected in (
            ([], "Nenhum destino"),
            ([rows[1]], "1 destino pode entrar no roteiro"),
            ([rows[0]], "1 destino em pesquisa"),
            ([rows[4]], "1 destino em outra etapa"),
            (rows[:2], "2 destinos · 1 pode entrar no roteiro · 1 em pesquisa"),
            (eligible, "2 destinos · 2 podem entrar no roteiro"),
            ([rows[0], rows[2]], "2 destinos · 2 em pesquisa"),
            (rows, "5 destinos · 2 podem entrar no roteiro · 2 em pesquisa · 1 em outra etapa"),
        ):
            self.assertEqual(_result_caption(items, eligibility), expected)

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
        app.button(key="ux126b_next").click().run()
        app.button(key="ux126b_next").click().run()
        self.assertIn(f"Página 3 de {pages}", captions())
        app.radio(key="ux126_eligibility_filter").set_value("Posso planejar agora").run()
        self.assertIn(f"Página 1 de {(n+11)//12}", captions())
        self.assertEqual(app.session_state["ux502_discovery_filters"]["ux501_page"], 1)
        app.text_input(key="ux501_search").set_value("Lux").run()
        self.assertNotIn("ux126b_next", {b.key for b in app.button})
        self.assertNotIn("ux126b_previous", {b.key for b in app.button})
        self.assertEqual(app.session_state["ux502_discovery_filters"]["ux501_page"], 1)
        app.selectbox(key="ux501_country").set_value("Luxemburgo").run()
        categories = app.multiselect(key="ux501_categories")
        if categories.options:
            categories.set_value([categories.options[0]]).run()
        expected = deepcopy(app.session_state["ux502_discovery_filters"])
        app.button(key="ux_sidebar_nav_2").click().run()
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(app.radio(key="ux126_eligibility_filter").value, "Posso planejar agora")
        self.assertEqual(app.text_input(key="ux501_search").value, "Lux")
        self.assertEqual(app.selectbox(key="ux501_country").value, "Luxemburgo")
        self.assertEqual(app.multiselect(key="ux501_categories").value, expected["ux501_categories"])
        self.assertEqual(app.session_state["ux502_discovery_filters"], expected)
        self.assertEqual(app.session_state["advisor_plan"], original)
