"""Planning journey must permit direct wishlist -> draft review without comparison."""
import unittest
from copy import deepcopy
from ux_planning_journey_model import project_planning
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from attractions_model import load_attractions
from itinerary_flow_model import add_undated_choices,FRANCE_STAGE,ITALY_STAGE

class PlanningJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.catalog=load_attractions()

    def test_filled_wishlist_prioritizes_build_not_compare(self):
        plan=new_plan()
        wishes=empty_interests()
        for d in ("paris","colmar","angers"):
            wishes=set_interest(wishes,d,"must_visit",self.discovery)
        before=deepcopy((plan,wishes))
        view=project_planning(plan,wishes,self.discovery,self.catalog)
        self.assertEqual(view["next"],"build")
        self.assertEqual(view["counts"]["wished"],3)
        self.assertEqual(view["eligible_count"],2)
        self.assertEqual([r["id"] for r in view["unsupported"]],["angers"])
        self.assertEqual((plan,wishes),before)
        added=add_undated_choices(plan,self.catalog,["paris","colmar"],FRANCE_STAGE)
        review=project_planning(added,wishes,self.discovery,self.catalog)
        self.assertEqual(review["next"],"review")
        self.assertEqual(review["counts"]["planned"],2)
        self.assertEqual(review["counts"]["organized"],0)
        self.assertEqual(len(review["pending"]),2)
        self.assertFalse(review["private_saved"])

    def test_empty_wishlist_existing_draft_is_reviewable(self):
        plan=add_undated_choices(new_plan(),self.catalog,["paris"],FRANCE_STAGE)
        self.assertEqual(project_planning(plan,empty_interests(),self.discovery,self.catalog)["next"],"review")

    def test_empty_plan_and_wishlist(self):
        view=project_planning(new_plan(),empty_interests(),self.discovery,self.catalog)
        self.assertEqual(view["next"],"choose")
        self.assertEqual(view["counts"]["planned"],0)

if __name__=="__main__":
    unittest.main()
