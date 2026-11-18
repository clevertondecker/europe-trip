import copy
import json
import tempfile
from pathlib import Path
import unittest

from routes7_reference_model import load_route_references, planning_reference, DATA
from evidence_query_model import get_rail_evidence

class Route7OverlayTests(unittest.TestCase):
    def test_exactly_fifteen_pairs_and_nine_previously_missing(self):
        refs=load_route_references()
        self.assertEqual(len(refs["records"]),15)
        self.assertEqual(len(refs["by_pair"]),15)
        missing=[("mulhouse","belfort"),("strasbourg","belfort"),("lille","belfort"),
                 ("mulhouse","haguenau"),("strasbourg","haguenau"),("lille","haguenau"),
                 ("lille","mulhouse"),("mulhouse","ghent"),("strasbourg","ghent")]
        for b,d in missing:
            result=planning_reference(b,d,references=refs)
            self.assertEqual(result["status"],"published_reference")
            self.assertGreater(result["fastest_min"],0)
            self.assertEqual(result["display_basis"],"published_fastest_reference")
        local=planning_reference("mulhouse","mulhouse",references=refs)
        self.assertIsNone(local["display_min"])

    def test_legacy_is_not_overridden(self):
        old=get_rail_evidence("lille","ghent")
        result=planning_reference("lille","ghent",legacy=old)
        self.assertEqual(result["legacy_min"],old["minimum_oneway_min"])
        self.assertEqual(result["display_min"],old["minimum_oneway_min"])
        self.assertEqual(result["fastest_min"],68)
        self.assertEqual(result["average_min"],76)
        self.assertFalse(result["weekend_return_known"])

    def test_no_typical_or_fare_from_fastest(self):
        x=planning_reference("mulhouse","belfort")
        self.assertIsNone(x["average_min"])
        self.assertFalse(x["typical_time_known"])
        for row in load_route_references()["records"]:
            self.assertIsNone(row["fare_for_two_eur"])
            self.assertIsNone(row["transfer_count"])

    def test_reject_duplicate_missing_bad_url_and_fabricated_return(self):
        fixture=json.loads(DATA.read_text(encoding="utf-8"))
        edits=[]
        v=copy.deepcopy(fixture);v["records"].append(v["records"][0]);edits.append(v)
        v=copy.deepcopy(fixture);v["records"].pop();edits.append(v)
        v=copy.deepcopy(fixture);v["records"][0]["source_url"]="http://example.com";edits.append(v)
        v=copy.deepcopy(fixture);v["records"][0]["weekend_return_status"]="verified_2027";edits.append(v)
        v=copy.deepcopy(fixture);v["records"][0]["average_min"]=1;edits.append(v)
        with tempfile.TemporaryDirectory() as p:
            path=Path(p)/"test.json"
            for v in edits:
                path.write_text(json.dumps(v),encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_route_references(path)

if __name__=="__main__":
    unittest.main()
