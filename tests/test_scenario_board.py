"""Draft board: reactive repricing, no double fare, undo and explicit approval."""
import unittest
from copy import deepcopy
from attractions_model import load_attractions,load_base_routes
from data_model import load_data
from trip_plan_model import new_plan
from scenario_editor_model import (new_board,change_board,undo_board,
                                   reprice_board,cost_details,is_stale,board_to_approval)
from travel_profile_scenarios import build_profile_scenarios
from recommended_itineraries import approve_profile_scenario

class ScenarioBoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.routes=load_base_routes()
        cls.data=load_data()
    def board(self):
        plan=new_plan(base="mulhouse")
        options=build_profile_scenarios(plan,self.catalog,self.routes,self.data,False,6.35,7.1)
        return plan,new_board(plan,options[1])
    def test_draft_adding_and_removing_does_not_change_official(self):
        plan,board=self.board()
        snapshot=deepcopy(plan)
        dest=next(d["id"] for d in self.catalog["destinations"] if d["id"] not in board["packages"])
        a=next(a["id"] for a in self.catalog["attractions"] if a["destination_id"]==dest)
        changed=change_board(board,self.catalog,dest,[a])
        self.assertIn(dest,changed["packages"])
        changed=change_board(changed,self.catalog,dest,[])
        self.assertNotIn(dest,changed["packages"])
        self.assertEqual(plan,snapshot)
        restored=undo_board(changed)
        self.assertIn(dest,restored["packages"])
    def test_rail_ticket_is_once_for_multiple_attractions(self):
        plan,board=self.board()
        board["packages"]={"colmar":["colmar_venise"]}
        one=cost_details(board,self.catalog,self.routes)
        board["packages"]["colmar"].append("colmar_tanners")
        two=cost_details(board,self.catalog,self.routes)
        self.assertEqual(one["total"]["known_by_currency"],two["total"]["known_by_currency"])
        self.assertEqual(sum("Transporte" in x["name"] for x in two["rows"][0]["components"]),1)
    def test_finance_reprices_after_remove_without_fake_savings(self):
        plan,board=self.board()
        before=reprice_board(board,plan,self.catalog,self.routes,self.data,False,6.35,7.1)
        target=next(iter(board["packages"]))
        removed=change_board(board,self.catalog,target,[])
        after=reprice_board(removed,plan,self.catalog,self.routes,self.data,False,6.35,7.1)
        self.assertNotEqual(after["detail"]["total"]["selected_count"],
                            before["detail"]["total"]["selected_count"])
        self.assertLessEqual(after["finance"]["known_billets_brl"],
                             before["finance"]["known_billets_brl"])
        self.assertTrue(after["changed"])
        self.assertEqual(after["known_delta"]["EUR"],
                         round(after["detail"]["total"]["known_by_currency"]["EUR"]-
                               before["detail"]["total"]["known_by_currency"]["EUR"],2))
    def test_official_destinations_are_locked(self):
        plan=new_plan()
        plan["packages"]={"colmar":["colmar_venise"]}
        option=build_profile_scenarios(plan,self.catalog,self.routes,self.data,
                                      False,6.35,7.1)[1]
        board=new_board(plan,option)
        with self.assertRaises(ValueError):
            change_board(board,self.catalog,"colmar",[])
        self.assertEqual(plan["packages"],{"colmar":["colmar_venise"]})
    def test_approval_requires_fresh_revision_and_click(self):
        plan,board=self.board()
        simulation=reprice_board(board,plan,self.catalog,self.routes,self.data,False,6.35,7.1)
        proposal=board_to_approval(board,plan,simulation)
        self.assertEqual(approve_profile_scenario(plan,proposal,approved=False),plan)
        accepted=approve_profile_scenario(plan,proposal,approved=True)
        self.assertEqual(accepted["packages"],board["packages"])
        self.assertEqual(plan["packages"],{})
        with self.assertRaises(ValueError):board_to_approval(board,accepted,simulation)
    def test_distinct_board_per_style_and_no_unpriced_as_zero(self):
        plan,board=self.board()
        price=cost_details(board,self.catalog,self.routes)
        self.assertIsInstance(price["total"]["missing"],list)
        self.assertIn("EUR",price["total"]["known_by_currency"])
        self.assertIn("CHF",price["total"]["known_by_currency"])
        self.assertFalse(is_stale(board,plan))
        changed=deepcopy(plan);changed["revision"]+=1
        self.assertTrue(is_stale(board,changed))

if __name__=="__main__":unittest.main()
