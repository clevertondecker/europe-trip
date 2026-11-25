"""UX127 acceptance: official financial parity across the public navigation."""
import re
import unittest
from unittest.mock import patch
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from data_model import load_data, money_brl
from official_budget_model import official_budget_for_plan
from attractions_model import load_attractions

ROOT = Path(__file__).resolve().parents[1]
BRL = re.compile(r"^R\$ -?\d{1,3}(?:\.\d{3})*,\d{2}$")


class BudgetParityAppTests(unittest.TestCase):
    def assert_clean(self, app):
        self.assertFalse(app.exception, [x.message for x in app.exception])

    def assert_cards(self, app, label, amount):
        self.assertTrue(any(label in x.value and amount in x.value
                            for x in app.markdown), (label, amount))

    def assert_money_tables(self, app):
        for table in app.dataframe:
            frame = table.value
            for column in frame.columns:
                if "(R$)" in str(column):
                    for value in frame[column].dropna():
                        self.assertIsInstance(value, str)
                        self.assertRegex(value, BRL)

    def test_official_simulation_restore_and_navigation(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        self.assert_clean(app)
        plan = deepcopy(app.session_state["advisor_plan"])
        official = official_budget_for_plan(load_data(), False, plan)
        total, margin = money_brl(official["total"]), money_brl(official["margin"])

        def check_planning():
            self.assert_clean(app)
            self.assertTrue(any(total in x.value and margin in x.value
                                for x in app.caption), (total, margin))
            self.assertEqual(app.session_state["advisor_plan"], plan)

        app.button(key="ux64_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Visão geral").run()
        check_planning()
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Visão financeira").run()
        self.assert_clean(app)
        self.assert_cards(app, "Total oficial estimado", total)
        self.assert_cards(app, "Margem oficial", margin)
        self.assert_money_tables(app)

        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        self.assert_clean(app)
        self.assert_cards(app, "Total oficial", total)
        self.assert_cards(app, "Margem oficial", margin)
        self.assert_cards(app, "Total simulado", total)
        self.assert_cards(app, "Margem simulada", margin)
        self.assertTrue(any("R$ 0,00 vs. oficial" in x.value for x in app.caption))
        self.assert_money_tables(app)
        # UX125B: only the canonical simulator owns mode and duration.
        self.assertNotIn("ux_mode", {x.key for x in app.segmented_control})
        self.assertNotIn("ux_days", {x.key for x in app.number_input})
        self.assertTrue(app.slider(key="unified_stay").disabled)
        app.checkbox(key="ux127_custom_simulation").check().run()
        self.assertEqual(app.session_state["ux_mode_value"], "Simulação")
        self.assertFalse(app.slider(key="unified_stay").disabled)
        app.number_input(key="unified_flight_extra").set_value(500).run()
        self.assert_clean(app)
        self.assert_cards(app, "Total oficial", total)
        self.assert_cards(app, "Total simulado", money_brl(official["total"] + 500))
        self.assertTrue(any("+R$ 500,00 vs. oficial" in x.value for x in app.caption))
        self.assertEqual(app.session_state["advisor_plan"], plan)
        app.checkbox(key="ux127_custom_simulation").uncheck().run()
        self.assert_clean(app)
        self.assert_cards(app, "Total simulado", total)
        self.assertTrue(any("R$ 0,00 vs. oficial" in x.value for x in app.caption))
        app.button(key="ux64_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Visão geral").run()
        check_planning()

    def test_parity_with_known_outing_overage(self):
        # Synthetic ticket fixture, not a research-data change. Choose a real
        # Colmar attraction and give it a controlled published price above the allowance.
        catalog = deepcopy(load_attractions())
        attraction = next(a for a in catalog["attractions"] if a["destination_id"] == "colmar")
        attraction["ticket"] = {**attraction["ticket"], "status": "operator_published",
                                "amount": 10000, "currency": "EUR", "per": "adult"}
        with patch("attractions_model.load_attractions", return_value=catalog):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
            self.assert_clean(app)
            plan = deepcopy(app.session_state["advisor_plan"])
            plan["packages"] = {"colmar": [attraction["id"]]}
            app.session_state["advisor_plan"] = deepcopy(plan)
            official = official_budget_for_plan(load_data(), False, plan, catalog=catalog)
            self.assertGreater(official["known_excursions_overage_brl"], 0)
            total, margin = money_brl(official["total"]), money_brl(official["margin"])
            app.button(key="ux64_sidebar_nav_1").click().run()
            app.segmented_control(key="ux64_public_task").set_value("Visão geral").run()
            self.assert_clean(app)
            self.assertTrue(any(total in x.value and margin in x.value for x in app.caption))
            app.button(key="ux64_sidebar_nav_2").click().run()
            app.segmented_control(key="ux64_public_task").set_value("Visão financeira").run()
            self.assert_clean(app)
            self.assert_cards(app, "Total oficial estimado", total)
            self.assert_cards(app, "Margem oficial", margin)
            self.assertTrue(any("Excedente conhecido de passeios" in table.value.to_string()
                                and money_brl(official["known_excursions_overage_brl"]) in table.value.to_string()
                                for table in app.dataframe))
            app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
            self.assert_clean(app)
            self.assert_cards(app, "Total oficial", total)
            self.assert_cards(app, "Total simulado", total)
            self.assert_cards(app, "Margem simulada", margin)
            self.assertTrue(any("R$ 0,00 vs. oficial" in x.value for x in app.caption))
            self.assertEqual(app.session_state["advisor_plan"], plan)
