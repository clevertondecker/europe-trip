"""UX119: public destination workspace opens existing editor by ID."""
import unittest
from copy import deepcopy
from attractions_model import load_attractions
from itinerary_flow_model import add_undated_choices, FRANCE_STAGE
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests


class DestinationWorkspaceTests(unittest.TestCase):
    def test_existing_destinations_are_visible_and_edit_cancel_is_read_only(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        plan=add_undated_choices(new_plan(),load_attractions(),["colmar","strasbourg"],FRANCE_STAGE)
        app=AppTest.from_string("""
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions())
""",default_timeout=90)
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=empty_interests()
        app.session_state["ux_area"]="Meu roteiro"
        app.session_state["ux_section"]="Meu planejamento"
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            self.assertFalse(app.exception)
            self.assertIn("flow_workspace_edit_colmar",{b.key for b in app.button})
            app.button(key="flow_workspace_edit_colmar").click().run()
            self.assertFalse(app.exception)
            self.assertIn("flow_edit_save_colmar",{b.key for b in app.button})
            self.assertNotIn("flow_edit_save_strasbourg",{b.key for b in app.button})
            app.button(key="flow_workspace_cancel_colmar").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["advisor_plan"],plan)
            app.button(key="flow_workspace_organize_strasbourg").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["flow_organize_destination"],"strasbourg")
            self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_visual_batch_selection_does_not_commit_until_confirmed(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        from ux502_destination_interests_model import set_interest
        from trip01_supplemental_discovery import build_exploration_discovery
        plan=new_plan()
        wishes=set_interest(empty_interests(),"colmar","must_visit",build_exploration_discovery())
        app=AppTest.from_string("""
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions())
""",default_timeout=90)
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.session_state["ux_area"]="Meu roteiro"
        app.session_state["ux_section"]="Meu planejamento"
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            app.button(key="flow_journey_primary").click().run()
            self.assertFalse(app.exception)
            key="flow_journey_batch_"+FRANCE_STAGE
            card=key+"_card_colmar"
            app.button(key=card).click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.multiselect(key=key).value,["colmar"])
            self.assertEqual(app.session_state["advisor_plan"],plan)
            app.button(key=card).click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.multiselect(key=key).value,[])
            app.button(key=card).click().run()
            app.button(key=key+"_confirm").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["advisor_plan"]["revision"],plan["revision"]+1)
            self.assertEqual(app.session_state["advisor_plan"]["assignments"],{})
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            self.assertIn("flow_workspace_edit_colmar",{b.key for b in app.button})
