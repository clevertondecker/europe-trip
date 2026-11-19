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
        self.assertEqual(audit["research_rows"],319)
        self.assertEqual(audit["verified_displayable"],319)
        self.assertEqual(audit["pending_source_review"],0)
        self.assertEqual(displayed[("aachen","lille")]["minimum_oneway_min"],134)
        self.assertEqual(len(displayed),len(self.records))
        actual=load_data13()
        self.assertEqual(len(actual["records"]),319)
        self.assertEqual(len(actual["by_pair"]),319)

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

    def test_data14_aliases_and_source_minima(self):
        observed = {
            ("saint_louis","reims"):178,
            ("strasbourg","lausanne"):232,
            ("selestat","brussels"):264,
            ("saverne","mulhouse"):88,
            ("offenburg","brussels"):278,
            ("offenburg","liege"):251,
            ("offenburg","interlaken"):181,
            ("saint_louis","lausanne"):151,
            ("besancon","namur"):366,
            ("selestat","basel"):56,
            ("selestat","lille"):220,
            ("selestat","lyon"):227,
            ("belfort","lausanne"):229,
            ("arras","lausanne"):321,
        }
        for key,minutes in observed.items():
            with self.subTest(pair=key):
                row=next(r for r in self.records
                         if (r["origin_id"],r["destination_id"])==key)
                validate_record_url(row)
                self.assertEqual(row["minimum_oneway_min"],minutes)

    def test_data14_rejects_inverted_trainline_alias(self):
        row=next(r for r in self.records if
                 (r["origin_id"],r["destination_id"])==("offenburg","interlaken"))
        self.assertEqual(row["source_url"].split("/")[-1],
                         "offenburg-to-interlaken-ost")
        with self.assertRaises(EvidenceError):
            validate_record_url({
                **row,
                "source_url":"https://www.thetrainline.com/en/train-times/interlaken-ost-to-offenburg"
            })
        with self.assertRaises(EvidenceError):
            validate_record_url({
                **row,
                "source_url":"https://www.thetrainline.com/en/train-times/offenburg-to-lausanne"
            })

    def test_reconciled_data14_minima_and_manifest_match(self):
        import csv
        expected={
            ("saint_louis","reims"):178,
            ("strasbourg","lausanne"):232,
            ("selestat","brussels"):264,
            ("saverne","mulhouse"):88,
            ("selestat","lille"):220,
            ("arras","lausanne"):321,
        }
        with MANIFEST.open(newline="", encoding="utf-8") as file:
            index={(r["origin_id"],r["destination_id"]):r for r in csv.DictReader(file)}
        for key,minimum in expected.items():
            with self.subTest(pair=key):
                record=next(r for r in self.records
                            if (r["origin_id"],r["destination_id"])==key)
                self.assertEqual(record["minimum_oneway_min"],minimum)
                validate_record_url(record)
                manifest=index[key]
                self.assertEqual(manifest["verification_status"],"verified_minimum")
                self.assertEqual(manifest["source_url"],record["source_url"])
                self.assertEqual(int(manifest["minimum_dataset_min"]),minimum)
                self.assertEqual(int(manifest["published_min_rechecked"]),minimum)
                self.assertEqual(record["direction"],"outbound_only")
                self.assertFalse(record["valid_for_2027"])
                self.assertFalse(record["return_2027_verified"])

    def test_data14_batch2_all_70_rechecked_minima(self):
        import csv
        fixture = json.loads((ROOT/"tests"/"fixtures"/
                              "data14_batch2_2026_11_snc_minima.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(fixture),70)
        with MANIFEST.open(newline="",encoding="utf-8") as source:
            by_pair={(r["origin_id"],r["destination_id"]):r for r in csv.DictReader(source)}
        for x in fixture:
            key=x["origin_id"],x["destination_id"]
            with self.subTest(pair=key):
                row=next(r for r in self.records
                         if (r["origin_id"],r["destination_id"])==key)
                manifest=by_pair[key]
                self.assertEqual(row["minimum_oneway_min"],x["published_min"])
                self.assertEqual(row["source_url"],x["source_url"])
                self.assertEqual(manifest["source_url"],row["source_url"])
                self.assertEqual(int(manifest["minimum_dataset_min"]),x["published_min"])
                self.assertEqual(int(manifest["published_min_rechecked"]),x["published_min"])
                self.assertEqual(manifest["verification_status"],"verified_minimum")
                self.assertEqual(manifest["verification_checked_at"],"2026-11-18")
                self.assertIn("DATA14.2",manifest["brief_evidence"])
                validate_record_url(row)
                self.assertFalse(row["return_2027_verified"])
                self.assertFalse(row["valid_for_2027"])

    def test_data14_batch3_new_minima_are_source_reconciled(self):
        import csv
        fixture=json.loads((ROOT/"tests"/"fixtures"/
                           "data14_batch3_2026_11_official_minima.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(fixture),18)
        with MANIFEST.open(newline="",encoding="utf-8") as source:
            idx={(r["origin_id"],r["destination_id"]):r for r in csv.DictReader(source)}
        for x in fixture:
            key=x["origin_id"],x["destination_id"]
            with self.subTest(pair=key):
                record=next(r for r in self.records
                            if (r["origin_id"],r["destination_id"])==key)
                evidence=idx[key]
                self.assertEqual(record["minimum_oneway_min"],x["published_min"])
                self.assertEqual(record["source_url"],x["source_url"])
                self.assertEqual(evidence["source_url"],x["source_url"])
                self.assertEqual(evidence["verification_status"],"verified_minimum")
                self.assertEqual(int(evidence["published_min_rechecked"]),x["published_min"])
                self.assertIn("DATA14.3",evidence["brief_evidence"])
                validate_record_url(record)

    def test_data14_batch4_60_official_minima(self):
        import csv
        fixture=json.loads((ROOT/"tests"/"fixtures"/
                           "data14_batch4_2026_11_official_minima.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(fixture),60)
        with MANIFEST.open(newline="",encoding="utf-8") as source:
            by_pair={(m["origin_id"],m["destination_id"]):m for m in csv.DictReader(source)}
        for item in fixture:
            key=item["origin_id"],item["destination_id"]
            with self.subTest(pair=key):
                record=next(x for x in self.records
                            if (x["origin_id"],x["destination_id"])==key)
                manifest=by_pair[key]
                self.assertEqual(record["minimum_oneway_min"],item["published_min"])
                self.assertEqual(record["source_url"],item["source_url"])
                self.assertEqual(manifest["verification_status"],"verified_minimum")
                self.assertEqual(manifest["source_url"],record["source_url"])
                self.assertEqual(int(manifest["published_min_rechecked"]),item["published_min"])
                self.assertEqual(int(manifest["minimum_dataset_min"]),item["published_min"])
                self.assertIn("DATA14.4",manifest["brief_evidence"])
                validate_record_url(record)
                self.assertFalse(record["return_2027_verified"])
                self.assertFalse(record["valid_for_2027"])

    def test_data14_batch5_all_51_secondary_minima(self):
        import csv
        fixture=json.loads((ROOT/"tests"/"fixtures"/
                           "data14_batch5_2026_11_trainline_minima.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(fixture),51)
        with MANIFEST.open(newline="",encoding="utf-8") as source:
            index={(m["origin_id"],m["destination_id"]):m for m in csv.DictReader(source)}
        for item in fixture:
            key=item["origin_id"],item["destination_id"]
            with self.subTest(pair=key):
                r=next(rec for rec in self.records
                       if (rec["origin_id"],rec["destination_id"])==key)
                m=index[key]
                self.assertEqual(r["reference_kind"],"secondary_route_minimum")
                self.assertEqual(r["confidence"],"low")
                self.assertEqual(r["minimum_oneway_min"],item["published_min"])
                self.assertEqual(r["source_url"],item["source_url"])
                self.assertEqual(m["verification_status"],"verified_minimum")
                self.assertEqual(int(m["published_min_rechecked"]),item["published_min"])
                self.assertEqual(m["source_url"],r["source_url"])
                self.assertIn("DATA14.5",m["brief_evidence"])
                self.assertEqual(m["source_kind"],r["reference_kind"])
                validate_record_url(r)
                self.assertFalse(r["return_2027_verified"])
                self.assertFalse(r["valid_for_2027"])

    def test_data14_batch6_18_new_official_routes(self):
        import csv
        fixture=json.loads((ROOT/"tests"/"fixtures"/
                           "data14_batch6_2026_11_new_snc_minima.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(fixture),18)
        with MANIFEST.open(newline="",encoding="utf-8") as source:
            idx={(m["origin_id"],m["destination_id"]):m for m in csv.DictReader(source)}
        for item in fixture:
            key=item["origin_id"],item["destination_id"]
            with self.subTest(pair=key):
                row=next(x for x in self.records
                         if (x["origin_id"],x["destination_id"])==key)
                m=idx[key]
                self.assertEqual(row["source_url"],item["source_url"])
                self.assertEqual(row["minimum_oneway_min"],item["published_min"])
                self.assertEqual(row["reference_kind"],"official_operator_minimum")
                self.assertEqual(row["confidence"],"medium")
                self.assertEqual(m["verification_status"],"verified_minimum")
                self.assertEqual(int(m["published_min_rechecked"]),item["published_min"])
                self.assertEqual(m["source_url"],item["source_url"])
                self.assertIn("DATA14.6",m["brief_evidence"])
                validate_record_url(row)
                self.assertFalse(row["return_2027_verified"])
                self.assertFalse(row["valid_for_2027"])

    def test_data14_batch7_31_secondary_minima(self):
        import csv
        fixture=json.loads((ROOT/"tests"/"fixtures"/
                           "data14_batch7_2026_11_secondary_minima.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(len(fixture),31)
        with MANIFEST.open(newline="",encoding="utf-8") as source:
            evidence={(row["origin_id"],row["destination_id"]):row for row in csv.DictReader(source)}
        for item in fixture:
            key=item["origin_id"],item["destination_id"]
            with self.subTest(pair=key):
                r=next(x for x in self.records if
                       (x["origin_id"],x["destination_id"])==key)
                m=evidence[key]
                self.assertEqual(r["source_url"],item["source_url"])
                self.assertEqual(r["minimum_oneway_min"],item["published_min"])
                self.assertEqual(r["reference_kind"],"secondary_route_minimum")
                self.assertEqual(r["confidence"],"low")
                self.assertEqual(m["verification_status"],"verified_minimum")
                self.assertEqual(int(m["published_min_rechecked"]),item["published_min"])
                self.assertIn("DATA14.7",m["brief_evidence"])
                validate_record_url(r)
                self.assertFalse(r["valid_for_2027"])
                self.assertFalse(r["return_2027_verified"])

    def test_data14_interlaken_ost_not_generic_destination(self):
        from rail_reference_projection_model import decorate_comparison
        row={"base_id":"besancon","destination_id":"interlaken",
             "evidence_status":"not_researched","minimum_oneway_min":None,
             "source_url":None,"divergent_sources":False}
        c=decorate_comparison({"rows":[row]})["cells"][("besancon","interlaken")]
        if c["data13_connectivity_applied"]:
            self.assertEqual(c["arrival_station"],"Interlaken Ost")
            self.assertIn("Interlaken Ost",c["station_caveat"])
            self.assertEqual(c["station_comparability"],"station_named_in_route_page")
        self.assertFalse(c["weekend_return_known"])
        self.assertFalse(c["valid_for_2027"])

    def test_never_claims_2027_schedule_or_return(self):
        for record in self.records:
            self.assertEqual(record["direction"],"outbound_only")
            self.assertIs(record["return_2027_verified"],False)
            self.assertIs(record["valid_for_2027"],False)


if __name__=="__main__":
    unittest.main()
