import unittest
from copy import deepcopy
from pathlib import Path
import json
from tools.validate_research_data import validate_research_contracts, verify_snapshot_baseline


DATA=Path(__file__).resolve().parents[1]/"data"
class ResearchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=[
            json.loads((DATA/name).read_text(encoding="utf-8"))
            for name in ("attractions_2027.json",
                         "dq32_macro_tourism_2026_11.json",
                         "base_city_research_expanded_2026_11.json",
                         "exploration_bases_2027.json")]
    def test_current_snapshot(self):
        result=validate_research_contracts(*deepcopy(self.payload))
        self.assertEqual(result["bases"],30)
        self.assertEqual(result["canonical_attractions"],65)
        self.assertEqual(result["dq32_source_records"],30)
        self.assertEqual(result["dq32_cities"],23)
    def test_duplicate_identity_is_rejected(self):
        data=deepcopy(self.payload)
        data[1]["attractions"].append(deepcopy(data[1]["attractions"][0]))
        with self.assertRaises(ValueError):
            validate_research_contracts(*data)
    def test_unverified_return_cannot_be_promoted(self):
        data=deepcopy(self.payload)
        data[3]["routes"][0]["return_verified_2027"]=True
        with self.assertRaises(ValueError):
            validate_research_contracts(*data)
    def test_fractional_train_duration_is_rejected(self):
        data=deepcopy(self.payload)
        data[3]["routes"][0]["train_minutes_oneway_min"]=48.5
        with self.assertRaises(ValueError):
            validate_research_contracts(*data)

    def test_legitimate_expansion_is_structurally_valid_but_needs_baseline_review(self):
        data=deepcopy(self.payload)
        data[0]["destinations"].append({
            "id":"new_future_city","name":"New Future City","country":"França"})
        data[0]["attractions"].append({
            "id":"new_future_attraction","destination_id":"new_future_city",
            "name":"Test attraction","source_urls":["https://example.org/documented"]})
        observed=validate_research_contracts(*data)
        self.assertEqual(observed["canonical_destinations"],15)
        self.assertEqual(observed["canonical_attractions"],66)
        baseline={"expected_counts":{
            "bases":30,"canonical_destinations":14,"canonical_attractions":65,
            "dq32_source_records":30,"dq32_cities":23,
            "historical_exploration_routes":34}}
        with self.assertRaises(ValueError):
            verify_snapshot_baseline(observed,baseline)
        reviewed=deepcopy(baseline)
        reviewed["expected_counts"].update(observed)
        verify_snapshot_baseline(observed,reviewed)

    def test_wrong_city_for_semantic_alias_is_rejected(self):
        data=deepcopy(self.payload)
        data[1]["attractions"][0]["canonical_attraction_id"]="lux_bock"
        with self.assertRaises(ValueError):
            validate_research_contracts(*data)
