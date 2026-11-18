import copy
import unittest
from data8_attraction_evidence_model import (
    validate_entry, validate_dataset, coverage_report, card_projection,
)

DEMO = {
    "attraction_id":"dq32_aachen_07", "destination_id":"aachen",
    "valid_for_2027":False,
    "experience":{"why_visit":"Patrimônio medieval e história carolíngia",
        "source_url":"https://www.aachenerdom.de/en/",
        "checked_at":"2026-11-18"},
    "duration":{"state":"editorial_estimate","min_minutes":35,
        "max_minutes":75,"method":"estimativa editorial de visita, não bilhete"},
    "admission":{"state":"free_general_entry","amount":0,"currency":"EUR",
        "unit":"person","source_url":"https://www.aachenerdom.de/en/a-place-to-visit/faqs/",
        "checked_at":"2026-11-18","valid_for_2027":False},
    "opening":{"state":"unknown","rule":None,"valid_for_2027":False},
    "seasonality":{"state":"unknown","note":None},
    "location":{"state":"unknown","address":None},
}
DISCOVERY={"destinations":[{"id":"aachen","attractions":[{"id":"dq32_aachen_07"}]}]}

class DATA8ContractTests(unittest.TestCase):
    def test_valid_projection_does_not_mutate(self):
        doc={"schema_version":1,"scope":"tourism_planning_overlay",
             "checked_at":"2026-11-18","entries":[DEMO]}
        before=copy.deepcopy(doc)
        value=validate_dataset(doc,discovery=DISCOVERY)
        self.assertEqual(coverage_report(value)["general_entry_known"],1)
        self.assertEqual(coverage_report(value)["general_hours_documented"],0)
        projection=card_projection({"id":"dq32_aachen_07","name":"Canon"},research=value)
        self.assertEqual(projection["name"],"Canon")
        self.assertEqual(doc,before)
        self.assertFalse(value["mutates_catalog"])

    def test_negative_identity_and_duplicate(self):
        doc={"schema_version":1,"scope":"tourism_planning_overlay",
             "checked_at":"2026-11-18","entries":[DEMO,copy.deepcopy(DEMO)]}
        with self.assertRaises(ValueError):
            validate_dataset(doc,discovery=DISCOVERY)
        with self.assertRaises(ValueError):
            validate_entry({**DEMO,"attraction_id":"fabricated"},identity_map={"dq32_aachen_07":"aachen"})

    def test_no_free_from_unknown_and_no_2027_promise(self):
        for bad in (
            {**DEMO,"admission":{**DEMO["admission"],"state":"unknown"}},
            {**DEMO,"admission":{**DEMO["admission"],"amount":12}},
            {**DEMO,"opening":{**DEMO["opening"],"valid_for_2027":True}},
            {**DEMO,"duration":{**DEMO["duration"],"min_minutes":0}},
            {**DEMO,"travel_time_from_station":8},
            {**DEMO,"experience":{**DEMO["experience"],"source_url":"http://example.org"}},
        ):
            with self.subTest(case=bad),self.assertRaises(ValueError):
                validate_entry(bad,identity_map={"dq32_aachen_07":"aachen"})

    def test_unreconciled_candidates_keep_null_canonical_id(self):
        doc={"schema_version":1,"scope":"tourism_planning_overlay",
             "checked_at":"2026-11-18","entries":[],
             "unreconciled_candidates":[{"destination_id":"cologne","name":"Dom",
                "canonical_attraction_id":None,"source_url":"https://www.koelntourismus.de/en/"}]}
        validated=validate_dataset(doc,discovery=DISCOVERY)
        self.assertEqual(len(validated["unreconciled_candidates"]),1)
        doc["unreconciled_candidates"][0]["canonical_attraction_id"]="fabricated"
        with self.assertRaises(ValueError):
            validate_dataset(doc,discovery=DISCOVERY)

if __name__=="__main__":
    unittest.main()
