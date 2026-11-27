"""UX132C1: audit parity, documentary gaps and domain navigation."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from statistics import median
from time import perf_counter

from streamlit.testing.v1 import AppTest
from data24_audit_model import attraction_inventory, attraction_counts
from attractions_model import load_attractions
from data23_france_candidates_model import load_data23
from dq32_macro_opportunities_model import load_macro_tourism
from dq30_walking_access_model import load_walking_access
from trip01_supplemental_discovery import build_exploration_discovery
from ux132c1_attraction_coverage_model import (
    build_attraction_view, project_attraction_view, indicator_rows, attraction_gaps,
    gap_count, filter_destinations, detail_rows,
)


class AttractionCoverageTests(unittest.TestCase):
    def test_real_inventory_parity(self):
        inventory = attraction_inventory(build_exploration_discovery(), load_attractions(),
                                         load_data23(), load_macro_tourism(), load_walking_access())
        view = build_attraction_view()
        self.assertEqual(view["counts"], inventory["counts"])
        for key, count in inventory["counts"].items():
            self.assertEqual(sum(r["counts"][key] for r in view["destinations"]), count, key)
        self.assertEqual(len({a["id"] for d in view["destinations"] for a in d["rows"]}),
                         inventory["counts"]["attractions"])
        self.assertEqual(sum(r["counts"]["ticket_published"] + r["counts"]["ticket_not_applicable"]
                             + r["counts"]["ticket_unknown"] for r in view["destinations"]),
                         inventory["counts"]["attractions"])
        for dest in view["destinations"]:
            for field in ("described", "editorial_duration", "ticket_unknown",
                          "attraction_photo_attributed", "station_access_documented"):
                self.assertEqual(gap_count(dest, field),
                                 len(detail_rows(dest, gap=field, gaps_only=True)))

    def test_zero_denominator_and_distinct_ticket_photo_and_access_states(self):
        photo = {"url":"https://example.org/photo.jpg","source_page":"https://example.org/photo",
                 "author":"Author","license":"CC BY","license_url":"https://example.org/license"}
        discovery = {"destinations":[
            {"id":"empty","name":"Vazio","attractions":[],"attraction_count":0,"photo":photo},
            {"id":"city","name":"Sélestat","attractions":[
                {"id":"a","name":"A","kind":"museum","source_url":"https://example.org/a"},
                {"id":"b","name":"B","kind":"park","source_url":"https://example.org/b",
                 "reconciled_source_ids":["alias"]},
                {"id":"c","name":"C","kind":"museum","source_url":"https://example.org/c"},
            ],"attraction_count":3,"photo":photo},
        ]}
        catalog = {"attractions":[
            {"id":"a","summary":"Description","visit_minutes":45,"visit_minutes_status":"editorial_assumption",
             "ticket":{"status":"operator_published","amount":0,"currency":"EUR","per":"adult",
                       "source_url":"https://example.org/ticket","checked_at":"2026-11-20"},
             "checked_at":"2026-11-14"},
            {"id":"b","ticket":{"status":"not_applicable"},"photo":photo},
            {"id":"c","visit_minutes":30,"visit_minutes_status":"unknown"},
        ]}
        geography = {"stations":[{"id":"station"}],"walking_routes":[
            {"origin_id":"station","destination_id":"a","status":"pedestrian_routed",
             "duration_min":10,"source_url":"https://example.org/access","checked_at":"2026-11-21"},
            {"origin_id":"not_station","destination_id":"b","status":"pedestrian_routed",
             "duration_min":5,"source_url":"https://example.org/invalid"},
        ]}
        def build():
            return attraction_inventory(discovery,catalog,{"attractions":[]},{"attractions":[]},geography)
        inventory = build()
        before = deepcopy(inventory)
        view = project_attraction_view(inventory)
        self.assertEqual(inventory,before)
        counts = view["counts"]
        self.assertEqual(counts["attractions"],3)
        self.assertEqual(counts["reconciled_aliases"],1)
        self.assertEqual(counts["destinations_with_attributed_photo"],2)
        self.assertEqual(counts["attraction_photo_attributed"],1)
        self.assertEqual(counts["editorial_duration"],1)
        self.assertEqual(counts["station_access_documented"],1)
        self.assertEqual((counts["ticket_published"],counts["ticket_not_applicable"],counts["ticket_unknown"]),(1,1,1))
        city = filter_destinations(view,query=" SELESTAT ")[0]
        empty = filter_destinations(view,gap="catalog",gaps_only=True)[0]
        self.assertEqual(empty["id"],"empty")
        self.assertIsNone(next(r for r in indicator_rows(empty["counts"]) if r["key"]=="described")["fraction"])
        a,b,c = city["rows"]
        self.assertNotIn("ticket_unknown",attraction_gaps(b))
        self.assertIn("ticket_unknown",attraction_gaps(c))
        self.assertIn("attraction_photo_attributed",attraction_gaps(a))
        self.assertEqual(a["ticket"]["source_url"],"https://example.org/ticket")
        self.assertEqual(a["station_access"][0]["checked_at"],"2026-11-21")
        self.assertEqual(a["checked_at"],"2026-11-14")
        self.assertIsNone(c["editorial_duration_min"])
        self.assertEqual(b["station_access"],[])
        catalog["attractions"][2]["summary"] = "New documented description"
        updated = project_attraction_view(build())
        self.assertEqual(updated["counts"]["described"],counts["described"]+1)
        self.assertEqual(updated["counts"]["attractions"],counts["attractions"])
        self.assertEqual(len(detail_rows(city,gap="ticket_unknown",gaps_only=True)),1)

    def test_real_trip01_and_reconciled_alias_provenance(self):
        view = build_attraction_view()
        rows = {a["id"]: a for d in view["destinations"] for a in d["rows"]}
        for ident in ("obernai_market", "lucerne_chapel"):
            self.assertEqual(rows[ident]["checked_at"], "2026-11-20")
            self.assertIsNone(rows[ident]["description"])
            self.assertEqual(rows[ident]["ticket_status"], "unknown")
        bock = rows["lux_bock"]
        self.assertIn("dq32_luxembourg_city_22", bock["reconciled_source_ids"])
        self.assertEqual(bock["ticket_status"], "operator_published")
        self.assertEqual(bock["field_records"]["ticket"]["record_id"], "lux_bock")
        self.assertNotIn("dq32_luxembourg_city_22", rows)

    def test_complementary_alias_and_supplemental_fields(self):
        photo = {"url":"https://example.org/photo.jpg","source_page":"https://example.org/photo",
                 "author":"Author","license":"CC BY","license_url":"https://example.org/license"}
        discovery = {"destinations":[{"id":"city","name":"City","attraction_count":2,"attractions":[
            {"id":"a","name":"A","kind":"legacy_catalog","source_url":"https://example.org/a",
             "reconciled_source_ids":["alias"]},
            {"id":"b","name":"B","kind":"supplemental_exploratory","source_url":"https://example.org/b",
             "documentary_record":{"id":"b","summary":"Supplemental description",
                                   "checked_at":"2026-11-20","source_url":"https://example.org/b"}},
        ]}]}
        catalog = {"attractions":[{"id":"a","summary":"Canonical description",
                                   "ticket":{"status":"not_applicable"}}]}
        macro = {"attractions":[{"id":"alias","description":"Alternative description",
             "source_url":"https://example.org/alias","checked_at":"2026-11-21",
             "photo":photo,"editorial_duration_min":45,
             "ticket":{"status":"operator_published","amount":12,"currency":"EUR","per":"adult"}}]}
        geo = {"stations":[{"id":"station"}],"walking_routes":[
            {"origin_id":"station","destination_id":"alias","status":"pedestrian_routed",
             "duration_min":12,"source_url":"https://example.org/access","checked_at":"2026-11-22"}]}
        inventory = attraction_inventory(discovery,catalog,{"attractions":[]},macro,geo)
        a,b = inventory["rows"]
        self.assertEqual(a["description"],"Canonical description")
        self.assertEqual(a["ticket_status"],"not_applicable")
        self.assertEqual(a["field_records"]["photo"]["record_id"],"alias")
        self.assertEqual(a["field_records"]["editorial_duration"]["record_date"],"2026-11-21")
        self.assertEqual(a["station_access"][0]["destination_id"],"alias")
        self.assertEqual(b["description"],"Supplemental description")
        self.assertEqual(b["field_records"]["description"]["record_id"],"b")
        self.assertEqual(b["ticket_status"],"unknown")
        self.assertEqual(inventory["counts"]["attractions"],2)
        self.assertEqual(inventory["counts"]["reconciled_aliases"],1)

    def test_attraction_projection_timing(self):
        timings, details = [], []
        baseline = None
        for _ in range(3):
            start = perf_counter()
            view = build_attraction_view()
            timings.append(perf_counter()-start)
            start = perf_counter()
            rows = filter_destinations(view,gap="all",sort="Mais pendências no filtro")
            if rows:
                detail_rows(rows[0],gaps_only=True)
            details.append(perf_counter()-start)
            if baseline is None:
                baseline = view
            else:
                self.assertEqual(view,baseline)
        print("UX132C1_ATTRACTION_TIMING", {"samples_seconds":timings,
              "median_seconds":median(timings),"detail_median_seconds":median(details)})


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


class AttractionNavigationTests(unittest.TestCase):
    def test_overview_links_and_independent_domain_loads(self):
        app = AppTest.from_string(APP,default_timeout=90).run()
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control(key="ux132_domain").value,"Visão geral")
        with patch("ux132_coverage_page.build_attraction_inventory") as summary, \
             patch("ux132c1_attraction_coverage_ui.build_attraction_view") as detail:
            app.button(key="ux132_open_rail").click().run()
            self.assertFalse(app.exception)
            summary.assert_not_called()
            detail.assert_not_called()
        app.segmented_control(key="ux132_domain").set_value("Visão geral").run()
        with patch("ux132_coverage_page.rail_coverage") as summary, \
             patch("ux132_research_coverage_ui.build_coverage_view") as detail:
            app.button(key="ux132_open_attractions").click().run()
            self.assertFalse(app.exception)
            summary.assert_not_called()
            detail.assert_not_called()
        self.assertEqual(app.segmented_control(key="ux132_domain").value,"Atrações turísticas")

    def test_domain_switch_preserves_filters_and_plan(self):
        app = AppTest.from_string(APP,default_timeout=90).run()
        before = {k:deepcopy(app.session_state[k]) for k in ("advisor_plan","ux502_interests")}
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
        app.segmented_control(key="ux132_coverage_section").set_value("Cidades-base").run()
        app.text_input(key="ux132_search_bases").set_value("Metz").run()
        app.segmented_control(key="ux132_domain").set_value("Atrações turísticas").run()
        self.assertFalse(app.exception)
        self.assertTrue(any(m.label=="Atrações únicas" for m in app.metric))
        app.text_input(key="ux132c1_search").set_value("Colmar").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="ux132c1_destination").value,"colmar")
        app.selectbox(key="ux132c1_sort").select("Mais pendências no filtro").run()
        app.segmented_control(key="ux132_domain").set_value("Transporte ferroviário").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="ux132_search_bases").value,"Metz")
        app.segmented_control(key="ux132_domain").set_value("Atrações turísticas").run()
        self.assertEqual(app.text_input(key="ux132c1_search").value,"Colmar")
        self.assertEqual(app.selectbox(key="ux132c1_sort").value,"Mais pendências no filtro")
        app.text_input(key="ux132c1_search").set_value("not-a-city").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Nenhum destino corresponde" in i.value for i in app.info))
        app.text_input(key="ux132c1_search").set_value("Paris").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="ux132c1_destination").value,"paris")
        app.segmented_control(key="ux112_active_view").set_value("Explorar alternativas").run()
        app.segmented_control(key="ux112_active_view").set_value("Cobertura dos dados").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.segmented_control(key="ux132_domain").value,"Atrações turísticas")
        self.assertEqual(app.text_input(key="ux132c1_search").value,"Paris")
        for key,value in before.items():
            self.assertEqual(app.session_state[key],value)


if __name__ == "__main__":
    unittest.main()
