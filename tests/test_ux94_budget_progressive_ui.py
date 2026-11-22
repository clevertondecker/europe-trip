"""UX94: progressive simulation keeps the official TripPlan immutable."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


class ProgressiveBudgetAppTests(unittest.TestCase):
    def test_durations_base_and_teto_are_only_hypothetical(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        official=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux94_simulation_city",{x.key for x in app.selectbox})
        self.assertNotIn("scenario_sidebar",{x.key for x in app.selectbox})
        self.assertEqual(
            sum(x.label=="Cidade-base hipotética" for x in app.selectbox),1)
        self.assertIn("unified_stay",{x.key for x in app.slider})
        self.assertIn("unified_outings",{x.key for x in app.slider})
        app.slider(key="unified_stay").set_value(65).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        app.selectbox(key="ux94_simulation_city").set_value("nancy").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"nancy")
        self.assertEqual(app.session_state["advisor_plan"],official)
        changed="60k" if official["budget_scenario"]=="70k" else "70k"
        app.segmented_control(key="unified_scenario").set_value(changed).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)


    def test_simulation_navigation_to_map_compare_and_planning_preserves_choices(self):
        from ux502_destination_interests_model import empty_interests,set_interest
        wishes=set_interest(empty_interests(),"colmar","must_visit")
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.run()
        official=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        app.slider(key="unified_stay").set_value(68).run()
        app.selectbox(key="ux94_simulation_city").set_value("nancy").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Mapa").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        app.segmented_control(key="ux64_public_task").set_value("Comparar bases").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.button(key="ux64_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Meus destinos").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        self.assertEqual(app.session_state["ux502_interests"],wishes)



class BudgetProjectionEquivalenceTests(unittest.TestCase):
    def test_scenarios_60k_70k_durations_and_exchange_use_original_formula(self):
        from data_model import load_data,get_scenario
        from unified_budget import resolve_french_budget,scenario_total
        from math import isclose
        data=load_data()
        for sid in ("60k","70k"):
            scenario=get_scenario(data,sid)
            original=deepcopy(scenario)
            budget=resolve_french_budget(scenario,False)
            for days,fx in ((40,5.5),(60,6.3),(80,7.2)):
                with self.subTest(scenario=sid,days=days,fx=fx):
                    result=scenario_total(scenario,budget,french_days=days,
                            outings_weekly=2,outing_couple_eur=60,
                            fx_brl_per_eur=fx)
                    # UI components are rounded individually to cents; the
                    # engine totals the unrounded amounts before rounding.
                    self.assertAlmostEqual(
                        result["total"],
                        round(scenario["reported_total_brl"]
                              +sum(result["new_components"].values())
                              -sum(budget["amounts"].values()),2),delta=0.03)
                    self.assertAlmostEqual(result["margin"],
                        round(scenario["cap_brl"]-result["total"],2))
                    self.assertEqual(result["source"],"snapshot_2026")
                    self.assertEqual(result["reserve_already_in_total"],
                                     scenario["emergency_reserve_brl"])
            self.assertEqual(scenario,original)

    def test_known_and_unknown_rent_are_not_added_twice(self):
        from data_model import load_data,get_scenario
        from unified_budget import resolve_french_budget,scenario_total
        scenario=get_scenario(load_data(),"70k")
        budget=resolve_french_budget(scenario,False)
        common={"french_days":60,"outings_weekly":2,
                "outing_couple_eur":60,"fx_brl_per_eur":6.3}
        unknown=scenario_total(scenario,budget,**common)
        quoted=scenario_total(scenario,budget,**common,
                              rent_override_eur_month=1250)
        self.assertEqual(unknown["new_components"]["rent"],
                         round(budget["amounts"]["rent"]*(60/budget["french_days"]),2))
        self.assertEqual(quoted["new_components"]["rent"],round(1250*2*6.3,2))
        self.assertAlmostEqual(quoted["total"]-unknown["total"],
            round(quoted["new_components"]["rent"]
                  -unknown["new_components"]["rent"],2))

    def test_deposit_is_cash_not_expense_fees_and_valid_negative_deltas(self):
        from data_model import load_data,get_scenario
        from unified_budget import resolve_french_budget,scenario_total
        from rec04_housing_costs import housing_cashflow
        scenario=get_scenario(load_data(),"70k")
        budget=resolve_french_budget(scenario,False)
        cash=housing_cashflow(fx_brl_per_eur=6.3,
                              fees_eur=100,refundable_deposit_eur=500)
        args={"french_days":60,"outings_weekly":2,
              "outing_couple_eur":60,"fx_brl_per_eur":6.3}
        baseline=scenario_total(scenario,budget,**args)
        revised=scenario_total(scenario,budget,**args,
            flight_delta_brl=-200,excursions_delta_brl=300,
            local_transport_delta_brl=-100,
            rent_delta_brl=cash["one_time_fee_expense_brl"])
        self.assertAlmostEqual(revised["total"]-baseline["total"],
                               -200+300-100+630)
        self.assertEqual(cash["refundable_deposit_brl"],3150)
        self.assertEqual(cash["quote_2027_verified"],False)
        self.assertEqual(housing_cashflow(fx_brl_per_eur=6.3)
                         ["refundable_deposit_brl"],None)
        self.assertAlmostEqual(revised["total"]+cash["refundable_deposit_brl"],
                               revised["total"]+3150)


if __name__=="__main__":
    unittest.main()
