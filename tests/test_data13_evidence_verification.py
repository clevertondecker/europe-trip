"""Offline DATA13 URL identity, duration extraction and provenance-gate tests."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from data13_evidence_validation import (
    EvidenceError, extract_minimum, validate_record_url,
    vetted_overlay_by_pair, verify_observation,
)
from data13_directed_connectivity_model import load_data13

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"data13_directed_connectivity_2026_11.json"
MANIFEST=ROOT/"data"/"data13_evidence_manifest_2026_11.csv"


class Data13EvidenceVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=json.loads(DATA.read_text(encoding="utf-8"))["records"]

    def test_full_manifest_is_explicit_and_unverified_are_not_displayed(self):
        displayed, audit=vetted_overlay_by_pair(self.records,MANIFEST)
        self.assertEqual(audit["research_rows"],221)
        self.assertEqual(audit["verified_displayable"],39)
        self.assertEqual(audit["pending_source_review"],182)
        self.assertEqual(displayed[("aachen","lille")]["minimum_oneway_min"],134)
        self.assertNotIn(("haguenau","saverne"),displayed)
        actual=load_data13()
        self.assertEqual(len(actual["records"]),221)
        self.assertEqual(len(actual["by_pair"]),39)

    def test_all_record_urls_match_directional_canonical_ids(self):
        for row in self.records:
            with self.subTest(o=row["origin_id"],d=row["destination_id"]):
                validate_record_url(row)

    def test_alternative_aliases_and_timetable_path(self):
        a=next(r for r in self.records if (r["origin_id"],r["destination_id"])==("aachen","lille"))
        validate_record_url(a)
        b=next(r for r in self.records if (r["origin_id"],r["destination_id"])==("trier","luxembourg_city"))
        validate_record_url(b)
        c=next(r for r in self.records if (r["origin_id"],r["destination_id"])==("nancy","paris"))
        validate_record_url(c)

    def test_reverse_unrelated_and_unsafe_url_are_rejected(self):
        a=next(r for r in self.records if (r["origin_id"],r["destination_id"])==("aachen","lille"))
        for url in (
            "https://www.sncf-connect.com/train/trajet/lille/aix-la-chapelle",
            "https://www.sncf-connect.com/train/trajet/aix-la-chapelle/paris",
            "https://www.sncf-connect.com/help",
            "https://www.sncf-connect.com.evil.example/train/trajet/aix-la-chapelle/lille",
        ):
            with self.subTest(url=url),self.assertRaises(EvidenceError):
                validate_record_url({**a,"source_url":url})

    def test_html_static_sncf_only_shortest_and_mismatch(self):
        a=next(r for r in self.records if (r["origin_id"],r["destination_id"])==("aachen","lille"))
        html='<table><tr><td>Durée moyenne d’un trajet</td><td>2h24</td></tr><tr><td>Durée du trajet le plus court</td><td>2h14</td></tr></table>'
        self.assertEqual(extract_minimum(html,provider="sncf"),134)
        self.assertEqual(verify_observation(a,html),{"status":"verified","published_min":134})
        self.assertEqual(verify_observation({**a,"minimum_oneway_min":138},html),
                         {"status":"duration_mismatch","published_min":134})
        self.assertIsNone(extract_minimum('<p>Durée moyenne d’un trajet 2h24</p>',provider="sncf"))

    def test_html_static_trainline_average_is_not_minimum(self):
        html='<p>Average duration 50m</p><table><tr><td>Journey time</td><td>From 46m</td></tr></table>'
        self.assertEqual(extract_minimum(html,provider="trainline"),46)
        self.assertIsNone(extract_minimum('<p>Average duration 50m</p>',provider="trainline"))
        html2='<p>Journey time From 46m</p><p>Journey time From 1h15m</p>'
        self.assertIsNone(extract_minimum(html2,provider="trainline"))
        self.assertIsNone(extract_minimum('<script>Journey time From 1h15m</script>',provider="trainline"))

    def test_manifest_mismatch_does_not_silently_promote(self):
        changed=deepcopy(self.records)
        row=next(x for x in changed if (x["origin_id"],x["destination_id"])==("metz","colmar"))
        row["minimum_oneway_min"]+=1
        with self.assertRaises(EvidenceError):
            vetted_overlay_by_pair(changed,MANIFEST)

    def test_never_claims_2027_schedule_or_return(self):
        for record in self.records:
            self.assertEqual(record["direction"],"outbound_only")
            self.assertIs(record["return_2027_verified"],False)
            self.assertIs(record["valid_for_2027"],False)


if __name__=="__main__":
    unittest.main()
