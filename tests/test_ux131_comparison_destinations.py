"""UX131: independent authorities, explicit scope, and real evidence consumers."""
import unittest
from copy import deepcopy
from attractions_model import load_attractions
from itinerary_flow_model import add_undated_choices, remove_choice, FRANCE_STAGE, ITALY_STAGE
from trip_plan_model import new_plan
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests, set_interest, remove_interest
from comparison_destinations_model import (
    project_comparison_destinations, comparison_items, active_ids, PLANNED,
)
from recommendation_scope_model import confirm_scope, reconcile_scope
from base_recommendation_model import recommend_bases
from base_research_expanded_model import load_research
from ux87_inline_base_comparison_ui import project_inline_comparison
from rec03b_handoffs import validate_handoff, planning_handoff_projection


class CombinedScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.catalog=load_attractions()

    def project(self,wishes,plan):
        return project_comparison_destinations(wishes,plan,self.discovery,self.catalog)

    def wish(self,*pairs):
        result=empty_interests()
        for key,priority in pairs:
            result=set_interest(result,key,priority,self.discovery)
        return result

    def plan(self,*ids):
        return add_undated_choices(new_plan(),self.catalog,list(ids),FRANCE_STAGE)

    def test_union_priority_discarded_and_italy_without_mutation(self):
        plan=self.plan("colmar","basel","strasbourg")
        plan=add_undated_choices(plan,self.catalog,["italy_rome"],ITALY_STAGE)
        wishes=self.wish(("colmar","must_visit"),("basel","discarded"),
                         ("angers","maybe"),("paris","discarded"))
        before=deepcopy((wishes,plan))
        projected=self.project(wishes,plan)
        rows={x["destination_id"]:x for x in comparison_items(projected,self.discovery)}
        self.assertEqual(set(active_ids(projected,self.discovery)),{"colmar","basel","strasbourg","angers"})
        self.assertEqual(rows["colmar"]["priority"],"must_visit")
        self.assertEqual(rows["colmar"]["origin"],"Minha lista + No roteiro")
        self.assertEqual(rows["basel"]["priority"],PLANNED)
        self.assertEqual(rows["basel"]["wishlist_priority"],"discarded")
        self.assertEqual(rows["strasbourg"]["priority"],PLANNED)
        self.assertIsNone(rows["strasbourg"]["wishlist_priority"])
        self.assertEqual(rows["angers"]["origin"],"Minha lista")
        self.assertEqual((wishes,plan),before)

    def test_confirmed_exclusion_new_visit_and_two_source_removal(self):
        wishes=self.wish(("colmar","interested"),("angers","maybe"))
        plan=self.plan("colmar")
        scope=confirm_scope(self.project(wishes,plan),["colmar"],self.discovery)
        plan=add_undated_choices(plan,self.catalog,["basel"],FRANCE_STAGE)
        changed=reconcile_scope(self.project(wishes,plan),scope,self.discovery)
        self.assertEqual(changed["pending_ids"],["basel"])
        self.assertEqual(changed["scope"]["destination_ids"],["colmar"])
        self.assertFalse(changed["scope"]["confirmed"])
        scope=confirm_scope(self.project(wishes,plan),["colmar","basel"],self.discovery)
        wishes=remove_interest(wishes,"colmar",self.discovery)
        changed=reconcile_scope(self.project(wishes,plan),scope,self.discovery)
        self.assertEqual(changed["state"],"ready")
        self.assertEqual(changed["scope"]["destination_ids"],["basel","colmar"])
        plan=remove_choice(plan,self.catalog,"colmar")
        changed=reconcile_scope(self.project(wishes,plan),changed["scope"],self.discovery)
        self.assertEqual(changed["state"],"ready")
        self.assertEqual(changed["scope"]["destination_ids"],["basel"])
        self.assertNotIn("angers",changed["scope"]["destination_ids"])

    def test_wishlist_replacement_vs_non_material_plan_change(self):
        wishes=self.wish(("colmar","interested"))
        plan=self.plan("basel")
        scope=confirm_scope(self.project(wishes,plan),["basel","colmar"],self.discovery)
        changed_plan=deepcopy(plan)
        changed_plan["revision"]+=1
        self.assertEqual(reconcile_scope(self.project(wishes,changed_plan),scope,self.discovery)["scope"],scope)
        replacement=deepcopy(wishes)
        replacement["items"][0]["priority"]="maybe"
        self.assertIsNone(reconcile_scope(self.project(replacement,plan),scope,self.discovery)["scope"])
        self.assertIsNone(reconcile_scope(self.project(wishes,self.plan("basel")),scope,self.discovery)["scope"])

    def test_legacy_scope_preserves_exclusions_and_reviews_new_visits(self):
        wishes=self.wish(("colmar","must_visit"),("angers","maybe"))
        scope=confirm_scope(wishes,["colmar"],self.discovery)
        updated=reconcile_scope(self.project(wishes,self.plan("basel")),scope,self.discovery)
        self.assertEqual(updated["pending_ids"],["basel"])
        self.assertEqual(updated["scope"]["destination_ids"],["colmar"])

    def test_real_matrix_and_handoff_use_same_union_and_weights(self):
        wishes=self.wish(("colmar","must_visit"))
        plan=self.plan("basel")
        before=deepcopy((wishes,plan))
        projected=self.project(wishes,plan)
        scope=confirm_scope(projected,["basel","colmar"],self.discovery)
        research=load_research(include_candidates=True)
        result=recommend_bases(projected,scope,discovery=self.discovery,research=research)
        self.assertEqual({d["id"] for d in result["destinations"]},{"colmar","basel"})
        self.assertEqual(result["weights"][PLANNED],3)
        custom=recommend_bases(projected,scope,discovery=self.discovery,research=research,
                               weights={"must_visit":5,"interested":3,"maybe":1,PLANNED:4})
        self.assertEqual(custom["weights"][PLANNED],4)
        with self.assertRaises(ValueError):
            recommend_bases(projected,scope,discovery=self.discovery,research=research,
                            weights={"must_visit":5,"interested":3,"maybe":1,PLANNED:0})
        inline=project_inline_comparison(projected,scope,["strasbourg","metz"],
                                        discovery=self.discovery,research=research)
        self.assertEqual({d["id"] for d in inline["destinations"]},{"colmar","basel"})
        context=validate_handoff(scope,projected,self.discovery,research,[],"planning")
        handoff=planning_handoff_projection(context,plan,wishes,self.discovery,self.catalog)
        self.assertEqual(handoff["eligible"],["colmar"])
        self.assertEqual(handoff["included"],["basel"])
        self.assertEqual((wishes,plan),before)
