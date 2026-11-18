"""Rail transfers are a count and optionally source-backed connection legs."""
import unittest
from rail_transfer_contract import normalize_transfers, validate_transfer_chain
from datetime import datetime

CONNECTION = {
    "station_id": "brussels_midi",
    "arrival_at": "2026-11-21T09:00+01:00",
    "departure_at": "2026-11-21T09:15+01:00",
    "source_url": "https://www.belgiantrain.be/en/",
}

class TransferContractTests(unittest.TestCase):
    def test_legacy_int_count_is_not_detailed(self):
        a=normalize_transfers({"transfers":1})
        self.assertEqual(a["transfer_count"],1)
        self.assertFalse(a["transfer_details_complete"])
        with self.assertRaises(ValueError):
            normalize_transfers({"transfers":1},require_details=True)

    def test_legacy_list_and_canonical_list_are_equivalent(self):
        old=normalize_transfers({"transfers":[CONNECTION]},require_details=True)
        new=normalize_transfers({"transfer_count":1,"transfer_legs":[CONNECTION]},
                                require_details=True)
        self.assertEqual(old["transfer_legs"],new["transfer_legs"])
        self.assertTrue(old["transfer_details_complete"])

    def test_no_transfers_is_a_valid_rail_leg(self):
        self.assertTrue(normalize_transfers({"transfers":[]},
                                             require_details=True)["transfer_details_complete"])

    def test_transfer_conflicts_or_invalid_station_rejected(self):
        for data in ({"transfers":1,"transfer_count":2},
                     {"transfers":[CONNECTION],"transfer_count":2},
                     {"transfers":True}):
            with self.assertRaises(ValueError):
                normalize_transfers(data)
        before=datetime.fromisoformat("2026-11-21T08:00+01:00")
        after=datetime.fromisoformat("2026-11-21T10:00+01:00")
        transfer=normalize_transfers({"transfers":[CONNECTION]},require_details=True)
        self.assertTrue(validate_transfer_chain(
            transfer,departure=before,arrival=after,
            origin_station_id="lille_europe",
            destination_station_id="antwerp_centraal"))
        with self.assertRaises(ValueError):
            validate_transfer_chain(transfer,departure=before,arrival=after,
                                    origin_station_id="brussels_midi",
                                    destination_station_id="antwerp_centraal")

if __name__=="__main__":
    unittest.main()
