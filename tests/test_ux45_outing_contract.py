"""UX 4.5: unified confirmed outing changes and reversible navigation."""
import unittest
from copy import deepcopy
from attractions_model import load_attractions
from itinerary_flow_model import UNASSIGNED,ITALY_STAGE,FRANCE_STAGE,selected_rows
from planning_store import add_assignment
from trip_plan_model import new_plan
from ux45_outing_contract import preview_outing,apply_outing,remove_outing
from ux45_navigation_context import handoff,return_to_origin

class SharedOutingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.colmar=[a["id"] for a in cls.catalog["attractions"]
                    if a["destination_id"]=="colmar"]
        cls.luxembourg=[a["id"] for a in cls.catalog["attractions"]
                        if a["destination_id"]=="luxembourg"]

    def test_preview_never_mutates_and_requires_confirmation(self):
        plan=new_plan()
        original=deepcopy(plan)
        draft=preview_outing(plan,self.catalog,"colmar",self.colmar[:2])
        self.assertEqual(draft["action"],"add")
        self.assertTrue(draft["requires_confirmation"])
        self.assertEqual(plan,original)
        with self.assertRaisesRegex(ValueError,"Confirme"):
            apply_outing(plan,self.catalog,"colmar",self.colmar[:2])
        self.assertEqual(plan,original)

    def test_add_only_once_and_update_preserves_period_and_date(self):
        original=new_plan()
        added,one=apply_outing(original,self.catalog,"colmar",self.colmar[:2],
                               confirmed=True)
        self.assertEqual(one.action,"added")
        self.assertIn("colmar",added["packages"])
        self.assertEqual(len(added["flexible_visits"]),1)
        self.assertEqual(added["assignments"],{})
        updated,two=apply_outing(added,self.catalog,"colmar",self.colmar[:2],
                                 "Férias restantes",confirmed=True)
        dated=add_assignment(updated,"2027-10-02","colmar")
        changed,three=apply_outing(dated,self.catalog,"colmar",self.colmar[1:3],
                                    confirmed=True)
        self.assertEqual(three.action,"updated")
        self.assertEqual(changed["flexible_visits"][0]["period"],"Férias restantes")
        self.assertEqual(changed["assignments"]["2027-10-02"],"colmar")
        self.assertEqual(changed["packages"]["colmar"],self.colmar[1:3])
        self.assertEqual(len(changed["packages"]),1)
        unchanged,four=apply_outing(changed,self.catalog,"colmar",self.colmar[1:3],
                                    confirmed=True)
        self.assertEqual(unchanged["revision"],changed["revision"])

    def test_remove_requires_explicit_confirmation_and_removes_dates(self):
        plan=new_plan()
        plan,_=apply_outing(plan,self.catalog,"colmar",self.colmar[:1],confirmed=True)
        plan=add_assignment(plan,"2027-10-02","colmar")
        with self.assertRaisesRegex(ValueError,"Confirme"):
            remove_outing(plan,self.catalog,"colmar")
        after,result=remove_outing(plan,self.catalog,"colmar",confirmed=True)
        self.assertEqual(result.action,"removed")
        self.assertNotIn("colmar",after["packages"])
        self.assertFalse(after["assignments"])
        self.assertFalse(after["flexible_visits"])
        self.assertEqual(plan["assignments"],{"2027-10-02":"colmar"})

    def test_two_destinations_and_italy_are_independent(self):
        plan=new_plan()
        plan,_=apply_outing(plan,self.catalog,"colmar",self.colmar[:1],confirmed=True)
        plan,_=apply_outing(plan,self.catalog,"luxembourg",self.luxembourg[:1],
                            confirmed=True)
        plan,_=apply_outing(plan,self.catalog,"italy_rome",["italy_rome__1"],
                            "Durante Roma",confirmed=True)
        self.assertEqual(set(plan["packages"]),{"colmar","luxembourg"})
        italian=[r for r in selected_rows(plan,self.catalog) if r["stage"]==ITALY_STAGE]
        self.assertEqual(len(italian),1)
        self.assertEqual(italian[0]["id"],"italy_rome")

    def test_rejects_invalid_and_duplicate_attractions(self):
        plan=new_plan()
        # UX 6.2: a city can be planned before selecting any attraction.
        empty,result=apply_outing(plan,self.catalog,"colmar",[],confirmed=True)
        self.assertEqual(result.attraction_count,0)
        self.assertNotIn("colmar",empty["packages"])
        with self.assertRaises(ValueError):
            apply_outing(plan,self.catalog,"colmar",["italy_rome__1"],confirmed=True)
        with self.assertRaises(ValueError):
            apply_outing(plan,self.catalog,"colmar",[self.colmar[0]]*2,confirmed=True)

class HandoffTests(unittest.TestCase):
    def test_explore_to_editor_and_back_with_filters(self):
        original={"ux_area":"Explorar","ux_section":"Passeios",
                  "explore_countries":["França","Bélgica"],
                  "scenario_base_selected":"mulhouse","explore_max_minutes":120,
                  "explore_route_filter":"Todos","ux_mode":"Oficial",
                  "flow_active_stage":"Itália"}
        state=deepcopy(original)
        handoff(state,area="Explorar",section="Passeios",destination_id="colmar")
        self.assertEqual(state["ux_area"],"Meu roteiro")
        self.assertEqual(state["ux_section"],"Meu planejamento")
        self.assertEqual(state["flow_edit_target"],"colmar")
        state.pop("explore_countries")
        state["scenario_base_selected"]="strasbourg"
        self.assertTrue(return_to_origin(state))
        self.assertEqual(state["ux_area"],"Explorar")
        self.assertEqual(state["ux_section"],"Passeios")
        self.assertEqual(state["explore_countries"],original["explore_countries"])
        self.assertEqual(state["scenario_base_selected"],"mulhouse")
        self.assertNotIn("flow_edit_target",state)
        self.assertFalse(return_to_origin(state))

    def test_discovery_handoff_does_not_mutate_plan(self):
        state={"ux_area":"Meu roteiro","ux_section":"Melhorar meu roteiro",
               "workspace_destination_search":"lux","workspace_discovery_sort":"Nome (A–Z)"}
        plan=new_plan()
        original=deepcopy(plan)
        handoff(state,area="Meu roteiro",section="Melhorar meu roteiro",
                destination_id="luxembourg")
        self.assertEqual(state["flow_active_destination"],"luxembourg")
        self.assertTrue(return_to_origin(state))
        self.assertEqual(state["workspace_destination_search"],"lux")
        self.assertEqual(plan,original)

if __name__=="__main__":
    unittest.main()
