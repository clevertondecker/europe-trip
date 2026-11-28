import unittest
from attractions_model import load_attractions, load_base_routes
from destination_village_research_model import load_village_research
from ux501_destination_discovery_model import build_destination_discovery
from rail_evidence_unified_model import load_rail_evidence, route_evidence

class VillageResearchTest(unittest.TestCase):
    def test_catalog_and_matrix(self):
        catalog = load_attractions()
        self.assertTrue({"wengen", "riquewihr"} <= {d["id"] for d in catalog["destinations"]})
        self.assertTrue({"wengen", "riquewihr"} <= {d["id"] for d in build_destination_discovery()["destinations"]})
        self.assertEqual(len(load_village_research()["connections"]), 10)
        self.assertEqual(len([r for r in load_base_routes()["routes"] if r["destination_id"] in ("wengen", "riquewihr")]), 8)

    def test_no_mixed_mode_duration_in_rail_projection(self):
        rail = load_rail_evidence()
        self.assertEqual(route_evidence(rail, "lille", "wengen")["minimum_oneway_min"], 462)
        for base in ("mulhouse", "strasbourg", "metz", "nancy", "lille"):
            self.assertIsNone(route_evidence(rail, base, "riquewihr")["minimum_oneway_min"])
        for base in ("metz", "nancy"):
            self.assertIsNone(route_evidence(rail, base, "wengen")["minimum_oneway_min"])
