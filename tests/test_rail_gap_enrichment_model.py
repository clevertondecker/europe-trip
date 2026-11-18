"""DATA 9: provenance, coverage and conservative visualization tests."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json
import unittest

from rail_gap_enrichment_model import (
    DATA, load_gap_enrichment, validate_gap_dataset, missing_pair_report,
)
from routes7_comparison_projection import decorate_comparison
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import empty_interests, set_interest
from base_research_expanded_model import load_research
from trip_plan_model import new_plan


PRIORITY_PAIRS = {
    ("mulhouse", "aachen"), ("strasbourg", "aachen"),
    ("lille", "aachen"), ("karlsruhe", "aachen"),
    ("mulhouse", "karlsruhe"), ("strasbourg", "karlsruhe"),
    ("lille", "karlsruhe"), ("aachen", "karlsruhe"),
    ("mulhouse", "amsterdam"), ("aachen", "amsterdam"),
    ("karlsruhe", "amsterdam"), ("lille", "interlaken"),
    ("aachen", "interlaken"), ("karlsruhe", "interlaken"),
}


def basket():
    discovery = build_destination_discovery()
    interests = empty_interests()
    for dest in ("aachen", "karlsruhe", "amsterdam", "interlaken"):
        interests = set_interest(interests, dest, "interested", discovery)
    compare = compare_wishlist_bases(
        interests, ["mulhouse", "strasbourg", "lille", "aachen", "karlsruhe"],
        discovery=discovery)
    return interests, compare


class RailGapResearchTests(unittest.TestCase):
    def test_14_visible_gaps_and_additional_real_catalog_pairs(self):
        data = load_gap_enrichment()
        self.assertEqual(len(data["by_pair"]), 29)
        self.assertTrue(PRIORITY_PAIRS <= set(data["by_pair"]))
        self.assertEqual(len(set(data["by_pair"]) - PRIORITY_PAIRS), 15)
        self.assertEqual(data["known_unlinked_candidates"], ["zurich", "geneva"])
        self.assertFalse(data["mutates_catalog"])
        self.assertEqual(data["verified_2027_services"], 0)
        self.assertEqual(sum(x["evidence_type"] == "secondary_sample"
                             for x in data["records"]), 5)
        for row in data["records"]:
            self.assertFalse(row["return_weekend_verified"])
            self.assertFalse(row["door_to_door_verified"])
            self.assertFalse(row["valid_for_2027"])
            self.assertIsNone(row["fare_couple_eur"])
            self.assertIsNone(row["transfer_count"])
            self.assertIsNone(row["origin_station_id"])
            self.assertIsNone(row["destination_station_id"])

    def test_priority_matrix_reads_overlay_without_mutating_plan_or_wishes(self):
        interests, comparison = basket()
        before = deepcopy(comparison)
        wishes = deepcopy(interests)
        plan = new_plan(base="mulhouse")
        oldplan = deepcopy(plan)
        output = decorate_comparison(comparison)
        self.assertEqual(output["total"], 20)
        self.assertEqual(len(output["cells"]), 20)
        self.assertTrue(all(output["cells"][k]["gap_applied"]
                            for k in PRIORITY_PAIRS))
        self.assertEqual(
            sum(output[k] for k in ("historical","reference_only","local","no_time")),
            20)
        self.assertEqual(output["local"], 2)
        self.assertEqual(output["no_time"], 0)
        self.assertIn("mínimo publicado",
                      output["cells"][("strasbourg","karlsruhe")]["label"])
        self.assertIn("referência secundária",
                      output["cells"][("mulhouse","aachen")]["label"])
        self.assertIn("amostra datada de 2026",
                      output["cells"][("lille","aachen")]["label"])
        self.assertEqual(comparison, before)
        self.assertEqual(interests, wishes)
        self.assertEqual(plan, oldplan)

    def test_historical_source_wins_over_new_overlay(self):
        original = {"rows":[{
            "base_id":"aachen", "destination_id":"amsterdam",
            "evidence_status":"historical_time",
            "minimum_oneway_min":222, "source_url":"https://example.org/legacy",
            "observations":[], "divergent_sources":False,
        }]}
        before = deepcopy(original)
        item = decorate_comparison(original)["cells"][("aachen","amsterdam")]
        self.assertEqual(item["category"],"historical")
        self.assertEqual(item["display_min"],222)
        self.assertEqual(item["historical_source_url"],"https://example.org/legacy")
        self.assertFalse(item["gap_applied"])
        self.assertEqual(original,before)

    def test_reverse_is_not_inferred(self):
        row={"base_id":"amsterdam", "destination_id":"aachen",
             "evidence_status":"not_researched", "minimum_oneway_min":None,
             "source_url":None, "divergent_sources":False}
        item=decorate_comparison({"rows":[row]})["cells"][("amsterdam","aachen")]
        self.assertEqual(item["category"],"no_time")
        self.assertIsNone(item["display_min"])

    def test_all_bases_all_destinations_are_not_fabricated(self):
        discovery=build_destination_discovery()
        bases=[x["id"] for x in load_research()["cities"]]
        destinations=[x["id"] for x in discovery["destinations"]]
        result=missing_pair_report(bases,destinations)
        self.assertEqual(result["total"],len(bases)*len(destinations))
        self.assertGreater(result["still_unknown"],500)
        self.assertLess(result["reference_only"],29+1)
        self.assertTrue(result["no_schedule_2027_confirmed"])

    def test_schema_rejects_unsupported_evidence_and_2027_promise(self):
        base=json.loads(DATA.read_text(encoding="utf-8"))
        allow_dest={x["destination_id"] for x in base["records"]}
        allow_bases={x["origin_id"] for x in base["records"]}
        mutated=[]
        for field,value in (
            ("source_url","http://www.bahn.de/example"),
            ("source_checked_at","2029-01-01"),
            ("confidence","high"),
            ("oneway_min",0),
            ("oneway_min",1.5),
            ("return_weekend_verified",True),
            ("valid_for_2027",True),
            ("fare_couple_eur",20),
            ("origin_station_id","fabricated_hbf"),
            ("destination_id","fabricated_destination"),
            ("direction","return_and_outbound"),
            ("service_date","2027-09-09"),
            ("note",""),
        ):
            doc=deepcopy(base)
            doc["records"][0][field]=value
            mutated.append((field,doc))
        dupe=deepcopy(base)
        dupe["records"].append(deepcopy(dupe["records"][0]))
        mutated.append(("duplicate",dupe))
        for key,doc in mutated:
            with self.subTest(field=key), self.assertRaises(ValueError):
                validate_gap_dataset(doc,destination_ids=allow_dest,
                                     base_ids=allow_bases)

    def test_dataset_values_do_not_change_on_validation(self):
        doc=json.loads(DATA.read_text(encoding="utf-8"))
        before=deepcopy(doc)
        validate_gap_dataset(doc)
        self.assertEqual(doc,before)


if __name__ == "__main__":
    unittest.main()
