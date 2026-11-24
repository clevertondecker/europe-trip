"""UX115 regression: one shared evidence resolution, no duplicate data."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from base_change_model import destination_catalog,known_route,destination_impact
from city_decision_model import compare_city_decisions
from city_decision_ui import contextual_impact_projection
from data_model import load_data
from evidence_query_model import get_rail_evidence
from rail_reference_projection_model import decorate_comparison
from rec03a_suggestions_ui import _review_destinations
from trip_plan_model import new_plan

class SharedEvidenceTests(unittest.TestCase):
    def test_same_resolution(self):
        for base,dest in [("metz","basel"),("metz","colmar"),("metz","paris"),
                          ("mulhouse","paris"),("mulhouse","obernai"),
                          ("metz","obernai"),("metz","interlaken"),("metz","metz")]:
            with self.subTest(base=base,dest=dest):
                raw=get_rail_evidence(base,dest)
                row={"base_id":base,"destination_id":dest,"evidence_status":raw["status"],
                     "minimum_oneway_min":raw["minimum_oneway_min"],"source_url":raw["source_url"]}
                cell=decorate_comparison({"rows":[row]})["cells"][(base,dest)]
                route=known_route(base,dest)
                self.assertEqual(route["minutes"],cell["display_min"])
                self.assertEqual(route["category"],cell["category"])
                self.assertFalse(route["return_verified"])
                self.assertFalse(route["valid_for_2027"])
    def test_secondary_and_local(self):
        route=known_route("metz","obernai")
        self.assertEqual(route["minutes"],104)
        self.assertEqual(route["confidence"],"low")
        self.assertEqual(known_route("metz","metz")["category"],"local")
        self.assertIsNone(known_route("metz","metz")["minutes"])
        self.assertIn("obernai",destination_catalog())
        self.assertEqual(_review_destinations(["paris","obernai","unknown_ux115"]),
                         (["paris","obernai"],["unknown_ux115"]))
    def test_like_for_like(self):
        plan=new_plan()
        plan["base_city"]="metz"
        template=dict(minutes=42,fare=None,source=None,fare_condition=None,basis=None,
                      note="",category="historical",confidence="medium",provenance="sample",
                      representative_minutes=None)
        for before,after,expected,basis in [(42,91,49,"fastest_reference"),
                                             (50,106,56,"representative")]:
            a=dict(template,representative_minutes=None if basis=="fastest_reference" else before)
            b=dict(template,minutes=91,representative_minutes=106)
            with patch("base_change_model.known_route",side_effect=[a,b]):
                row=destination_impact(plan,"nancy",["luxembourg"])[0]
            self.assertEqual(row["delta_minutes"],expected)
            self.assertEqual(row["comparison_basis"],basis)
    def test_context_is_read_only_and_priorities_visible(self):
        plan=new_plan()
        plan["base_city"]="metz"
        before=deepcopy(plan)
        dests=["basel","colmar","paris","interlaken","obernai","strasbourg"]
        c=compare_city_decisions(plan,["mulhouse"],dests,{},load_data(),False,60,6.3)
        v=contextual_impact_projection(c,{"obernai":"must_visit"})
        self.assertEqual(v["total"],len(dests))
        self.assertEqual(sum(map(len,v["groups"].values())),len(dests))
        self.assertEqual(v["comparable"],sum(len(v["groups"][k]) for k in ("Melhorou","Piorou","Semelhante")))
        row=next(x for rows in v["groups"].values() for x in rows if x["name"]=="Obernai")
        self.assertEqual(row["priority_label"],"Imperdível")
        self.assertEqual(plan,before)
        self.assertIsNone(c["winner"])
