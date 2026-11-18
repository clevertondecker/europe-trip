"""DATA 11 source contract and DQ3.2 frontend projection regression tests."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from data11_priority_connectivity_model import (
    load_priority_connectivity, validate_priority_connectivity,
)
from dq32_macro_opportunities_model import opportunity_overview
from rail_reference_projection_model import decorate_comparison


class Data11PriorityConnectivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load_priority_connectivity()

    def test_coverage_is_deduplicated_and_mapped_to_canonical_ids(self):
        rows = self.overlay["records"]
        self.assertGreaterEqual(len(rows), 35)
        self.assertEqual(len({(r["origin_id"], r["destination_id"])
                              for r in rows}), len(rows))
        self.assertGreaterEqual(
            len([r for r in rows if r["origin_id"] == "mulhouse"]), 25)
        for item in rows:
            self.assertFalse(item["return_2027_verified"])
            self.assertFalse(item["valid_for_2027"])
            self.assertEqual(item["direction"], "outbound_only")
            self.assertGreater(item["minimum_oneway_min"], 0)

    def test_validation_fails_on_unsourced_or_invented_time(self):
        original = {
            "schema_version": 1, "scope": self.overlay["scope"],
            "selection_policy": "fallback_after_historical_routes7_data9_data10",
            "checked_at": self.overlay["checked_at"],
            "records": deepcopy(self.overlay["records"]),
        }
        for mutation in ("wrong_direction", "future_guarantee", "unknown_source",
                         "duplicate_pair", "wrong_provenance"):
            with self.subTest(mutation=mutation):
                payload = deepcopy(original)
                if mutation == "wrong_direction":
                    payload["records"][0]["direction"] = "both"
                elif mutation == "future_guarantee":
                    payload["records"][0]["return_2027_verified"] = True
                elif mutation == "unknown_source":
                    payload["records"][0]["source_url"] = "https://example.com"
                elif mutation == "duplicate_pair":
                    payload["records"].append(deepcopy(payload["records"][0]))
                else:
                    payload["records"][0]["confidence"] = "high"
                with self.assertRaises(ValueError):
                    validate_priority_connectivity(payload)

    def test_shared_projection_surfaces_new_source_without_overwriting_legacy(self):
        sample = {"rows": [{
            "base_id": "mulhouse", "destination_id": "arlon",
            "evidence_status": "unresearched",
            "minimum_oneway_min": None, "source_url": None,
            "divergent_sources": False,
        }]}
        output = decorate_comparison(sample)
        cell = output["cells"][("mulhouse", "arlon")]
        self.assertEqual(cell["category"], "reference_only")
        self.assertEqual(cell["display_basis"], "data11_reference")
        self.assertTrue(cell["priority_connectivity_applied"])
        self.assertTrue(cell["reference_source_url"].startswith("https://"))
        self.assertFalse(cell["valid_for_2027"])
        historical = deepcopy(sample)
        historical["rows"][0]["evidence_status"] = "historical"
        historical["rows"][0]["minimum_oneway_min"] = 123
        historical["rows"][0]["source_url"] = "https://example.org/historical"
        existing = decorate_comparison(historical)["cells"][("mulhouse", "arlon")]
        self.assertEqual(existing["display_min"], 123)
        self.assertFalse(existing["priority_connectivity_applied"])

    def test_streamlit_discovery_all_destinations_shows_mins_and_sources(self):
        root = Path(__file__).resolve().parents[1]
        app = AppTest.from_file(str(root/"app.py"), default_timeout=120).run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.selectbox(key="attractions_scenario_base").set_value("mulhouse").run()
        app.selectbox(key="ux_dq32_opportunity_group").set_value("Todos os destinos").run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        tables = [frame.value for frame in app.dataframe
                  if "Mínimo de ida (min)" in frame.value.columns]
        self.assertTrue(tables, "DQ3.2 must expose sortable travel minutes")
        table = tables[0]
        arlon = table[table["Destino"] == "Arlon"]
        self.assertEqual(len(arlon), 1)
        self.assertEqual(int(arlon.iloc[0]["Mínimo de ida (min)"]), 197)
        self.assertIn("Referência", str(arlon.iloc[0]["Transporte"]).title())
        self.assertEqual(len(table), 46)

    def test_dq32_frontend_receives_new_routes_and_correct_counts(self):
        overview = opportunity_overview("mulhouse")
        self.assertGreaterEqual(overview["rail_reference_total_count"], 35)
        assert_ids = ("arlon", "esch", "kehl", "lausanne", "lauterbrunnen",
                      "liege", "lorrach", "metz", "namur")
        by_id = {row["destination_id"]: row for row in overview["destinations"]}
        for target in assert_ids:
            with self.subTest(destination=target):
                row = by_id[target]
                self.assertNotEqual(row["status"], "unresearched_from_base")
                self.assertTrue(row["minimum_train_oneway_min"] is not None
                                or row["indicative_train_oneway_min"] is not None)
                self.assertFalse(row["weekend_return_verified"])
                self.assertFalse(row["reachable_confirmed"])
        self.assertEqual(
            overview["rail_reference_total_count"],
            overview["rail_time_documented_count"]+
            overview["indicative_rail_reference_count"])
        self.assertEqual(
            len(overview["destinations"]),
            overview["rail_reference_total_count"]+
            overview["unresearched_count"]+
            len(overview["local_destinations"]))


if __name__ == "__main__":
    unittest.main()
