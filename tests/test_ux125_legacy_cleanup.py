"""UX125: public navigation replaces duplicated task panels, not stored data."""
import unittest
import re
import unicodedata
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from ux502_destination_interests_model import empty_interests, set_interest
from trip01_supplemental_discovery import build_exploration_discovery

ROOT = Path(__file__).resolve().parents[1]


class LegacyCleanupTests(unittest.TestCase):
    def test_wishlist_discovery_and_planning_use_public_tabs(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        plan = deepcopy(app.session_state["advisor_plan"])
        doc = set_interest(empty_interests(), "colmar", "must_visit",
                           build_exploration_discovery())
        app.session_state["ux502_interests"] = deepcopy(doc)
        app.button(key="ux64_sidebar_nav_0").click().run()
        for task in ("Descobrir", "Minha lista", "Descobrir"):
            app.segmented_control(key="ux64_public_task").set_value(task).run()
            self.assertFalse(app.exception, [x.message for x in app.exception])
            self.assertNotIn("ux502_view", {w.key for w in app.radio})
            self.assertNotIn("ux503_open_from_wishlist", {w.key for w in app.button})
            self.assertFalse(any("visualização anterior" in x.label.casefold() or
                                 "comparação personalizada anterior" in x.label.casefold() or
                                 "indicadores do catálogo de desejos" in x.label.casefold()
                                 for x in app.expander))
            self.assertEqual(app.session_state["ux502_interests"], doc)
            self.assertEqual(app.session_state["advisor_plan"], plan)
        app.button(key="ux64_sidebar_nav_1").click().run()
        for task in ("Meus destinos", "Organizar"):
            app.segmented_control(key="ux64_public_task").set_value(task).run()
            self.assertFalse(app.exception, [x.message for x in app.exception])
            self.assertFalse(any("acessar outras etapas" in x.label.casefold()
                                 for x in app.expander))
            self.assertEqual(app.session_state["advisor_plan"], plan)
            self.assertEqual(app.session_state["ux502_interests"], doc)

    def test_no_unapproved_legacy_expanders_across_public_tasks(self):
        # No remaining transitional panel is allowed on a public task.
        allowlist = {}
        from ux64_navigation_model import PUBLIC_TASKS
        def normalize(label):
            return " ".join("".join(ch for ch in unicodedata.normalize("NFKD", label.casefold())
                                    if not unicodedata.combining(ch)).split())
        for restored in (False, True):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
            if restored:
                app.session_state["ux502_view"] = "Minha lista"
                app.session_state["ux_compare_mode"] = "Evidências e lacunas"
            app.run()
            self.assertFalse(app.exception, [x.message for x in app.exception])
            plan = deepcopy(app.session_state["advisor_plan"])
            for index, (area, tasks) in enumerate(PUBLIC_TASKS.items()):
                app.button(key="ux64_sidebar_nav_"+str(index)).click().run()
                for task in tasks:
                    app.segmented_control(key="ux64_public_task").set_value(task).run()
                    self.assertFalse(app.exception, [x.message for x in app.exception])
                    self.assertNotIn("scenario_sidebar", {w.key for w in app.selectbox})
                    self.assertNotIn("ux_mode", {w.key for w in app.segmented_control})
                    self.assertNotIn("ux_days", {w.key for w in app.number_input})
                    self.assertNotIn("ux_budget_view", {w.key for w in app.segmented_control})
                    labels = [normalize(e.label) for e in app.expander]
                    violations = [label for label in labels
                                  if re.search(r"anterior|temporario|[·•]\s*avancado",label)
                                  and label not in allowlist.get((area,task),{})]
                    self.assertEqual(violations, [], (area,task,restored))
                    self.assertEqual(app.session_state["advisor_plan"], plan)

    def test_base_studies_are_secondary_and_preserve_official_plan(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        plan = deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Comparar bases").run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertNotIn("ux_compare_mode", {w.key for w in app.segmented_control})
        app.button(key="ux125b_open_base_studies").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_guide_view"], "Estudos de cidades-base")
        self.assertIsNone(app.segmented_control(key="ux64_public_task").value)
        self.assertNotIn("ux_improve_view",{w.key for w in app.selectbox})
        self.assertNotIn("ux_guide_view",{w.key for w in app.selectbox})
        self.assertFalse(any("Melhorar nosso roteiro" in m.value for m in app.markdown))
        self.assertIn("ux_compare_mode", {w.key for w in app.segmented_control})
        app.segmented_control(key="ux_compare_mode").set_value("Referências históricas").run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertIn("city_compare_section", {w.key for w in app.segmented_control})
        self.assertIsNone(app.segmented_control(key="ux64_public_task").value)
        app.button(key="ux125b_return_comparison").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertNotIn("ux_compare_mode", {w.key for w in app.segmented_control})
        self.assertEqual(app.session_state["advisor_plan"], plan)

    def test_base_outings_guide_is_not_mounted_in_discovery_or_wishlist(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        plan = deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_0").click().run()
        for task in ("Descobrir", "Minha lista"):
            app.segmented_control(key="ux64_public_task").set_value(task).run()
            self.assertFalse(app.exception, [x.message for x in app.exception])
            self.assertNotIn("attractions_scenario_base", {w.key for w in app.selectbox})
        app.button(key="ux64_sidebar_nav_1").click().run()
        app.button(key="ux125b_home_base_outings").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertIn("attractions_scenario_base", {w.key for w in app.selectbox})
        self.assertNotIn("ux501_search", {w.key for w in app.text_input})
        self.assertIsNone(app.segmented_control(key="ux64_public_task").value)
        self.assertNotIn("ux_guide_view",{w.key for w in app.selectbox})
        app.button(key="ux125b_return_discovery").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertIn("ux501_search", {w.key for w in app.text_input})
        self.assertNotIn("attractions_scenario_base", {w.key for w in app.selectbox})
        self.assertEqual(app.session_state["advisor_plan"], plan)

    def test_consultant_is_in_planning_not_budget(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        plan = deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertNotIn("ux_budget_view", {w.key for w in app.segmented_control})
        self.assertNotIn("advisor_base", {w.key for w in app.selectbox})
        self.assertNotIn("budget_preset_review_button", {w.key for w in app.button})
        app.button(key="ux_sidebar_nav_2").click().run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Consultor de passeios").run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertIn("budget_preset_review_button", {w.key for w in app.button})
        self.assertEqual(app.session_state["advisor_plan"], plan)

    def test_focused_guide_can_navigate_directly_to_destination_editor(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        plan = deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Comparar bases").run()
        app.button(key="ux125b_open_base_studies").click().run()
        self.assertIsNone(app.segmented_control(key="ux64_public_task").value)
        app.segmented_control(key="ux64_public_task").set_value("Meus destinos").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual((app.session_state["ux_area"],app.session_state["ux_section"]),
                         ("Meu roteiro","Meu planejamento"))
        self.assertNotIn("ux_compare_mode",{w.key for w in app.segmented_control})
        self.assertNotIn("ux125b_focused_guide",app.session_state)
        app.segmented_control(key="ux64_public_task").set_value(None).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.segmented_control(key="ux64_public_task").value,"Meus destinos")
        self.assertEqual(app.session_state["advisor_plan"],plan)
