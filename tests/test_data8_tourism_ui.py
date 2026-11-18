import copy
import unittest
from data8_tourism_ui import (
    parse_user_range, build_data8_card, destination_research_overview,
)

class Data8UIProjectionTests(unittest.TestCase):
    def test_aachen_card_preserves_provenance_and_unknown_future(self):
        c=build_data8_card("dq32_aachen_07")
        self.assertEqual(c["admission"]["state"],"free_general_entry")
        self.assertEqual(c["duration"]["state"],"editorial_estimate")
        self.assertEqual(c["local_walk"]["state"],"editorial_two_direction_range")
        self.assertFalse(c["actual_station_connection_verified"])
        self.assertFalse(c["valid_for_2027"])

    def test_missing_and_unreconciled_distinct(self):
        self.assertIsNone(build_data8_card("noncanonical_cologne"))
        cologne=destination_research_overview("cologne")
        self.assertEqual(cologne["researched_attractions"],0)
        self.assertEqual(len(cologne["unreconciled_candidates"]),1)
        self.assertIsNone(cologne["unreconciled_candidates"][0]["canonical_attraction_id"])
        self.assertFalse(cologne["trip_plan_mutated"])

    def test_editable_ranges_are_not_implicit_free_prices(self):
        self.assertIsNone(parse_user_range(""))
        a=parse_user_range("30-65")
        self.assertEqual((a["min_eur"],a["max_eur"]),(30,65))
        for raw in ("30","60-20","-1-2","abc","10.123-20","10-100001"):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                parse_user_range(raw)

    def test_research_card_is_read_only(self):
        from data8_priority_tourism_model import load_priority_lot
        from data8_local_access_model import load_access_dataset
        tourism=load_priority_lot()
        access=load_access_dataset(tourism=tourism)
        before=copy.deepcopy(tourism),copy.deepcopy(access)
        build_data8_card("strasbourg_cathedral",tourism=tourism,access=access)
        self.assertEqual((tourism,access),before)

if __name__=="__main__":
    unittest.main()
