"""UX 6.2: canonical city inclusion with zero selected attractions."""
import unittest
from copy import deepcopy
from datetime import date

from trip_plan_model import new_plan, validate_plan
from attractions_model import load_attractions, load_base_routes, package_cost
from itinerary_flow_model import (
    get_choice, selected_rows, validate_flow_backup, schedule_italy_day,
)
from ux45_outing_contract import apply_outing, remove_outing
from planning_store import add_assignment, remove_assignment, summary
from calendar_model import calendar_plan
from ux48_weekend_groups_model import empty_groups, create_group
from continuity_archive_model import make_archive, export_archive, import_archive


class CityWithoutAttractionsTests(unittest.TestCase):
    def setUp(self):
        self.plan = new_plan()
        self.catalog = load_attractions()

    def french_day(self):
        days = calendar_plan(
            date.fromisoformat(self.plan["departure_date"]),
            self.plan["total_days"], self.plan["italy_days"],
            self.plan["vacation_days"], self.plan["setup_days"])
        return next(d["date"] for d in days if d["stage"] == "França"
                    and d["activity"] != "Instalação" and
                    "Trabalho remoto" not in d["activity"])

    def test_supplemental_obernai_without_attractions_can_schedule_and_restore(self):
        self.assertEqual(get_choice(self.catalog, "obernai")["name"], "Obernai")
        plan, result = apply_outing(self.plan, self.catalog, "obernai", [],
                                    confirmed=True)
        self.assertEqual(result.attraction_count, 0)
        self.assertIn("obernai", {r["id"] for r in selected_rows(plan, self.catalog)})
        self.assertNotIn("obernai", plan["packages"])
        day = self.french_day()
        dated = add_assignment(plan, day, "obernai")
        validate_flow_backup(dated, self.catalog)
        self.assertEqual(dated["assignments"][day], "obernai")
        group = create_group(empty_groups(dated), dated, self.catalog,
                             name="Suíça / Alsácia", destinations=["obernai"])
        archive = make_archive(dated, self.catalog, weekend_groups=group)
        recovered = import_archive(export_archive(archive, self.catalog),
                                   self.catalog)
        self.assertEqual(recovered["plan"]["assignments"][day], "obernai")
        self.assertEqual(recovered["plan"]["flexible_visits"][0]["attractions"], [])
        self.assertEqual(recovered["weekend_groups"]["groups"][0]["destinations"],
                         ["obernai"])
        cleaned = remove_assignment(recovered["plan"], day)
        removed, _ = remove_outing(cleaned, self.catalog, "obernai", confirmed=True)
        self.assertNotIn("obernai", {r["id"] for r in selected_rows(removed, self.catalog)})

    def test_selecting_and_removing_supplemental_attractions_preserves_date(self):
        empty, _ = apply_outing(self.plan, self.catalog, "obernai", [], confirmed=True)
        day = self.french_day()
        dated = add_assignment(empty, day, "obernai")
        changed, _ = apply_outing(dated, self.catalog, "obernai",
                                  ["obernai_market"], confirmed=True)
        self.assertEqual(changed["packages"]["obernai"], ["obernai_market"])
        self.assertEqual(changed["assignments"][day], "obernai")
        reset, _ = apply_outing(changed, self.catalog, "obernai", [], confirmed=True)
        self.assertNotIn("obernai", reset["packages"])
        self.assertEqual(reset["assignments"][day], "obernai")
        validate_flow_backup(reset, self.catalog)

    def test_costs_for_unpriced_city_are_missing_not_zero(self):
        costs = package_cost(self.catalog, load_base_routes(),
                             self.plan["base_city"], [],
                             planned_destination_ids=["obernai"])
        self.assertFalse(costs["complete"])
        self.assertTrue(any("Transporte" in x for x in costs["missing"]))
        self.assertTrue(any("Atividades" in x for x in costs["missing"]))
        self.assertEqual(costs["selected_count"], 0)

    def test_legacy_package_only_remains_visible_and_valid(self):
        dest = self.catalog["attractions"][0]["destination_id"]
        attr = self.catalog["attractions"][0]["id"]
        legacy = deepcopy(self.plan)
        legacy["packages"] = {dest: [attr]}
        validate_plan(legacy)
        self.assertIn(dest, {r["id"] for r in selected_rows(legacy, self.catalog)})
        validate_flow_backup(legacy, self.catalog)
        self.assertEqual(summary(legacy)["destinations"], 1)

    def test_italy_without_attractions_remains_separate(self):
        from itinerary_flow_model import italian_catalog
        italy = italian_catalog()[0]["id"]
        created, _ = apply_outing(self.plan, self.catalog, italy, [], confirmed=True)
        scheduled = schedule_italy_day(created, self.catalog, italy,
                                       created["departure_date"])
        self.assertEqual(scheduled["flexible_visits"][0]["exact_date"],
                         created["departure_date"])
        self.assertFalse(scheduled["packages"])
        validate_flow_backup(scheduled, self.catalog)


if __name__ == "__main__":
    unittest.main()
