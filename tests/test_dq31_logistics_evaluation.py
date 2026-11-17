"""DQ3.1: no false rankings or travel/booking facts from sparse research."""
import unittest
from copy import deepcopy

from dq31_logistics_evaluation_model import (
    DEFAULT_WEIGHTS, validate_weights, select_common_basket,
    logistics_comparison, maturity_for_city,
)
from base_coverage_model import coverage_matrix
from five_base_comparison_model import load_five_base_evidence
from rail_evidence_unified_model import load_rail_evidence
from dq30_walking_access_model import load_walking_access
from base_explorer_model import load_exploration


class DQ31LogisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = coverage_matrix("general")
        cls.five = load_five_base_evidence()
        cls.rail = load_rail_evidence()
        cls.exploration = load_exploration()
        cls.geography = load_walking_access()

    def compare(self, ids, destinations=(), weights=None):
        return logistics_comparison(
            ids, selected_destinations=destinations,
            weights=weights or DEFAULT_WEIGHTS, coverage=self.coverage,
            five=self.five, rail=self.rail, exploration=self.exploration,
            geography=self.geography)

    def test_weights_are_configurable_and_sum_to_100(self):
        self.assertEqual(sum(DEFAULT_WEIGHTS.values()), 100)
        self.assertEqual(validate_weights({"logistics":75,
            "living_cost":20,"daily_practicality":5})["logistics"],75)
        for invalid in ({"logistics":65,"living_cost":30},
                        {"logistics":65,"living_cost":20,"daily_practicality":5},
                        {"logistics":float("nan"),"living_cost":0,
                         "daily_practicality":0},
                        {"logistics":True,"living_cost":95,"daily_practicality":4}):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                validate_weights(invalid)

    def test_default_basket_is_not_official_and_all_cities_use_same_destinations(self):
        view=self.compare(["mulhouse","strasbourg","lille","offenburg","freiburg"])
        self.assertEqual(view["basket"]["type"],"standard_exploratory_not_official")
        self.assertEqual(view["basket"]["reference_basket_size"],15)
        self.assertTrue(view["basket"]["same_basket_required"])
        for city in view["rows"]:
            self.assertEqual(city["basket_ids"],view["basket"]["ids"])
            self.assertEqual(len(city["routes"]),len(view["basket"]["ids"]))
        self.assertFalse(view["official_plan_modified"])

    def test_priority_basket_is_identical_for_bases_and_unknown_id_fails(self):
        chosen=("brussels","bruges_be","strasbourg")
        view=self.compare(["lille","offenburg","mulhouse"],chosen)
        self.assertEqual(view["basket"]["ids"],list(chosen))
        self.assertEqual(view["basket"]["type"],"user_priority_candidates")
        with self.assertRaises(ValueError):
            self.compare(["lille"],("not_in_basket",))

    def test_lille_rail_is_documented_but_never_a_return_or_total(self):
        view=self.compare(["lille","freiburg"],("brussels","bruges_be"))
        lille,freiburg=view["rows"]
        self.assertGreaterEqual(lille["train_time_coverage"],1)
        for trip in lille["routes"]:
            if trip["oneway_train_min"] is not None:
                self.assertGreater(trip["oneway_train_min"],0)
                self.assertTrue(trip["train_source_url"].startswith("https://"))
            self.assertIsNone(trip["return_train_min"])
            self.assertIsNone(trip["complete_door_to_door_min"])
            self.assertIsNone(trip["full_two_person_transport_eur"])
            self.assertFalse(trip["weekend_return_verified"])
        self.assertEqual(freiburg["train_time_coverage"],0)
        self.assertTrue(all(t["oneway_train_min"] is None for t in freiburg["routes"]))
        self.assertIsNone(freiburg["quality_score_0_100"])

    def test_published_walking_does_not_create_base_dependent_advantage(self):
        view=self.compare(["mulhouse","strasbourg","lille"],("bruges_be",))
        access=[x["routes"][0]["station_to_attraction_evidence"] for x in view["rows"]]
        self.assertEqual(access[0],access[1])
        self.assertEqual(access[1],access[2])
        self.assertTrue(any(item["minutes"]==20 for item in access[0]))
        for city in view["rows"]:
            trip=city["routes"][0]
            self.assertIsNone(trip["attraction_to_attraction_min"])
            self.assertIsNone(trip["complete_door_to_door_min"])
            self.assertIsNone(trip["full_two_person_transport_eur"])

    def test_local_destination_has_no_fake_zero_time_or_cost(self):
        city=self.compare(["strasbourg"],("strasbourg",))["rows"][0]
        trip=city["routes"][0]
        self.assertTrue(trip["local"])
        self.assertIsNone(trip["oneway_train_min"])
        self.assertIsNone(trip["complete_door_to_door_min"])
        self.assertEqual(trip["trip_status"],"local_access_unknown")

    def test_maturity_levels_and_2027_gate_are_distinct(self):
        empty=maturity_for_city(trains_known=0,basket_size=6,
            housing_observations=0,daily_researched=False)
        partial=maturity_for_city(trains_known=2,basket_size=6,
            housing_observations=1,daily_researched=False)
        grounded=maturity_for_city(trains_known=6,basket_size=6,
            housing_observations=3,daily_researched=True)
        definitive=maturity_for_city(trains_known=6,basket_size=6,
            housing_observations=3,daily_researched=True,final_ready=True)
        self.assertEqual(empty["current"],"pesquisa_inicial")
        self.assertEqual(partial["current"],"triagem_exploratoria")
        self.assertEqual(grounded["current"],"comparacao_fundamentada")
        self.assertFalse(grounded["decision_verified_2027"])
        self.assertTrue(definitive["decision_verified_2027"])

    def test_sparse_evidence_does_not_shrink_denominator_or_produce_rank(self):
        view=self.compare(["mulhouse","strasbourg","freiburg"],
                          ("strasbourg","colmar","basel"))
        self.assertFalse(view["quality_ranking_available"])
        for city in view["rows"]:
            self.assertEqual(city["basket_size"],3)
            self.assertIsNone(city["quality_score_0_100"])
            self.assertEqual(city["complete_itineraries"],0)

    def test_historical_housing_is_not_a_2027_quote_or_fabricated_price(self):
        view=self.compare(["offenburg","freiburg"],("strasbourg",))
        for city in view["rows"]:
            self.assertIsNone(city["quality_score_0_100"])
            self.assertFalse(city["final_decision_ready"])
            self.assertTrue(all(t["full_two_person_transport_eur"] is None
                                for t in city["routes"]))
        self.assertGreater(view["rows"][0]["housing_sample_count"],0)

    def test_inputs_are_not_mutated(self):
        source=deepcopy(self.coverage)
        geo=deepcopy(self.geography)
        view=self.compare(["lille"],("brussels",))
        view["rows"][0]["routes"][0]["destination_id"]="changed"
        self.assertEqual(self.coverage,source)
        self.assertEqual(self.geography,geo)

    def test_invalid_cities_duplicate_and_empty_basket(self):
        for bases in ([],["unknown"],["lille","lille"]):
            with self.subTest(bases=bases),self.assertRaises(ValueError):
                self.compare(bases,("brussels",))


if __name__ == "__main__":
    unittest.main()
