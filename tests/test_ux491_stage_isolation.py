"""UX 4.9.1: stage isolation, widget reconciliation, and proposal safety."""
import unittest
from copy import deepcopy
from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions
from itinerary_flow_model import (
    FRANCE_STAGE, ITALY_STAGE, selected_rows_for_stage, upsert_choice,
    italy_starter_preview, adopt_italy_starter, period_options,
)
from trip_plan_model import new_plan
from itinerary_flow_ui import _reconcile_organize_state, _assert_organize_stage


class StageIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_attractions()

    def french_only(self):
        plan = new_plan()
        a = next(x["id"] for x in self.catalog["attractions"]
                 if x["destination_id"] == "colmar")
        return upsert_choice(plan, self.catalog, "colmar", [a],
                             "Férias restantes")

    def test_french_destination_never_leaks_into_italy(self):
        plan = self.french_only()
        before = deepcopy(plan)
        self.assertEqual(selected_rows_for_stage(plan, self.catalog, ITALY_STAGE), [])
        self.assertEqual([r["id"] for r in
                          selected_rows_for_stage(plan, self.catalog, FRANCE_STAGE)],
                         ["colmar"])
        self.assertEqual(plan, before)

    def test_reconcile_stale_destination_without_touching_plan(self):
        plan = self.french_only()
        original = deepcopy(plan)
        state = {"flow_organize_destination": "colmar",
                 "flow_organize_period": "Férias restantes",
                 "ux49_editor": {"name": "Saved draft"}}
        _reconcile_organize_state(
            state, selected_rows_for_stage(plan, self.catalog, ITALY_STAGE),
            ITALY_STAGE)
        self.assertNotIn("flow_organize_destination", state)
        self.assertNotIn("flow_organize_period", state)
        self.assertEqual(state["ux49_editor"]["name"], "Saved draft")
        self.assertEqual(plan, original)
        _reconcile_organize_state(
            state, selected_rows_for_stage(plan, self.catalog, FRANCE_STAGE),
            FRANCE_STAGE)
        self.assertEqual(state["flow_organize_destination"], "colmar")
        self.assertIn(state["flow_organize_period"], period_options(FRANCE_STAGE))
        self.assertEqual(plan, original)

    def test_cross_stage_organization_write_is_rejected(self):
        with self.assertRaises(ValueError):
            _assert_organize_stage(self.catalog, "colmar", ITALY_STAGE)
        _assert_organize_stage(self.catalog, "colmar", FRANCE_STAGE)

    def test_preview_is_not_adoption(self):
        plan = self.french_only()
        before = deepcopy(plan)
        preview = italy_starter_preview(plan, self.catalog, "economy")
        self.assertTrue(preview["requires_confirmation"])
        self.assertEqual(plan, before)
        self.assertEqual(adopt_italy_starter(plan, self.catalog, "economy"), plan)
        applied = adopt_italy_starter(plan, self.catalog, "economy", confirmed=True)
        self.assertTrue(selected_rows_for_stage(applied, self.catalog, ITALY_STAGE))
        self.assertEqual([r["id"] for r in selected_rows_for_stage(applied, self.catalog,
                         FRANCE_STAGE)], ["colmar"])

    def test_apptest_switch_preserves_plan_and_filters(self):
        source = """
import streamlit as st
from attractions_model import load_attractions
from trip_plan_model import new_plan
from itinerary_flow_model import selected_rows_for_stage, upsert_choice, ITALY_STAGE, FRANCE_STAGE
catalog=load_attractions()
if "plan" not in st.session_state:
    plan=new_plan()
    a=next(x["id"] for x in catalog["attractions"] if x["destination_id"]=="colmar")
    st.session_state.plan=upsert_choice(plan,catalog,"colmar",[a],"Férias restantes")
stage=st.segmented_control("Etapa",[ITALY_STAGE,FRANCE_STAGE],key="stage")
rows=selected_rows_for_stage(st.session_state.plan,catalog,stage)
st.write("Destinos da etapa: "+str(len(rows)))
"""
        app = AppTest.from_string(source).run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        revision = app.session_state.plan["revision"]
        app.segmented_control(key="stage").set_value(FRANCE_STAGE).run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertEqual(app.session_state.plan["revision"], revision)
        app.segmented_control(key="stage").set_value(ITALY_STAGE).run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertEqual(app.session_state.plan["revision"], revision)


if __name__ == "__main__":
    unittest.main()
