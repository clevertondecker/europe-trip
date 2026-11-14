import copy
import unittest
from itinerary_planner import (load_itinerary, validate_itinerary, select_outings,
                               basket_totals, published_ticket_total, visible_map_places)
class ItineraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_itinerary()
    def test_two_phases_with_coordinates(self):
        self.assertGreaterEqual(len(visible_map_places(self.data, "italy")), 7)
        self.assertGreaterEqual(len(visible_map_places(self.data, "france")), 8)
    def test_validated_ferry_roundtrip_for_couple(self):
        ferry = next(o for o in self.data["outings"] if o["id"]=="ferry_salerno_amalfi")
        self.assertEqual(published_ticket_total(ferry),48)
    def test_cable_car_fare_already_includes_return(self):
        car = next(o for o in self.data["outings"] if o["id"]=="oeschinen_cable")
        self.assertEqual(published_ticket_total(car),72)
        self.assertEqual(car["currency"],"CHF")
    def test_sum_does_not_mix_chf_and_eur(self):
        items = select_outings(self.data, "france", "mulhouse")
        out = basket_totals(items, ["mulhouse_colmar","oeschinen_cable","luxembourg_trip"])
        self.assertEqual(out["known_ticket_subtotals"],{"EUR":21.6,"CHF":72})
        self.assertEqual(len(out["unpriced"]),1)
        self.assertEqual(len(out["discount_conditional"]),1)
        self.assertFalse(out["complete"])
    def test_unknown_ferry_remains_unpriced(self):
        items = select_outings(self.data, "italy", "salerno")
        out = basket_totals(items,["capri"])
        self.assertEqual(len(out["unpriced"]),1)
    def test_duplicate_and_cross_base_rejected(self):
        with self.assertRaises(ValueError):
            basket_totals(select_outings(self.data,"italy","maiori"),["ferry_salerno_amalfi"])
        with self.assertRaises(ValueError):
            basket_totals(select_outings(self.data,"italy","salerno"),["capri","capri"])
    def test_price_must_have_source(self):
        altered=copy.deepcopy(self.data)
        altered["outings"][0]["source_url"]=""
        with self.assertRaises(ValueError):validate_itinerary(altered)
if __name__=="__main__":unittest.main()
