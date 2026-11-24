"""UX126 acceptance tests for canonical identity and public itinerary inventory."""
import unittest
from copy import deepcopy

from attractions_model import load_attractions
from destination_identity import canonical_destination_id
from itinerary_eligibility import itinerary_eligibility
from itinerary_flow_model import destinations, selected_rows, is_selected, FRANCE_STAGE
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests, validate_interests
from evidence_query_model import get_rail_evidence


class EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_attractions()
        cls.discovery = build_exploration_discovery()

    def test_aliases(self):
        for key in ("luxembourg_city", "luxemburgo", "luxembourg"):
            self.assertEqual(canonical_destination_id(key), "luxembourg")
            self.assertEqual(itinerary_eligibility(key, self.catalog)["status"], "eligible")

    def test_inventory_parity(self):
        ids = [row["id"] for row in self.discovery["destinations"]]
        self.assertEqual(ids, [canonical_destination_id(key) for key in ids])
        self.assertEqual(len(ids), len(set(ids)))
        for row in destinations(self.catalog):
            if row["stage"] == FRANCE_STAGE:
                self.assertEqual(ids.count(canonical_destination_id(row["id"])), 1)
        for key in ("luxembourg", "obernai", "lucerne"):
            self.assertIn(key, ids)

    def test_statuses_are_pure(self):
        before = deepcopy(self.catalog)
        self.assertEqual(itinerary_eligibility("colmar", self.catalog)["status"], "eligible")
        aachen = itinerary_eligibility("aachen", self.catalog)
        self.assertEqual(aachen["status"], "research_only")
        self.assertTrue(aachen["reason"])
        self.assertEqual(itinerary_eligibility("roma", self.catalog)["status"], "other_stage")
        self.assertEqual(before, self.catalog)

    def test_legacy_wishes_and_visits_remain_readable(self):
        for key in ("luxembourg_city", "luxemburgo", "luxembourg"):
            doc = empty_interests()
            doc["items"] = [{"destination_id": key, "priority": "interested"}]
            original = deepcopy(doc)
            self.assertEqual(validate_interests(doc, self.discovery)["items"][0]["destination_id"], "luxembourg")
            self.assertEqual(doc, original)
            plan = new_plan()
            plan["flexible_visits"] = [{"destination_id": key, "stage": FRANCE_STAGE,
                "attractions": [], "period": "Ainda não definido"}]
            original = deepcopy(plan)
            self.assertTrue(is_selected(plan, "luxembourg"))
            self.assertEqual(selected_rows(plan, self.catalog)[0]["id"], "luxembourg")
            self.assertEqual(plan, original)

    def test_rail_evidence_preserved(self):
        expected = get_rail_evidence("metz", "luxembourg_city")
        self.assertIsNotNone(expected["minimum_oneway_min"])
        self.assertEqual(expected, get_rail_evidence("metz", "luxembourg"))
        self.assertEqual(expected, get_rail_evidence("metz", "luxemburgo"))


