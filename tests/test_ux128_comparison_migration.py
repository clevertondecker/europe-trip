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

    def test_no_retired_renderer_or_public_entry(self):
        from pathlib import Path
        import ast
        root=Path(__file__).resolve().parents[1]
        self.assertFalse((root/"ux503_destination_base_comparison_ui.py").exists())
        renderer=(root/"rec03a_suggestions_ui.py").read_text(encoding="utf-8")
        self.assertNotIn("Ajustar comparação detalhada",renderer)
        self.assertNotIn("render_wishlist_base_comparison",renderer)
        consumers=[]
        for file in root.rglob("*.py"):
            if any(part.startswith(".") or part in ("venv","__pycache__","site-packages")
                   for part in file.relative_to(root).parts):
                continue
            for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
                modules=[]
                if isinstance(node,ast.Import):
                    modules=[alias.name for alias in node.names]
                elif isinstance(node,ast.ImportFrom):
                    modules=[node.module or ""]
                elif isinstance(node,ast.Call) and node.args:
                    func=node.func
                    if ((isinstance(func,ast.Name) and func.id in ("__import__","import_module")) or
                        (isinstance(func,ast.Attribute) and func.attr=="import_module")):
                        arg=node.args[0]
                        if isinstance(arg,ast.Constant) and isinstance(arg.value,str):
                            modules=[arg.value]
                if any(x.split(".")[-1]=="ux503_destination_base_comparison_ui" for x in modules):
                    consumers.append(str(file.relative_to(root)))
        self.assertEqual(consumers,[])


    def test_bootstrap_migration_skips_modern_state(self):
        from unittest.mock import patch
        from ux128_comparison_migration import migrate_restored_comparison
        state={CHOICE:["metz","lille"],SCOPE:confirm_scope(self.wishes,["colmar"],self.discovery)}
        before=deepcopy(state)
        with patch("base_research_expanded_model.load_research") as load:
            self.assertFalse(migrate_restored_comparison(state))
            load.assert_not_called()
        self.assertEqual(state,before)

    def test_bootstrap_consumes_legacy_once(self):
        from rec03a_session import apply_navigation
        state={ACTIVITY:MANUAL,"ux504_bases_shadow":["metz","lille"],
               "ux504_visible_destinations_shadow":["colmar","paris"],
               "ux502_interests":deepcopy(self.wishes)}
        apply_navigation(state)
        self.assertEqual(state[CHOICE],["metz","lille"])
        self.assertEqual(state[DRAFT],["colmar"])
        self.assertNotIn("ux504_bases_shadow",state)
        before=deepcopy(state)
        apply_navigation(state)
        self.assertEqual(state,before)

    def test_journey_pending_components_keep_temporal_association(self):
        from ux506_decision_readiness_projection import journey_readiness_detail
        result=journey_readiness_detail({"minimum_oneway_min":35})
        self.assertEqual(result["temporal_status"],"not_checked")
        self.assertIn("missing_component",result["association_reasons"])
        self.assertEqual(len(result["missing_components"]),3)
        self.assertFalse(result["outing_feasible_2027"])
