"""Regression: one wishlist shared by Browse and Compare, including Obernai."""
from copy import deepcopy
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import (
    empty_interests, set_interest, validate_interests,
)
from ux503_destination_base_comparison_model import compare_wishlist_bases

ROOT = Path(__file__).resolve().parents[1]


def itinerary_a_wishlist(discovery):
    wanted = empty_interests()
    for destination_id in ("colmar", "obernai", "paris", "basel", "strasbourg"):
        wanted = set_interest(wanted, destination_id, "interested", discovery)
    return wanted


class Trip01BrowseComparisonTests(unittest.TestCase):
    def test_wishlist_with_supplemental_id_can_be_compared_without_guessing_rail(self):
        discovery = build_exploration_discovery()
        wishlist = itinerary_a_wishlist(discovery)
        before = deepcopy(wishlist)
        self.assertEqual(validate_interests(wishlist, discovery), before)
        result = compare_wishlist_bases(
            wishlist, ["mulhouse", "lille", "strasbourg"], discovery=discovery
        )
        self.assertEqual(len(result["destinations"]), 5)
        self.assertEqual(len(result["rows"]), 15)
        self.assertEqual([d["id"] for d in result["destinations"]],
                         ["colmar", "obernai", "paris", "basel", "strasbourg"])
        obernai_rows = [r for r in result["rows"] if r["destination_id"] == "obernai"]
        self.assertEqual(len(obernai_rows), 3)
        self.assertTrue(all(r["minimum_oneway_min"] is None
                            and r["return_weekend_verified"] is False
                            for r in obernai_rows))
        self.assertEqual(wishlist, before)
        self.assertFalse(result["official_plan_modified"])

    def test_actual_streamlit_compare_accepts_itinerary_a_and_keeps_state(self):
        discovery = build_exploration_discovery()
        wishlist = itinerary_a_wishlist(discovery)
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
        original_plan = deepcopy(app.session_state["advisor_plan"])
        app.session_state["ux502_interests"] = deepcopy(wishlist)
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertFalse(any("Lista de destinos incompatível" in e.message
                             for e in app.error))
        comparison_tables = [
            item.value for item in app.dataframe
            if "Destino · prioridade" in item.value.columns
        ]
        self.assertTrue(comparison_tables, "Comparison matrix was not rendered")
        rows = list(comparison_tables[0]["Destino · prioridade"])
        self.assertTrue(any("Obernai" in row for row in rows))
        self.assertEqual(app.session_state["ux502_interests"], wishlist)
        self.assertEqual(app.session_state["advisor_plan"], original_plan)


if __name__ == "__main__":
    unittest.main()
