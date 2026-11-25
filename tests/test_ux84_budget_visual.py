"""UX84: visual consistency and non-mutating budget scenario contracts."""
from copy import deepcopy
from pathlib import Path
import unittest

from data_model import load_data, get_scenario, calculate_scenario, money_brl

ROOT=Path(__file__).resolve().parents[1]


class BudgetUx84Tests(unittest.TestCase):
    def test_both_scenarios_are_presented_without_mutating_sources(self):
        data=load_data()
        original=deepcopy(data)
        for scenario_id in ("60k","70k"):
            with self.subTest(scenario=scenario_id):
                scenario=get_scenario(data,scenario_id)
                before=deepcopy(scenario)
                projection=calculate_scenario(scenario)
                self.assertEqual(scenario,before)
                self.assertIn("cap_brl",scenario)
                self.assertIn("total",projection)
                self.assertIn("balance",projection)
                self.assertTrue(money_brl(projection["total"]).startswith("R$"))
        self.assertEqual(data,original)

    def test_summary_and_simulation_use_same_pure_component_contract(self):
        budget=(ROOT/"budget_sections_ui.py").read_text()
        app=(ROOT/"app.py").read_text()
        for source in (budget,app):
            self.assertIn("page_header(",source)
            self.assertIn("kpi_cards(",source)
            self.assertIn("section_heading(",source)
        self.assertIn('key="ux84_finance_metrics"',budget)
        self.assertIn('key="ux84_simulation_metrics"',app)
        self.assertIn('next_action(',budget)

    def test_simulation_keys_remain_and_official_confirmation_is_isolated(self):
        app=(ROOT/"app.py").read_text()
        for key in ('unified_scenario','unified_style',
                    'scenario_id!=active_plan()["budget_scenario"]',
                    'ux127_custom_simulation'):
            self.assertIn(key,app)
        self.assertIn('["60k","70k"]',app)
        self.assertNotIn('budget_cap_confirm',app)
        self.assertNotIn('update_fields(budget_scenario=scenario_id)',app)
        settings=(ROOT/"planning_context_ui.py").read_text()
        self.assertIn('budget_scenario=budget',settings)
        self.assertIn('update_fields(**changes)',settings)
        self.assertIn('sync_sources["finance"]["status"] == "live"',app)
        self.assertIn('render_quotes_summary(data,plan,finance_live)',(ROOT/"budget_sections_ui.py").read_text())

    def test_native_navigation_from_financial_overview(self):
        from streamlit.testing.v1 import AppTest
        script="""
import streamlit as st
from budget_sections_ui import render_budget_summary
from data_model import load_data
from trip_plan_model import new_plan
render_budget_summary(load_data(),new_plan(),False)
"""
        app=AppTest.from_string(script,default_timeout=90).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("ui-kpi-card" in x.value for x in app.markdown))
        app.button(key="ux84_go_simulations").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual((app.session_state["ux_area"],app.session_state["ux_section"]),
                         ("Orçamento","Simulações"))


if __name__=="__main__":
    unittest.main()
