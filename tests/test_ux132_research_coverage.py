"""UX132A public-only coverage projection and navigation regressions."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from time import perf_counter
from statistics import median

from streamlit.testing.v1 import AppTest
from data24_coverage_model import rail_coverage, coverage_counts
from ux132_research_coverage_model import (
    build_coverage_view, project_coverage_view, filter_coverage_rows, connection_rows,
    STATUS_OPTIONS,
)


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
        detail_durations = []
        baseline = None
        for _ in range(3):
            start = perf_counter()
            result = build_coverage_view()
            durations.append(perf_counter() - start)
            start = perf_counter()
            connection_rows(result, "bases", "metz", "Todas")
            detail_durations.append(perf_counter() - start)
            if baseline is None:
                baseline = result
            else:
                self.assertEqual(result, baseline)
        print("UX132_COVERAGE_TIMING", {
            "samples_seconds": [round(x, 4) for x in durations],
            "median_seconds": round(median(durations), 4),
            "max_seconds": round(max(durations), 4),
            "detail_median_seconds": round(median(detail_durations), 4),
            "detail_max_seconds": round(max(detail_durations), 4),
        })

    def test_filter_and_order_preserve_input_and_denominators(self):
        rows = [
            {"id": "a", "name": "Sélestat", "fraction": .5, "missing": 2},
            {"id": "b", "name": "Metz", "fraction": .2, "missing": 4},
            {"id": "c", "name": "Annecy", "fraction": None, "missing": 0},
            {"id": "d", "name": "Paris", "fraction": 1, "missing": 0},
        ]
        before = deepcopy(rows)
        self.assertEqual([r["id"] for r in filter_coverage_rows(rows, query=" SELESTAT ")], ["a"])
        self.assertEqual([r["id"] for r in filter_coverage_rows(rows, gaps_only=True, sort="Mais lacunas")], ["b","a"])
        self.assertEqual([r["id"] for r in filter_coverage_rows(rows, sort="Menor cobertura")], ["b","a","d","c"])
        self.assertEqual(filter_coverage_rows(rows, query="absent"), [])
        self.assertEqual(rows, before)

    def test_detail_direction_counts_and_source_provenance(self):
        view = build_coverage_view()
        before = deepcopy(view)
        for axis, ident in (("bases","metz"), ("destinations","annecy")):
            summary = next(r for r in view[axis] if r["id"] == ident)
            all_rows = connection_rows(view, axis, ident, "Todas")
            self.assertEqual(len(all_rows), summary["total"])
            for status, count_key in (("Histórico","historical"), ("Indicativo","indicative"),
                                      ("Local","local"), ("Sem tempo pesquisado","missing")):
                filtered = connection_rows(view, axis, ident, status)
                self.assertEqual(len(filtered), summary[count_key])
                for row in filtered:
                    self.assertEqual(row["category"], STATUS_OPTIONS[status])
                    self.assertEqual(row["base_id" if axis == "bases" else "destination_id"], ident)
                    original = view["pairs"][(row["base_id"],row["destination_id"])]
                    if status == "Histórico":
                        self.assertEqual(row["source_date"], original["row"]["source_date"])
                        self.assertEqual(row["source_url"], original["row"]["source_url"])
                    elif status == "Indicativo":
                        self.assertEqual(row["minimum"], original["cell"]["display_min"])
                    else:
                        self.assertIsNone(row["source_url"])
                        self.assertIsNone(row["minimum"])
            self.assertEqual(len(connection_rows(view, axis, ident)), summary["missing"])
        route = next(r for r in connection_rows(view,"bases","metz","Indicativo")
                     if r["destination_id"] == "annecy")
        self.assertEqual(route["minimum"], 363)
        self.assertEqual(route["source_url"], "https://www.sncf-connect.com/train/trajet/metz/annecy")
        self.assertEqual(route["source_date"], "2026-11-25")
        self.assertEqual(view, before)

    def test_historical_source_not_replaced_by_alternate_reference(self):
        view = {"bases":[{"id":"a","name":"A"}], "destinations":[{"id":"b","name":"B"}],
                "pairs":{("a","b"):{"cell":{"category":"historical","label":"1h · histórico",
                        "display_min":60,"source_url":"https://example.org/alternate",
                        "reference_source_url":"https://example.org/alternate","checked_at":"2026-11-25"},
                        "row":{"source_url":"https://example.org/historical","source_date":"2026-01-01"}}}}
        result = connection_rows(view,"bases","a","Histórico")[0]
        self.assertEqual(result["source_url"],"https://example.org/historical")
        self.assertEqual(result["source_date"],"2026-01-01")

    def test_qualifications_belong_to_the_matching_evidence(self):
        # Identical URL and duration on different dates must not attach stale notes.
        primary = {"source_url":"https://example.org/history","evidence_date":"2026-01-02",
                   "source_dataset":"historic","minimum_oneway_min":60,
                   "origin_station":"A Central","destination_station":"B Central","notes":"Primary note"}
        older = {**primary,"evidence_date":"2026-01-01","notes":"Older note"}
        view = {"bases":[{"id":"a","name":"A"}], "destinations":[{"id":"b","name":"B"}],
                "pairs":{("a","b"):{"cell":{"category":"historical","label":"1h · histórico",
                        "display_min":60,"source_url":"https://example.org/recheck",
                        "reference_source_url":"https://example.org/original","checked_at":"2026-11-25",
                        "fastest_min":70,"reference_display_allowed":True,
                        "station_caveat":"Alternative station qualification",
                        "evidence_notes":"Alternative note","reference_differs_from_legacy":True},
                        "row":{"source_url":primary["source_url"],"source_date":primary["evidence_date"],
                               "source_dataset":"historic","observations":[older,primary]}}}}
        before = deepcopy(view)
        row = connection_rows(view,"bases","a","Histórico")[0]
        self.assertEqual(row["minimum"],60)
        self.assertEqual(row["notes"],"Primary note")
        self.assertIn("A Central → B Central", row["station_caveat"])
        self.assertNotIn("Alternative", row["station_caveat"])
        self.assertEqual(row["observations"],[older])
        alternative = row["alternative"]
        self.assertEqual(alternative["minimum"],70)
        self.assertEqual(alternative["source_url"],"https://example.org/recheck")
        self.assertEqual(alternative["source_date"],"2026-11-25")
        self.assertEqual(alternative["station_caveat"],"Alternative station qualification")
        self.assertEqual(alternative["notes"],"Alternative note")
        self.assertEqual(view,before)
        cell = view["pairs"][("a","b")]["cell"]
        cell["reference_display_allowed"] = False
        self.assertIsNone(connection_rows(view,"bases","a","Histórico")[0]["alternative"])
        cell.update(category="reference_only", display_min=70, reference_display_allowed=True)
        indicative = connection_rows(view,"bases","a","Indicativo")[0]
        self.assertEqual(indicative["source_url"],"https://example.org/recheck")
        self.assertEqual(indicative["source_date"],"2026-11-25")
        self.assertEqual(indicative["notes"],"Alternative note")
        self.assertEqual(indicative["station_caveat"],"Alternative station qualification")
        self.assertEqual(indicative["observations"],[older,primary])

    def test_comparator_parity_for_real_mixed_evidence(self):
        from ux503_destination_base_comparison_model import build_destination_matrix
        from rail_reference_projection_model import decorate_comparison
        from trip01_supplemental_discovery import build_exploration_discovery
        from base_research_expanded_model import load_research
        view = build_coverage_view()
        discovery = build_exploration_discovery()
        research = load_research(include_candidates=True)
        destinations = [d["id"] for d in view["destinations"]]
        matrix = build_destination_matrix(["metz"],destinations,discovery=discovery,research=research)
        projected = decorate_comparison(matrix)["cells"]
        rows = connection_rows(view,"bases","metz","Todas")
        self.assertEqual(len(rows),len(projected))
        for row in rows:
            cell = projected[("metz",row["destination_id"])]
            self.assertEqual(row["category"],cell["category"])
            self.assertEqual(row["label"],cell["label"])
            self.assertEqual(row["minimum"],cell.get("display_min"))

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
    def test_search_filter_and_evidence_detail(self):
        app = AppTest.from_string(APP, default_timeout=90)
        app.run()
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
        app.segmented_control(key="ux132_coverage_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception)
        global_before = next(m.value for m in app.metric if m.label=="Cobertura ferroviária")
        app.text_input(key="ux132_search_bases").set_value("Metz").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value), 1)
        self.assertEqual(app.session_state["ux132_detail_Cidades-base"], "metz")
        app.selectbox(key="ux132_status_bases").select("Indicativo").run()
        self.assertFalse(app.exception)
        app.selectbox(key="ux132_connection_bases").select("annecy").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Metz → Annecy" in m.value for m in app.markdown))
        app.text_input(key="ux132_search_bases").set_value("no-such-city").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Nenhuma cidade corresponde" in m.value for m in app.info))
        self.assertEqual(next(m.value for m in app.metric if m.label=="Cobertura ferroviária"),global_before)
        app.text_input(key="ux132_search_bases").set_value("").run()
        app.selectbox(key="ux132_sort_bases").select("Mais lacunas").run()
        self.assertFalse(app.exception)
        gaps = app.dataframe[0].value["Sem tempo"].tolist()
        self.assertEqual(gaps, sorted(gaps,reverse=True))

    def test_axis_filters_and_valid_selection_survive_hidden_widgets(self):
        app = AppTest.from_string(APP, default_timeout=90)
        app.run()
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
        app.segmented_control(key="ux132_coverage_section").set_value("Cidades-base").run()
        app.text_input(key="ux132_search_bases").set_value("Metz").run()
        app.selectbox(key="ux132_sort_bases").select("Mais lacunas").run()
        app.checkbox(key="ux132_only_gaps_bases").check().run()
        app.selectbox(key="ux132_status_bases").select("Indicativo").run()
        app.selectbox(key="ux132_connection_bases").select("annecy").run()
        self.assertFalse(app.exception)
        app.segmented_control(key="ux132_coverage_section").set_value("Destinos").run()
        app.text_input(key="ux132_search_destinations").set_value("Annecy").run()
        app.segmented_control(key="ux112_active_view").set_value("Explorar alternativas").run()
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control(key="ux132_coverage_section").value,"Destinos")
        self.assertEqual(app.text_input(key="ux132_search_destinations").value,"Annecy")
        app.segmented_control(key="ux132_coverage_section").set_value("Cidades-base").run()
        self.assertEqual(app.text_input(key="ux132_search_bases").value,"Metz")
        self.assertEqual(app.selectbox(key="ux132_sort_bases").value,"Mais lacunas")
        self.assertTrue(app.checkbox(key="ux132_only_gaps_bases").value)
        self.assertEqual(app.selectbox(key="ux132_detail_Cidades-base").value,"metz")
        self.assertEqual(app.selectbox(key="ux132_status_bases").value,"Indicativo")
        self.assertEqual(app.selectbox(key="ux132_connection_bases").value,"annecy")
        app.selectbox(key="ux132_status_bases").select("Histórico").run()
        self.assertFalse(app.exception)
        self.assertNotEqual(app.selectbox(key="ux132_connection_bases").value,"annecy")
        app.text_input(key="ux132_search_bases").set_value("no-such-city").run()
        self.assertFalse(app.exception)
        app.text_input(key="ux132_search_bases").set_value("Metz").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="ux132_detail_Cidades-base").value,"metz")

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
            app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
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
