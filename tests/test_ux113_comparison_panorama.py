"""UX113: selected-base projections are documentary and never select a stay."""
import unittest

from base_research_expanded_model import load_research
from city_research_round2 import load_round2
from ux113_comparison_panorama_ui import project_comparison_panorama


class UX113PanoramaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research = load_research(include_candidates=True)
        cls.cost = load_round2()

    def projection(self, bases):
        return {
            "base_ids": list(bases),
            "destinations": [{"id": key} for key in ("paris", "brussels", "basel")],
            "counts": {
                base: {"historical": 1, "reference_only": 1,
                       "local": 0, "no_time": 1}
                for base in bases
            },
        }

    def test_same_selection_in_both_panels_without_choosing_base(self):
        bases = ["mulhouse", "lille", "strasbourg"]
        chosen = self.projection(bases)
        before = list(chosen["base_ids"])
        panel = project_comparison_panorama(chosen, self.research, self.cost)
        self.assertEqual(panel["base_ids"], before)
        self.assertEqual([x["Cidade-base"] for x in panel["logistics"]],
                         [x["Cidade-base"] for x in panel["living"]])
        self.assertEqual(panel["pilot_bases"], ["mulhouse", "strasbourg"])
        self.assertIsNone(panel["selected_base_for_itinerary"])
        self.assertFalse(panel["comparison_has_full_trip_logistics"])
        self.assertFalse(panel["cost_of_stay_2027_quoted"])
        self.assertEqual(chosen["base_ids"], before)

    def test_partial_cost_coverage_preserves_unknown_instead_of_zero(self):
        panel = project_comparison_panorama(
            self.projection(["mulhouse", "lille"]), self.research, self.cost)
        self.assertEqual(panel["covered_living_count"], 1)
        indexed = {x["Cidade-base"]: x for x in panel["living"]}
        self.assertIsNotNone(indexed["Mulhouse"]["Jantar para dois (€)"])
        self.assertIsNone(indexed["Lille"]["Jantar para dois (€)"])
        self.assertIsNone(indexed["Lille"]["Aluguel residencial (€/m²/mês)"])
        self.assertEqual(indexed["Lille"]["Coworking pesquisado"], "Não pesquisado")
        self.assertEqual(panel["logistics"][0]["Idas com tempo documentado"], "2/3")
        self.assertEqual(panel["logistics"][0]["Retorno e última milha"], "Não validados")

    def test_multiple_bases_are_not_split_into_multiple_stays(self):
        projection = self.projection(["mulhouse", "strasbourg", "metz"])
        panel = project_comparison_panorama(projection, self.research, self.cost)
        self.assertEqual(len(panel["living"]), 3)
        self.assertNotIn("first_base", panel)
        self.assertNotIn("second_base", panel)
        self.assertNotIn("split_days", panel)
        self.assertIsNone(panel["selected_base_for_itinerary"])


if __name__ == "__main__":
    unittest.main()
