"""UX132C2: D-004 parity, scope, documentary semantics and navigation."""
import unittest
from copy import deepcopy
from statistics import median
from time import perf_counter
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from data24_audit_model import build_audit
from data24_d004_audit_model import living_counts, living_research_gaps, coworking_state
from ux132c2_living_coverage_model import (
    build_living_view, scope_rows, scope_counts, indicator_rows,
    city_detail, compact_rows, PRIORITY, ALL,
)


class LivingCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.view = build_living_view()

    def test_canonical_audit_parity_and_scopes(self):
        audit = build_audit()["d004"]
        self.assertEqual(self.view["counts"], audit["counts"])
        self.assertEqual(self.view["scope"], audit["scope"])
        self.assertEqual(scope_counts(self.view, ALL), audit["counts"])
        priority = scope_rows(self.view)
        self.assertEqual({r["id"] for r in priority},
                         set(self.view["scope"]["approved_research_base_ids"]))
        self.assertEqual(len(priority), 5)
        self.assertEqual(len(scope_rows(self.view, ALL)), 7)
        self.assertEqual(scope_counts(self.view)["bases"], 5)
        self.assertIsNone(city_detail(self.view, "colmar"))
        self.assertIsNone(self.view["scope"]["official_finalist_ids"])
        for original in audit["rows"]:
            r = city_detail(self.view, original["id"])
            self.assertNotIn("rail", r)
            for key in ("housing", "daily_life", "remote_work"):
                self.assertEqual(r[key], original[key])
            for key in ("complementary", "sufficient_for_context_only"):
                self.assertEqual(r["research_gaps"][key], original["research_gaps"][key])
            self.assertEqual(original["research_gaps"]["decision_blockers"][:len(r["research_gaps"]["decision_blockers"])],
                             r["research_gaps"]["decision_blockers"])
        self.assertFalse(self.view["official_plan_modified"])

    def test_documentary_semantics_and_provenance(self):
        before = deepcopy(self.view)
        for r in scope_rows(self.view, ALL):
            h, d, w = (r[k] for k in ("housing", "daily_life", "remote_work"))
            self.assertEqual(h["summary"]["count"], len(h["historical_offers"]))
            self.assertEqual(len({o["listing_ref"] for o in h["historical_offers"]}),
                             len(h["historical_offers"]))
            self.assertIsNone(h["total_2027"])
            self.assertIsNone(h["deposit_2027"])
            self.assertIsNone(h["contract_2027_verified"])
            self.assertIsNone(w["residential_internet_2027"])
            self.assertEqual(w["compatibility_2027"], "indeterminate")
            self.assertEqual(w["compatibility_2026"], coworking_state(w["coworking"]))
            for offer in h["historical_offers"]:
                self.assertTrue(offer["checked_at"])
                self.assertTrue(offer.get("listing_url") or offer.get("catalogue_url"))
            if d["restaurant_eur_two"] is not None:
                self.assertTrue(d["restaurant_source_url"])
                self.assertTrue(d["restaurant_basis"])
            if d["urban_pass"] is not None:
                self.assertTrue(d["urban_pass"]["source_url"])
                self.assertTrue(d["urban_pass"]["price_period"])
            if (d["climate"] or {}).get("months_9_10_11") is not None:
                self.assertEqual(set(d["climate"]["months_9_10_11"]), {"9","10","11"})
                self.assertTrue(d["climate"]["normal_period"])
                self.assertTrue(d["climate"]["station_name"])
                self.assertTrue(d["climate"]["source_url"])
                self.assertTrue(d["climate"]["observed_at"])
            if w["coworking"]:
                self.assertTrue(w["coworking"]["source_url"])
                self.assertTrue(w["coworking"]["price_basis"])
        self.assertFalse(self.view["shared_budget_context_not_local"]["city_specific"])
        metz = city_detail(self.view, "metz")
        self.assertEqual(metz["daily_life"]["restaurant_eur_two"], 60)
        self.assertEqual(metz["daily_life"]["urban_pass"]["fare_eur_month_person"], 45.9)
        self.assertIsNone(metz["daily_life"]["comparable_local_basket_eur"])
        self.assertEqual(metz["remote_work"]["compatibility_2026"], "indeterminate")
        self.assertEqual(city_detail(self.view, "mulhouse")["remote_work"]["compatibility_2026"], "incompatible_2026")
        self.assertEqual(coworking_state({"late_work_compatible": True}), "compatible_2026")
        self.assertEqual(self.view, before)

    def test_controlled_update_zero_and_empty_denominator(self):
        original = deepcopy(self.view)
        fixture = deepcopy(self.view)
        r = city_detail(fixture, "lille")
        self.assertIsNone(r["daily_life"]["restaurant_eur_two"])
        r["daily_life"].update(restaurant_eur_two=0, restaurant_source_url="https://example.org/record",
                               restaurant_basis="Controlled fixture")
        r["research_gaps"] = living_research_gaps(r)
        self.assertEqual(scope_counts(fixture)["with_restaurant"],
                         scope_counts(self.view)["with_restaurant"] + 1)
        self.assertTrue(next(x for x in compact_rows(scope_rows(fixture)) if x["id"] == "lille")["restaurant"])
        self.assertNotIn("restaurante para dois", r["research_gaps"]["complementary"])
        self.assertEqual(scope_counts(fixture)["with_three_verified_quotes"],
                         scope_counts(self.view)["with_three_verified_quotes"])
        self.assertTrue(all(x["fraction"] is None for x in indicator_rows(living_counts([]))))
        self.assertEqual(self.view, original)

    def test_living_projection_timing(self):
        timings, details = [], []
        for _ in range(3):
            start = perf_counter()
            view = build_living_view()
            timings.append(perf_counter() - start)
            start = perf_counter()
            scope_counts(view)
            compact_rows(scope_rows(view))
            city_detail(view, "metz")
            details.append(perf_counter() - start)
            self.assertEqual(view, self.view)
        print("UX132C2_LIVING_TIMING", {"samples_seconds": timings,
              "median_seconds": median(timings), "detail_median_seconds": median(details)})


