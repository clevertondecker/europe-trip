"""UX132C3: independent public task and one-time session migration."""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

from ux_navigation import bootstrap, route, from_legacy, set_from_legacy, LEGACY_PAGES, SECTIONS
from rec03a_suggestions_ui import highlight_explanation
from ux64_navigation_model import PUBLIC_TASKS, select_public_task, public_task


class CoverageRouteTests(unittest.TestCase):
    def test_independent_route_and_return_preserve_state(self):
        state = {"ux_area": "Explorar", "ux_section": "Comparar",
                 "ux112_active_view": "Minha comparação",
                 "ux112_active_view_shadow": "Minha comparação",
                 "ux132_domain_shadow": "Morar e trabalhar",
                 "ux132c2_scope_shadow": "all",
                 "rec03a_scope": {"confirmed": True},
                 "rec03a_draft": ["paris"], "advisor_plan": {"revision": 3}}
        before = deepcopy(state)
        self.assertIn("Cobertura dos dados", PUBLIC_TASKS["Explorar"])
        select_public_task(state, "Explorar", "Cobertura dos dados")
        self.assertEqual(bootstrap(state), ("Cobertura dos dados", None, None, None))
        self.assertEqual(public_task(state["ux_area"], state["ux_section"]), "Cobertura dos dados")
        select_public_task(state, "Explorar", "Comparar bases")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")
        for key in before:
            self.assertEqual(state[key], before[key])

    def test_migrate_old_coverage_session_once(self):
        state = {"ux_area": "Explorar", "ux_section": "Comparar",
                 "ux112_active_view_shadow": "Cobertura dos dados",
                 "ux112_active_view": "Cobertura dos dados",
                 "ux132_domain_shadow": "Atrações turísticas"}
        self.assertEqual(bootstrap(state)[0], "Cobertura dos dados")
        self.assertEqual(state["ux112_active_view_shadow"], "Explorar alternativas")
        self.assertEqual(state["ux132_domain_shadow"], "Atrações turísticas")
        select_public_task(state, "Explorar", "Comparar bases")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")

    def test_explicit_comparison_request_beats_stale_coverage(self):
        state = {"ux_area": "Explorar", "ux_section": "Passeios",
                 "ux112_active_view_shadow": "Cobertura dos dados"}
        select_public_task(state, "Explorar", "Comparar bases")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")

    def test_explicit_legacy_request_beats_stale_nested_view(self):
        state = {"ux_area": "Explorar", "ux_section": "Comparar",
                 "ux112_active_view_shadow": "Cobertura dos dados"}
        set_from_legacy(state, "Comparar cidades")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")

    def test_all_canonical_pages_registered(self):
        for area, sections in SECTIONS.items():
            for section in sections:
                with self.subTest(area=area, section=section):
                    self.assertIn(route(area, section)[0], LEGACY_PAGES)

    def test_legacy_routes(self):
        self.assertEqual(from_legacy("Comparar cidades"), ("Explorar", "Comparar"))
        self.assertEqual(from_legacy("Cobertura dos dados"), ("Explorar", "Cobertura dos dados"))
        self.assertEqual(route("Explorar", "Mapa")[0], "Mapa & destinos")


class HighlightTests(unittest.TestCase):
    def test_four_kinds_and_reasons(self):
        def label(kind, reasons=()):
            return highlight_explanation({"highlight": True, "highlight_kind": kind,
                                          "reasons": reasons})
        self.assertIn("mesmos trajetos", label("complete_reference_group"))
        self.assertIn("sem grupo completo equivalente", label("individual_complete"))
        self.assertIn("acesso dentro da cidade", label("local_investigation"))
        self.assertIn("não significa que seja a melhor", label("conditional_investigation"))
        self.assertIn("trajetos pesquisados em comum", label("conditional_investigation",
                      ["menor_minimo_ponderado_no_mesmo_subconjunto"]))
        self.assertIsNone(highlight_explanation({"highlight": False, "highlight_kind": "individual_complete"}))


class RealAppNavigationTests(unittest.TestCase):
    def test_real_app_coverage_and_return_preserve_navigation(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"),
                                default_timeout=120)
        app.session_state["ux_area"] = "Explorar"
        app.session_state["ux_section"] = "Comparar"
        app.run()
        self.assertFalse(app.exception, str(app.exception))
        app.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertFalse(app.exception, str(app.exception))
        app.segmented_control(key="ux112_active_view").set_value(None).run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.segmented_control(key="ux112_active_view").value, "Minha comparação")
        self.assertEqual(app.session_state["ux112_active_view_shadow"], "Minha comparação")
        keys = ("advisor_plan", "ux502_interests", "rec03a_scope", "rec03a_draft",
                "rec03a_handoff_base_selection", "ux36_cloud_dirty", "ux_mode", "ux_days")
        before = {k: deepcopy(app.session_state[k]) for k in keys if k in app.session_state}
        with patch("rec03a_suggestions_ui.recommend_bases") as engine:
            app.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados").run()
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(app.session_state["main_navigation"], "Cobertura dos dados")
            self.assertEqual(sum(w.key == "ux132_domain" for w in app.segmented_control), 1)
            self.assertFalse(any(w.key == "ux112_active_view" for w in app.segmented_control))
            app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
            app.segmented_control(key="ux132_coverage_section").set_value("Destinos").run()
            app.text_input(key="ux132_search_destinations").set_value("Colmar").run()
            app.segmented_control(key="ux132_coverage_section").set_value(None).run()
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(app.segmented_control(key="ux132_coverage_section").value, "Destinos")
            app.segmented_control(key="ux132_domain").set_value(None).run()
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(app.segmented_control(key="ux132_domain").value, "Transporte ferroviário")
            self.assertEqual(app.text_input(key="ux132_search_destinations").value, "Colmar")
            engine.assert_not_called()
        app.segmented_control(key="ux64_public_task").set_value("Comparar bases").run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.segmented_control(key="ux112_active_view").value, "Minha comparação")
        app.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados").run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.segmented_control(key="ux132_domain").value, "Transporte ferroviário")
        self.assertEqual(app.text_input(key="ux132_search_destinations").value, "Colmar")
        for key, value in before.items():
            self.assertEqual(app.session_state[key], value, key)


if __name__ == "__main__":
    unittest.main()
