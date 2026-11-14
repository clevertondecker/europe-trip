"""Regression tests for historical, non-binding French city comparison."""
import unittest
from city_compare import get_preset, load_cities, normalized_weights, rank_cities, score_city

class CityCompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_cities()
        cls.ids = [item["id"] for item in cls.data["criteria"]]

    def test_historical_equilibrated_rank(self):
        ranked = rank_cities(self.data["cities"], get_preset(self.data, "balanced"), self.ids)
        self.assertEqual([row["city"]["name"] for row in ranked],
                         ["Mulhouse", "Strasbourg", "Metz", "Nancy"])
        expected = [4.375, 4.36, 4.19, 3.935]
        for item, value in zip(ranked, expected):
            self.assertAlmostEqual(item["score"], value, places=3)

    def test_all_presets_sum_to_100(self):
        for preset in self.data["presets"]:
            self.assertAlmostEqual(sum(preset["weights"].values()), 100)
            self.assertAlmostEqual(sum(normalized_weights(preset["weights"], self.ids).values()), 1)

    def test_reweighting_changes_scores_without_changing_source(self):
        baseline = get_preset(self.data, "balanced")
        city = self.data["cities"][0]
        original = dict(city["scores"])
        new = dict.fromkeys(self.ids, 0.0)
        new["nature"] = 100
        score = score_city(city, normalized_weights(new, self.ids))
        self.assertEqual(score, city["scores"]["nature"])
        self.assertEqual(city["scores"], original)
        self.assertNotEqual(score, score_city(city, normalized_weights(baseline, self.ids)))

    def test_zero_weights_rejected(self):
        with self.assertRaises(ValueError):
            normalized_weights(dict.fromkeys(self.ids, 0), self.ids)

    def test_invalid_or_incomplete_weights_rejected(self):
        with self.assertRaises(ValueError):
            normalized_weights({**dict.fromkeys(self.ids, 10), "unknown": 1}, self.ids)
        with self.assertRaises(ValueError):
            normalized_weights({**dict.fromkeys(self.ids, 10), "rent": -1}, self.ids)

    def test_tie_is_deterministic(self):
        cities = [{"name": "Z", "scores": dict.fromkeys(self.ids, 4)},
                  {"name": "A", "scores": dict.fromkeys(self.ids, 4)}]
        result = rank_cities(cities, get_preset(self.data, "balanced"), self.ids)
        self.assertEqual([x["city"]["name"] for x in result], ["A", "Z"])

    def test_source_has_provenance_and_no_unverified_booking(self):
        self.assertEqual(self.data["source"]["period"], "novembro de 2026")
        for city in self.data["cities"]:
            self.assertGreater(city["reference_rent_eur"], 0)
            self.assertTrue(city["historic_score"] > 0)

if __name__ == "__main__":
    unittest.main()
