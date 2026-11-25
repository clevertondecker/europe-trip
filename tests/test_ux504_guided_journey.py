"""UX 5.0.4 — read-only journey status and non-mutating UI navigation."""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests,set_interest
from ux504_guided_journey_model import (
    STEPS,project_journey,navigation_request,apply_navigation_request,
)

ROOT=Path(__file__).resolve().parents[1]


def wished():
    return set_interest(empty_interests(),"colmar","must_visit")


class JourneyProjectionTests(unittest.TestCase):
    def test_first_visit_and_implicit_decisions_stay_pending(self):
        plan=new_plan()
        before=deepcopy(plan)
        result=project_journey(plan,empty_interests())
        self.assertEqual(result["next"]["label"],"Começar pelos destinos")
        self.assertEqual(len(result["steps"]),5)
        self.assertFalse(result["base_decision_confirmed"])
        self.assertFalse(result["comparison_concluded"])
        self.assertFalse(result["budget_confirmed"])
        self.assertEqual(plan,before)

    def test_wishlist_vs_outings_vs_dates(self):
        plan=new_plan()
        self.assertEqual(project_journey(plan,wished())["next"]["id"],"itinerary")
        changed=deepcopy(plan)
        changed["packages"]={"colmar":["colmar_little_venice"]}
        self.assertEqual(project_journey(changed,wished())["next"]["id"],"itinerary")
        changed["assignments"]={"2027-10-06":"colmar"}
        result=project_journey(changed,wished())
        self.assertEqual(result["next"]["id"],"itinerary")
        self.assertIn("1 com data",result["steps"][3]["status"])
        self.assertFalse(result["base_decision_confirmed"])

    def test_two_paths_without_implicit_comparison_completion(self):
        view=project_journey(new_plan(),wished())
        self.assertEqual(view["next"],{"label":"Montar roteiro com meus destinos","id":"itinerary"})
        self.assertEqual(view["alternatives"],[
            {"label":"Comparar cidades-base","id":"compare"}])
        self.assertFalse(view["comparison_concluded"])
        self.assertFalse(view["base_decision_confirmed"])

    def test_per_destination_organization_not_raw_date_count(self):
        from itinerary_flow_model import UNASSIGNED
        plan=new_plan()
        plan["packages"]={"colmar":["colmar_little_venice"],
                          "strasbourg":["strasbourg_cathedral"]}
        plan["assignments"]={"2027-10-05":"colmar","2027-10-06":"colmar"}
        view=project_journey(plan,wished())
        self.assertEqual(view["outings"],2)
        self.assertEqual(view["dated_visits"],1)
        self.assertEqual(view["organized_destinations"],1)
        self.assertEqual(view["pending_destinations"],1)
        self.assertEqual(view["next"]["id"],"itinerary")

        plan["flexible_visits"]=[{
            "destination_id":"strasbourg","stage":"França",
            "attractions":["strasbourg_cathedral"],"period":UNASSIGNED,
        }]
        not_organized=project_journey(plan,wished())
        self.assertEqual(not_organized["pending_destinations"],1)
        plan["flexible_visits"][0]["period"]="Férias restantes"
        with_period=project_journey(plan,wished())
        self.assertEqual(with_period["organized_destinations"],2)
        self.assertEqual(with_period["pending_destinations"],0)
        # A chosen period is not a confirmed exact date.
        self.assertEqual(with_period["dated_visits"],1)
        self.assertEqual(with_period["next"]["id"],"itinerary")

    def test_navigation_intent_only_changes_view_keys(self):
        state={"ux_area":"Minha viagem","ux_section":"Resumo","ux502_view":"Descobrir lugares",
               "advisor_plan":new_plan(),"ux503_bases":["mulhouse","lille"],
               "ux501_search":"bruges","ux502_interests":wished()}
        before=deepcopy(state["advisor_plan"])
        state["_ux504_navigation_request"]=navigation_request("wishlist")
        self.assertTrue(apply_navigation_request(state))
        self.assertEqual((state["ux_area"],state["ux_section"],state["ux502_view"]),
                         ("Explorar","Passeios","Minha lista"))
        self.assertEqual(state["ux503_bases"],["mulhouse","lille"])
        self.assertEqual(state["ux501_search"],"bruges")
        self.assertEqual(state["advisor_plan"],before)
        self.assertFalse(apply_navigation_request(state))
        state["_ux504_navigation_request"]={"area":"Meu roteiro",
                                              "section":"Organizar viagem","view":None}
        self.assertTrue(apply_navigation_request(state))
        self.assertEqual(state["ux_section"],"Organizar viagem")
        with self.assertRaises(ValueError):
            navigation_request("missing")

    def test_previous_bookmark_alias_kept(self):
        from ux_navigation import from_legacy,route
        self.assertEqual(from_legacy("Comparar cidades"),("Explorar","Comparar"))
        self.assertEqual(from_legacy("Mapa & destinos"),("Explorar","Mapa"))
        self.assertEqual(route("Explorar","Passeios")[0],"Roteiro")


