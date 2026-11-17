"""UX 4.7: one read-only destination card, one existing editor."""
import unittest
from copy import deepcopy
from pathlib import Path
from attractions_model import load_attractions,load_base_routes
from itinerary_flow_model import selected_rows
from trip_plan_model import new_plan
from ux47_destination_card_model import destination_card_view
from ux47_photo_ui import photo_markup,photo_credit,permitted_photo_url
from ux45_outing_contract import apply_outing,remove_outing
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

    def test_photo_aspect_fallback_and_untrusted_url(self):
        for name in ("Basel","Metz","Colmar"):
            photo=next(d["photo"] for d in self.catalog["destinations"]
                       if d["name"]==name)
            html=photo_markup(photo,name)
            self.assertIn("aspect-ratio:4/5",html)
            self.assertIn("max-height:365px",html)
            self.assertIn("Imagem indisponível",html)
            self.assertIn("background-image:url(",html)
            self.assertIn("Crédito da foto cadastrada:",photo_credit(photo))
        invalid={"url":"https://example.invalid/missing.jpg"}
        self.assertNotIn("background-image:url(",photo_markup(invalid,"Metz"))
        self.assertIsNone(photo_credit(invalid))
        self.assertIsNone(permitted_photo_url("javascript:alert(1)"))
        self.assertIsNone(permitted_photo_url("https://evil.example/image.jpg"))
        self.assertIn("Imagem indisponível",photo_markup(None,"Sem imagem"))

    def test_three_destinations_and_independent_canonical_edit_remove(self):
        p=self._plan(("basel","metz","colmar"))
        rows=[row for row in selected_rows(p,self.catalog)
              if row["stage"]=="França"]
        self.assertEqual(len(rows),3)
        self.assertEqual({r["id"] for r in rows},{"basel","metz","colmar"})
        all_cards=[destination_card_view(p,self.catalog,self.routes,row)
                   for row in rows]
        self.assertTrue(all(not c["reservation_confirmed"] for c in all_cards))
        original_metz=p["packages"]["metz"][:]
        extra=[a["id"] for a in self.catalog["attractions"]
               if a["destination_id"]=="basel"][2:3]
        new_basel=p["packages"]["basel"]+extra
        changed,outcome=apply_outing(p,self.catalog,"basel",new_basel,confirmed=True)
        self.assertEqual(outcome.action,"updated")
        self.assertEqual(changed["packages"]["metz"],original_metz)
        removed,removal=remove_outing(changed,self.catalog,"metz",confirmed=True)
        self.assertEqual(removal.action,"removed")
        self.assertEqual(set(removed["packages"]),{"basel","colmar"})
        self.assertEqual(removed["packages"]["basel"],new_basel)
        self.assertEqual(removed["packages"]["colmar"],p["packages"]["colmar"])

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
