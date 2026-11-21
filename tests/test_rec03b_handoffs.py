"""REC03B handoff contracts tested against real catalogs and REC02 evidence."""
import unittest
from copy import deepcopy
from rec03b_handoffs import (PENDING,CONTEXT,PREVIOUS,queue_handoff,apply_handoff,
                            queue_restore_manual,contextual_points)
from rec03a_session import clear_recommendation_context,SCOPE,sync_identity
from recommendation_scope_model import confirm_scope
from ux502_destination_interests_model import empty_interests,set_interest,remove_interest
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research
from base_recommendation_model import recommend_bases
from ux503_destination_base_comparison_model import compare_wishlist_bases
from routes7_comparison_projection import decorate_comparison
from trip_plan_model import new_plan

class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.research=load_research(include_candidates=True)

    def state(self):
        items=empty_interests()
        for d,p in (("paris","must_visit"),("colmar","interested"),("strasbourg","maybe"),
                    ("basel","must_visit"),("lucerne","interested"),("interlaken","maybe"),
                    ("angers","interested")):
            items=set_interest(items,d,p,self.discovery)
        ids=[x["destination_id"] for x in items["items"]]
        return {"ux502_interests":items,SCOPE:confirm_scope(items,ids,self.discovery),
                "advisor_plan":new_plan(),"scenario_base_selected":"metz","ux_mode":"Simulação",
                "ux41_favorites":["metz"],"ux36_cloud_dirty":False,
                "ux504_bases_shadow":["metz","nancy"],"ux504_visible_destinations_shadow":["paris"]}

    def apply(self,state):
        return apply_handoff(state,discovery=self.discovery,research=self.research)

    def test_transfer_whole_scope_and_restore_previous(self):
        state=self.state()
        before=deepcopy(state)
        queue_handoff(state,"manual",["strasbourg","angers","mulhouse"])
        self.assertEqual(self.apply(state),"manual")
        self.assertNotIn(PENDING,state)
        self.assertEqual(state["ux503_visible_destinations"],before[SCOPE]["destination_ids"])
        self.assertEqual(len(state["ux503_visible_destinations"]),7)
        self.assertEqual(state["ux503_bases"],["strasbourg","angers","mulhouse"])
        rec=recommend_bases(state["ux502_interests"],state[SCOPE],discovery=self.discovery,research=self.research)
        raw=compare_wishlist_bases(state["ux502_interests"],state["ux503_bases"],
                                   visible_destination_ids=state["ux503_visible_destinations"],
                                   discovery=self.discovery,research=self.research)
        manual=decorate_comparison(raw)
        for c in rec["candidates"]:
            if c["base_id"] in state["ux503_bases"]:
                for d,cell in c["evidence"].items():
                    self.assertEqual(cell,manual["cells"][c["base_id"],d])
        queue_restore_manual(state)
        self.assertEqual(self.apply(state),"restore_manual")
        self.assertEqual(state["ux503_bases"],["metz","nancy"])
        self.assertEqual(state["ux503_visible_destinations"],["paris"])
        self.assertNotIn(PREVIOUS,state)
        for k in ("advisor_plan","scenario_base_selected","ux_mode","ux502_interests","ux41_favorites","ux36_cloud_dirty"):
            self.assertEqual(state[k],before[k])

    def test_reject_stale_and_invalid_intents(self):
        for ids in (["angers"],["metz","metz"],["unknown","nancy"]):
            state=self.state()
            queue_handoff(state,"manual",ids)
            self.assertIsNone(self.apply(state))
            self.assertEqual(state["ux504_bases_shadow"],["metz","nancy"])
            self.assertNotIn(PENDING,state)
        state=self.state()
        queue_handoff(state,"manual",["angers","metz"])
        state["ux502_interests"]=remove_interest(state["ux502_interests"],"paris",self.discovery)
        self.assertIsNone(self.apply(state))
        self.assertNotIn(CONTEXT,state)

    def test_profile_and_map_never_choose_scenario_or_official(self):
        state=self.state()
        before=deepcopy(state)
        queue_handoff(state,"profile",["angers"])
        self.assertEqual(self.apply(state),"profile")
        self.assertEqual(state["ux40_selected_city"],"angers")
        self.assertEqual(state["ux_section"],"Cidades-base")
        queue_handoff(state,"map",["angers"])
        self.assertEqual(self.apply(state),"map")
        from attractions_model import load_attractions
        from base_explorer_model import load_exploration
        pins,missing=contextual_points(state[CONTEXT],state["advisor_plan"],discovery=self.discovery,
                                       research=self.research,exploration=load_exploration(),catalog=load_attractions())
        self.assertEqual(len({p["id"] for p in pins}),len(pins))
        self.assertTrue(any(p["id"]=="angers" and "Base candidata" in p["role"] for p in pins))
        self.assertTrue(any(p["id"]=="mulhouse" and "Base oficial" in p["role"] for p in pins))
        for k in ("advisor_plan","scenario_base_selected","ux_mode","ux502_interests","ux41_favorites","ux36_cloud_dirty"):
            self.assertEqual(state[k],before[k])
        sync_identity(state,"new-account")
        self.assertNotIn(CONTEXT,state)
        self.assertNotIn(SCOPE,state)

    def test_reset_discards_pending_and_prior_context(self):
        state=self.state()
        queue_handoff(state,"manual",["angers","metz"])
        self.apply(state)
        queue_handoff(state,"map",["angers"])
        clear_recommendation_context(state)
        for key in (SCOPE,PENDING,CONTEXT,PREVIOUS):
            self.assertNotIn(key,state)
        self.assertEqual(state["scenario_base_selected"],"metz")


if __name__=="__main__":
    unittest.main()
