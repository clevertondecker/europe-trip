import unittest
from copy import deepcopy
from time import perf_counter

from arch14_macro_coverage_cache import (
    macro_coverage_rows, cached_macro_coverage_rows,
)
from base_scenario_model import base_options


class MacroCoverageCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids=tuple(x["id"] for x in base_options())

    def test_all_30_rows_have_same_metrics_with_and_without_cache(self):
        before=macro_coverage_rows(self.ids)
        cached_macro_coverage_rows.clear()
        cached=cached_macro_coverage_rows(self.ids)
        self.assertEqual(len(before),30)
        self.assertEqual(cached,before)
        cached[0]["Cidade-base"]="mutated"
        self.assertEqual(cached_macro_coverage_rows(self.ids),before)

    def test_subset_including_reorder_remains_correct(self):
        ids=("lille","mulhouse","freiburg")
        rows=cached_macro_coverage_rows(ids)
        self.assertEqual([x["Cidade-base"] for x in rows],
                         [x["Cidade-base"] for x in macro_coverage_rows(ids)])
        self.assertEqual(len(rows),3)

    def test_invalid_base_list_does_not_create_cache_entry(self):
        for bad in ([],["lille"],("lille","lille"),()):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                macro_coverage_rows(bad)

    def test_lightweight_repeatable_profile_without_speed_assertions(self):
        start=perf_counter()
        baseline=macro_coverage_rows(("mulhouse","strasbourg"))
        full_duration=perf_counter()-start
        start=perf_counter()
        cached_macro_coverage_rows(("mulhouse","strasbourg"))
        cached_duration=perf_counter()-start
        self.assertEqual(len(baseline),2)
        self.assertGreaterEqual(full_duration,0)
        self.assertGreaterEqual(cached_duration,0)
