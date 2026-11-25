"""Focused cards must not introduce a second plan writer."""
import unittest
from datetime import date
from ux129_visit_focus import visible_visits,_dirty,DRAFTS


class VisitFocusTests(unittest.TestCase):
    def test_deep_link_stays_visible(self):
        rows=[{"id":str(i)} for i in range(30)]
        self.assertEqual(len(visible_visits(rows,14,"25")),15)
        self.assertEqual(visible_visits(rows,14,"25")[-1]["id"],"25")
        self.assertEqual(len(visible_visits(rows,14,"3")),14)
        self.assertEqual(visible_visits(rows,14,"unknown"),rows[:14])

    def test_only_real_draft_changes_require_confirmation(self):
        row={"id":"colmar","period":"Ainda não definido","exact_dates":[]}
        state={DRAFTS:{("França","colmar"):{"flow_organize_date_França":date(2027,10,1)}}}
        self.assertFalse(_dirty(state,row,"França"))
        state[DRAFTS][("França","colmar")]["date_changed"]=True
        self.assertTrue(_dirty(state,row,"França"))
        row["exact_dates"]=["2027-10-01"]
        self.assertFalse(_dirty(state,row,"França"))
        state[DRAFTS][("França","colmar")]["flow_organize_period"]="Férias restantes"
        self.assertTrue(_dirty(state,row,"França"))
