"""UX132A public-only coverage projection and navigation regressions."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from time import perf_counter
from statistics import median

from streamlit.testing.v1 import AppTest
from data24_coverage_model import rail_coverage, coverage_counts
from ux132_research_coverage_model import build_coverage_view, project_coverage_view


class CoverageModelTests(unittest.TestCase):
    def test_projection_matches_data24(self):
        raw = rail_coverage()
        view = build_coverage_view()
        self.assertEqual(view["global"], raw["global"])
        self.assertEqual(view["base_count"], len(raw["base_ids"]))
        self.assertEqual(view["destination_count"], len(raw["destination_ids"]))
        for row in view["bases"]:
            self.assertEqual(row["fraction"], raw["by_base"][row["id"]]["fraction"])
            self.assertEqual(len(row["missing_names"]), row["missing"])
        for row in view["destinations"]:
            counts = coverage_counts(p["cell"]["category"] for (b,d),p in raw["pairs"].items()
                                     if d == row["id"])
            self.assertEqual(row["fraction"], counts["fraction"])
            self.assertEqual(len(row["missing_names"]), counts["missing"])
        self.assertEqual(view["priority"]["eligible"],
                         sum(r["eligible"] for r in view["bases"] if r["id"] in view["priority_ids"]))

    def test_new_reference_updates_both_axes_without_changing_denominator(self):
        from data25_priority_rail_model import load_data25
        records = load_data25()["by_pair"]
        key = ("metz", "annecy")
        old = build_coverage_view(projection_options={"data25_overlay": {
            "by_pair": {k: v for k, v in records.items() if k != key}}})
        new = build_coverage_view(projection_options={"data25_overlay": {"by_pair": records}})
        self.assertEqual(new["global"]["eligible"], old["global"]["eligible"])
        self.assertEqual(new["global"]["timed"], old["global"]["timed"] + 1)
        self.assertEqual(new["global"]["missing"], old["global"]["missing"] - 1)
        for axis, ident, missing in (("bases", "metz", "Annecy"),
                                     ("destinations", "annecy", "Metz")):
            before = next(r for r in old[axis] if r["id"] == ident)
            after = next(r for r in new[axis] if r["id"] == ident)
            self.assertEqual(after["eligible"], before["eligible"])
            self.assertEqual(after["timed"], before["timed"] + 1)
            self.assertEqual(after["missing"], before["missing"] - 1)
            self.assertIn(missing, before["missing_names"])
            self.assertNotIn(missing, after["missing_names"])

    def test_projection_rerun_cost_diagnostic(self):
        # Record real timings in CI without a flaky wall-clock assertion.
        durations = []
        baseline = None
        for _ in range(3):
            start = perf_counter()
            result = build_coverage_view()
            durations.append(perf_counter() - start)
            if baseline is None:
                baseline = result
            else:
                self.assertEqual(result, baseline)
        print("UX132_COVERAGE_TIMING", {
            "samples_seconds": [round(x, 4) for x in durations],
            "median_seconds": round(median(durations), 4),
            "max_seconds": round(max(durations), 4),
        })

    def test_local_only_and_empty(self):
        for categories in ([], ["local"]):
            raw = {"base_ids": ["metz"], "destination_ids": ["metz"] if categories else [],
                   "pairs": {("metz","metz"): {"cell": {"category": "local"}}} if categories else {},
                   "global": coverage_counts(categories)}
            before = deepcopy(raw)
            view = project_coverage_view(raw, {"metz": "Metz"}, {"metz": "Metz"})
            self.assertIsNone(view["global"]["fraction"])
            self.assertIsNone(view["bases"][0]["fraction"])
            self.assertEqual(view["bases"][0]["missing_names"], [])
            self.assertEqual(raw, before)


APP = """
import streamlit as st
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests
from rec03a_suggestions_ui import render_suggestions
s = st.session_state
if "advisor_plan" not in s:
    s["advisor_plan"] = new_plan()
if "ux502_interests" not in s:
    s["ux502_interests"] = empty_interests()
render_suggestions(plan=s["advisor_plan"])
"""


class CoverageNavigationTests(unittest.TestCase):
    def test_empty_wishlist_access_and_return(self):
        app = AppTest.from_string(APP, default_timeout=90)
        with patch("rec03a_suggestions_ui.recommend_bases") as engine:
            app.run()
            self.assertFalse(app.exception)
            before = {key: deepcopy(app.session_state[key]) for key in
                      ("advisor_plan", "ux502_interests")}
            app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
            self.assertFalse(app.exception)
            self.assertTrue(any(m.label == "Cobertura ferroviária" for m in app.metric))
            app.segmented_control(key="ux132_coverage_section").set_value("Cidades-base").run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.dataframe[0].value), 5)
            app.selectbox(key="ux132_base_scope").select("Todas as bases").run()
            self.assertFalse(app.exception)
            self.assertGreater(len(app.dataframe[0].value), 5)
            app.selectbox(key="ux132_detail_Cidades-base").select("offenburg").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["ux132_detail_Cidades-base"], "offenburg")
            self.assertTrue(any(m.label == "Lacunas de pesquisa" for m in app.metric))
            app.selectbox(key="ux132_base_scope").select("Cinco bases prioritárias").run()
            self.assertFalse(app.exception)
            self.assertIn(app.session_state["ux132_detail_Cidades-base"],
                          ("lille", "metz", "mulhouse", "nancy", "strasbourg"))
            self.assertEqual(len(app.dataframe[0].value), 5)
            app.segmented_control(key="ux132_coverage_section").set_value("Destinos").run()
            self.assertFalse(app.exception)
            self.assertTrue(app.dataframe)
            app.segmented_control(key="ux112_active_view").set_value(None).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["ux112_active_view"], "Explorar alternativas")
            self.assertFalse(app.exception)
            self.assertTrue(any("Nenhum destino ativo" in x.value for x in app.info))
            engine.assert_not_called()
            for key,value in before.items():
                self.assertEqual(app.session_state[key], value)


if __name__ == "__main__":
    unittest.main()