class DiscoveryAppTests(unittest.TestCase):
    def test_card_action_and_filter(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        root = Path(__file__).resolve().parents[1]
        app = AppTest.from_file(str(root / "app.py"), default_timeout=120).run()
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        app.text_input(key="ux501_search").set_value("Aachen").run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertNotIn("ux126_add_aachen", {x.key for x in app.button})
        self.assertTrue(any("Em pesquisa" in x.value for x in app.caption))
        self.assertTrue(any("ainda não foram catalogadas" in x.value for x in app.caption))
        app.radio(key="ux126_eligibility_filter").set_value("Posso planejar agora").run()
        self.assertNotIn("ux502_add_aachen", {x.key for x in app.button})
        app.text_input(key="ux501_search").set_value("Colmar").run()
        app.button(key="ux126_add_colmar").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertTrue(is_selected(app.session_state["advisor_plan"], "colmar"))
        self.assertIn("ux126_organize_colmar", {x.key for x in app.button})
        app.button(key="ux126_organize_colmar").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertEqual(app.session_state["ux64_public_task"], "Organizar")
        self.assertEqual(app.session_state["flow_organize_destination"], "colmar")
        self.assertEqual(app.session_state["flow_active_stage"], FRANCE_STAGE)
        self.assertTrue(is_selected(app.session_state["advisor_plan"], "colmar"))


class AliasWriterTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_attractions()
        self.plan = new_plan()

    def test_conflicting_packages_fail_without_loss(self):
        ids = [a["id"] for a in self.catalog["attractions"] if a["destination_id"] == "luxembourg"]
        self.plan["packages"] = {"luxembourg_city": ids[:1], "luxembourg": ids[1:2]}
        before = deepcopy(self.plan)
        from trip_plan_model import validate_plan
        from itinerary_flow_model import upsert_choice
        for action in (lambda: validate_plan(self.plan),
                       lambda: selected_rows(self.plan, self.catalog),
                       lambda: upsert_choice(self.plan, self.catalog, "luxembourg", [], "Ainda não definido")):
            with self.assertRaisesRegex(ValueError, "conflitantes"):
                action()
        self.assertEqual(self.plan, before)

    def test_edit_schedule_remove_old_key(self):
        from itinerary_flow_model import upsert_choice, remove_choice, UNASSIGNED
        from planning_store import add_assignment
        from calendar_model import calendar_plan
        from datetime import date
        from ux48_weekend_groups_model import empty_groups, create_group, validate_groups
        self.plan["flexible_visits"] = [{"destination_id": "luxembourg_city", "stage": FRANCE_STAGE,
                                        "attractions": [], "period": UNASSIGNED}]
        before = deepcopy(self.plan)
        ids = [a["id"] for a in self.catalog["attractions"] if a["destination_id"] == "luxembourg"]
        updated = upsert_choice(self.plan, self.catalog, "luxembourg", ids[:1], UNASSIGNED)
        self.assertEqual(updated["packages"], {"luxembourg_city": ids[:1]})
        days = calendar_plan(date.fromisoformat(updated["departure_date"]), updated["total_days"],
                             updated["italy_days"], updated["vacation_days"], updated["setup_days"])
        day = next(d["date"] for d in days if d["stage"] == FRANCE_STAGE and
                   d["activity"] != "Instalação" and "Trabalho remoto" not in d["activity"])
        updated = add_assignment(updated, day, "luxemburgo")
        self.assertEqual(updated["assignments"][day], "luxembourg_city")
        self.assertEqual(add_assignment(updated, day, "luxembourg"), updated)
        groups = create_group(empty_groups(updated), updated, self.catalog, name="Luxemburgo",
                              destinations=["luxembourg_city"])
        self.assertEqual(validate_groups(groups, updated, self.catalog), groups)
        removed = remove_choice(updated, self.catalog, "luxembourg")
        self.assertEqual(removed["packages"], {})
        self.assertEqual(removed["assignments"], {})
        self.assertEqual(removed["flexible_visits"], [])
        self.assertEqual(self.plan, before)

    def test_italian_eligibility_returns_actual_writer_id(self):
        from itinerary_flow_model import ITALY_STAGE, UNASSIGNED, upsert_choice
        for place, expected in (("roma", "italy_rome"), ("naples", "italy_naples")):
            result = itinerary_eligibility(place, self.catalog, ITALY_STAGE)
            self.assertEqual(result["status"], "eligible")
            self.assertEqual(result["outing_id"], expected)
            plan = upsert_choice(self.plan, self.catalog, place, [], UNASSIGNED)
            self.assertEqual(plan["flexible_visits"][0]["destination_id"], expected)

    def test_batch_alias_collision_rejected(self):
        from itinerary_flow_model import add_undated_choices
        before = deepcopy(self.plan)
        with self.assertRaises(ValueError):
            add_undated_choices(self.plan, self.catalog, ["luxembourg", "luxembourg_city"], FRANCE_STAGE)
        self.assertEqual(self.plan, before)
