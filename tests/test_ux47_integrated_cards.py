"""UX 4.7: one read-only destination card, one existing editor."""
import unittest
from copy import deepcopy
from pathlib import Path
from attractions_model import load_attractions,load_base_routes
from itinerary_flow_model import selected_rows
from trip_plan_model import new_plan
from ux47_destination_card_model import destination_card_view
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class IntegratedDestinationCardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.routes=load_base_routes()

    def _plan(self,destinations=("colmar",)):
        p=new_plan()
        for dest in destinations:
            ids=[a["id"] for a in self.catalog["attractions"]
                 if a["destination_id"]==dest]
            p["packages"][dest]=ids[:2]
        return p

    def test_card_read_only_and_unknown_not_free(self):
        p=self._plan(("colmar","strasbourg"))
        before=deepcopy(p)
        rows=selected_rows(p,self.catalog)
        for row in rows:
            if row["stage"]!="França":continue
            card=destination_card_view(p,self.catalog,self.routes,row)
            self.assertEqual(card["attraction_count"],2)
            self.assertTrue(card["photo"]["url"].startswith("https://"))
            self.assertFalse(card["reservation_confirmed"])
            self.assertFalse(card["cost_complete"])
            self.assertIn("Custo total ainda não confirmado",card["cost"])
        self.assertEqual(p,before)

    def test_period_date_and_credit_data(self):
        p=self._plan()
        p["assignments"]["2027-10-02"]="colmar"
        row=next(r for r in selected_rows(p,self.catalog) if r["id"]=="colmar")
        card=destination_card_view(p,self.catalog,self.routes,row)
        self.assertTrue(card["organized"])
        self.assertEqual(card["dates"],["2027-10-02"])
        self.assertTrue(card["photo"]["author"])
        self.assertTrue(card["photo"]["license"])

    def test_single_card_in_app_without_separate_gallery(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Meu planejamento").run()
        app.segmented_control(key="flow_active_stage").set_value("França").run()
        p=deepcopy(app.session_state["advisor_plan"])
        p["packages"]=self._plan(("colmar",))["packages"]
        p["assignments"]={}
        app.session_state["advisor_plan"]=p
        app.run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(len([b for b in app.button
                              if b.key=="flow_edit_save_colmar"]),1)
        self.assertFalse(any("Lugares que escolhemos" in m.value
                             for m in app.markdown))
        self.assertTrue(any("Colmar" in m.value for m in app.markdown))
        self.assertTrue(any("Custo total ainda não confirmado" in x.value
                             for x in app.caption))

    def test_multiple_destinations_one_editor_each(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Meu planejamento").run()
        app.segmented_control(key="flow_active_stage").set_value("França").run()
        p=deepcopy(app.session_state["advisor_plan"])
        p["packages"]=self._plan(("colmar","strasbourg"))["packages"]
        p["assignments"]={}
        app.session_state["advisor_plan"]=p
        app.run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        keys={b.key for b in app.button}
        self.assertIn("flow_edit_save_colmar",keys)
        self.assertIn("flow_edit_save_strasbourg",keys)

if __name__=="__main__":unittest.main()
