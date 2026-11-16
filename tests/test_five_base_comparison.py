"""Reproducible evidence gates for five 60-night base-city candidates."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest
from five_base_comparison_model import (
    BASE_IDS,load_five_base_evidence,route_observation,
    housing_sample,base_comparison,illustrative_cashflow)

ROOT=Path(__file__).resolve().parents[1]


class FiveBaseComparisonModelTests(unittest.TestCase):
    def setUp(self):
        self.data=load_five_base_evidence()
        self.bases={b["id"]:b for b in self.data["housing"]}

    def test_five_cities_fifteen_same_destinations_and_no_2027_quotes(self):
        self.assertEqual(tuple(self.data["base_ids"]),BASE_IDS)
        self.assertEqual(len(self.data["common_destinations"]),15)
        self.assertEqual(len(self.data["verified_time_routes"]),27)
        self.assertEqual(sum(len(b["listings"]) for b in self.data["housing"]),15)
        self.assertTrue(all(len(b["listings"])==3 for b in self.data["housing"]))
        self.assertEqual(self.data["research_window"]["nights"],60)
        self.assertTrue(all(x["stay_60_night_total_eur"] is None for b in self.data["housing"]
                            for x in b["listings"]))
        self.assertEqual(self.data["research_window"]["status"],
                         "comparison_hypothesis_not_official_plan_date")

    def test_documented_station_times_are_not_travel_day_guarantees(self):
        france=route_observation(self.data,"offenburg","strasbourg")
        self.assertEqual((france["train_min"],france["regional_min"]),(25,29))
        self.assertFalse(france["weekend_return_verified"])
        self.assertFalse(france["door_to_door_verified"])
        lux=route_observation(self.data,"trier","luxembourg_city")
        self.assertEqual(lux["train_min"],47)
        self.assertEqual(lux["source_status"],"timetable_aggregator_2026")
        ams=route_observation(self.data,"lille","amsterdam")
        self.assertEqual(ams["train_min"],169)
        self.assertEqual(ams["fare_from_eur_person_oneway"],69)
        self.assertFalse(ams["weekend_return_verified"])
        unknown=route_observation(self.data,"trier","basel")
        self.assertIsNone(unknown["train_min"])
        self.assertIsNone(unknown["fare_from_eur_person_oneway"])
        with self.assertRaises(ValueError):
            route_observation(self.data,"missing_base","basel")

    def test_comparison_counts_known_without_zeroing_unknowns(self):
        original=deepcopy(self.data)
        rows=base_comparison(self.data)
        self.assertEqual(len(rows),5)
        by={row["base_id"]:row for row in rows}
        self.assertEqual(by["offenburg"]["with_station_times"],5)
        self.assertEqual(by["trier"]["with_station_times"],1)
        self.assertEqual(by["mulhouse"]["with_station_times"],6)
        self.assertEqual(by["strasbourg"]["with_station_times"],10)
        self.assertEqual(by["lille"]["with_station_times"],6)
        self.assertEqual(by["trier"]["with_fare_samples"],0)
        self.assertEqual(by["trier"]["without_station_times"],14)
        self.assertIsNotNone(by["lille"]["minimum_train_oneway_minutes_known"])
        self.assertEqual(by["lille"]["country_count_lower_bound"],4)
        self.assertTrue(all(not x["full_return_date_verified"] for x in rows))
        self.assertTrue(all(x["fare_2027_coverage"]==0 for x in rows))
        self.assertTrue(all(not x["can_rank_final"] for x in rows))
        self.assertEqual(original,self.data)
        with self.assertRaises(ValueError):
            base_comparison(self.data,[])
        with self.assertRaises(ValueError):
            base_comparison(self.data,["basel","basel"])

    def test_housing_samples_dont_mean_equality_or_2027_lease(self):
        off=housing_sample(self.bases["offenburg"])
        self.assertEqual(off["size_30_to_60_count"],0)
        self.assertEqual(off["sample_median_eur_month"],2500)
        self.assertIsNone(off["total_60_nights_eur"])
        trier=housing_sample(self.bases["trier"])
        self.assertEqual(trier["size_30_to_60_count"],2)
        self.assertEqual(trier["sample_median_eur_month"],1000)
        lille=housing_sample(self.bases["lille"])
        self.assertEqual(lille["size_30_to_60_count"],3)
        self.assertEqual(lille["sample_count"],3)
        self.assertEqual(lille["verified_for_same_60_nights"],0)

    def test_cashflow_is_user_input_only_no_deposit_cost(self):
        incomplete=illustrative_cashflow({"housing":3200},6.3)
        self.assertEqual(incomplete["known_input_subtotal_eur"],3200)
        self.assertIsNone(incomplete["full_six_category_hypothesis_eur"])
        self.assertIn("groceries",incomplete["missing_categories"])
        full=illustrative_cashflow({
            "housing":3200,"groceries":900,"restaurants":700,"urban":200,
            "excursions":600,"extras":200,"refundable_deposit":1000
        },6.3)
        self.assertEqual(full["full_six_category_hypothesis_eur"],5800)
        self.assertEqual(full["full_six_category_hypothesis_brl"],36540)
        self.assertEqual(full["deposit_cash_eur"],1000)
        self.assertFalse(full["complete_trip_cost"])
        self.assertFalse(full["official_budget_changed"])
        with self.assertRaises(ValueError):
            illustrative_cashflow({"housing":-10},6.3)
        with self.assertRaises(ValueError):
            illustrative_cashflow({"housing":100},0)
        with self.assertRaises(ValueError):
            illustrative_cashflow({"housing":float("nan")},6.3)


class FiveBaseComparisonAppTests(unittest.TestCase):
    def test_five_base_panel_is_read_only(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux_city_view").set_value("Pesquisa ampliada").run()
        original=deepcopy(app.session_state["advisor_plan"])
        self.assertEqual(app.session_state["ux_city_view"],"Pesquisa ampliada")
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("five_base_detail",{x.key for x in app.selectbox})
        self.assertIn("five_base_destinations",{x.key for x in app.multiselect})
        app.selectbox(key="five_base_detail").set_value("trier").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.number_input(key="five_base_manual_housing").set_value(3000.0).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(original["revision"],
                         app.session_state["advisor_plan"]["revision"])


if __name__=="__main__":
    unittest.main()
