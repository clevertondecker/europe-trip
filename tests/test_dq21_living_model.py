import unittest
from dq21_living_model import compare_living_depth,brazil_to_europe_hours,load_living_evidence

class DQ21Living(unittest.TestCase):
    def test_dated_dst_change(self):
        a=brazil_to_europe_hours("2027-10-30",start_hour=9,end_hour=18)
        b=brazil_to_europe_hours("2027-10-31",start_hour=9,end_hour=18)
        self.assertEqual(a["europe_hours"],[14,23])
        self.assertEqual(b["europe_hours"],[13,22])
        self.assertEqual(a["offset_hours"],5)
        self.assertEqual(b["offset_hours"],4)

    def test_requires_explicit_dates_for_work_window(self):
        x=compare_living_depth()
        self.assertFalse(x["work_hours_selected"])
        self.assertEqual(len(x["cities"]),3)
        self.assertTrue(all(not c["work_scenarios"] for c in x["cities"]))
        with self.assertRaises(ValueError):compare_living_depth(brazil_hours=(9,18))
        with self.assertRaises(ValueError):brazil_to_europe_hours("2027-08-30",start_hour=9,end_hour=18)

    def test_freiburg_climate_secondary_not_fully_validated(self):
        r=next(c for c in compare_living_depth()["cities"] if c["city_id"]=="freiburg")
        climate=r["dimensions"]["clima_set_nov"]
        self.assertEqual(climate["months_9_10_11"]["9"]["tmean_c"],15.9)
        self.assertIsNone(climate["months_9_10_11"]["11"]["precip_mm"])
        self.assertFalse(climate["precipitation_verified"])
        self.assertIsNone(r["comparable_crime_rate"])
        self.assertIsNone(r["city_score"])

    def test_dated_scenario_no_coworking_guarantee(self):
        x=compare_living_depth(study_dates=("2027-09-15","2027-11-15"),brazil_hours=(9,18))
        for city in x["cities"]:
            self.assertEqual(len(city["work_scenarios"]),2)
            self.assertFalse(city["property_internet_confirmed"])
            self.assertFalse(city["work_scenarios"][0]["verified_coworking_open_at_shift_end"])

if __name__=="__main__":unittest.main()
