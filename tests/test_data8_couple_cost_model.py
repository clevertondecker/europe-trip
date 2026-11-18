import unittest

from data8_couple_cost_model import estimate_couple_excursion, load_cost_addons


def rng(a, b, *, roundtrip=True):
    result = {"min_eur": a, "max_eur": b,
              "state": "user_editorial_assumption",
              "method": "planning assumption entered by two travelers"}
    if roundtrip:
        result["journey_scope"] = "roundtrip_two_adults"
    return result


class CoupleCostTests(unittest.TestCase):
    def complete_inputs(self):
        return {"intercity_couple": rng(10, 20),
                "local_couple": rng(5, 15),
                "dining_couple": rng(30, 60)}

    def test_known_free_main_and_paid_optional_tour_are_separate(self):
        result = estimate_couple_excursion(["dq32_aachen_07"],
            selected_addons=["aachen_cathedral_guided_tour"],
            eur_to_brl=6, **self.complete_inputs())
        self.assertEqual(result["known_general_and_optional_eur"], 17)
        self.assertEqual(result["full_scenario_range_eur"], [62, 112])
        self.assertEqual(result["full_scenario_range_brl"], [372, 672])
        self.assertEqual(result["transport_scope"], "roundtrip_for_two_adults")
        self.assertFalse(result["valid_for_2027"])
        self.assertFalse(result["plan_mutated"])

    def test_optional_activity_is_an_explicit_scope(self):
        r = estimate_couple_excursion(["dq32_aachen_07"],
            visit_scopes={"dq32_aachen_07": "optional_activity"},
            selected_addons=["aachen_cathedral_guided_tour"],
            **self.complete_inputs())
        self.assertEqual(r["full_scenario_range_eur"], [62, 112])
        missing = estimate_couple_excursion(["dq32_aachen_07"],
            visit_scopes={"dq32_aachen_07": "optional_activity"},
            **self.complete_inputs())
        self.assertIsNone(missing["full_scenario_range_eur"])
        self.assertIn("atividade_opcional:dq32_aachen_07", missing["missing"])

    def test_without_transport_or_food_is_not_complete_quote(self):
        result = estimate_couple_excursion(["dq32_aachen_07"])
        self.assertIsNone(result["full_scenario_range_eur"])
        self.assertIn("intercity_couple", result["missing"])
        self.assertIn("dining_couple", result["missing"])

    def test_external_scope_must_be_explicit_and_documented(self):
        base = ["dq32_aachen_07", "dq32_aachen_08"]
        inputs = {"intercity_couple": rng(20, 60),
                  "local_couple": rng(0, 15), "dining_couple": rng(30, 70)}
        unscoped = estimate_couple_excursion(base, **inputs)
        self.assertIsNone(unscoped["full_scenario_range_eur"])
        self.assertIn("escopo_visita:dq32_aachen_08", unscoped["missing"])
        self.assertIsNone(unscoped["known_reference_breakdown"][1]["known_eur"])
        scoped = estimate_couple_excursion(base,
            visit_scopes={"dq32_aachen_08": "external_visit"}, **inputs)
        self.assertEqual(scoped["full_scenario_range_eur"], [50, 145])
        self.assertEqual(scoped["exterior_without_main_ticket"], ["dq32_aachen_08"])
        self.assertEqual(scoped["known_reference_breakdown"][1]["known_eur"], 0)
        self.assertTrue(scoped["fare_counted_once_per_destination"])
        self.assertEqual(scoped["user_assumption_components"]["intercity_couple"], [20, 60])

    def test_unknown_or_unproved_external_cannot_be_free(self):
        args = {"intercity_couple": rng(60, 120),
                "local_couple": rng(10, 20), "dining_couple": rng(20, 50)}
        result = estimate_couple_excursion(["brussels_atomium"],
            visit_scopes={"brussels_atomium": "external_visit"}, **args)
        self.assertIn("comprovacao_visita_externa:brussels_atomium", result["missing"])
        self.assertIsNone(result["full_scenario_range_eur"])
        unknown = estimate_couple_excursion(["brussels_eu_quarter"],
            visit_scopes={"brussels_eu_quarter": "general_entry"}, **args)
        self.assertIn("ingresso:brussels_eu_quarter", unknown["missing"])
        self.assertIsNone(unknown["full_scenario_range_eur"])

    def test_roundtrip_not_inferred_from_one_way_fare(self):
        one_way = rng(10, 20, roundtrip=False)
        r = estimate_couple_excursion(["dq32_aachen_07"],
            intercity_couple=one_way, local_couple=rng(5, 15),
            dining_couple=rng(30, 60))
        self.assertIn("ida_volta_casal:intercity_couple", r["missing"])
        self.assertIsNone(r["full_scenario_range_eur"])

    def test_money_uses_decimal_half_up_and_manual_fx(self):
        r = estimate_couple_excursion(["dq32_aachen_07"],
            intercity_couple=rng(0.005, 0.005), local_couple=rng(0, 0),
            dining_couple=rng(0, 0), eur_to_brl=6)
        self.assertEqual(r["full_scenario_range_eur"], [0.01, 0.01])
        self.assertEqual(r["full_scenario_range_brl"], [0.03, 0.03])
        self.assertEqual(r["fx_source"], "user_assumption_not_live_fx")

    def test_reject_bad_scope_and_double_count(self):
        for ids in (["dq32_aachen_07", "strasbourg_cathedral"],
                    ["dq32_aachen_07", "dq32_aachen_07"]):
            with self.assertRaises(ValueError):
                estimate_couple_excursion(ids)
        for kwargs in (
            {"visit_scopes": {"fabricated": "external_visit"}},
            {"visit_scopes": {"dq32_aachen_07": "free"}},
            {"intercity_couple": rng(50, 10)},
            {"eur_to_brl": 0},
            {"selected_addons": ["aachen_cathedral_guided_tour"],
             "visit_scopes": {"dq32_aachen_07": "unknown"}},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                estimate_couple_excursion(["dq32_aachen_07"], **kwargs)
        self.assertEqual(len(load_cost_addons()["optional_activities"]), 1)


if __name__ == "__main__":
    unittest.main()
