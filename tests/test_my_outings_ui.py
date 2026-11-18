"""Direct canonical outings acceptance tests."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions
from my_outings_ui import selected_cards
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class DirectOutingsTests(unittest.TestCase):
    def test_only_selected_packages_are_cards(self):
        plan=new_plan()
        catalog=load_attractions()
        self.assertEqual(selected_cards(plan,catalog),[])
        attraction=next(a for a in catalog["attractions"]
                        if a["destination_id"]=="colmar")
        plan["packages"]={"colmar":[attraction["id"]]}
        plan["assignments"]={"2027-09-30":"colmar"}
        cards=selected_cards(plan,catalog)
        self.assertEqual(len(cards),1)
        self.assertEqual(cards[0]["id"],"colmar")
        self.assertEqual(cards[0]["dates"],["2027-09-30"])

    def test_add_edit_remove_are_canonical_and_removal_needs_confirmation(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Meu roteiro"))).click().run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Temporada europeia").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn("scenario_review_button_balanced",{b.key for b in app.button})
        self.assertEqual(app.session_state["advisor_plan"]["packages"],{})
        app.button(key="outing_add_open").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.selectbox(key="outing_new_destination").set_value("colmar").run()
        catalog=load_attractions()
        colmar=[a["id"] for a in catalog["attractions"]
                if a["destination_id"]=="colmar"]
        app.multiselect(key="outing_new_attractions").set_value(colmar[:2]).run()
        app.button(key="outing_add_save").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["packages"]["colmar"],colmar[:2])
        self.assertEqual(app.session_state["advisor_plan"]["packages"],
                         app.session_state["explore_packages"])
        app.button(key="outing_edit_colmar").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.multiselect(key="outing_edit_attractions_colmar").set_value(colmar[:1]).run()
        app.button(key="outing_edit_save_colmar").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["packages"]["colmar"],colmar[:1])
        app.button(key="outing_remove_colmar").click().run()
        self.assertIn("colmar",app.session_state["advisor_plan"]["packages"])
        app.button(key="outing_cancel_remove_colmar").click().run()
        self.assertIn("colmar",app.session_state["advisor_plan"]["packages"])
        app.button(key="outing_remove_colmar").click().run()
        app.button(key="outing_confirm_remove_colmar").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn("colmar",app.session_state["advisor_plan"]["packages"])
        self.assertIsNone(app.session_state.get("advisor_github_sha"))


if __name__=="__main__":
    unittest.main()
