import copy
from unittest.mock import patch
import unittest
from datetime import date
from decimal import Decimal
from trip_plan_model import new_plan,validate_plan,with_revision,apply_proposal
from trip_plan_repository import safe_path
from attractions_model import load_attractions,load_base_routes
from travel_advisor import assess_plan,recommendations,objective_weights
from travel_optimizer import propose_schedule,available_days,score_proposal

class AdvisorDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.routes=load_base_routes()
    def make_plan(self):
        p=new_plan()
        p["packages"]={"colmar":["colmar_venise","colmar_tanners"],
                       "oeschinen":["oesch_cable"]}
        return p
    def test_default_preferences(self):
        p=new_plan()
        self.assertEqual(p["profile"],"balanced")
        self.assertEqual(sum(objective_weights(p["profile"]).values()),100)
        self.assertEqual(p["revision"],0)
    def test_reject_does_not_change_plan(self):
        p=self.make_plan()
        proposals=propose_schedule(p,self.catalog,self.routes)
        before=copy.deepcopy(p)
        self.assertEqual(apply_proposal(p,proposals[0],False),before)
        self.assertEqual(p,before)
    def test_approve_requires_fresh_revision(self):
        p=self.make_plan()
        candidate=propose_schedule(p,self.catalog,self.routes)[0]
        approved=apply_proposal(p,candidate,True)
        self.assertEqual(approved["revision"],p["revision"]+1)
        self.assertNotEqual(approved["assignments"],p["assignments"])
        with self.assertRaises(ValueError):
            apply_proposal(approved,candidate,True)
    def test_alpine_unknown_does_not_get_scheduled(self):
        p=self.make_plan()
        candidates=propose_schedule(p,self.catalog,self.routes)
        self.assertGreaterEqual(len(candidates),1)
        self.assertLessEqual(len(candidates),3)
        self.assertIn("colmar",candidates[0]["placed"])
        self.assertNotIn("oeschinen",candidates[0]["placed"])
        self.assertTrue(any(x["destination"]=="oeschinen" for x in candidates[0]["unresolved"]))
        valid_dates={d["date"] for d in available_days(p)}
        for prop in candidates:
            self.assertTrue(set(prop["assignments"])<=valid_dates)
    def test_draft_score_never_reports_inferred_roundtrip_as_known(self):
        plan=self.make_plan()
        before=copy.deepcopy(plan)
        proposal=propose_schedule(plan,self.catalog,self.routes)[0]
        score=proposal["score"]
        self.assertIsNone(score["known_roundtrip_train_minutes"])
        self.assertIsNone(score["return_train_minutes"])
        self.assertIsNone(score["local_access_minutes"])
        self.assertFalse(score["return_2027_verified"])
        self.assertGreater(score["known_outbound_train_minutes"],0)
        self.assertEqual(score["symmetric_train_proxy_minutes"],
                         score["known_outbound_train_minutes"]*2)
        self.assertEqual(score["score_time_basis"],
                         "outbound_twice_editorial_proxy_not_verified_return")
        self.assertEqual(plan,before)

    def test_scoring_unknown_oneway_is_not_implicitly_zero(self):
        plan=self.make_plan()
        proposal={"placed":["oeschinen"],"assignments":{},"unresolved":[]}
        with self.assertRaises(ValueError):
            score_proposal(proposal,plan,self.routes,"balanced")

    def test_stable_legacy_heuristic_values_and_proposal_order(self):
        plan=self.make_plan()
        for profile in ("balanced","economy","experience"):
            with self.subTest(profile=profile):
                original=copy.deepcopy(plan)
                proposals=propose_schedule(plan,self.catalog,self.routes,profile)
                self.assertTrue(proposals)
                pairs=[]
                for candidate in proposals:
                    score=candidate["score"]
                    count=len(candidate["placed"])
                    outward=sum(
                        __import__("attractions_model").route_for(
                            self.routes,plan["base_city"],d)["train_minutes_one_way"]
                        for d in candidate["placed"])
                    holidays=sum(1 for day in candidate["assignments"]
                                 if day not in plan["assignments"] and
                                 date.fromisoformat(day).weekday()<5)
                    unplanned=len(candidate["unresolved"])
                    if profile=="economy":
                        old=count*70-outward*2/12-unplanned*30
                    elif profile=="experience":
                        old=count*95-outward*2/35-unplanned*40+holidays*2
                    else:
                        old=count*85-outward*2/20-unplanned*35
                    self.assertEqual(score["relative_score"],round(old,2))
                    self.assertIsNone(score["logistical_feasibility"])
                    self.assertFalse(score["confirmed_2027"])
                    self.assertIsNone(score["known_roundtrip_train_minutes"])
                    pairs.append((-score["relative_score"],candidate["proposal_id"]))
                self.assertEqual(pairs,sorted(pairs))
                self.assertEqual(plan,original)

    def test_local_draft_does_not_invent_urban_travel(self):
        plan=self.make_plan()
        score=score_proposal(
            {"placed":[plan["base_city"]],"assignments":{},"unresolved":[]},
            plan,self.routes,"balanced")
        self.assertEqual(score["known_outbound_train_minutes"],0)
        self.assertIsNone(score["local_access_minutes"])
        self.assertIsNone(score["return_train_minutes"])
        self.assertIsNone(score["logistical_feasibility"])

    def test_invalid_nonlocal_time_is_unresolved_instead_of_crashing(self):
        for invalid in (None,0,-3,True,34.5,"34"):
            with self.subTest(invalid=invalid):
                plan=self.make_plan()
                plan["packages"]={"colmar":["colmar_venise"]}
                with patch("travel_optimizer.route_for",
                           return_value={"train_minutes_one_way":invalid}):
                    self.assertEqual(propose_schedule(plan,self.catalog,self.routes),[])
                    with self.assertRaises(ValueError):
                        score_proposal(
                            {"placed":["colmar"],"assignments":{},"unresolved":[]},
                            plan,self.routes,"balanced")

    def test_missing_data_and_discount_are_flagged(self):
        p=self.make_plan()
        warnings=assess_plan(p,self.catalog,self.routes)
        codes={x["code"] for x in warnings}
        for flag in ("MISSING_PRICES","RETURN_UNVERIFIED","OVERNIGHT","DISCOUNT_CONDITIONAL"):
            self.assertIn(flag,codes)
        advice=recommendations(p,self.catalog,self.routes,warnings)
        self.assertTrue(all(not x["auto_apply"] for x in advice))
    def test_budget_limit_protection(self):
        p=self.make_plan()
        d=assess_plan(p,self.catalog,self.routes,{"margin":Decimal("-100"),"cap":Decimal("70000")})
        self.assertIn("OVER_BUDGET",{x["code"] for x in d})
    def test_id_whitelist_and_version(self):
        p=new_plan()
        self.assertTrue(safe_path(p["plan_id"]).startswith("data/user_plans/"))
        with self.assertRaises(ValueError):safe_path("../../.github/workflows/x.yml")
        bad=with_revision(p,{"base_city":"metz"})
        self.assertEqual(bad["revision"],1)
        with self.assertRaises(ValueError):
            validate_plan({**p,"departure_date":"2027-09-04"})
    def test_mandatory_and_excluded_cannot_overlap(self):
        p=new_plan()
        p["mandatory_destinations"]=["colmar"]
        p["excluded_destinations"]=["colmar"]
        with self.assertRaises(ValueError):validate_plan(p)

if __name__=="__main__":unittest.main()
