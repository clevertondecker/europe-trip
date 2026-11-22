"""UX 7.7 — choose multiple wishlist destinations without assigning days."""
import unittest
from copy import deepcopy
from unittest.mock import patch

from itinerary_flow_model import (
    FRANCE_STAGE, ITALY_STAGE, UNASSIGNED,
    add_undated_choices, selected_rows_for_stage,
)
from trip_plan_model import new_plan, validate_plan


class BulkUndatedItineraryTests(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan()
        self.catalog={
            "destinations":[{"id":"colmar","name":"Colmar"},
                            {"id":"basel","name":"Basel"},
                            {"id":"obernai","name":"Obernai"}],
            "attractions":[{"id":"colmar_oldtown","name":"Centro histórico",
                            "destination_id":"colmar"}],
        }

    def test_three_destinations_added_in_one_revision_without_dates_or_tickets(self):
        original=deepcopy(self.plan)
        updated=add_undated_choices(self.plan,self.catalog,
                                    ["colmar","basel","obernai"],FRANCE_STAGE)
        validate_plan(updated)
        self.assertEqual(updated["revision"],original["revision"]+1)
        self.assertEqual(updated["assignments"],{})
        self.assertEqual(updated["packages"],{})
        rows=selected_rows_for_stage(updated,self.catalog,FRANCE_STAGE)
        self.assertEqual({r["id"] for r in rows},{"colmar","basel","obernai"})
        self.assertTrue(all(r["period"]==UNASSIGNED and
                            r["attractions"]==[] and not r["exact_dates"] for r in rows))
        self.assertEqual(self.plan,original)

    def test_mixed_valid_and_invalid_selection_is_atomic(self):
        original=deepcopy(self.plan)
        with self.assertRaises(ValueError):
            add_undated_choices(self.plan,self.catalog,
                                ["colmar","not-in-catalog"],FRANCE_STAGE)
        self.assertEqual(self.plan,original)

    def test_duplicates_and_already_confirmed_cities_are_rejected(self):
        for ids in (["colmar","colmar"],[],["colmar"]*51):
            with self.subTest(ids=ids[:3]),self.assertRaises(ValueError):
                add_undated_choices(self.plan,self.catalog,ids,FRANCE_STAGE)
        confirmed=add_undated_choices(self.plan,self.catalog,["colmar"],FRANCE_STAGE)
        with self.assertRaisesRegex(ValueError,"já está"):
            add_undated_choices(confirmed,self.catalog,["colmar","basel"],FRANCE_STAGE)

    def test_stage_mismatch_does_not_mutate(self):
        original=deepcopy(self.plan)
        with self.assertRaisesRegex(ValueError,"etapa"):
            add_undated_choices(self.plan,self.catalog,["colmar"],ITALY_STAGE)
        self.assertEqual(self.plan,original)

    @patch("planning_session._commit")
    @patch("planning_session.load_attractions")
    @patch("planning_session.bootstrap")
    def test_session_uses_single_commit_after_confirmation(self, bootstrap, catalog, commit):
        from planning_session import commit_undated_destinations
        bootstrap.return_value=self.plan
        catalog.return_value=self.catalog
        with self.assertRaisesRegex(ValueError,"Confirme"):
            commit_undated_destinations(["colmar","basel"],FRANCE_STAGE)
        commit.assert_not_called()
        commit_undated_destinations(["colmar","basel"],FRANCE_STAGE,confirmed=True)
        commit.assert_called_once()
        draft=commit.call_args.args[0]
        self.assertEqual(draft["revision"],self.plan["revision"]+1)
        self.assertEqual(len(selected_rows_for_stage(draft,self.catalog,FRANCE_STAGE)),2)


if __name__=="__main__":
    unittest.main()
