import copy
import json
import tempfile
from pathlib import Path
import unittest

from routes7_reference_model import (
    load_route_references, planning_reference, DATA, SNAPSHOT,
)
from evidence_query_model import get_rail_evidence


class Route7ProvenanceTests(unittest.TestCase):
    def test_snapshot_reproduces_all_15_original_observations(self):
        value = load_route_references()
        self.assertEqual(len(value["by_pair"]), 15)
        self.assertTrue(SNAPSHOT.is_file())
        self.assertEqual(
            sum(r["fastest_provenance"] == "corroborated_city_level"
                for r in value["records"]), 13)
        self.assertEqual(
            sum(r["average_provenance"] == "disagrees_with_current_page"
                for r in value["records"]), 1)

    def test_station_ambiguity_does_not_claim_verified_itinerary(self):
        value = load_route_references()
        b = value["by_pair"][("mulhouse", "belfort")]
        self.assertEqual(b["station_comparability"], "city_level_ambiguous")
        self.assertIsNone(b["origin_station_id"])
        self.assertIsNone(b["destination_station_id"])
        ref = planning_reference("mulhouse", "belfort", references=value)
        self.assertEqual(ref["display_basis"], "indicative_published_city_minimum")
        self.assertEqual(ref["fastest_min"], 25)
        self.assertEqual(ref["comparability"], "indicative_only_not_station_comparable")
        self.assertFalse(ref["weekend_return_known"])

    def test_legacy_and_secondary_references_are_distinct(self):
        old = get_rail_evidence("lille", "ghent")
        first = copy.deepcopy(old)
        view = planning_reference("lille", "ghent", legacy=old)
        self.assertEqual(view["display_min"], first["minimum_oneway_min"])
        self.assertEqual(view["fastest_min"], 68)
        self.assertEqual(view["average_min"], 76)
        self.assertTrue(view["reference_differs_from_legacy"])
        self.assertFalse(view["conflict_with_legacy"])
        self.assertEqual(first, old)

    def test_average_disagreement_is_not_overwritten(self):
        view = planning_reference("strasbourg", "belfort")
        self.assertEqual(view["original_snapshot_average_min"], 116)
        self.assertIsNone(view["average_min"])
        self.assertEqual(view["average_provenance"], "disagrees_with_current_page")
        item = load_route_references()["by_pair"][("strasbourg", "belfort")]
        self.assertEqual(item["recheck"]["average_min"], 106)

    def test_local_and_unreproduced_are_not_treated_as_trains(self):
        local = planning_reference("mulhouse", "mulhouse")
        self.assertEqual(local["status"], "local")
        self.assertIsNone(local["display_min"])
        # 49 min stays in the legacy layer; the new source snapshot was not
        # independently reproduced and cannot claim stronger provenance.
        other = planning_reference("strasbourg", "mulhouse")
        self.assertEqual(other["status"], "unreproduced_snapshot")
        self.assertIsNone(other["fastest_min"])
        self.assertEqual(other["display_basis"], "legacy_historical")

    def test_no_fare_transfer_or_future_service_inferred(self):
        for row in load_route_references()["records"]:
            self.assertIsNone(row["fare_for_two_eur"])
            self.assertIsNone(row["transfer_count"])
            self.assertEqual(row["weekend_return_status"], "unknown")

    def test_cross_field_negative_cases(self):
        original = json.loads(DATA.read_text(encoding="utf-8"))
        changes = []
        def mutated(index, field, value):
            o = copy.deepcopy(original)
            o["records"][index][field] = value
            return o
        changes += [
            mutated(0, "source_kind", "secondary_timetable_aggregator"),
            mutated(0, "source_url", "https://www.thetrainline.com/route"),
            mutated(0, "confidence", "high"),
            mutated(0, "time_scope", "local"),
            mutated(0, "fastest_provenance", "snapshot_only_unreproduced"),
            mutated(0, "station_comparability", "station_named_in_route_page"),
            mutated(0, "station_status", "route_page_identified_stations"),
            mutated(0, "fastest_min", 19),
            mutated(0, "weekend_return_status", "verified_2027"),
            mutated(0, "transfer_count", 1),
            mutated(6, "fastest_min", 3),
            mutated(9, "average_provenance", "corroborated_city_level"),
        ]
        o = copy.deepcopy(original)
        o["records"].append(copy.deepcopy(o["records"][0]))
        changes.append(o)
        o = copy.deepcopy(original)
        o["records"].pop()
        changes.append(o)
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "recheck.json"
            for case in changes:
                file.write_text(json.dumps(case), encoding="utf-8")
                with self.subTest(mutation=case["records"][0].get("fastest_min"),
                                  count=len(case["records"])), self.assertRaises(ValueError):
                    load_route_references(file)
