"""UX 6.1 read-only destination board contract."""
import unittest
from copy import deepcopy
from ux61_destination_board_model import build_destination_board, board_metrics
from ux502_destination_interests_model import empty_interests
from trip_plan_model import new_plan


class BoardProjectionTests(unittest.TestCase):
    def setUp(self):
        self.discovery = {"destinations": [
            {"id": "colmar", "name": "Colmar", "country": "França"},
            {"id": "obernai", "name": "Obernai", "country": "França"},
            {"id": "basel", "name": "Basel", "country": "Suíça"}]}
        self.catalog = {"destinations": [
            {"id": "colmar", "name": "Colmar"}],
            "attractions": [{"id": "colmar_oldtown", "name": "Centro histórico",
                            "destination_id": "colmar"}]}
        self.plan = new_plan()
        self.interests = empty_interests()
        self.interests["items"] = [
            {"destination_id": "colmar", "priority": "must_visit"},
            {"destination_id": "obernai", "priority": "interested"},
            {"destination_id": "basel", "priority": "maybe"}]

    def test_wishlist_only_has_zero_confirmed_visits(self):
        before = deepcopy(self.plan)
        wishes = deepcopy(self.interests)
        result = build_destination_board(self.interests, self.plan,
                                         self.discovery, self.catalog)
        self.assertEqual(board_metrics(result)["wished"], 3)
        self.assertEqual(board_metrics(result)["planned"], 0)
        self.assertEqual({x["id"] for x in result}, {"colmar", "obernai", "basel"})
        self.assertEqual(self.plan, before)
        self.assertEqual(self.interests, wishes)

    def test_selected_visit_is_not_duplicate_and_group_without_date_is_not_organized(self):
        self.plan["packages"] = {"colmar": ["colmar_oldtown"]}
        self.plan["flexible_visits"] = [{
            "destination_id": "colmar", "stage": "França",
            "attractions": ["colmar_oldtown"], "period": "Ainda não definido"}]
        groups = {"groups": [{"destinations": ["colmar"],
                             "start_date": None, "period": "Ainda não definido"}]}
        result = build_destination_board(self.interests, self.plan, self.discovery,
                                         self.catalog, groups)
        self.assertEqual(len(result), 3)
        self.assertTrue(result[0]["in_group"])
        self.assertFalse(result[0]["organized"])
        self.assertEqual(board_metrics(result)["planned"], 1)
        self.assertEqual(board_metrics(result)["organized"], 0)

    def test_removing_interest_does_not_remove_visit(self):
        self.plan["packages"] = {"colmar": ["colmar_oldtown"]}
        self.interests["items"] = [
            row for row in self.interests["items"] if row["destination_id"] != "colmar"]
        result = build_destination_board(self.interests, self.plan, self.discovery,
                                         self.catalog)
        colmar = next(row for row in result if row["id"] == "colmar")
        self.assertTrue(colmar["planned"])
        self.assertFalse(colmar["wanted"])


if __name__ == "__main__":
    unittest.main()