APP = """
import streamlit as st
from rec03a_suggestions_ui import render_suggestions
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests
if "advisor_plan" not in st.session_state:
    st.session_state["advisor_plan"] = new_plan()
if "ux502_interests" not in st.session_state:
    st.session_state["ux502_interests"] = empty_interests()
render_suggestions(plan=st.session_state["advisor_plan"])
"""


class LivingNavigationTests(unittest.TestCase):
    def test_scope_selection_domain_independence_and_return(self):
        app = AppTest.from_string(APP, default_timeout=90).run()
        before = {k: deepcopy(app.session_state[k]) for k in ("advisor_plan", "ux502_interests")}
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        self.assertFalse(app.exception)
        self.assertTrue(any(m.label == "Três cotações de 2027" for m in app.metric))
        with patch("ux132_coverage_page.rail_coverage") as rail_summary, \
             patch("ux132_coverage_page.build_attraction_inventory") as attraction_summary, \
             patch("ux132_research_coverage_ui.build_coverage_view") as rail_detail, \
             patch("ux132c1_attraction_coverage_ui.build_attraction_view") as attraction_detail:
            app.button(key="ux132_open_living").click().run()
            self.assertFalse(app.exception)
            for loader in (rail_summary, attraction_summary, rail_detail, attraction_detail):
                loader.assert_not_called()
        self.assertEqual(app.segmented_control(key="ux132_domain").value, "Morar e trabalhar")
        self.assertEqual(app.selectbox(key="ux132c2_scope").value, PRIORITY)
        app.selectbox(key="ux132c2_scope").select(ALL).run()
        app.selectbox(key="ux132c2_base").select("trier").run()
        self.assertFalse(app.exception)
        with patch("ux132c2_living_coverage_ui.build_living_view") as living:
            app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
            self.assertFalse(app.exception)
            living.assert_not_called()
            app.segmented_control(key="ux132_domain").set_value("Atrações turísticas").run()
            self.assertFalse(app.exception)
            living.assert_not_called()
        app.segmented_control(key="ux132_domain").set_value("Morar e trabalhar").run()
        self.assertEqual(app.selectbox(key="ux132c2_scope").value, ALL)
        self.assertEqual(app.selectbox(key="ux132c2_base").value, "trier")
        app.selectbox(key="ux132c2_scope").select(PRIORITY).run()
        self.assertFalse(app.exception)
        self.assertIn(app.selectbox(key="ux132c2_base").value,
                      {"lille","metz","mulhouse","nancy","strasbourg"})
        app.selectbox(key="ux132c2_base").select("metz").run()
        app.segmented_control(key="ux112_active_view").set_value("Explorar alternativas").run()
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control(key="ux132_domain").value, "Morar e trabalhar")
        self.assertEqual(app.selectbox(key="ux132c2_base").value, "metz")
        for key, value in before.items():
            self.assertEqual(app.session_state[key], value)


if __name__ == "__main__":
    unittest.main()
