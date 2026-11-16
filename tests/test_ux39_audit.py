"""Structural UX3.9 audit: current navigation contract and readonly invariants."""
import unittest
from copy import deepcopy
from ux_navigation import AREAS,SECTIONS,route
from trip_plan_model import new_plan
from base_change_model import destination_impact


class UX39AuditTests(unittest.TestCase):
    def test_four_existing_areas_and_valid_routes(self):
        self.assertEqual(AREAS,("Minha viagem","Explorar","Meu roteiro","Orçamento"))
        for area in AREAS:
            for section in SECTIONS[area]:
                self.assertIsInstance(route(area,section),tuple)

    def test_comparison_stays_readonly(self):
        plan=new_plan()
        original=deepcopy(plan)
        output=destination_impact(plan,"strasbourg",["luxembourg","brussels"])
        self.assertEqual(len(output),2)
        self.assertEqual(plan,original)
        self.assertIsNone(output[0]["official_fare"])

if __name__=="__main__":
    unittest.main()
