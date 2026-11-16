"""UX 3.7: concrete next steps, no hidden writes or duplicate rail research."""
import unittest
from copy import deepcopy

from attractions_model import load_attractions
from trip_plan_model import new_plan
from ux37_next_actions_model import next_actions


def evidence_for(destination: str) -> dict:
    return {"items": [
        {"destination_id": destination, "category": "intercity_return",
         "amount": None, "source_url": None},
        {"destination_id": destination, "category": "local_transport",
         "amount": None, "source_url": None},
        {"destination_id": destination, "category": "dining",
         "amount": None, "source_url": None},
    ]}


class ContextualActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_attractions()
        cls.strasbourg = next(
            a["id"] for a in cls.catalog["attractions"]
            if a["destination_id"] == "strasbourg"
        )

    def test_empty_plan_has_real_start_action(self):
        plan = new_plan()
        before = deepcopy(plan)
        actions = next_actions(plan, self.catalog, {"items": []})
        self.assertIn("start", [x["id"] for x in actions])
        self.assertEqual(before, plan)

    def test_one_destination_has_only_one_return_action(self):
        plan = new_plan()
        plan["packages"]["strasbourg"] = [self.strasbourg]
        before = deepcopy(plan)
        actions = next_actions(plan, self.catalog, evidence_for("strasbourg"), limit=15)
        self.assertEqual(1, len([x for x in actions if x["id"] == "return:strasbourg"]))
        self.assertEqual(1, len([x for x in actions if x["id"] == "cost:strasbourg"]))
        self.assertEqual(before, plan)
        self.assertEqual(before["revision"], plan["revision"])

    def test_missing_route_never_described_as_impossible_or_free(self):
        plan = new_plan()
        plan["packages"]["strasbourg"] = [self.strasbourg]
        actions = next_actions(plan, self.catalog, evidence_for("strasbourg"))
        string = " ".join(x["detail"] for x in actions).lower()
        self.assertIn("ausência de pesquisa", string)
        self.assertNotIn("impossível", string)
        self.assertNotIn("gratuito", string)

    def test_never_introduces_new_source_of_financial_truth(self):
        plan = new_plan()
        plan["packages"]["strasbourg"] = [self.strasbourg]
        actions = next_actions(plan, self.catalog, evidence_for("strasbourg"), limit=20)
        self.assertFalse(any("amount" in x or "total" in x for x in actions))
        self.assertLessEqual(len(next_actions(plan, self.catalog, evidence_for("strasbourg"))), 4)

    def test_actions_have_valid_existing_navigation(self):
        from ux_navigation import SECTIONS
        plan = new_plan()
        plan["packages"]["strasbourg"] = [self.strasbourg]
        actions = next_actions(plan, self.catalog, evidence_for("strasbourg"), limit=20)
        self.assertTrue(all(x["section"] in SECTIONS[x["area"]] for x in actions))


if __name__ == "__main__":
    unittest.main()
