"""ARCH 1.0 — One precedence contract across 3 read-only railway consumers."""
import unittest
from copy import deepcopy

from evidence_query_model import get_rail_evidence
from rail_evidence_unified_model import (
    load_rail_evidence, route_evidence, canonical_place,
)
from base_explorer_model import load_exploration
from outing_base_coverage_model import preview_for_base
from dq31_logistics_evaluation_model import logistics_comparison
from dq32_macro_opportunities_model import opportunity_overview


class RailQueryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rail=load_rail_evidence()
        cls.exploration=load_exploration()

    def get(self,base,destination,**kwargs):
        return get_rail_evidence(base,destination,rail=self.rail,
                                 exploration=self.exploration,**kwargs)

    def test_selected_unified_evidence_keeps_source_and_typical(self):
        for origin,destination in (
            ("lille","brussels"),("offenburg","strasbourg"),
            ("mulhouse","colmar"),("strasbourg","brussels")):
            with self.subTest(origin=origin,destination=destination):
                before=route_evidence(self.rail,origin,destination)
                after=self.get(origin,destination)
                if before["status"]=="historical_time":
                    self.assertEqual(after["minimum_oneway_min"],
                                     before["minimum_oneway_min"])
                    self.assertEqual(after["typical_oneway_min"],
                                     before["typical_oneway_min"])
                    self.assertEqual(after["source_dataset"],
                                     before["source_dataset"])
                    self.assertEqual(after["source_url"],before["source_url"])
                    self.assertEqual(after["selection_reason"],
                                     "unified_adapter_precedence")
                self.assertFalse(after["return_2027_verified"])
                self.assertFalse(after["comparable"])

    def test_fallback_only_when_unified_evidence_has_no_time(self):
        rail={"by_pair":{}}
        exploration={"routes":[{
            "base_id":"lille","destination_id":"rotterdam",
            "train_minutes_oneway_min":148,
            "source_url":"https://www.sncf-connect.com",
            "retrieved_at":"2026-11-15"}]}
        chosen=get_rail_evidence("lille","rotterdam",rail=rail,
                                 exploration=exploration)
        self.assertEqual(chosen["minimum_oneway_min"],148)
        self.assertIsNone(chosen["typical_oneway_min"])
        self.assertEqual(chosen["source_dataset"],"exploration_bases_2027")
        self.assertEqual(chosen["selection_reason"],
                         "exploration_fallback_no_unified_time")
        self.assertFalse(chosen["return_2027_verified"])
        self.assertEqual(len(chosen["observations"]),1)
        selected=chosen["observations"][0]
        self.assertEqual(selected["selection_role"],"selected_fallback")
        self.assertEqual(selected["source_dataset"],"exploration_bases_2027")
        self.assertEqual(selected["evidence_date"],"2026-11-15")
        self.assertEqual(selected["minimum_oneway_min"],148)
        self.assertEqual(selected["source_url"],chosen["source_url"])
        self.assertFalse(selected["return_2027_verified"])

    def test_partial_unified_observation_is_preserved_alongside_fallback(self):
        original={
            "origin_id":"lille","destination_id":"rotterdam",
            "source_dataset":"incomplete_rail_research_2026",
            "minimum_oneway_min":None,
            "typical_oneway_min":None,
            "source_url":"https://rail.example/incomplete",
            "evidence_date":"2026-11-12",
        }
        rail={"by_pair":{("lille","rotterdam"):[deepcopy(original)]}}
        exploratory={
            "routes":[{
                "base_id":"lille","destination_id":"rotterdam",
                "train_minutes_oneway_min":148,
                "source_url":"https://rail.example/valid",
                "retrieved_at":"2026-11-15",
            }]
        }
        snapshot=deepcopy(rail)
        chosen=get_rail_evidence("lille","rotterdam",rail=rail,
                                 exploration=exploratory)
        self.assertEqual(chosen["status"],"historical_time")
        self.assertEqual(chosen["minimum_oneway_min"],148)
        self.assertEqual(chosen["selection_reason"],
                         "exploration_fallback_no_unified_time")
        self.assertEqual(len(chosen["observations"]),2)
        self.assertEqual(chosen["observations"][0],original)
        self.assertEqual(chosen["observations"][1]["selection_role"],
                         "selected_fallback")
        self.assertEqual(chosen["observations"][1]["source_url"],
                         "https://rail.example/valid")
        chosen["observations"][0]["source_url"]="mutated"
        self.assertEqual(rail,snapshot)

    def test_exploration_minutes_match_loader_int_contract(self):
        rail={"by_pair":{}}
        for invalid in (144.0, 144.5, True, "144", 0, -1, None):
            with self.subTest(invalid=invalid):
                exploratory={"routes":[{
                    "base_id":"lille","destination_id":"rotterdam",
                    "train_minutes_oneway_min":invalid,
                    "source_url":"https://rail.example/route",
                    "retrieved_at":"2026-11-15",
                }]}
                result=get_rail_evidence("lille","rotterdam",rail=rail,
                                         exploration=exploratory)
                self.assertIsNone(result["minimum_oneway_min"])
                self.assertEqual(result["observations"],[])
        valid=get_rail_evidence("lille","rotterdam",rail=rail,
            exploration={"routes":[{
                "base_id":"lille","destination_id":"rotterdam",
                "train_minutes_oneway_min":144,
                "source_url":"https://rail.example/route",
            }]})
        self.assertIs(type(valid["minimum_oneway_min"]),int)

    def test_unknown_and_local_do_not_become_zero_or_impossible(self):
        empty_rail={"by_pair":{}}
        empty_exploration={"routes":[]}
        unknown=get_rail_evidence("lille","reims",rail=empty_rail,
                                  exploration=empty_exploration)
        self.assertEqual(unknown["status"],"not_researched")
        self.assertIsNone(unknown["minimum_oneway_min"])
        local=get_rail_evidence("luxembourg","luxembourg_city",
                                rail=empty_rail,exploration=empty_exploration)
        self.assertEqual(local["status"],"local")
        self.assertIsNone(local["minimum_oneway_min"])
        self.assertFalse(local["return_2027_verified"])

    def test_reject_exploration_without_source_or_positive_duration(self):
        rail={"by_pair":{}}
        rows=[{"base_id":"lille","destination_id":"rotterdam",
               "train_minutes_oneway_min":0,"source_url":"https://operator.example"},
              {"base_id":"lille","destination_id":"rotterdam",
               "train_minutes_oneway_min":140,"source_url":None},
              {"base_id":"lille","destination_id":"rotterdam",
               "train_minutes_oneway_min":True,"source_url":"https://operator.example"}]
        result=get_rail_evidence("lille","rotterdam",rail=rail,
                                exploration={"routes":rows})
        self.assertIsNone(result["minimum_oneway_min"])

    def test_defensive_observations_and_inputs_not_mutated(self):
        source=deepcopy(self.rail)
        study=deepcopy(self.exploration)
        item=self.get("lille","brussels")
        item["observations"].clear()
        self.assertEqual(self.rail,source)
        self.assertEqual(self.exploration,study)

    def test_same_evidence_across_three_consumers_for_covered_pair(self):
        base,destination="lille","brussels"
        contract=self.get(base,destination)
        outing=preview_for_base(base,rail=self.rail,
                                exploration=self.exploration)
        o=next(row for row in outing["destinations"]
               if canonical_place(row["destination_id"])==destination)
        macro=opportunity_overview(base,rail=self.rail,
                                   exploration=self.exploration)
        m=next(row for row in macro["destinations"]
               if row["destination_id"]==destination)
        comparison=logistics_comparison(
            [base],selected_destinations=[destination],
            rail=self.rail,exploration=self.exploration)
        c=comparison["rows"][0]["routes"][0]
        for observed in (o["train_oneway_min"],
                         m["minimum_train_oneway_min"],
                         c["oneway_train_min"]):
            self.assertEqual(observed,contract["minimum_oneway_min"])
        for source in (o["train_evidence_url"],m["train_source_url"],
                       c["train_source_url"]):
            self.assertEqual(source,contract["source_url"])

    def test_missing_time_consistent_across_three_consumers(self):
        city="freiburg"
        destination="brussels"
        contract=self.get(city,destination)
        outing=preview_for_base(city,rail=self.rail,
                                exploration=self.exploration)
        o=next(row for row in outing["destinations"]
               if canonical_place(row["destination_id"])==destination)
        macro=opportunity_overview(city,rail=self.rail,
                                   exploration=self.exploration)
        m=next(row for row in macro["destinations"]
               if row["destination_id"]==destination)
        comparison=logistics_comparison(
            [city],selected_destinations=[destination],
            rail=self.rail,exploration=self.exploration)
        c=comparison["rows"][0]["routes"][0]
        self.assertEqual(o["train_oneway_min"],contract["minimum_oneway_min"])
        self.assertEqual(m["minimum_train_oneway_min"],contract["minimum_oneway_min"])
        self.assertEqual(c["oneway_train_min"],contract["minimum_oneway_min"])
        self.assertIsNone(c["return_train_min"])
        self.assertIsNone(m["full_trip_cost_eur"])

if __name__=="__main__":
    unittest.main()
