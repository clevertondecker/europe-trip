from pathlib import Path
import unittest
from data_model import load_data, calculate_scenario, get_scenario, select_places

class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_data()

    def test_core_constraints(self):
        self.assertEqual(self.data['wedding_date'], '2027-09-04')
        self.assertEqual(self.data['travelers'], 2)
        self.assertEqual(self.data['duration_min_days'], 65)

    def test_budget_70k(self):
        s=get_scenario(self.data,'70k')
        d=calculate_scenario(s)
        self.assertEqual(d['total'],69683)
        self.assertEqual(d['balance'],317)
        self.assertEqual(d['component_sum'],69683)

    def test_budget_60k_rounding(self):
        s=get_scenario(self.data,'60k')
        d=calculate_scenario(s)
        self.assertEqual(d['rounding_difference'],1)
        self.assertEqual(d['balance'],25)

    def test_rent_simulation_does_not_mutate_base(self):
        s=get_scenario(self.data,'70k')
        res=calculate_scenario(s,200,2,6.3)
        self.assertEqual(res['delta'],2520)
        self.assertEqual(res['balance'],-2203)
        self.assertEqual(s['reported_total_brl'],69683)

    def test_map_filter(self):
        options=select_places(self.data['places'],['França'],['candidata'])
        self.assertTrue(all(x['country']=='França' and x['status']=='candidata' for x in options))
        self.assertGreaterEqual(len(options),4)

    def test_geo(self):
        for place in self.data['places']:
            self.assertTrue(-90<=place['lat']<=90)
            self.assertTrue(-180<=place['lon']<=180)

if __name__=='__main__':
    unittest.main()