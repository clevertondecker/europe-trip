import copy
import unittest

from routes7_comparison_projection import decorate_comparison
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import (
    empty_interests, set_interest, selected_destinations_for_comparison,
)
from ux503_destination_base_comparison_model import compare_wishlist_bases
from trip_plan_model import new_plan


def make_comparison(bases, destinations):
    discovery = build_destination_discovery()
    wishes = empty_interests()
    for dest in destinations:
        wishes = set_interest(wishes, dest, "interested", discovery)
    comparison = compare_wishlist_bases(
        wishes, bases, discovery=discovery)
    return wishes, comparison, discovery


class Route7UXRegressionTests(unittest.TestCase):
    def test_public_five_destinations_three_bases_exclusive_counts(self):
        wish, matrix, discovery = make_comparison(
            ["mulhouse", "strasbourg", "lille"],
            ["belfort", "haguenau", "mulhouse", "brussels", "ghent"])
        orig = copy.deepcopy(matrix)
        copy_wish = copy.deepcopy(wish)
        plan = new_plan(base="mulhouse")
        plan_before = copy.deepcopy(plan)
        view = decorate_comparison(matrix)
        self.assertEqual(view["total"], 15)
        self.assertEqual(
            (view["historical"], view["reference_only"], view["local"], view["no_time"]),
            (5, 9, 1, 0))
        self.assertEqual(sum(view[x] for x in (
            "historical", "reference_only", "local", "no_time")), view["total"])
        self.assertIn("mínimo indicativo", view["cells"][("mulhouse", "belfort")]["label"])
        self.assertIn("estação pendente", view["cells"][("mulhouse", "belfort")]["label"])
        self.assertIn("histórico", view["cells"][("lille", "ghent")]["label"])
        self.assertFalse(view["cells"][("lille", "ghent")]["conflict_with_legacy"])
        self.assertTrue(view["cells"][("lille", "ghent")]["reference_differs_from_legacy"])
        self.assertEqual(matrix, orig)
        self.assertEqual(wish, copy_wish)
        self.assertEqual(plan, plan_before)
        self.assertFalse(view["comparison_mutated"])
        self.assertFalse(view["automatic_base_ranking"])

    def test_average_disagreement_shown_with_two_distinct_values(self):
        _, matrix, _ = make_comparison(
            ["mulhouse", "strasbourg"], ["belfort"])
        view = decorate_comparison(matrix)
        label = view["cells"][("strasbourg", "belfort")]["typical_label"]
        self.assertIn("1h46", label)
        self.assertIn("1h56", label)
        self.assertIn("reconsultada", label)
        self.assertEqual(view["cells"][("mulhouse", "belfort")]["typical_label"],
                         "Tempo médio não documentado")

    def test_other_wishlist_destinations_never_require_overlay(self):
        _, matrix, _ = make_comparison(
            ["freiburg", "metz"], ["paris", "berlin"])
        view = decorate_comparison(matrix)
        self.assertEqual(view["total"], 4)
        self.assertEqual(
            sum(view[x] for x in ("historical", "reference_only", "local", "no_time")),
            4)

    def test_two_to_five_bases_and_different_destination_baskets(self):
        discovery = build_destination_discovery()
        bases = ["mulhouse", "strasbourg", "lille", "metz", "freiburg"]
        for count in range(2, 6):
            _, matrix, _ = make_comparison(bases[:count], ["belfort", "ghent"])
            view = decorate_comparison(matrix)
            self.assertEqual(view["total"], count * 2)
            self.assertEqual(len(view["cells"]), count * 2)

    def test_selected_wishlist_filter_and_priority_are_untouched(self):
        discovery = build_destination_discovery()
        wishes = empty_interests()
        wishes = set_interest(wishes, "belfort", "must_visit", discovery)
        wishes = set_interest(wishes, "ghent", "interested", discovery)
        previous = copy.deepcopy(wishes)
        matrix = compare_wishlist_bases(
            wishes, ["mulhouse", "strasbourg"], discovery=discovery,
            visible_destination_ids=["ghent"])
        before = copy.deepcopy(matrix)
        view = decorate_comparison(matrix)
        self.assertEqual(view["total"], 2)
        self.assertEqual(matrix, before)
        self.assertEqual(wishes, previous)

    def test_unsupported_pair_and_empty_matrix(self):
        empty = decorate_comparison({"rows": []})
        self.assertEqual(empty["total"], 0)
        self.assertEqual(empty["no_time"], 0)
        synthetic = {"rows": [{
            "base_id": "unregistered", "destination_id": "noncatalog",
            "evidence_status": "not_researched", "minimum_oneway_min": None,
            "source_url": None, "divergent_sources": False, "observations": [],
        }]}
        view = decorate_comparison(synthetic)
        self.assertEqual(view["no_time"], 1)
        self.assertEqual(view["cells"][("unregistered", "noncatalog")]["label"],
                         "Tempo não estimado")

    def test_duplicate_matrix_row_rejected(self):
        row = {"base_id": "mulhouse", "destination_id": "belfort",
               "evidence_status": "unknown", "minimum_oneway_min": None,
               "source_url": None, "divergent_sources": False}
        with self.assertRaises(ValueError):
            decorate_comparison({"rows": [row, dict(row)]})
