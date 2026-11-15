import unittest
from copy import deepcopy
from attractions_model import load_attractions,load_base_routes
from trip_plan_model import new_plan
from draft_plan_store import export_draft,import_draft,get_draft,save_draft,list_drafts
from calendar_visit_model import legacy_to_visits,validate_repeat_visits,intercity_trip_count,travel_fares_by_visit
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
class VisitsTests(unittest.TestCase):
 def test_two_explicit_visits_count_twice_and_one_visit_only_once(self):
  plan=new_plan();routes=load_base_routes();catalog=load_attractions()
  visits=[{"visit_id":"v1","date":"2027-09-25","destination_id":"colmar",
           "attraction_ids":["colmar_venise","colmar_tanners"]},
          {"visit_id":"v2","date":"2027-09-26","destination_id":"colmar",
           "attraction_ids":["colmar_venise"]}]
  result=validate_repeat_visits(plan,visits,catalog)
  self.assertEqual(intercity_trip_count(result,"mulhouse")["colmar"],2)
  fare=travel_fares_by_visit(result,routes,"mulhouse")
  one=travel_fares_by_visit(result[:1],routes,"mulhouse")
  self.assertEqual(fare["known_eur"],2*one["known_eur"])
 def test_remote_work_day_rejected(self):
  with self.assertRaises(ValueError):
   validate_repeat_visits(new_plan(),[{"visit_id":"v","date":"2027-10-05",
                       "destination_id":"colmar","attraction_ids":["colmar_venise"]}])
if __name__=="__main__":unittest.main()
