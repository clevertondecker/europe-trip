"""UX124 contracts: one profile, same rail cells, no writes, sparse data."""
import unittest
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from base_research_expanded_model import load_research
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest
from ux503_destination_base_comparison_model import build_wishlist_matrix
from routes7_comparison_projection import decorate_comparison
from ux124_city_profile_model import city_profile,TOPICS,route_scope,personalize_routes

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
                countries={d["id"]:d["country"] for d in self.discovery["destinations"]}
                self.assertTrue(all(r["country"]==countries[r["destination_id"]] for r in v["routes"]))
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
    def test_public_projection_never_contains_private_interests(self):
        from ux124_city_profile_ui import _public_profile
        a=_public_profile("mulhouse",self.research)
        self.assertTrue(all(r["priority"] is None for r in a["routes"]))
        a["routes"][0]["priority"]="must_visit"
        b=_public_profile("mulhouse",self.research)
        self.assertTrue(all(r["priority"] is None for r in b["routes"]))
        self.assertTrue(all(r["cell"]["category"] in ("historical","reference_only")
                            and r["attraction_count"]>0 for r in b["excursions"]))
    def test_scope_priority_and_counts(self):
        v=city_profile("mulhouse")
        priorities={"paris":"maybe","strasbourg":"interested","basel":"must_visit",
                    "mulhouse":"interested","colmar":"discarded"}
        routes=personalize_routes(v["routes"],priorities)
        desired=route_scope(routes,"Minha lista")
        self.assertEqual([r["priority"] for r in desired["rows"]],
                         ["must_visit","interested","interested","maybe"])
        self.assertEqual(desired["total"],4)
        self.assertEqual(desired["local"],1)
        self.assertEqual(desired["eligible"],3)
        self.assertEqual(desired["timed"]+desired["missing"],3)
        catalog=route_scope(routes,"Todos os destinos")
        self.assertEqual(catalog["total"],len(self.discovery["destinations"]))
        timed=route_scope(routes,"Com tempo pesquisado")
        self.assertEqual(timed["total"],catalog["timed"])
        self.assertEqual(timed["missing"],0)
        self.assertTrue(all(r["priority"] is None for r in v["routes"]))
    def test_all_subjects_in_full_and_sparse_profiles(self):
        for city in ("mulhouse","metz","strasbourg","annecy","colmar"):
            app=AppTest.from_string(
                "from ux124_city_profile_ui import render_city_profile\n"
                f"render_city_profile({city!r})",default_timeout=120).run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            for topic in TOPICS:
                app.segmented_control(key="ux124_topic_"+city).set_value(topic).run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
            app.segmented_control(key="ux124_topic_"+city).set_value("Logística").run()
            for scope in ("Minha lista","Todos os destinos","Com tempo pesquisado"):
                app.segmented_control(key="ux124_routes_"+city).set_value(scope).run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
                self.assertTrue(any(x.value.startswith(scope+":") for x in app.caption))
            self.assertNotIn("expanded_bases_rank_preset",{w.key for w in app.segmented_control})

if __name__=="__main__":
    unittest.main()
