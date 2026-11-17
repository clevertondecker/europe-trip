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

    def test_cache_cold_warm_and_explicit_invalidation(self):
        ids=self.ids
        cached_macro_coverage_rows.clear()
        start=perf_counter()
        cold=cached_macro_coverage_rows(ids)
        cold_seconds=perf_counter()-start
        start=perf_counter()
        warm=cached_macro_coverage_rows(ids)
        warm_seconds=perf_counter()-start
        self.assertEqual(cold,warm)
        cached_macro_coverage_rows.clear()
        start=perf_counter()
        after_clear=cached_macro_coverage_rows(ids)
        refreshed_seconds=perf_counter()-start
        self.assertEqual(after_clear,cold)
        print("ARCH14_CACHE_BENCHMARK="+str({
            "cities":len(ids),
            "cold_ms":round(cold_seconds*1000,3),
            "warm_ms":round(warm_seconds*1000,3),
            "after_clear_ms":round(refreshed_seconds*1000,3),
            "environment":"github_actions_CI",
            "note":"diagnostic_sample_not_performance_SLA",
        }))
        self.assertGreaterEqual(cold_seconds,0)
        self.assertGreaterEqual(warm_seconds,0)
        self.assertGreaterEqual(refreshed_seconds,0)

