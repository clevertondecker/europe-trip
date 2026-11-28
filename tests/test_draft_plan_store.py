import unittest
from copy import deepcopy
from attractions_model import load_attractions
from trip_plan_model import new_plan
from draft_plan_store import export_draft,import_draft,get_draft,save_draft,list_drafts
class DraftTests(unittest.TestCase):
 def setUp(self):
  self.plan=new_plan()
  self.catalog=load_attractions()
  self.board={"plan_id":self.plan["plan_id"],"profile":"balanced",
              "base_revision":0,"base_city":"mulhouse",
              "packages":{"colmar":["colmar_venise"]}}
 def test_export_restore_and_isolation(self):
  stored=import_draft(export_draft(self.board),self.plan,self.catalog)
  self.assertEqual(stored["packages"],self.board["packages"])
  repo={};save_draft(repo,stored)
  retrieved=get_draft(repo,self.plan["plan_id"],"balanced")
  retrieved["packages"].clear()
  self.assertTrue(get_draft(repo,self.plan["plan_id"],"balanced")["packages"])
  self.assertEqual(list_drafts(repo,self.plan["plan_id"]),["balanced"])
 def test_stale_refused(self):
  changed=deepcopy(self.plan);changed["revision"]+=1
  with self.assertRaises(ValueError):import_draft(export_draft(self.board),changed,self.catalog)
 def test_no_official_removal(self):
  self.plan["packages"]={"colmar":["colmar_venise"]}
  with self.assertRaises(ValueError):import_draft(export_draft(self.board).replace("colmar_venise","colmar_tanners"),self.plan,self.catalog)
if __name__=="__main__":unittest.main()
