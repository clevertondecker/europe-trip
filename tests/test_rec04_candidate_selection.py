"""REC04: explicit candidate selection must not silently fall back to official base."""
from unittest import TestCase
from unittest.mock import patch

import exploratory_selection as selection


class CandidateSelectionTests(TestCase):
    def test_candidate_selection_preserves_exploratory_state(self):
        state = {"city_widget": "angers"}
        options = [{"id": "mulhouse"}, {"id": "angers"}]
        with patch.object(selection.st, "session_state", state), \
             patch.object(selection, "base_options", return_value=options) as catalog:
            selection.set_city_from_widget("city_widget")
        catalog.assert_called_once_with(include_candidates=True)
        self.assertEqual(state["scenario_base_selected"], "angers")
        self.assertEqual(state["scenario_sidebar"], "angers")
        self.assertEqual(state["ux_last_candidate"], "angers")
        self.assertEqual(state["ux_pending_mode"], "Simulação")

    def test_invalid_selection_fails_without_mutating_state(self):
        state = {"city_widget": "invalid", "scenario_base_selected": "mulhouse"}
        with patch.object(selection.st, "session_state", state), \
             patch.object(selection, "base_options", return_value=[{"id": "mulhouse"}]):
            with self.assertRaises(ValueError):
                selection.set_city_from_widget("city_widget")
        self.assertEqual(state["scenario_base_selected"], "mulhouse")
        self.assertNotIn("ux_pending_mode", state)
