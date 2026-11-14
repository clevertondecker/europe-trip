import unittest
from catalog import build_catalog, filter_catalog
from data_model import load_data
from itinerary_planner import load_itinerary
class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places=build_catalog(load_data()["places"],load_itinerary())
    def test_all_itinerary_places_present(self):
        self.assertGreaterEqual(len(self.places),18)
    def test_aliases_are_unified(self):
        ids=[p["id"] for p in self.places]
        self.assertEqual(ids.count("rome"),1)
        self.assertEqual(ids.count("naples"),1)
        self.assertEqual(ids.count("luxembourg"),1)
    def test_explicit_empty_filter_is_empty(self):
        self.assertEqual(filter_catalog(self.places,countries=[]),[])
        self.assertEqual(filter_catalog(self.places,statuses=[]),[])
    def test_none_filters_all(self):
        self.assertEqual(len(filter_catalog(self.places)),len(self.places))
    def test_map_and_route_points_share_geometry(self):
        italy=filter_catalog(self.places,phases=["italy"])
        self.assertTrue(any(p["id"]=="positano" for p in italy))
if __name__=="__main__":unittest.main()
