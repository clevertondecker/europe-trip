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
        # Explicit transitional exceptions belong exclusively to UX125B.
        allowlist = {
            ("Explorar", "Comparar bases"): {
                "pesquisas e estudos preservados · temporario":
                    "DATA24A migration and private studies must be verified first"},
            ("Orçamento", "Simulações"): {
                "outras ferramentas financeiras · avancado":
                    "UX127 integration required before retiring finance tools"},
        }
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
                    labels = [normalize(e.label) for e in app.expander]
                    violations = [label for label in labels
                                  if re.search(r"anterior|temporario|[·•]\\s*avancado",label)
                                  and label not in allowlist.get((area,task),{})]
                    self.assertEqual(violations, [], (area,task,restored))
                    self.assertEqual(app.session_state["advisor_plan"], plan)
