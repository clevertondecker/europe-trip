"""Regression: an official city is renderable without chosen attractions.

UX77 permits a destination to enter TripPlan.flexible_visits with zero
attractions. The strict guide validator must remain strict until the user
selects 1..5 attractions.
"""
import unittest
from unittest.mock import patch

from trip_plan_model import new_plan
from itinerary_flow_model import FRANCE_STAGE, UNASSIGNED, add_undated_choices, selected_rows_for_stage
from ux47_destination_card_model import destination_card_view
from outing_guide_model import build_outing_guide


class UndatedDestinationCardTests(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan(base="metz")
        self.catalog={
            "destinations":[
                {"id":"metz","name":"Metz","country":"França"},
                {"id":"basel","name":"Basel","country":"Suíça"},
                {"id":"colmar","name":"Colmar","country":"França"}],
            "attractions":[{"id":"colmar_oldtown","name":"Centro histórico",
                            "destination_id":"colmar"}]}
        self.plan=add_undated_choices(
            self.plan,self.catalog,["basel","colmar"],FRANCE_STAGE)

    @patch("ux47_destination_card_model.build_outing_guide")
    def test_undated_city_without_attractions_is_renderable(self, guide):
        rows=selected_rows_for_stage(self.plan,self.catalog,FRANCE_STAGE)
        self.assertEqual(len(rows),2)
        for row in rows:
            view=destination_card_view(self.plan,self.catalog,None,row)
            self.assertEqual(view["attraction_count"],0)
            self.assertEqual(view["attractions"],[])
            self.assertEqual(view["dates"],[])
            self.assertIsNone(view["period"])
            self.assertFalse(view["organized"])
            self.assertFalse(view["reservation_confirmed"])
            self.assertFalse(view["cost_complete"])
            self.assertIn("não",view["cost"])
        guide.assert_not_called()

    @patch("ux47_destination_card_model.build_outing_guide")
    def test_undated_row_may_have_flexible_period(self, guide):
        row=next(x for x in selected_rows_for_stage(
            self.plan,self.catalog,FRANCE_STAGE) if x["id"]=="basel")
        row["period"]="Durante a estadia na França"
        view=destination_card_view(self.plan,self.catalog,None,row)
        self.assertEqual(view["period"],"Durante a estadia na França")
        self.assertTrue(view["organized"])
        guide.assert_not_called()

    def test_strict_guide_contract_is_not_weakened(self):
        with self.assertRaisesRegex(ValueError,"1 a 5 atrações"):
            build_outing_guide(self.plan,self.catalog,{},"basel",[])

    @patch("ux47_destination_card_model.build_outing_guide")
    def test_existing_attraction_cards_still_use_the_guide(self, guide):
        from copy import deepcopy
        row=deepcopy(next(x for x in selected_rows_for_stage(
            self.plan,self.catalog,FRANCE_STAGE) if x["id"]=="colmar"))
        row["attractions"]=["colmar_oldtown"]
        guide.return_value={
            "route":{"weekend_return_verified":False},
            "train_minutes_one_way":35,
            "local":False,
            "known_cost":{"EUR":0.0,"CHF":0.0},
        }
        view=destination_card_view(self.plan,self.catalog,{},row)
        self.assertEqual(view["attraction_count"],1)
        guide.assert_called_once_with(self.plan,self.catalog,{},"colmar",["colmar_oldtown"])


if __name__=="__main__":
    unittest.main()
