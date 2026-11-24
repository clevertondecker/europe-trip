"""UX113: selected-base projections are documentary and never select a stay."""
import unittest

from base_research_expanded_model import load_research
from city_research_round2 import load_round2
from ux113_comparison_panorama_ui import (
    coworking_night_status,project_comparison_panorama
)


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
        self.assertEqual([x["Cidade-base"] for x in panel["living"]],
                         [x["Cidade-base"] for x in panel["routine"]])
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
        routine = {x["Cidade-base"]: x for x in panel["routine"]}
        self.assertIsNone(routine["Lille"]["Coworking pesquisado"])
        self.assertIsNone(routine["Lille"]["Preço de referência (€)"])
        self.assertEqual(indexed["Lille"]["Amostra de anúncios (2026)"],
                         len(next(c["housing_offers"] for c in self.research["cities"]
                                  if c["id"] == "lille")))
        self.assertEqual(panel["logistics"][0]["Idas com tempo documentado"], "2/3")
        self.assertEqual(panel["logistics"][0]["Retorno e última milha"], "Não validados")

    def test_housing_range_is_documented_not_2027_quote(self):
        panel = project_comparison_panorama(
            self.projection(["metz","nancy"]), self.research, self.cost)
        for row in panel["living"]:
            count = row["Amostra de anúncios (2026)"]
            self.assertGreaterEqual(count, 0)
            if count:
                self.assertLessEqual(row["Mínimo observado (€ / mês)"],
                                     row["Mediana observada (€ / mês)"])
                self.assertLessEqual(row["Mediana observada (€ / mês)"],
                                     row["Máximo observado (€ / mês)"])
            else:
                self.assertIsNone(row["Mediana observada (€ / mês)"])
        self.assertFalse(panel["cost_of_stay_2027_quoted"])

    def test_coworking_observation_is_tristate_and_not_2027_promise(self):
        self.assertEqual(coworking_night_status(None),"Não pesquisado")
        for status,expected in (
            (True,"Compatibilidade observada em 2026"),
            (False,"Horário publicado não cobre"),
            (None,"Compatibilidade ainda não confirmada"),
        ):
            with self.subTest(status=status):
                label=coworking_night_status({"late_work_compatible":status})
                self.assertIn(expected,label)
                self.assertNotEqual(label,"Não pesquisado")
        panel=project_comparison_panorama(
            self.projection(["mulhouse","metz","nancy"]),self.research,self.cost)
        routine={r["Cidade-base"]:r for r in panel["routine"]}
        self.assertIn("Horário publicado",routine["Mulhouse"]["Expediente noturno (ref. 2026)"])
        self.assertIn("não confirmada",routine["Metz"]["Expediente noturno (ref. 2026)"])

    def test_historical_housing_sources_remain_accessible(self):
        panel=project_comparison_panorama(
            self.projection(["mulhouse","metz","lille"]),self.research,self.cost)
        expected=sum(len(c["housing_offers"]) for c in self.research["cities"]
                     if c["id"] in {"mulhouse","metz","lille"})
        self.assertEqual(len(panel["housing_sources"]),expected)
        self.assertTrue(all(url.startswith("https://")
                            for _,url in panel["housing_sources"]))
        self.assertFalse(panel["cost_of_stay_2027_quoted"])

    def test_four_and_five_base_cost_panels_keep_same_canonical_order(self):
        for bases in (["metz","nancy","mulhouse","strasbourg"],
                      ["metz","nancy","mulhouse","strasbourg","lille"]):
            with self.subTest(count=len(bases)):
                panel=project_comparison_panorama(
                    self.projection(bases),self.research,self.cost)
                names=[c["name"] for key in bases
                       for c in self.research["cities"] if c["id"]==key]
                self.assertEqual([r["Cidade-base"] for r in panel["living"]],names)
                self.assertEqual([r["Cidade-base"] for r in panel["routine"]],names)
                self.assertIsNone(panel["selected_base_for_itinerary"])

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
