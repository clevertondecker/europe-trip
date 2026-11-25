"""UX 3.0 routing: four primary areas, preserved legacy deep links and safe state."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from ux_navigation import (
    AREAS, SECTIONS, LEGACY_PAGES, LEGACY_ITINERARY, GUIDES,
    route, from_legacy, bootstrap, set_area, set_task, set_from_legacy,
)

ROOT=Path(__file__).resolve().parents[1]


class UX3NavigationModelTests(unittest.TestCase):
    def test_four_primary_areas_and_every_task_resolves(self):
        self.assertEqual(AREAS, ("Minha viagem", "Explorar", "Meu roteiro", "Orçamento"))
        for area, sections in SECTIONS.items():
            self.assertTrue(sections)
            for section in sections:
                with self.subTest(area=area, section=section):
                    page, itinerary, guide, base_mode = route(area, section)
                    self.assertIn(page, LEGACY_PAGES)
                    if page == "Roteiro":
                        self.assertIn(itinerary, LEGACY_ITINERARY)
                    self.assertIn(guide, (None,) + GUIDES)
                    self.assertIn(base_mode, (None,"Destinos próximos","Pesquisa ampliada"))

    def test_legacy_routes_remain_reachable(self):
        for page in LEGACY_PAGES:
            area, section = from_legacy(page)
            self.assertIn(section, SECTIONS[area])
        for itinerary in LEGACY_ITINERARY:
            area, section = from_legacy("Roteiro", itinerary)
            self.assertIn(section, SECTIONS[area])
        for guide in GUIDES:
            area, section = from_legacy("Roteiro","Guias e pesquisas",guide)
            self.assertIn(section, SECTIONS[area])

    def test_bootstrap_never_modifies_trip_plan(self):
        old_plan={"base_city":"mulhouse","revision":4,"assignments":{"2027-09-20":"colmar"}}
        state={"advisor_plan":deepcopy(old_plan),"main_navigation":"Roteiro",
               "itinerary_section":"Itália"}
        bootstrap(state)
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Meu roteiro","Melhorar meu roteiro"))
        set_area(state,"Explorar")
        set_task(state,"Explorar","Cidades-base")
        self.assertEqual(state["main_navigation"],"Roteiro")
        self.assertEqual(state["itinerary_section"],"Explorar bases")
        self.assertEqual(state["advisor_plan"],old_plan)
        set_from_legacy(state,"Roteiro","Calendário")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Meu roteiro","Organizar viagem"))

    def test_old_consultant_routes_migrate_to_planning(self):
        for state in (
            {"main_navigation":"Roteiro","itinerary_section":"Orçamento"},
            {"ux_area":"Orçamento","ux_section":"Simulações",
             "ux_budget_view":"Consultor de passeios"},
        ):
            with self.subTest(state=state):
                self.assertEqual(bootstrap(state)[:2],("Roteiro","Orçamento"))
                self.assertEqual((state["ux_area"],state["ux_section"]),
                                 ("Meu roteiro","Melhorar meu roteiro"))
                self.assertEqual(state["ux_improve_view"],"Consultor de passeios")
                set_task(state,"Orçamento","Simulações")
                self.assertEqual(state["main_navigation"],"Orçamento")
        self.assertEqual(route("Orçamento","Simulações",
                         budget_view="Consultor de passeios")[0],"Orçamento")

    def test_comparisons_research_and_suggestions_are_reachable(self):
        self.assertEqual(route("Explorar","Comparar cidades")[0],"Comparar cidades")
        self.assertEqual(route("Explorar","Cidades-base")[3],"Destinos próximos")
        self.assertEqual(route("Meu roteiro","Melhorar meu roteiro",
                               suggestion="Guias especializados",
                               guide_view="Transportes e custos")[2],"Transportes e custos")
        self.assertEqual(route("Meu roteiro","Melhorar meu roteiro",
                               suggestion="Simular roteiros")[1],"Simular roteiros")


class UX3StreamlitNavigationSmokeTests(unittest.TestCase):
    def test_native_sidebar_buttons_share_one_navigation_state(self):
        app = AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        keys = {widget.key for widget in app.button}
        self.assertTrue({
            "ux_sidebar_nav_0", "ux_sidebar_nav_1",
            "ux_sidebar_nav_2", "ux_sidebar_nav_3",
        }.issubset(keys))
        self.assertNotIn("ux_area",{widget.key for widget in app.radio})
        baseline = deepcopy(app.session_state["advisor_plan"])
        for index, area in enumerate(AREAS):
            with self.subTest(area=area):
                app.button(key=f"ux_sidebar_nav_{index}").click().run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
                self.assertEqual(app.session_state["ux_area"], area)
                self.assertEqual(app.session_state["advisor_plan"], baseline)

    def test_four_areas_and_sections_with_offenburg_preserve_official(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        official=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        app.checkbox(key="ux127_custom_simulation").check().run()
        app.selectbox(key="ux94_simulation_city").set_value("offenburg").run()
        app.button(key="ux_sidebar_nav_1").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        for area, sections in SECTIONS.items():
            with self.subTest(area=area):
                app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index(area))).click().run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
                if area=="Minha viagem":
                    self.assertNotIn("ux_section",{v.key for v in app.segmented_control})
                    app.button(key="home_next_tasks").click().run()
                    self.assertEqual(app.session_state["ux_section"],"Pendências")
                    self.assertFalse(app.exception,[x.message for x in app.exception])
                    app.segmented_control(key="ux_section").set_value("Decisões").run()
                    self.assertFalse(app.exception,[x.message for x in app.exception])
                    app.segmented_control(key="ux_section").set_value("Resumo").run()
                    self.assertEqual(app.session_state["ux_section"],"Resumo")
                    continue
                for section in sections:
                    with self.subTest(section=section):
                        app.segmented_control(key="ux_section").set_value(section).run()
                        self.assertFalse(app.exception,[x.message for x in app.exception])
                        self.assertEqual(app.session_state["advisor_plan"]["base_city"],
                                         official["base_city"])
        self.assertIn(app.session_state["main_navigation"], LEGACY_PAGES)

    def test_shared_city_and_duration_between_explore_and_budget(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        official=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        app.checkbox(key="ux127_custom_simulation").check().run()
        app.selectbox(key="ux94_simulation_city").set_value("offenburg").run()
        app.slider(key="unified_stay").set_value(65).run()
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"offenburg")
        self.assertNotIn("scenario_sidebar",{w.key for w in app.selectbox})
        self.assertEqual(app.session_state["advisor_plan"],official)
        self.assertEqual(app.session_state["ux_days_value"],65)
        app.button(key="ux_sidebar_nav_3").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"offenburg")
        self.assertEqual(app.session_state["ux_days_value"],65)
        app.segmented_control(key="ux_section").set_value("Simulações").run()
        self.assertTrue(app.checkbox(key="ux127_custom_simulation").value)
        self.assertFalse(app.slider(key="unified_stay").disabled)
        self.assertEqual(app.slider(key="unified_stay").value,65)
        self.assertEqual(app.selectbox(key="ux94_simulation_city").value,"offenburg")
        app.slider(key="unified_stay").set_value(60).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_days"],60)
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],
                         official["base_city"])

    def test_budget_and_italy_access_through_guided_menu(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.button(key="ux_sidebar_nav_2").click().run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Itália").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["main_navigation"],"Roteiro")
        self.assertEqual(app.session_state["itinerary_section"],"Itália")
        app.button(key="ux_sidebar_nav_3").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["main_navigation"],"Orçamento")

if __name__=="__main__": unittest.main()
