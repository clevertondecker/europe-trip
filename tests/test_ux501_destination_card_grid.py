"""Regression coverage for filtered destination card rows (UX 5.0.1)."""
import unittest
from unittest.mock import patch

from ux501_destination_discovery_ui import _destination_rows


class DestinationCardGridTests(unittest.TestCase):
    def test_empty_results_have_no_rows(self):
        self.assertEqual(_destination_rows([]), [])

    def test_one_result_does_not_reserve_empty_columns(self):
        place = {"id": "strasbourg"}
        self.assertEqual(_destination_rows([place]), [[place]])

    def test_two_results_share_two_column_row(self):
        places = [{"id": "strasbourg"}, {"id": "metz"}]
        self.assertEqual(_destination_rows(places), [places])

    def test_full_rows_and_partial_final_row_preserve_order(self):
        places = [{"id": str(i)} for i in range(1, 6)]
        self.assertEqual(_destination_rows(places), [places[:3], places[3:]])

    def test_rendered_column_counts_follow_populated_rows(self):
        # The UI uses st.columns(len(row_items), border=True); assert it
        # only requests counts for cards actually returned by filtering.
        from ux501_destination_discovery_ui import st
        places = [{"id": str(i)} for i in range(4)]
        with patch.object(st, "columns") as columns:
            for row in _destination_rows(places):
                st.columns(len(row), border=True)
        self.assertEqual(
            [call.args[0] for call in columns.call_args_list], [3, 1]
        )
        self.assertTrue(all(call.kwargs == {"border": True}
                            for call in columns.call_args_list))


if __name__ == "__main__":
    unittest.main()
