"""Legacy route identities survive 3-area visual migration."""
import unittest
from tests.nav_helpers import open_public
from ux64_navigation_model import (
    PUBLIC_AREAS, PUBLIC_TASKS, TARGETS,
    public_area, public_task, select_public_area, select_public_task,
)


class PublicNavigationTests(unittest.TestCase):
    def test_three_areas_cover_all_public_tasks(self):
        self.assertEqual(PUBLIC_AREAS,("Explorar","Planejar","Orçamento"))
        self.assertEqual(len(TARGETS),sum(len(v) for v in PUBLIC_TASKS.values()))

    def test_legacy_areas_map_to_plan(self):
        self.assertEqual(public_area("Minha viagem"),"Planejar")
        self.assertEqual(public_area("Meu roteiro"),"Planejar")
        self.assertEqual(public_task("Meu roteiro","Organizar viagem"),"Organizar")
        self.assertIsNone(public_task("Meu roteiro","Melhorar meu roteiro"))

    def test_wishlist_and_discovery_share_one_legacy_tool(self):
        state={}
        select_public_task(state,"Explorar","Minha lista")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Explorar","Passeios"))
        self.assertEqual(state["ux502_view"],"Minha lista")
        select_public_task(state,"Explorar","Descobrir")
        self.assertEqual(state["ux502_view"],"Descobrir lugares")

    def test_plan_area_home_still_routes_to_old_authoritative_screen(self):
        state={}
        select_public_area(state,"Planejar")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Minha viagem","Resumo"))
        select_public_task(state,"Planejar","Meus destinos")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Meu roteiro","Meu planejamento"))

    def test_public_compare_focus_resets_manual_without_touching_selection(self):
        state={"rec03a_activity":"Comparação personalizada",
               "rec03a_handoff_base_selection":["metz","strasbourg"],
               "rec03a_handoff_previous_manual":{"ux504_bases_shadow":["mulhouse","nancy"]}}
        select_public_task(state,"Explorar","Comparar bases")
        self.assertEqual(state["rec03a_activity"],"Cidades sugeridas")
        self.assertEqual(state["rec03a_handoff_base_selection"],["metz","strasbourg"])
        self.assertEqual(state["rec03a_handoff_previous_manual"],
                         {"ux504_bases_shadow":["mulhouse","nancy"]})

    def test_unknown_task_fails_closed(self):
        with self.assertRaises(ValueError):
            select_public_task({},"Planejar","Delete all plans")


class ContextualActivityAppTests(unittest.TestCase):
    def test_wishlist_has_one_comparison_entry_and_no_finance_header(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        open_public(app,"Explorar","Minha lista")
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertFalse(any("page-title'>Meu roteiro" in m.value
                             for m in app.markdown))
        self.assertFalse(any(b.key=="workflow_open_alternative"
                             for b in app.button))
        self.assertFalse(any(b.key=="workflow_open_settings"
                             for b in app.button))
        from ux502_destination_interests_model import empty_interests,set_interest
        app.session_state["ux502_interests"]=set_interest(empty_interests(),"colmar","must_visit")
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(
            [b.label for b in app.button if b.key=="rec03a_open_from_wishlist"],
            ["Comparar cidades-base"])
        # Detailed comparison is reachable only within its canonical task.
        self.assertFalse(any(b.key=="ux503_open_from_wishlist"
                             for b in app.button))
        app.button(key="rec03a_open_from_wishlist").click().run()
        self.assertNotIn("ux125_open_manual_comparison",{b.key for b in app.button})
        self.assertIn("rec03a_confirm_subset",{b.key for b in app.button})
        app.segmented_control(key="ux64_public_task").set_value("Minha lista").run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertFalse(any("page-title'>Meu roteiro" in m.value
                             for m in app.markdown))

    def test_public_tabs_are_still_the_single_visible_task_selector(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        original=app.session_state["advisor_plan"]
        for area,task in (("Explorar","Mapa"),("Explorar","Comparar bases"),
                          ("Planejar","Visão geral"),("Planejar","Meus destinos"),
                          ("Planejar","Organizar"),("Orçamento","Visão financeira"),
                          ("Orçamento","Simulações")):
            with self.subTest(area=area,task=task):
                open_public(app,area,task)
                self.assertFalse(app.exception,[x.message for x in app.exception])
                self.assertEqual(app.session_state["advisor_plan"],original)


if __name__=="__main__":
    unittest.main()
