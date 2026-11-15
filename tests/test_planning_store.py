"""UX status, pure plan actions and legacy migration regression coverage."""
import unittest
from copy import deepcopy
from planning_store import (create_from_legacy,change_plan,set_package,remove_package,
                            add_assignment,remove_assignment,summary,is_dirty,sync_legacy_view)
from planning_status import save_label,explain_storage_error
from trip_plan_model import new_plan

class PlanningStoreTests(unittest.TestCase):
    def test_import_legacy_and_revisions(self):
        old={"explore_packages":{"colmar":["colmar_venise"]},
             "explore_calendar":{"2027-09-24":"colmar"},"explore_base":"strasbourg"}
        p=create_from_legacy(old)
        self.assertEqual(p["packages"],old["explore_packages"])
        self.assertEqual(p["assignments"],old["explore_calendar"])
        self.assertEqual(p["base_city"],"strasbourg")
        self.assertEqual(p["revision"],0)
        rev=change_plan(p,{"profile":"economy"})
        self.assertEqual(rev["revision"],1)
        self.assertEqual(change_plan(rev,{"profile":"economy"}),rev)
    def test_package_and_schedule_share_one_plan(self):
        p=new_plan()
        p=set_package(p,"colmar",["colmar_venise"])
        p=add_assignment(p,"2027-09-24","colmar")
        self.assertEqual(summary(p)["attractions"],1)
        self.assertEqual(summary(p)["scheduled_days"],1)
        legacy={}
        sync_legacy_view(p,legacy)
        self.assertEqual(legacy["explore_packages"],p["packages"])
        self.assertEqual(legacy["explore_calendar"],p["assignments"])
        legacy["explore_packages"]["colmar"].append("irrelevant")
        self.assertNotIn("irrelevant",p["packages"]["colmar"])
        p=remove_package(p,"colmar")
        self.assertEqual(p["assignments"],{})
        self.assertEqual(p["packages"],{})
    def test_no_repeated_revision(self):
        p=new_plan()
        changed=set_package(p,"colmar",["colmar_venise"])
        same=set_package(changed,"colmar",["colmar_venise"])
        self.assertEqual(changed,same)
        self.assertEqual(remove_assignment(same,"2027-09-24"),same)
    def test_no_silent_save_confirmation(self):
        p=new_plan()
        self.assertTrue(is_dirty(p,None))
        status,_=save_label(p,None,True)
        self.assertEqual(status,"Ainda não salvo")
        self.assertEqual(save_label(p,deepcopy(p),True)[0],"Planejamento salvo")
        changed=change_plan(p,{"base_city":"nancy"})
        self.assertEqual(save_label(changed,p,True)[0],"Alterações não salvas")
        self.assertEqual(save_label(p,p,False)[0],"Backup disponível")
    def test_missing_authorization_is_human_readable(self):
        from urllib.error import HTTPError
        message=explain_storage_error(HTTPError("https://github.com",403,"Forbidden",None,None))
        self.assertIn("acesso",message)
        self.assertNotIn("403",message)

if __name__=="__main__":unittest.main()
