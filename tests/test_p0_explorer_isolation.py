"""P0 regression: simulated explorer must never mutate canonical planning."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from trip_plan_model import new_plan
from attractions_model import load_attractions
from planning_store import summary
import explorer_mutation_guard as guard


class ExplorerGuardTests(unittest.TestCase):
    def setUp(self):
        self.plan = new_plan()
        self.base = self.plan["base_city"]
        self.other = next(x for x in ("mulhouse", "strasbourg", "metz", "nancy")
                          if x != self.base)
        catalog = load_attractions()
        self.attraction = next(a for a in catalog["attractions"]
                               if a["destination_id"] == "strasbourg")

    def test_simulation_blocks_every_mutation_even_direct_handler_calls(self):
        original = deepcopy(self.plan)
        with patch.object(guard, "active_plan", return_value=self.plan):
            for invoke in (
                lambda: guard.save_outing(self.other, "Oficial", "strasbourg", [self.attraction["id"]]),
                lambda: guard.remove_outing(self.other, "Oficial", "strasbourg"),
                lambda: guard.change_interest(self.other, "Oficial", self.attraction["id"], "Quero visitar"),
                lambda: guard.schedule_outing(self.other, "Oficial", "2027-09-25", "strasbourg"),
                lambda: guard.unschedule_outing(self.other, "Oficial", "2027-09-25"),
                lambda: guard.save_outing(self.base, "Simulação", "strasbourg", [self.attraction["id"]]),
                lambda: guard.remove_outing(self.base, "Simulação", "strasbourg"),
                lambda: guard.change_interest(self.base, "Simulação", self.attraction["id"], "Descartar"),
                lambda: guard.schedule_outing(self.base, "Simulação", "2027-09-25", "strasbourg"),
                lambda: guard.unschedule_outing(self.base, "Simulação", "2027-09-25"),
            ):
                with self.assertRaises(guard.SimulationWriteBlocked):
                    invoke()
        self.assertEqual(self.plan, original)
        self.assertEqual(self.plan["revision"], original["revision"])

    def test_active_handler_uses_existing_continuous_itinerary_operation(self):
        with patch.object(guard, "active_plan", return_value=self.plan), patch.object(
            guard, "upsert_flexible_choice"
        ) as operation:
            guard.save_outing(self.base, "Oficial", "strasbourg", [self.attraction["id"]])
            operation.assert_called_once_with(
                "strasbourg", [self.attraction["id"]], "Ainda não definido"
            )

    def test_active_delete_preference_schedule_use_canonical_handlers(self):
        with patch.object(guard, "active_plan", return_value=self.plan), patch.object(
            guard, "remove_flexible_choice"
        ) as remove, patch.object(guard, "update_interest") as preference, patch.object(
            guard, "schedule_package"
        ) as schedule, patch.object(guard, "unschedule_package") as unschedule:
            guard.remove_outing(self.base, "Oficial", "strasbourg")
            guard.change_interest(self.base, "Oficial", self.attraction["id"], "Descartar")
            guard.schedule_outing(self.base, "Oficial", "2027-09-25", "strasbourg")
            guard.unschedule_outing(self.base, "Oficial", "2027-09-25")
        remove.assert_called_once()
        preference.assert_called_once()
        schedule.assert_called_once()
        unschedule.assert_called_once()

    def test_financial_summary_ignores_simulation(self):
        before = summary(self.plan)
        with patch.object(guard, "active_plan", return_value=self.plan):
            with self.assertRaises(guard.SimulationWriteBlocked):
                guard.save_outing(self.other, "Oficial", "strasbourg", [self.attraction["id"]])
        self.assertEqual(before, summary(self.plan))

    def test_modal_is_contextual_and_old_bottom_editor_removed(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        explorer = (root / "attractions_ui.py").read_text()
        modal = (root / "explorer_dialog_ui.py").read_text()
        self.assertIn("render_attraction_dialog(chosen,base", explorer)
        self.assertIn("@st.dialog", modal)
        self.assertIn('f"Montar passeio em', modal)
        self.assertNotIn("Atrações em {escape(d['name'])}", explorer)
        self.assertIn("explore_close_", modal)


if __name__ == "__main__":
    unittest.main()
