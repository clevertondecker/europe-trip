"""Quality-of-evidence safeguards for 3×5 pilot and grouped outings."""
import unittest
from dq20_weekend_routes_model import (
    BASES,DESTINATIONS,STATUSES,load_pilot,route_matrix,combined_brussels_bruges,
    illustrative_weekends,classify_feasibility
)

class DQ20RailPilotTests(unittest.TestCase):
    def test_exact_same_basket_for_three_bases(self):
        rows=route_matrix()
        self.assertEqual(len(rows),15)
        for base in BASES:
            self.assertEqual([r["destination_id"] for r in rows if r["base_id"]==base],list(DESTINATIONS))
        self.assertTrue(all(not r["weekend_return_verified"] for r in rows))
        self.assertTrue(all(r["fare_eur_person_oneway"] is None for r in rows))
        self.assertTrue(all(r["door_to_door_min"] is None for r in rows))

    def test_missing_is_not_zero_or_impossible(self):
        rows=route_matrix()
        lack=next(r for r in rows if r["base_id"]=="freiburg" and r["destination_id"]=="bruges_be")
        self.assertIsNone(lack["station_to_station_fastest_min"])
        self.assertEqual(lack["feasibility"],"dados_insuficientes")
        self.assertFalse(any(r["feasibility"]=="bate_volta_comprovado" for r in rows))

    def test_canonical_and_supplemental_provenance_kept(self):
        rows=route_matrix()
        a=next(r for r in rows if r["base_id"]=="strasbourg" and r["destination_id"]=="brussels")
        self.assertGreaterEqual(len(a["source_records"]),2)
        self.assertEqual(a["representative_min"],246)
        self.assertIn(a["feasibility"],STATUSES)
        b=next(r for r in rows if r["base_id"]=="freiburg" and r["destination_id"]=="interlaken")
        self.assertEqual(b["station_to_station_fastest_min"],167)
        self.assertEqual(b["feasibility"],"dados_insuficientes")

    def test_requires_out_and_back_to_certify(self):
        self.assertEqual(classify_feasibility(oneway_min=90,weekend_outbound=True),
                         "dados_insuficientes")
        self.assertEqual(classify_feasibility(oneway_min=90,weekend_outbound=True,
                         weekend_return=True,visit_hours=5),"bate_volta_comprovado")
        self.assertEqual(classify_feasibility(oneway_min=280),
                         "viagem_longa_ou_exigente_indicativa")
        with self.assertRaises(ValueError):
            classify_feasibility(oneway_min=0)

    def test_brussels_bruges_is_only_a_verified_segment(self):
        x=combined_brussels_bruges()
        self.assertEqual(x["between_cities_min"],64)
        self.assertTrue(x["between_cities_verified_on_weekends"])
        self.assertFalse(x["full_weekend_verified_from_base"])

    def test_weekends_include_rest_and_no_fake_total(self):
        for count in (8,9):
            weeks=illustrative_weekends(count)
            self.assertEqual(len(weeks),count)
            self.assertTrue(any(x["status"]=="descanso" for x in weeks))
            self.assertEqual(set(sum((x["destinations"] for x in weeks),[])),set(DESTINATIONS))
            self.assertTrue(all(w["travel_total_minutes"] is None for w in weeks))

if __name__=="__main__":
    unittest.main()
