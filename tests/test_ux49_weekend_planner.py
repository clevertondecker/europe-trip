"""Regressions for reactive editing and domain-backed date previews."""
import unittest
from copy import deepcopy
from datetime import date, timedelta
from streamlit.testing.v1 import AppTest
from attractions_model import load_attractions
from trip_plan_model import new_plan
from ux45_outing_contract import apply_outing
from ux48_weekend_groups_model import empty_groups, create_group, eligible_weekends


class VisualWeekendTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_attractions()
        self.plan = new_plan()
        for dest in ("brussels", "bruges_be", "rotterdam"):
            ids = [a["id"] for a in self.catalog["attractions"] if a["destination_id"] == dest][:1]
            self.plan, _ = apply_outing(self.plan, self.catalog, dest, ids, confirmed=True)
        self.state = empty_groups(self.plan)

    def test_preview_excludes_conflicts_and_keeps_own_date(self):
        candidates = eligible_weekends(self.state, self.plan, self.catalog, destinations=["brussels"])
        start = next(r["start"] for r in candidates if r["eligible"])
        state = create_group(self.state, self.plan, self.catalog, name="Belgique",
                             destinations=["brussels"], start_date=start)
        own = eligible_weekends(state, self.plan, self.catalog, destinations=["brussels"],
                                group_id=state["groups"][0]["id"])
        other = eligible_weekends(state, self.plan, self.catalog, destinations=["rotterdam"])
        self.assertTrue(next(r["eligible"] for r in own if r["start"] == start))
        self.assertFalse(next(r["eligible"] for r in other if r["start"] == start))

    def test_extension_checks_monday_and_preserves_inputs(self):
        start = next(r["start"] for r in eligible_weekends(self.state, self.plan, self.catalog,
                     destinations=["brussels"]) if r["eligible"])
        monday = (date.fromisoformat(start) + timedelta(days=2)).isoformat()
        self.plan["assignments"][monday] = "rotterdam"
        before = deepcopy((self.state, self.plan))
        short = eligible_weekends(self.state, self.plan, self.catalog, destinations=["brussels"], nights=1)
        long = eligible_weekends(self.state, self.plan, self.catalog, destinations=["brussels"], nights=3)
        self.assertTrue(next(r["eligible"] for r in short if r["start"] == start))
        self.assertFalse(next(r["eligible"] for r in long if r["start"] == start))
        self.assertEqual((self.state, self.plan), before)

    def test_reactive_editor_and_roundtrip(self):
        source = '''
import streamlit as st
from attractions_model import load_attractions
from trip_plan_model import new_plan
from ux45_outing_contract import apply_outing
from ux48_weekend_groups_ui import render_weekend_planner
catalog = load_attractions()
if "test_plan" not in st.session_state:
    plan = new_plan()
    for dest in ("brussels", "bruges_be", "rotterdam"):
        ids = [a["id"] for a in catalog["attractions"] if a["destination_id"] == dest][:1]
        plan, _ = apply_outing(plan, catalog, dest, ids, confirmed=True)
    st.session_state.test_plan = plan
render_weekend_planner(st.session_state.test_plan, catalog)
'''
        app = AppTest.from_string(source).run()
        next(b for b in app.button if b.label == "+ Criar viagem").click().run()
        app.text_input(key="ux49_field_name").set_value("Belgique").run()
        app.multiselect(key="ux49_field_destinations").set_value(["brussels", "bruges_be"]).run()
        app.text_area(key="ux49_field_notes").set_value("Retour à vérifier").run()
        candidates = eligible_weekends(empty_groups(app.session_state.test_plan),
            app.session_state.test_plan, self.catalog, destinations=["brussels", "bruges_be"])
        start = next(row["start"] for row in candidates if row["eligible"])
        app.selectbox(key="ux49_field_start").set_value(start).run()
        monday = (date.fromisoformat(start) + timedelta(days=2)).isoformat()
        plan = deepcopy(app.session_state.test_plan)
        plan["assignments"][monday] = "rotterdam"
        app.session_state.test_plan = plan
        app.number_input(key="ux49_field_nights").set_value(3).run()
        self.assertTrue(any("incompatível" in warning.value for warning in app.warning))
        self.assertEqual(app.selectbox(key="ux49_field_start").value, start)
        self.assertTrue(next(b for b in app.button if b.label == "Salvar viagem").disabled)
        app.selectbox(key="ux49_field_start").set_value(None).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(app.text_input(key="ux49_field_name").value, "Belgique")
        self.assertEqual(app.text_area(key="ux49_field_notes").value, "Retour à vérifier")
        next(b for b in app.button if b.label == "Salvar viagem").click().run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        group = app.session_state["ux48_weekend_groups"]["groups"][0]
        self.assertEqual(group["destinations"], ["brussels", "bruges_be"])
        self.assertEqual(group["nights"], 3)
        self.assertIsNone(group["start_date"])
        app.button(key="ux49_edit_" + group["id"]).click().run()
        app.text_input(key="ux49_field_name").set_value("Belgique modifiée").run()
        next(b for b in app.button if b.label == "Salvar viagem").click().run()
        self.assertEqual(app.session_state["ux48_weekend_groups"]["groups"][0]["name"], "Belgique modifiée")
        self.assertFalse(app.exception, [e.message for e in app.exception])
