import unittest
from city_market import load_market, observed_rent_summary, example_train_couple_return
class MarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=load_market()
    def test_four_cities_and_equal_sample(self):
        self.assertEqual({x["id"] for x in self.data["cities"]},{"mulhouse","strasbourg","metz","nancy"})
        self.assertEqual([len(x["offers"]) for x in self.data["cities"]],[3,3,3,3])
    def test_no_fake_2027_booking(self):
        for city in self.data["cities"]:
            self.assertEqual(city["rental_quote_eligible_2027"],0)
            for offer in city["offers"]:
                self.assertIsNone(offer["total_stay_eur"])
                self.assertFalse(offer["quote_for_2027"])
    def test_rent_is_sample_not_full_stay(self):
        self.assertEqual(observed_rent_summary(self.data["cities"][0])["sample_median_eur_month"],980)
        self.assertEqual(observed_rent_summary(self.data["cities"][1])["sample_median_eur_month"],950)
    def test_rail_example_is_conditional(self):
        self.assertEqual(example_train_couple_return(5.4),21.6)
        self.assertIsNone(example_train_couple_return(None))
    def test_shared_groceries_not_four_different_quotes(self):
        self.assertEqual(self.data["common_costs"]["groceries_eur_week_couple"],137.06)
        self.assertFalse(self.data["common_costs"]["city_specific"])
    def test_urls_and_pass_prices(self):
        for city in self.data["cities"]:
            self.assertTrue(city["urban_pass"]["source_url"].startswith("https://"))
            self.assertGreater(city["urban_pass"]["fare_eur_month_person"],0)
if __name__=="__main__": unittest.main()
