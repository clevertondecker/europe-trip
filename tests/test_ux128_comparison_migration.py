"""UX128: migration is read-only outside ephemeral comparison state."""
import unittest
from copy import deepcopy
from ux128_comparison_migration import migrate_legacy_comparison
from rec03b_handoffs import CHOICE
from rec03a_session import SCOPE, DRAFT, ACTIVITY, MANUAL, SUGGESTED
from recommendation_scope_model import confirm_scope
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research
from ux502_destination_interests_model import empty_interests,set_interest
from trip_plan_model import new_plan


class UX128MigrationTests(unittest.TestCase):
    def setUp(self):
        self.discovery=build_exploration_discovery()
        self.research=load_research(include_candidates=True)
        self.wishes=set_interest(empty_interests(),"colmar","interested",self.discovery)
        self.wishes=set_interest(self.wishes,"paris","discarded",self.discovery)

    def migrate(self,state):
        migrate_legacy_comparison(state,self.wishes,self.discovery,self.research)

    def test_legacy_filter_becomes_unconfirmed_draft(self):
        state={ACTIVITY:MANUAL,"ux504_bases_shadow":["metz","lille","unknown"],
               "ux504_visible_destinations_shadow":["colmar","paris"],
               "advisor_plan":new_plan(),"ux502_interests":deepcopy(self.wishes)}
        before=deepcopy(state)
        self.migrate(state)
        self.assertEqual(state[CHOICE],["metz","lille"])
        self.assertEqual(state[DRAFT],["colmar"])
        self.assertNotIn(SCOPE,state)
        self.assertEqual(state[ACTIVITY],SUGGESTED)
        self.assertEqual(state["ux112_active_view_shadow"],"Minha comparação")
        self.assertNotIn("ux504_bases_shadow",state)
        self.assertEqual(state["advisor_plan"],before["advisor_plan"])
        self.assertEqual(state["ux502_interests"],before["ux502_interests"])
        after=deepcopy(state)
        self.migrate(state)
        self.assertEqual(state,after)

    def test_canonical_empty_selection_and_confirmed_scope_win(self):
        scope=confirm_scope(self.wishes,["colmar"],self.discovery)
        state={CHOICE:[],SCOPE:scope,"ux504_bases_shadow":["metz","lille"],
               "ux504_visible_destinations_shadow":[]}
        self.migrate(state)
        self.assertEqual(state[CHOICE],[])
        self.assertEqual(state[SCOPE],scope)
        self.assertNotIn(DRAFT,state)

    def test_no_truncation_of_legacy_selection(self):
        ids=[c["id"] for c in self.research["cities"][:6]]
        state={"ux504_bases_shadow":ids}
        self.migrate(state)
        self.assertEqual(state[CHOICE],ids)
