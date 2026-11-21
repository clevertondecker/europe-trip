"""City profile data: canonical identities, source transparency, no invented scores."""
import unittest
from copy import deepcopy

from base_research_expanded_model import load_research
from city_profiles_model import load_profiles,validate_profiles,profile_by_id,compact_comparison


class CityProfilesTest(unittest.TestCase):
    def setUp(self):
        self.canonical=load_research()
        self.data=load_profiles(canonical=self.canonical)

    def test_thirty_canonical_cities_and_twelve_finalists(self):
        self.assertEqual(len(self.data["cities"]),len(self.canonical["cities"]))
        self.assertEqual(len(self.data["cities"]),34)
        self.assertEqual(sum(x["shortlist"] for x in self.data["cities"]),12)
        self.assertEqual({x["city_id"] for x in self.data["cities"]},
                         {x["id"] for x in self.canonical["cities"]})

    def test_new_public_facts_have_source_and_limit(self):
        for row in self.data["cities"]:
            self.assertIsNone(row["quality_of_life"]["numeric_score"])
            self.assertIsNone(row["daily_costs"]["comparable_basket_eur"])
            self.assertFalse(row["housing"]["availability_2027_verified"])
            for ev in row["evidence"]:
                self.assertTrue(ev["source_url"].startswith("https://"))
                self.assertTrue(ev["limitations"])
        self.assertEqual(sum(len(r["evidence"]) for r in self.data["cities"] if r["shortlist"]),35)

    def test_comparison_without_unsupported_ranking(self):
        rows=compact_comparison(self.data,["mulhouse","strasbourg","freiburg"])
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["Estadia 2027"],"Não confirmada")
        self.assertEqual(rows[1]["Custo cotidiano"],"Não comparável")

    def test_invalid_duplicate_or_changed_id_rejected(self):
        variant=deepcopy(self.data)
        variant["cities"][0]["city_id"]=variant["cities"][1]["city_id"]
        with self.assertRaises(ValueError):validate_profiles(variant,self.canonical)
        variant=deepcopy(self.data)
        variant["cities"][0]["housing"]["availability_2027_verified"]=True
        with self.assertRaises(ValueError):validate_profiles(variant,self.canonical)
        variant=deepcopy(self.data)
        variant["cities"][0]["evidence"][0]["source_url"]="not-a-source"
        with self.assertRaises(ValueError):validate_profiles(variant,self.canonical)

    def test_profiles_do_not_modify_official_data(self):
        before=deepcopy(self.canonical)
        p=profile_by_id(self.data,"mulhouse")
        p["summary"]="mutated"
        self.assertNotEqual(p["summary"],profile_by_id(self.data,"mulhouse")["summary"])
        self.assertEqual(self.canonical,before)


if __name__=="__main__":
    unittest.main()
