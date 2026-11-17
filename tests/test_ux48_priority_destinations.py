"""UX 4.8: canonical destinations and honest 4 x 14 railway matrix."""
from copy import deepcopy
from pathlib import Path
import unittest
from attractions_model import load_attractions,load_base_routes,route_for
from itinerary_flow_model import selected_rows
from trip_plan_model import new_plan
from ux45_outing_contract import apply_outing,remove_outing

class PriorityDestinations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.routes=load_base_routes()

    def test_new_destinations_have_sources_stable_ids_and_unknown_costs(self):
        known={d["id"]:d for d in self.catalog["destinations"]}
        for key,country in [("brussels","Bélgica"),("bruges_be","Bélgica"),
                            ("rotterdam","Países Baixos")]:
            self.assertEqual(known[key]["country"],country)
            self.assertIsNone(known[key]["photo"])
            items=[a for a in self.catalog["attractions"] if a["destination_id"]==key]
            self.assertEqual(len(items),5)
            self.assertTrue(all(x["ticket"]["amount"] is None for x in items))
            self.assertTrue(all(x["visit_minutes_status"]=="editorial_assumption"
                                for x in items))
            for base in ("mulhouse","strasbourg","metz","nancy"):
                route=route_for(self.routes,base,key)
                self.assertIsNone(route["fare_eur_person_oneway"])
                self.assertIsNone(route["train_minutes_one_way"])
                self.assertFalse(route["eligible_2027"])
                self.assertFalse(route["weekend_return_verified"])

    def test_add_edit_remove_using_shared_ux45_contract(self):
        original=new_plan()
        p=deepcopy(original)
        for key in ("brussels","bruges_be","rotterdam"):
            ids=[x["id"] for x in self.catalog["attractions"]
                 if x["destination_id"]==key]
            p,result=apply_outing(p,self.catalog,key,ids[:2],confirmed=True)
            self.assertEqual(result.action,"added")
            self.assertEqual(p["packages"][key],ids[:2])
        self.assertEqual(len([r for r in selected_rows(p,self.catalog)
                              if r["id"] in p["packages"]]),3)
        ids=[x["id"] for x in self.catalog["attractions"]
             if x["destination_id"]=="brussels"]
        q,outcome=apply_outing(p,self.catalog,"brussels",ids[:3],confirmed=True)
        self.assertEqual(outcome.action,"updated")
        self.assertEqual(q["packages"]["brussels"],ids[:3])
        self.assertEqual(q["packages"]["rotterdam"],p["packages"]["rotterdam"])
        r,removed=remove_outing(q,self.catalog,"bruges_be",confirmed=True)
        self.assertEqual(removed.action,"removed")
        self.assertEqual(set(r["packages"]),{"brussels","rotterdam"})
        self.assertEqual(original["packages"],{})
        self.assertEqual(original["base_city"],r["base_city"])
        self.assertEqual(original["budget_scenario"],r["budget_scenario"])

if __name__=="__main__":
    unittest.main()
