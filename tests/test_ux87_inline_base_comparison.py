"""UX87: scope-safe inline comparison and documentary evidence semantics."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from ux87_inline_base_comparison_ui import project_inline_comparison
from ux87_inline_base_comparison_ui import CATEGORIES


class InlineProjectionContractTests(TestCase):
    def setUp(self):
        self.scope={"destination_ids":["colmar","basel"],"revision":2}
        self.interests={"marker":"intact"}
        self.discovery={"marker":"intact"}
        self.research={"marker":"intact"}
        self.bases=["mulhouse","strasbourg"]
        self.raw={
            "destinations":[
                {"id":"colmar","name":"Colmar","priority":"must_visit",
                 "priority_label":"Imperdível"},
                {"id":"basel","name":"Basel","priority":"must_visit",
                 "priority_label":"Imperdível"},
            ],
            "summaries":[
                {"base_id":"mulhouse","base_name":"Mulhouse"},
                {"base_id":"strasbourg","base_name":"Strasbourg"},
            ],
            "rows":[],"base_ids":self.bases,
        }
        self.cells={
            ("mulhouse","colmar"):{"category":"historical","display_min":18,
                                   "source_url":"https://example.org/historical"},
            ("mulhouse","basel"):{"category":"reference_only","display_min":35,
                                  "source_url":"https://example.org/indicative"},
            ("strasbourg","colmar"):{"category":"local","display_min":None},
            ("strasbourg","basel"):{"category":"no_time","display_min":None},
        }

    def project(self, *, scope_state="ready", cells=None, scope=None, bases=None):
        selected=self.bases if bases is None else bases
        supplied_scope=self.scope if scope is None else scope
        fake_cells=self.cells if cells is None else cells
        with (patch("ux87_inline_base_comparison_ui.reconcile_scope",
                    return_value={"state":scope_state,"scope":self.scope}),
              patch("ux87_inline_base_comparison_ui.compare_wishlist_bases",
                    return_value=deepcopy(self.raw)) as compare,
              patch("ux87_inline_base_comparison_ui.decorate_comparison",
                    return_value={"cells":deepcopy(fake_cells)}) as decorate):
            result=project_inline_comparison(
                self.interests,supplied_scope,selected,
                discovery=self.discovery,research=self.research)
        return result,compare,decorate

    def test_factual_categories_remain_separate_without_ranking(self):
        before=deepcopy((self.scope,self.interests,self.discovery,self.research))
        result,compare,decorate=self.project()
        self.assertEqual(result["counts"]["mulhouse"],
                         {"historical":1,"reference_only":1})
        self.assertEqual(result["counts"]["strasbourg"],{"local":1,"no_time":1})
        self.assertEqual(result["must_visit_without_time"]["strasbourg"],["Basel"])
        self.assertEqual(result["common_timed_destination_ids"],[])
        self.assertIn("~35 min",result["table"][1]["Mulhouse"])
        self.assertEqual(result["table"][1]["Strasbourg"],"Sem tempo pesquisado")
        self.assertFalse(result["ranking_available"])
        self.assertFalse(result["official_plan_modified"])
        self.assertEqual(before,(self.scope,self.interests,self.discovery,self.research))
        self.assertEqual(compare.call_args.kwargs["visible_destination_ids"],
                         self.scope["destination_ids"])
        self.assertEqual(compare.call_args.args[1],self.bases)
        decorate.assert_called_once()

    def test_scope_expiry_blocks_projecting_old_data(self):
        for state in ("scope_required","no_destinations","pending"):
            with self.subTest(state=state):
                with patch("ux87_inline_base_comparison_ui.reconcile_scope",
                           return_value={"state":state,"scope":None}), \
                     patch("ux87_inline_base_comparison_ui.compare_wishlist_bases") as cmp:
                    with self.assertRaises(ValueError):
                        project_inline_comparison(self.interests,self.scope,self.bases,
                                                  discovery=self.discovery,research=self.research)
                    cmp.assert_not_called()

    def test_missing_and_local_cannot_contain_time(self):
        for key in [("strasbourg","colmar"),("strasbourg","basel")]:
            with self.subTest(key=key):
                cells=deepcopy(self.cells)
                cells[key]["display_min"]=0
                with self.assertRaises(ValueError):
                    self.project(cells=cells)

    def test_empty_malformed_or_overlimit_selection_fails_closed(self):
        bad=[[],["mulhouse"],["mulhouse","mulhouse"],[1,"strasbourg"],
             ["a","b","c","d","e","f"]]
        for selection in bad:
            with self.subTest(selection=selection):
                with patch("ux87_inline_base_comparison_ui.reconcile_scope",
                           return_value={"state":"ready","scope":self.scope}), \
                     patch("ux87_inline_base_comparison_ui.compare_wishlist_bases") as cmp:
                    with self.assertRaises(ValueError):
                        project_inline_comparison(
                            self.interests,self.scope,selection,
                            discovery=self.discovery,research=self.research)
                    cmp.assert_not_called()

    def test_all_four_categories_are_documented(self):
        self.assertEqual(set(CATEGORIES),
                         {"historical","reference_only","local","no_time"})
