import unittest
from itinerary_planner import load_itinerary
from route_preview import route_endpoints
class RoutePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=load_itinerary()
    def test_real_known_endpoints_only(self):
        outing=next(x for x in self.data["outings"] if x["id"]=="ferry_salerno_amalfi")
        pins=route_endpoints(self.data,outing)
        self.assertEqual([p["id"] for p in pins],["salerno","amalfi"])
    def test_unknown_origin_has_no_fake_route(self):
        outing=next(x for x in self.data["outings"] if x["id"]=="luxembourg_trip")
        self.assertEqual(route_endpoints(self.data,outing),[])
    def test_known_rail(self):
        outing=next(x for x in self.data["outings"] if x["id"]=="mulhouse_colmar")
        self.assertEqual(len(route_endpoints(self.data,outing)),2)
if __name__=="__main__":unittest.main()