class JourneyAppTests(unittest.TestCase):
    def _home(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        return app

    def test_empty_home_and_discover_to_wishlist(self):
        app=self._home()
        original=deepcopy(app.session_state["advisor_plan"])
        self.assertEqual(app.session_state["ux_area"],"Minha viagem")
        self.assertTrue(app.button(key="flow_journey_primary"))
        app.button(key="flow_journey_primary").click().run()
        self.assertEqual((app.session_state["ux_area"],app.session_state["ux_section"]),
                         ("Explorar","Passeios"))
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.button(key="ux504_discovery_to_wishlist").click().run()
        self.assertEqual(app.session_state["ux502_view"],"Minha lista")
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))

    def test_home_wishlist_comparison_and_back(self):
        app=self._home()
        plan=deepcopy(app.session_state["advisor_plan"])
        app.session_state["ux502_interests"]=wished()
        app.run()
        app.button(key="flow_journey_primary").click().run()
        self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
        self.assertNotIn("flow_journey_suggestions",{b.key for b in app.button})
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Minha lista").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux502_interests"],wished())
        app.button(key="rec03a_open_from_wishlist").click().run()
        app.button(key="ux125_open_manual_comparison").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_section"],"Comparar")
        app.button(key="ux503_back_to_wishes").click().run()
        self.assertEqual((app.session_state["ux_area"],app.session_state["ux_section"]),
                         ("Explorar","Passeios"))
        self.assertEqual(app.session_state["ux502_view"],"Minha lista")
        self.assertEqual(app.session_state["ux502_interests"],wished())
        self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_itinerary_dates_budget_without_implicit_save(self):
        app=self._home()
        plan=deepcopy(app.session_state["advisor_plan"])
        app.segmented_control(key="ux64_public_task").set_value("Meus destinos").run()
        self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
        self.assertEqual(app.session_state["ux_area"],"Meu roteiro")
        app.segmented_control(key="ux64_public_task").set_value("Organizar").run()
        self.assertEqual(app.session_state["ux_section"],"Organizar viagem")
        # Return through the ordinary task navigation and go to budget.
        app.segmented_control(key="ux_section").set_value("Meu planejamento").run()
        app.button(key="flow_journey_budget").click().run()
        self.assertEqual((app.session_state["ux_area"],app.session_state["ux_section"]),
                         ("Orçamento","Resumo financeiro"))
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))

    def test_full_journey_preserves_filters_bases_and_plan(self):
        app=self._home()
        plan=deepcopy(app.session_state["advisor_plan"])
        wishes=wished()
        # Descobrir -> Minha lista, preserving filters before widgets unmount.
        app.button(key="flow_journey_primary").click().run()
        app.text_input(key="ux501_search").set_value("Colmar").run()
        app.button(key="ux504_discovery_to_wishlist").click().run()
        self.assertEqual(app.session_state["ux502_view"],"Minha lista")
        self.assertEqual(
            app.session_state["ux502_discovery_filters"]["ux501_search"],"Colmar")
        app.session_state["ux502_interests"]=wishes
        app.run()
        # Minha lista -> Comparar, then customize bases and the visible basket.
        app.button(key="rec03a_open_from_wishlist").click().run()
        app.button(key="ux125_open_manual_comparison").click().run()
        app.multiselect(key="ux503_bases").set_value(["lille","metz"]).run()
        app.multiselect(key="ux503_visible_destinations").set_value(["colmar"]).run()
        self.assertEqual(app.session_state["ux504_bases_shadow"],["lille","metz"])
        self.assertFalse(app.exception,[e.message for e in app.exception])
        # Comparar -> Montar roteiro -> Organizar datas -> Orçamento.
        app.button(key="ux504_compare_to_itinerary").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Organizar").run()
        app.segmented_control(key="ux_section").set_value("Meu planejamento").run()
        app.button(key="flow_journey_budget").click().run()
        self.assertEqual(app.session_state["ux_area"],"Orçamento")
        # Back to comparison. Streamlit removes unmounted widget keys; the
        # view-only shadow must rehydrate the previously selected bases.
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        app.button(key="ux125_open_manual_comparison").click().run()
        self.assertEqual(app.multiselect(key="ux503_bases").value,["lille","metz"])
        self.assertEqual(
            app.multiselect(key="ux503_visible_destinations").value,["colmar"])
        app.button(key="ux503_back_to_wishes").click().run()
        self.assertEqual(app.session_state["ux502_view"],"Minha lista")
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        self.assertEqual(app.text_input(key="ux501_search").value,"Colmar")
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))
        self.assertFalse(app.exception,[e.message for e in app.exception])

    def test_wishlist_alternative_action_opens_itinerary(self):
        app=self._home()
        plan=deepcopy(app.session_state["advisor_plan"])
        app.session_state["ux502_interests"]=wished()
        app.run()
        app.button(key="flow_journey_primary").click().run()
        self.assertEqual(
            (app.session_state["ux_area"],app.session_state["ux_section"]),
            ("Meu roteiro","Meu planejamento"))
        self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_existing_plan_state_remains_authoritative(self):
        app=self._home()
        plan=deepcopy(app.session_state["advisor_plan"])
        plan["packages"]={"colmar":["colmar_little_venice"]}
        plan["assignments"]={"2027-10-06":"colmar"}
        app.session_state["advisor_plan"]=plan
        app.session_state["ux502_interests"]=wished()
        app.run()
        app.button(key="flow_journey_primary").click().run()
        self.assertEqual(app.session_state["ux_area"],"Meu roteiro")
        self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
        self.assertEqual(app.session_state["advisor_plan"],plan)


if __name__=="__main__":
    unittest.main()
