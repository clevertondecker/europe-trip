"""Rail observations: provenance, aliases, incompleteness and unchanged TripPlan."""
from copy import deepcopy
import unittest

from rail_evidence_unified_model import canonical_place,load_rail_evidence,route_evidence
from base_research_expanded_model import load_research
from five_base_comparison_model import load_five_base_evidence
from city_profiles_model import load_profiles
from city_research_packs_model import load_city_packs
from ux41_favorites_model import comparative_matrix
from trip_plan_model import new_plan


class RailEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_rail_evidence()

    def test_aliases_explicit(self):
        self.assertEqual(canonical_place("luxembourg"),"luxembourg_city")
        self.assertEqual(canonical_place("Bruxelas"),"brussels")
        self.assertEqual(canonical_place("Bruges"),"bruges_be")
        self.assertNotEqual(canonical_place("bruges_be"),canonical_place("brussels"))

    def test_sources_and_duplicates_preserved(self):
        row=route_evidence(self.data,"offenburg","strasbourg")
        self.assertEqual(row["status"],"historical_time")
        self.assertGreaterEqual(len(row["observations"]),2)
        self.assertTrue(all(x["source_url"] for x in row["observations"]))
        self.assertFalse(row["return_2027_verified"])
        self.assertFalse(row["comparable"])

    def test_expanded_rail_reused(self):
        route=route_evidence(self.data,"karlsruhe","strasbourg")
        self.assertEqual(route["minimum_oneway_min"],41)
        self.assertEqual(route["typical_oneway_min"],70)
        self.assertEqual(route["source_dataset"],"expanded_rail_sample_2026")

    def test_unknown_vs_partial_vs_local(self):
        self.assertEqual(route_evidence(self.data,"freiburg","amsterdam")["status"],"not_researched")
        self.assertEqual(route_evidence(self.data,"mulhouse","mulhouse")["status"],"local")
        self.assertEqual(route_evidence(self.data,"metz","colmar")["status"],"partial")
        self.assertIsNone(route_evidence(self.data,"metz","colmar")["minimum_oneway_min"])

    def test_three_favorites_same_basket_and_no_official_mutation(self):
        plan=new_plan()
        original=deepcopy(plan)
        five=load_five_base_evidence()
        data=comparative_matrix(load_research(),five,load_profiles(),
                                load_city_packs(),["mulhouse","strasbourg","freiburg"],
                                ["strasbourg","colmar","amsterdam"])
        self.assertEqual([c["id"] for c in data["cities"]],
                         ["mulhouse","strasbourg","freiburg"])
        self.assertEqual(len(data["cities"][0]["routes"]),3)
        self.assertEqual(len(data["cities"][2]["routes"]),3)
        self.assertIsNone(data["complete_budget"])
        self.assertEqual(plan,original)

if __name__=="__main__":
    unittest.main()
