import unittest
from finance_margin_metrics import calculate_excursion_margin,compare_excursion_profiles
class FinanceMarginTests(unittest.TestCase):
 def test_same_global_margin_different_excursion_balance(self):
  p={"budget_excursions_allowance_brl":5000,"result":{"margin":2000}}
  a=calculate_excursion_margin(p,{"EUR":100,"CHF":0},6,7,["local transport"])
  b=calculate_excursion_margin(p,{"EUR":300,"CHF":0},6,7,[])
  self.assertEqual(a["budget_margin_brl"],b["budget_margin_brl"])
  self.assertGreater(a["known_allowance_remaining_brl"],b["known_allowance_remaining_brl"])
  self.assertEqual(a["pending_count"],1)
  self.assertEqual(len(compare_excursion_profiles({"economy":a,"balanced":b})),2)
 def test_above_allowance_and_chf(self):
  p={"budget_excursions_allowance_brl":100,"result":{"margin":-30}}
  m=calculate_excursion_margin(p,{"EUR":10,"CHF":10},6,8,[])
  self.assertEqual(m["known_overage_brl"],40)
  self.assertEqual(m["known_allowance_remaining_brl"],0)
  self.assertEqual(m["budget_margin_brl"],-30)
 def test_invalid_values(self):
  p={"budget_excursions_allowance_brl":100,"result":{"margin":2}}
  for bad in (-1,float("nan")):
   with self.assertRaises(ValueError):
    calculate_excursion_margin(p,{"EUR":bad,"CHF":0},6,7,[])
 def test_zero_spend_is_not_guaranteed_savings(self):
  m=calculate_excursion_margin({"budget_excursions_allowance_brl":1200,"result":{"margin":200}},
                                {"EUR":0,"CHF":0},6,7,["unknown"])
  self.assertEqual(m["known_allowance_remaining_brl"],1200)
  self.assertIn("não é economia garantida",m["coverage_caveat"])
if __name__=="__main__":unittest.main()
