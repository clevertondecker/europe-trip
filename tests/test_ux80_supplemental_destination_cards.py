"""Regression: real selected destinations may include supplemental (non-canonical) IDs.

The UX77 batch editor allows supplemental choices such as Obernai and Lucerne,
but those are not present in attractions_2027.json. A selected city must still
render, with unknown cost/rail data preserved as unknown.
"""
import unittest
from unittest.mock import patch

from attractions_model import load_attractions
from itinerary_flow_model import (
    FRANCE_STAGE, UNASSIGNED, add_undated_choices,
    selected_rows_for_stage, upsert_choice,
)
from trip_plan_model import new_plan, validate_plan
from ux47_destination_card_model import destination_card_view
from ux62_supplemental_outings import supplemental_destination


class SupplementalDestinationCardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()

    def test_all_five_cities_render_in_selected_stage(self):
        cities=["basel","colmar","interlaken","obernai","lucerne"]
        plan=add_undated_choices(
            new_plan(base="metz"),self.catalog,cities,FRANCE_STAGE)
        validate_plan(plan)
        rows=selected_rows_for_stage(plan,self.catalog,FRANCE_STAGE)
        self.assertEqual({r["id"] for r in rows},set(cities))
        with patch("ux47_destination_card_model.build_outing_guide") as strict_guide:
            cards=[destination_card_view(plan,self.catalog,{},r) for r in rows]
        self.assertEqual({c["id"] for c in cards},set(cities))
        self.assertTrue(all(c["attraction_count"]==0 for c in cards))
        self.assertTrue(all(c["reservation_confirmed"] is False for c in cards))
        self.assertTrue(all(c["cost_complete"] is False for c in cards))
        strict_guide.assert_not_called()

    def test_supplemental_city_not_in_canonical_catalog(self):
        canonical={d["id"] for d in self.catalog["destinations"]}
        self.assertNotIn("obernai",canonical)
        self.assertNotIn("lucerne",canonical)
        for city in ("obernai","lucerne"):
            with self.subTest(city=city):
                self.assertIsNotNone(supplemental_destination(city))
                plan=add_undated_choices(new_plan(base="metz"),self.catalog,
                                          [city],FRANCE_STAGE)
                row=selected_rows_for_stage(plan,self.catalog,FRANCE_STAGE)[0]
                view=destination_card_view(plan,self.catalog,{},row)
                self.assertEqual(view["id"],city)
                self.assertTrue(view["name"])
                self.assertTrue(view["country"])
                self.assertIn("não verificada",view["transport"])
                self.assertEqual(view["attraction_count"],0)
                self.assertFalse(view["reservation_confirmed"])

    def test_supplemental_attractions_are_shown_without_inventing_fares(self):
        plan=add_undated_choices(new_plan(base="metz"),self.catalog,
                                  ["obernai"],FRANCE_STAGE)
        plan=upsert_choice(plan,self.catalog,"obernai",
                           ["obernai_market"],UNASSIGNED)
        validate_plan(plan)
        row=selected_rows_for_stage(plan,self.catalog,FRANCE_STAGE)[0]
        with patch("ux47_destination_card_model.build_outing_guide") as guide:
            view=destination_card_view(plan,self.catalog,{},row)
        self.assertEqual(view["attraction_count"],1)
        self.assertTrue(any("Marché" in name for name in view["attractions"]))
        self.assertFalse(view["cost_complete"])
        self.assertFalse(view["reservation_confirmed"])
        self.assertIn("não",view["cost"])
        guide.assert_not_called()

    def test_unknown_destinations_still_fail(self):
        with self.assertRaisesRegex(ValueError,"não consta"):
            destination_card_view(new_plan(),self.catalog,{},
                {"id":"not-real","attractions":[],"period":UNASSIGNED,
                 "exact_dates":[]})


if __name__=="__main__":
    unittest.main()
