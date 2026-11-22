"""REC05 prioritizes evidence, never guesses travel or changes stored state."""
import json
import unittest
from copy import deepcopy
from rec05_priority_research_model import (
    prioritize_research, export_research_plan, POLICY_VERSION,
)


def sample():
    categories={
        "alpha":{"paris":"no_time","colmar":"historical","basel":"local"},
        "beta":{"paris":"historical","colmar":"reference_only","basel":"no_time"},
    }
    priorities={"paris":"must_visit","colmar":"interested","basel":"maybe"}
    candidates=[]
    for base,rows in categories.items():
        cells={}
        raw={}
        for dest,category in rows.items():
            cells[dest]={"category":category,
                         "source_url":"https://example.org/route" if category=="historical" else None,
                         "display_min":45 if category in ("historical","reference_only") else None}
            raw[dest]={"source_url":cells[dest]["source_url"],
                       "fare_from_eur_person_oneway":None,
                       "evidence_date":"2026-11-15"}
        candidates.append({"base_id":base,"base_name":base,"evidence":cells,
                           "raw_rail_evidence":raw,
                           "must_visit":{"missing":["paris"] if base=="alpha" else []},
                           "highlight":True})
    return {"policy_version":"rec02-logistics-v1","state":"partial_evidence",
            "complete_groups":[],"highlight_ids":["beta","alpha"],
            "destinations":[{"id":d,"name":d,"country":"Synthetic",
                             "priority":p} for d,p in priorities.items()],
            "candidates":candidates}


