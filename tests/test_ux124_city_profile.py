"""UX124 contracts: one profile, same rail cells, no writes, sparse data."""
import unittest
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from base_research_expanded_model import load_research
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest
from ux503_destination_base_comparison_model import build_wishlist_matrix
from routes7_comparison_projection import decorate_comparison
from ux124_city_profile_model import city_profile,TOPICS

class UnifiedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research=load_research(include_candidates=True)
        cls.discovery=build_exploration_discovery()
    def test_catalog_city_profiles_and_exact_route_projection(self):
        interests=set_interest(empty_interests(),"paris","must_visit",self.discovery)
        before=deepcopy(interests)
        research_before=deepcopy(self.research)
        for c in self.research["cities"]:
            with self.subTest(city=c["id"]):
                v=city_profile(c["id"],research=self.research,discovery=self.discovery,interests=interests)
                self.assertEqual(v["city"]["id"],c["id"])
                self.assertEqual(sum(v["counts"].values()),len(self.discovery["destinations"]))
                self.assertFalse(v["official_plan_modified"])
                matrix=decorate_comparison(build_wishlist_matrix(interests,[c["id"]],
                    discovery=self.discovery,research=self.research))
                row=next(r for r in v["routes"] if r["destination_id"]=="paris")
                self.assertEqual(row["cell"],matrix["cells"][(c["id"],"paris")])
                self.assertEqual(row["priority"],"must_visit")
        self.assertEqual(interests,before)
        self.assertEqual(self.research,research_before)
    def test_housing_and_remote_evidence_keep_separate_contracts(self):
        v=city_profile("mulhouse")
        self.assertEqual(v["housing"]["median_eur_month"],1350)
        self.assertEqual(v["market"]["urban_pass"]["fare_eur_month_person"],47)
        self.assertFalse(v["cost"]["coworking"]["late_work_compatible"])
        self.assertTrue(v["pack"]["climate"]["months_9_10_11"])
        sparse=city_profile("annecy")
        self.assertEqual(sparse["housing"]["count"],0)
        self.assertIsNone(sparse["cost"])
        self.assertTrue(sparse["extra_routes"])
    def test_all_subjects_in_full_and_sparse_profiles(self):
        for city in ("mulhouse","annecy"):
            app=AppTest.from_string(
                "from ux124_city_profile_ui import render_city_profile\n"
                f"render_city_profile({city!r})",default_timeout=120).run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            for topic in TOPICS:
                app.segmented_control(key="ux124_topic_"+city).set_value(topic).run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
            self.assertNotIn("expanded_bases_rank_preset",{w.key for w in app.segmented_control})

if __name__=="__main__":
    unittest.main()
