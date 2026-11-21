"""REC02: policy safety, scope evolution and parity with real REC01."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from base_recommendation_model import evaluate_matrix, recommend_bases
from base_recommendation_evidence_model import build_recommendation_matrix
from recommendation_scope_model import confirm_scope, reconcile_scope
from ux502_destination_interests_model import empty_interests, set_interest, remove_interest
from rec01_feasibility import SCENARIOS, DATA23_SCENARIOS, coverage_report
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research
from rail_evidence_unified_model import load_rail_evidence
from base_explorer_model import load_exploration
from trip_plan_model import new_plan


def fixture(rows, priorities=None):
    """Synthetic, directed cells; no source or time asserted as a real fact."""
    ids = sorted({d for values in rows.values() for d in values})
    cells = {}
    for b, values in rows.items():
        for d in ids:
            v = values.get(d)
            category = ("local" if v == "local" else "no_time" if v is None else
                        "reference_only" if isinstance(v, tuple) else "historical")
            cells[b,d] = {"base_id":b, "destination_id":d, "category":category,
                          "display_min":v[0] if isinstance(v,tuple) else v if isinstance(v,int) else None}
    return {"comparison":{"base_ids":list(rows), "destinations":[
        {"id":d,"name":d,"country":"Synthetic","priority":(priorities or {}).get(d,"interested")} for d in ids]},
        "evidence":{"cells":cells}}


class RecommendationPolicyTests(unittest.TestCase):
    def test_fast_partial_does_not_defeat_complete(self):
        longer = {str(i):100 for i in range(10)}
        matrix = fixture({"quick":{"0":1,"1":1}, "complete":longer,
                          "second":{d:110 for d in longer}})
        before = deepcopy(matrix)
        result = evaluate_matrix(matrix)
        self.assertEqual(result["highlight_ids"],["complete"])
        self.assertEqual(result["complete_groups"][0]["lowest_on_this_set"],["complete"])
        conditional = next(g for g in result["conditional_comparisons"] if "quick" in g["base_ids"])
        self.assertEqual(conditional["destination_ids"],["0","1"])
        self.assertEqual(len(conditional["omitted_destination_ids"]),8)
        self.assertFalse(result["global_ranking"])
        self.assertEqual(matrix,before)

    def test_complete_ties_and_mixed_evidence(self):
        result=evaluate_matrix(fixture({"b":{"x":10,"y":20},"a":{"x":(10,), "y":20}}))
        self.assertEqual(result["state"],"comparable")
        self.assertEqual(result["highlight_ids"],["a","b"])
        self.assertTrue(result["complete_groups"][0]["mixed_evidence"])
        self.assertFalse(result["complete_groups"][0]["total_logistics_decidable"])

    def test_partial_overlap_no_global_ranking_or_transitive_chain(self):
        m=fixture({"a":{"x":10,"y":20}, "b":{"x":30,"y":40,"z":50,"w":60},
                   "c":{"z":5,"w":10}, "d":{"q":None}})
        result=evaluate_matrix(m)
        self.assertEqual(result["state"],"partial_evidence")
        self.assertEqual({tuple(x["base_ids"]) for x in result["conditional_comparisons"]},
                         {("a","b"),("b","c")})
        self.assertEqual(result["highlight_ids"],["b"])
        self.assertEqual(len(result["candidates"]),4)
        self.assertFalse(result["global_ranking"])

    def test_local_is_never_zero_or_train_coverage(self):
        result=evaluate_matrix(fixture({"a":{"x":"local"},"b":{"x":None}},{"x":"must_visit"}))
        row=result["candidates"][0]
        self.assertTrue(row["local_only"])
        self.assertIsNone(row["weighted_coverage"]["value"])
        self.assertIsNone(row["weighted_minimum_oneway"]["value"])
        self.assertEqual(row["must_visit"]["local"],["x"])
        self.assertEqual(result["state"],"partial_evidence")
        self.assertFalse(result["complete_groups"])

    def test_single_scope_and_missing_must(self):
        result=evaluate_matrix(fixture({"a":{"x":10},"b":{"x":20}},{"x":"must_visit"}))
        self.assertEqual(result["state"],"comparable")
        self.assertEqual(result["highlight_ids"],["a"])
        partial=evaluate_matrix(fixture({"a":{"x":10,"z":20,"y":None},
                                         "b":{"x":15,"z":30,"y":None}},{"y":"must_visit"}))
        self.assertEqual(partial["state"],"partial_evidence")
        self.assertEqual(partial["conditional_comparisons"][0]["must_visit_omitted"],["y"])
        self.assertTrue(all("imperdiveis_com_evidencia_pendente" in c["reasons"] for c in partial["candidates"]))
        self.assertFalse(partial["complete_groups"])

    def test_disjoint_and_unknown(self):
        self.assertFalse(evaluate_matrix(fixture({"a":{"x":20},"b":{"y":30}}))["conditional_comparisons"])
        none=evaluate_matrix(fixture({"a":{"x":None},"b":{"x":None}}))
        self.assertEqual(none["state"],"insufficient_evidence")
        self.assertEqual(none["highlight_ids"],[])

    def test_priority_sensitivity_and_order_stability(self):
        m=fixture({"a":{"x":1,"y":30},"b":{"x":12,"y":10}},{"x":"must_visit","y":"interested"})
        first=evaluate_matrix(m)
        # 5*1+3*30 > 5*12+3*10; higher priority changes preferred reference.
        self.assertEqual(first["highlight_ids"],["b"])
        self.assertEqual(evaluate_matrix(m,weights={"must_visit":10,"interested":3,"maybe":1})["highlight_ids"],["a"])
        reordered=deepcopy(m)
        reordered["comparison"]["base_ids"].reverse()
        reordered["comparison"]["destinations"].reverse()
        self.assertEqual(evaluate_matrix(reordered),first)

    def test_invalid_matrix_fails_closed(self):
        m=fixture({"a":{"x":10},"b":{"x":20}})
        del m["evidence"]["cells"]["b","x"]
        with self.assertRaises(ValueError):
            evaluate_matrix(m)


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.discovery={"destinations":[{"id":x} for x in ("paris","colmar","rome")]}
        self.wishes=set_interest(empty_interests(),"paris","must_visit",self.discovery)
        self.wishes=set_interest(self.wishes,"colmar","maybe",self.discovery)

    def test_scope_requires_explicit_confirmation_and_reconciles(self):
        self.assertEqual(reconcile_scope(self.wishes,None,self.discovery)["state"],"scope_required")
        scope=confirm_scope(self.wishes,["paris"],self.discovery)
        changed=set_interest(self.wishes,"paris","interested",self.discovery)
        result=reconcile_scope(changed,scope,self.discovery)
        self.assertEqual(result["state"],"ready")
        self.assertEqual(result["scope"]["destination_ids"],["paris"])
        new=set_interest(changed,"rome","maybe",self.discovery)
        review=reconcile_scope(new,result["scope"],self.discovery)
        self.assertEqual(review["state"],"scope_required")
        self.assertEqual(review["pending_ids"],["rome"])
        self.assertEqual(review["scope"]["destination_ids"],["paris"])
        self.assertEqual(reconcile_scope(new,review["scope"],self.discovery)["state"],"scope_required")
        self.assertEqual(reconcile_scope(new,review["scope"],self.discovery,reset=True)["scope"],None)

    def test_same_revision_import_and_remove(self):
        scope=confirm_scope(self.wishes,["paris","colmar"],self.discovery)
        replaced=deepcopy(self.wishes)
        replaced["items"][0]["priority"]="discarded"
        self.assertIsNone(reconcile_scope(replaced,scope,self.discovery)["scope"])
        removed=remove_interest(self.wishes,"colmar",self.discovery)
        self.assertEqual(reconcile_scope(removed,scope,self.discovery)["scope"]["destination_ids"],["paris"])
        for invalid in ([],["paris","paris"],["unknown"]):
            with self.assertRaises(ValueError):
                confirm_scope(self.wishes,invalid,self.discovery)
        self.assertEqual(reconcile_scope(self.wishes,{"stage":"bad"},self.discovery)["state"],"scope_required")


class RealRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.research=load_research(include_candidates=True)
        cls.rail=load_rail_evidence()
        cls.exploration=load_exploration()

    def test_all_real_scenarios_match_diagnostic(self):
        plan=new_plan()
        original_plan=deepcopy(plan)
        for name,items in {**SCENARIOS,**DATA23_SCENARIOS}.items():
            with self.subTest(scenario=name):
                wishes=empty_interests()
                for d,p in items:
                    wishes=set_interest(wishes,d,p,self.discovery)
                scope=confirm_scope(wishes,[d for d,_ in items],self.discovery)
                before=deepcopy((wishes,scope))
                kwargs=dict(discovery=self.discovery,research=self.research,rail=self.rail,exploration=self.exploration)
                matrix=build_recommendation_matrix(wishes,scope["destination_ids"],**kwargs)
                result=recommend_bases(wishes,scope,**kwargs)
                expected=coverage_report(matrix)
                coverage={c["base_id"]:c["weighted_coverage_pct"] for c in expected["coverage_by_base"]}
                self.assertEqual(len(result["candidates"]),len(self.research["cities"]))
                for c in result["candidates"]:
                    value=c["weighted_coverage"]["value"]
                    self.assertEqual(None if value is None else round(value*100,2),coverage[c["base_id"]])
                    for d,cell in c["evidence"].items():
                        self.assertEqual(cell,matrix["evidence"]["cells"][c["base_id"],d])
                self.assertEqual((wishes,scope),before)
                self.assertEqual(result,recommend_bases(wishes,scope,**kwargs))
                self.assertFalse(result["official_plan_modified"])
                self.assertFalse(result["global_ranking"])
        self.assertEqual(plan,original_plan)

    def test_loader_error_and_empty(self):
        wishes=set_interest(empty_interests(),"paris","must_visit",self.discovery)
        scope=confirm_scope(wishes,["paris"],self.discovery)
        with patch("base_recommendation_model.build_recommendation_matrix",side_effect=RuntimeError("loader")):
            with self.assertRaisesRegex(RuntimeError,"loader"):
                recommend_bases(wishes,scope,discovery=self.discovery)
        self.assertEqual(recommend_bases(empty_interests(),discovery=self.discovery)["state"],"no_destinations")
        self.assertEqual(recommend_bases(wishes,discovery=self.discovery)["state"],"scope_required")
        discarded=set_interest(wishes,"paris","discarded",self.discovery)
        self.assertEqual(recommend_bases(discarded,scope,discovery=self.discovery)["state"],"no_destinations")


if __name__ == "__main__":
    unittest.main()