class PriorityResearchTests(unittest.TestCase):
    def test_deterministic_direction_and_must_visit_gap(self):
        result=sample()
        before=deepcopy(result)
        full=prioritize_research(result,base_ids=["beta","alpha"])
        self.assertEqual(full["state"],"ready")
        self.assertEqual(full["policy_version"],POLICY_VERSION)
        self.assertEqual(full["total_count"],len(full["tasks"]))
        keys={(r["base_id"],r["destination_id"],r["evidence_type"]) for r in full["tasks"]}
        self.assertEqual(len(keys),len(full["tasks"]))
        self.assertTrue(full["read_only"])
        self.assertFalse(full["claims_feasibility_2027"])
        self.assertEqual(full["tasks"][0]["priority"],"must_visit")
        alpha_paris=[x for x in full["tasks"] if x["base_id"]=="alpha"
                     and x["destination_id"]=="paris"]
        self.assertEqual([x["evidence_type"] for x in alpha_paris],["outbound_minimum"])
        self.assertTrue(alpha_paris[0]["blocks_complete_comparison"])
        self.assertNotIn(("alpha","basel","outbound_minimum"),keys)
        self.assertIn(("alpha","basel","urban_access"),keys)
        self.assertNotIn(("alpha","colmar","outbound_minimum"),keys)
        self.assertIn(("alpha","colmar","weekend_return"),keys)
        self.assertEqual(before,result)
        reversed_result=deepcopy(result)
        reversed_result["destinations"].reverse()
        reversed_result["candidates"].reverse()
        reversed_result["highlight_ids"].reverse()
        again=prioritize_research(reversed_result,base_ids=["alpha","beta"])
        self.assertEqual(full,again)

    def test_partial_export_is_manual_undisclosed_and_unverified(self):
        queue=prioritize_research(sample(),base_ids=["alpha"],limit=4)
        self.assertEqual(len(queue["tasks"]),4)
        self.assertGreater(queue["total_count"],4)
        blob=export_research_plan(queue,exported_at="2026-11-22")
        result=json.loads(blob)
        self.assertEqual(result["policy_version"],POLICY_VERSION)
        self.assertEqual(result["exported_at"],"2026-11-22")
        self.assertEqual(result["research_state"],"not_performed")
        self.assertEqual(len(result["items"]),4)
        self.assertNotIn("advisor_plan",blob.decode())
        self.assertNotIn("account",blob.decode())
        self.assertFalse(any("cost_brl" in x for x in result["items"]))

    def test_ux506_verified_components_are_not_reported_missing(self):
        readiness={"journeys":[{"base_id":"alpha","destination_id":"colmar",
                                "weekend_return_verified":True,"last_mile_verified":True}],
                   "base_housing":[{"base_id":"alpha",
                                    "verified_56_to_60_night_quotes_2027":1,
                                    "work_space_verified":True,
                                    "station_access_verified":True}]}
        q=prioritize_research(sample(),base_ids=["alpha"],readiness=readiness)
        keys={(x["base_id"],x["destination_id"],x["evidence_type"]) for x in q["tasks"]}
        self.assertNotIn(("alpha","colmar","weekend_return"),keys)
        self.assertNotIn(("alpha","colmar","last_mile"),keys)
        self.assertNotIn(("alpha",None,"housing_quote"),keys)
        self.assertNotIn(("alpha",None,"housing_internet"),keys)
        self.assertIn(("alpha","colmar","fare_2027"),keys)

    def test_only_https_sources_and_missing_data_never_zero(self):
        data=sample()
        c=data["candidates"][0]
        c["evidence"]["colmar"]["source_url"]="http://unverified.invalid"
        q=prioritize_research(data,base_ids=["alpha"])
        row=next(x for x in q["tasks"] if
                 x["destination_id"]=="colmar" and x["evidence_type"]=="weekend_return")
        self.assertIsNone(row["source_url"])
        self.assertIn(("alpha","colmar","source_trace"),
                      {(x["base_id"],x["destination_id"],x["evidence_type"]) for x in q["tasks"]})
        self.assertTrue(all(x["status"]=="pending_research" for x in q["tasks"]))
        self.assertFalse(any("0 min" in x["reason"] for x in q["tasks"]))

    def test_scope_or_catalog_mismatch_fails_closed(self):
        self.assertEqual(prioritize_research({"state":"scope_required"})["tasks"],[])
        for invalid in ([],["nothere"],["alpha","alpha"]):
            with self.assertRaises(ValueError):
                prioritize_research(sample(),base_ids=invalid)
        bad=sample()
        bad["candidates"][0]["evidence"].pop("paris")
        with self.assertRaises(ValueError):
            prioritize_research(bad)
        with self.assertRaises(ValueError):
            prioritize_research(sample(),limit=0)

    def test_real_rec02_data23_and_legacy_scope_remain_unchanged(self):
        from ux502_destination_interests_model import empty_interests,set_interest
        from trip01_supplemental_discovery import build_exploration_discovery
        from recommendation_scope_model import confirm_scope
        from base_recommendation_model import recommend_bases
        from trip_plan_model import new_plan
        discovery=build_exploration_discovery()
        wishes=empty_interests()
        for dest,priority in (("paris","must_visit"),("angers","interested"),
                              ("colmar","maybe"),("strasbourg","interested")):
            wishes=set_interest(wishes,dest,priority,discovery)
        scope=confirm_scope(wishes,[x["destination_id"] for x in wishes["items"]],discovery)
        plan=new_plan()
        before=deepcopy((plan,wishes,scope))
        recommendation=recommend_bases(wishes,scope,discovery=discovery)
        queue=prioritize_research(recommendation,base_ids=["angers","strasbourg","mulhouse"])
        self.assertEqual(queue["state"],"ready")
        self.assertTrue(queue["tasks"])
        self.assertEqual(queue["destination_ids"],sorted(scope["destination_ids"]))
        self.assertTrue(all(x["base_id"] in {"angers","strasbourg","mulhouse"}
                            for x in queue["tasks"]))
        self.assertEqual((plan,wishes,scope),before)

    def test_app_display_does_not_mutate_context(self):
        from streamlit.testing.v1 import AppTest
        script="""
import streamlit as st
from rec05_priority_research_ui import render_research_result
render_research_result(st.session_state["result"],key="rec05_test",base_ids=["alpha"])
"""
        app=AppTest.from_string(script,default_timeout=90)
        data=sample()
        app.session_state["result"]=deepcopy(data)
        app.run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertTrue(any("Pesquisas prioritárias" in e.label for e in app.expander))
        self.assertEqual(app.session_state["result"],data)


if __name__=="__main__":
    unittest.main()
