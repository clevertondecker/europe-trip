"""Integration regression: public discovery -> wishlist -> canonical planning.

Exercises widget callbacks rather than setting internal journey states directly.
"""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest
from itinerary_flow_model import FRANCE_STAGE
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest
from ux_planning_journey_model import project_planning
from attractions_model import load_attractions
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class PublicWishlistJourneyAppTests(unittest.TestCase):
    def test_discover_prioritize_build_review_return_without_losing_list(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        app.text_input(key="ux501_search").set_value("strasbourg").run()
        self.assertIn("ux502_add_strasbourg",{b.key for b in app.button})
        app.button(key="ux502_add_strasbourg").click().run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.segmented_control(key="ux64_public_task").set_value("Minha lista").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(len(app.session_state["ux502_interests"]["items"]),1)
        key=next(x.key for x in app.selectbox
                 if x.key and x.key.startswith("ux502_priority_strasbourg_"))
        app.selectbox(key=key).set_value("must_visit").run()
        self.assertEqual(app.session_state["ux502_interests"]["items"][0]["priority"],
                         "must_visit")
        self.assertEqual(app.session_state["advisor_plan"],original)
        wishes=deepcopy(app.session_state["ux502_interests"])
        app.button(key="flow_journey_from_wishlist").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        if app.session_state.get("flow_journey_view")!="build":
            app.run()
        self.assertEqual(app.session_state["flow_journey_view"],"build")
        batch="flow_journey_batch_"+FRANCE_STAGE
        app.multiselect(key=batch).set_value(["strasbourg"]).run()
        app.button(key=batch+"_confirm").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        plan=deepcopy(app.session_state["advisor_plan"])
        self.assertGreater(plan["revision"],original["revision"])
        self.assertEqual(plan["base_city"],original["base_city"])
        self.assertFalse(plan["assignments"])
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        # Confirm the actual store callback, not a UI-only success message.
        private=MagicMock()
        private.save.return_value=42
        with patch("continuity_ui._private_store",return_value=private):
            app.run()
            self.assertIn("ux75_private_save_now",{x.key for x in app.button})
            app.button(key="ux75_private_save_now").click().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            self.assertEqual(app.session_state["ux36_cloud_status"],
                             "Salvo em espaço privado")
            self.assertFalse(app.session_state["ux36_cloud_dirty"])
            private.save.assert_called_once()
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Minha lista").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.button(key="flow_journey_from_wishlist").label,
                         "Revisar meu roteiro")

    def test_discover_does_not_show_wishlist_save_or_recovery_controls(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        buttons={b.key for b in app.button}
        self.assertNotIn("ux502_cloud_save",buttons)
        self.assertNotIn("ux502_import_confirm",buttons)
        self.assertNotIn("ux502_migrate",buttons)
        self.assertIn("ux501_search",{x.key for x in app.text_input})
        self.assertIn("ux501_country",{x.key for x in app.selectbox})

    def test_partial_draft_and_exploratory_only_keep_one_primary_action(self):
        discovery=build_exploration_discovery()
        catalog=load_attractions()
        wishes=empty_interests()
        wishes=set_interest(wishes,"angers","must_visit",discovery)
        view=project_planning(new_plan(),wishes,discovery,catalog)
        self.assertEqual(view["next"],"exploratory")
        self.assertEqual(view["eligible_count"],0)


if __name__=="__main__":
    unittest.main()
