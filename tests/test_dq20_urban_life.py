"""Comparable factual life profiles, without invented safety/rental claims."""
import unittest
from copy import deepcopy
from dq20_urban_life_model import compare_urban_life,load_urban_delta,BASES,DIMENSIONS

class UrbanEvidenceTests(unittest.TestCase):
    def test_three_cities_same_dimensions(self):
        a=compare_urban_life()
        self.assertEqual([x["city_id"] for x in a["cities"]],list(BASES))
        self.assertTrue(all(tuple(x["dimensions"])==DIMENSIONS for x in a["cities"]))
        self.assertTrue(all(x["quality_score"] is None for x in a["cities"]))
        self.assertFalse(a["score_allowed"])

    def test_real_night_transport_sources_not_rental_access(self):
        a=compare_urban_life()
        for city in a["cities"]:
            transport=city["dimensions"]["mobilidade_sem_carro"]
            self.assertTrue(transport["source_url"].startswith("https://"))
            self.assertFalse(transport["late_access_to_actual_rental_verified"])

    def test_freiburg_coworking_and_missing_climate(self):
        a=compare_urban_life()
        freiburg=next(x for x in a["cities"] if x["city_id"]=="freiburg")
        self.assertIsNone(freiburg["dimensions"]["clima_set_nov"]["months_9_10_11"])
        self.assertTrue(freiburg["dimensions"]["trabalho_remoto"]["coworking_reference"]["source_url"].startswith("https://"))

    def test_brazil_hours_only_when_explicitly_requested(self):
        a=compare_urban_life()
        self.assertIsNone(a["cities"][0]["dimensions"]["trabalho_remoto"]["work_window"])
        b=compare_urban_life(brazil_work_window=(9,18))
        self.assertEqual(b["cities"][0]["dimensions"]["trabalho_remoto"]["work_window"]["europe_summer_hours"],[14,23])
        self.assertEqual(b["cities"][0]["dimensions"]["trabalho_remoto"]["work_window"]["europe_winter_hours"],[13,22])

    def test_no_invention_of_safety_statistics(self):
        a=compare_urban_life()
        self.assertTrue(all(x["dimensions"]["seguranca_comprovada"]["comparable_official_rate"] is None for x in a["cities"]))

if __name__=="__main__":
    unittest.main()
