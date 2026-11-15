import unittest
from copy import deepcopy
from attractions_model import load_attractions
from outing_cost_evidence import load_outing_evidence,evidence_for_outing,validate_evidence
class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=load_attractions();cls.data=load_outing_evidence(catalog=cls.catalog)
 def test_all_destinations_have_pending_cost_categories(self):
  for dest in self.catalog["destinations"]:
   rows=evidence_for_outing(dest["id"],[],self.data)
   self.assertEqual(len(rows["pending"]),4)
   self.assertEqual(sum(rows["known_by_currency"].values()),0)
   self.assertTrue(all(x["amount"] is None for x in rows["pending"]))
 def test_unverified_fake_price_rejected(self):
  data=deepcopy(self.data)
  data["items"][0]["amount"]=42
  with self.assertRaises(ValueError):validate_evidence(data,self.catalog)
 def test_source_required_for_verified_price(self):
  data=deepcopy(self.data)
  data["items"][0].update(amount=10,status="historical_observed")
  with self.assertRaises(ValueError):validate_evidence(data,self.catalog)
 def test_unknown_destination_rejected(self):
  data=deepcopy(self.data);data["items"][0]["destination_id"]="nonexistent"
  with self.assertRaises(ValueError):validate_evidence(data,self.catalog)
if __name__=="__main__":unittest.main()
