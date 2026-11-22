"""REC04: real capability inventory, explicit simulation intent and costs."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from base_scenario_model import base_options
from rec04_candidate_capabilities import candidate_capabilities,capability_for
from rec04_simulation_handoff import (
    PENDING,CONTEXT,request_simulation,apply_simulation_request,
    return_to_source,return_to_official,valid_context,
)
from rec04_housing_costs import housing_cashflow
from trip_plan_model import BASES,new_plan
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from recommendation_scope_model import confirm_scope


class CapabilityTests(unittest.TestCase):
    def test_all_current_candidates_are_represented_without_expanding_official_bases(self):
        caps=candidate_capabilities()
        options=base_options(include_candidates=True)
        self.assertEqual(set(caps),{x["id"] for x in options})
        self.assertGreaterEqual(len(caps),30)
        self.assertEqual({k for k,v in caps.items() if v["official_plan_supported"]},BASES)
        self.assertEqual({k for k,v in caps.items() if v["detailed_budget_supported"]},BASES)
        self.assertTrue(all(v["scenario_selectable"] and not v["rental_quote_2027_available"]
                            for v in caps.values()))
        self.assertTrue(all(v["researchable"] for v in caps.values()))
        for city in ("angers","le_mans","annecy","rennes"):
            with self.subTest(city=city):
                row=capability_for(city)
                self.assertFalse(row["official_plan_supported"])
                self.assertFalse(row["detailed_budget_supported"])
                self.assertTrue(row["missing"])
        with self.assertRaises(ValueError):
            capability_for("__not_a_city__")


class SimulationHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def state(self):
        plan=new_plan()
        wishes=set_interest(empty_interests(),"colmar","must_visit",self.discovery)
        scope=confirm_scope(wishes,["colmar"],self.discovery)
        return {"advisor_plan":plan,"ux502_interests":wishes,"rec03a_scope":scope,
                "rec03a_identity":"owner","scenario_base_selected":"mulhouse",
                "scenario_sidebar":"mulhouse","ux_mode":"Oficial",
                "ux41_favorites":["metz"],"ux36_cloud_dirty":False}

    def test_suggestion_to_budget_and_back_preserves_authoritative_decisions(self):
        state=self.state()
        before=deepcopy(state)
        request_simulation(state,"angers")
        self.assertTrue(apply_simulation_request(state))
        self.assertEqual((state["ux_area"],state["ux_section"]),("Orçamento","Simulações"))
        self.assertEqual(state["scenario_base_selected"],"angers")
        self.assertEqual(state["ux_mode"],"Simulação")
        self.assertEqual(valid_context(state)["city_id"],"angers")
        return_to_source(state)
        from rec03a_session import apply_navigation
        apply_navigation(state)
        self.assertEqual((state["ux_area"],state["ux_section"]),("Explorar","Comparar"))
        self.assertNotIn(CONTEXT,state)
        for field in ("advisor_plan","ux502_interests","rec03a_scope",
                      "ux41_favorites","ux36_cloud_dirty"):
            self.assertEqual(before[field],state[field])

    def test_restore_original_finance_view_without_mutating_trip(self):
        state=self.state()
        plan=deepcopy(state["advisor_plan"])
        request_simulation(state,"le_mans","profile")
        self.assertTrue(apply_simulation_request(state))
        self.assertIsNotNone(valid_context(state))
        return_to_official(state)
        self.assertEqual(state["scenario_base_selected"],plan["base_city"])
        self.assertEqual(state["ux_mode"],"Oficial")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Orçamento","Resumo financeiro"))
        self.assertEqual(state["advisor_plan"],plan)

    def test_stale_identity_scope_and_invalid_city_fail_without_side_effect(self):
        for invalid in ("identity","scope","city"):
            with self.subTest(invalid=invalid):
                state=self.state()
                request_simulation(state,"angers" if invalid!="city" else "unknown_city")
                if invalid=="identity":state["rec03a_identity"]="other"
                if invalid=="scope":state.pop("rec03a_scope")
                old=deepcopy(state)
                self.assertFalse(apply_simulation_request(state))
                self.assertNotIn(CONTEXT,state)
                self.assertEqual(state["advisor_plan"],old["advisor_plan"])
                self.assertEqual(state["scenario_base_selected"],old["scenario_base_selected"])
                self.assertEqual(state["ux_mode"],old["ux_mode"])


class HousingCashflowTests(unittest.TestCase):
    def test_fee_expense_is_separate_from_deposit_and_no_double_count(self):
        from unified_budget import scenario_total
        from finance_lifestyle import FRENCH_BUDGET
        base={"rent":10000.,"groceries":6000.,"dining":3000.,
              "transport":2500.,"excursions":6500.}
        scenario={"reported_total_brl":70000.,"cap_brl":75000.,
                  "emergency_reserve_brl":3000.}
        budget={"amounts":base,"french_days":60,"source":"snapshot_2026"}
        def calc(extra):
            return scenario_total(scenario,budget,french_days=60,
                                  outings_weekly=2,outing_couple_eur=60,
                                  fx_brl_per_eur=6.,rent_override_eur_month=1200.,
                                  rent_delta_brl=extra)
        baseline=calc(0)
        fee=300*6
        result=calc(fee)
        cash=housing_cashflow(fx_brl_per_eur=6.,fees_eur=300.,
                              refundable_deposit_eur=800.,
                              projected_total_brl=result["total"])
        self.assertAlmostEqual(result["total"]-baseline["total"],fee)
        self.assertEqual(cash["one_time_fee_expense_brl"],fee)
        self.assertEqual(cash["refundable_deposit_brl"],4800.)
        self.assertEqual(cash["initial_cash_reference_brl"],result["total"]+4800.)
        self.assertFalse(cash["quote_2027_verified"])

    def test_unknowable_costs_stay_none_and_invalid_values_rejected(self):
        out=housing_cashflow(fx_brl_per_eur=6.3)
        self.assertIsNone(out["refundable_deposit_brl"])
        self.assertIsNone(out["one_time_fee_expense_brl"])
        self.assertIsNone(out["initial_cash_reference_brl"])
        for value in (-1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                housing_cashflow(fx_brl_per_eur=6.3,fees_eur=value)


class SimulationAppTests(unittest.TestCase):
    def test_real_app_recommendation_to_budget_and_return(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        self.assertFalse(app.exception,str(app.exception))
        discovery=build_exploration_discovery()
        wants=empty_interests()
        for d in ("paris","colmar","strasbourg","basel","interlaken","angers"):
            wants=set_interest(wants,d,"interested",discovery)
        app.session_state["ux502_interests"]=deepcopy(wants)
        plan=deepcopy(app.session_state["advisor_plan"])
        favorites=deepcopy(app.session_state.get("ux41_favorites",[]))
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        app.radio(key="rec03a_activity_widget").set_value("Cidades sugeridas").run()
        app.button(key="rec03a_confirm_all").click().run()
        self.assertFalse(app.exception,str(app.exception))
        btn=next(x for x in app.button
                 if x.key and x.key.startswith("rec04_simulate_") and
                 x.key!="rec04_simulate_profile")
        btn.click().run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(app.session_state["ux_section"],"Simulações")
        self.assertEqual(app.session_state["ux_mode"],"Simulação")
        self.assertIsNotNone(app.button(key="rec04_return_to_source"))
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state.get("ux41_favorites",[]),favorites)
        app.button(key="rec04_return_to_source").click().run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(app.session_state["ux_section"],"Comparar")
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wants)


if __name__=="__main__":
    unittest.main()
