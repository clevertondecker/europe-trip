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
                         ("Meu roteiro","Itália"))
        set_area(state,"Explorar")
        set_task(state,"Explorar","Cidades-base")
        self.assertEqual(state["main_navigation"],"Roteiro")
        self.assertEqual(state["itinerary_section"],"Explorar bases")
        self.assertEqual(state["advisor_plan"],old_plan)
        set_from_legacy(state,"Roteiro","Calendário")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Meu roteiro","Calendário"))

    def test_comparisons_research_and_suggestions_are_reachable(self):
        self.assertEqual(route("Explorar","Comparar cidades")[0],"Comparar cidades")
        self.assertEqual(route("Explorar","Cidades-base")[3],"Destinos próximos")
        self.assertEqual(route("Meu roteiro","França",
                               france="Transportes e custos")[2],"Transportes e custos")
        self.assertEqual(route("Meu roteiro","Sugestões",
                               suggestion="Simular roteiros")[1],"Simular roteiros")


class UX3StreamlitNavigationSmokeTests(unittest.TestCase):
    def test_four_areas_and_sections_with_offenburg_preserve_official(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        official=deepcopy(app.session_state["advisor_plan"])
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_mode").set_value("Simulação").run()
        app.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        for area, sections in SECTIONS.items():
            with self.subTest(area=area):
                app.radio(key="ux_area").set_value(area).run()
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
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux_mode").set_value("Simulação").run()
        app.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"offenburg")
        self.assertEqual(app.session_state["scenario_sidebar"],"offenburg")
        self.assertEqual(app.session_state["advisor_plan"],official)
        app.number_input(key="ux_days").set_value(65).run()
        self.assertEqual(app.session_state["unified_stay"],65)
        app.radio(key="ux_area").set_value("Orçamento").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"offenburg")
        self.assertEqual(app.session_state["unified_stay"],65)
        app.segmented_control(key="ux_section").set_value("Simulações").run()
        app.slider(key="unified_stay").set_value(60).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_days"],60)
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],
                         official["base_city"])

    def test_budget_and_italy_access_through_guided_menu(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Itália").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["main_navigation"],"Roteiro")
        self.assertEqual(app.session_state["itinerary_section"],"Itália")
        app.radio(key="ux_area").set_value("Orçamento").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["main_navigation"],"Orçamento")

if __name__=="__main__": unittest.main()
