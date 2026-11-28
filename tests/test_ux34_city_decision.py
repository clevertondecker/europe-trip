"""UX 3.4 decision simulator: fixed assumptions, no fake lost trips or savings."""
import unittest
from tests.nav_helpers import open_public
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from trip_plan_model import new_plan
from data_model import load_data
from planning_workflow_model import approve_settings
from city_decision_model import (
    compare_city_decisions,review_base_application,shared_destinations,
)
from city_decision_store import (
    make_city_draft,export_city_draft,import_city_draft,
)

ROOT=Path(__file__).resolve().parents[1]


class DecisionModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_data()

    def study(self,plan=None,alternatives=None,dests=None,rents=None,days=60):
        plan=plan or new_plan()
        return compare_city_decisions(
            plan, alternatives or ["offenburg","strasbourg"],
            dests or ["strasbourg","colmar"],
            rents if rents is not None else {
                plan["base_city"]:None,
                **{candidate:None for candidate in
                   (alternatives or ["offenburg","strasbourg"])}},
            self.data,False,days,6.3,
        )

    def test_two_candidates_plus_current_only_and_no_mutation(self):
        plan=new_plan()
        plan["packages"]={"colmar":["colmar_old_marker"]}
        original=deepcopy(plan)
        result=self.study(plan)
        self.assertEqual(plan,original)
        self.assertEqual(result["official_base"],"mulhouse")
        self.assertEqual(len(result["candidates"]),2)
        self.assertIsNone(result["winner"])
        self.assertFalse(result["comparable_2027_totals"])
        self.assertEqual(result["destinations"],["strasbourg","colmar"])
        self.assertIn("colmar",shared_destinations(plan))
        by={r["id"]:r for r in result["candidates"]}
        self.assertFalse(by["offenburg"]["official_supported"])
        self.assertTrue(by["strasbourg"]["official_supported"])
        self.assertEqual(by["offenburg"]["routes"][0]["official_minutes"],49)
        self.assertEqual(by["offenburg"]["routes"][0]["candidate_minutes"],25)
        self.assertEqual(by["offenburg"]["changes"]["Melhorou"],1)
        self.assertEqual(sum(by["offenburg"]["changes"].values()),2)
        self.assertEqual(by["offenburg"]["paired_route_times"],sum(r["delta_minutes"] is not None for r in by["offenburg"]["routes"]))
        self.assertEqual(by["offenburg"]["lost_destinations"],[])
        self.assertFalse(by["offenburg"]["total_difference_known"])

    def test_unknown_rents_remain_null_even_when_routes_have_fares(self):
        result=self.study()
        for candidate in result["candidates"]:
            self.assertIsNone(candidate["financial_delta_brl"])
            self.assertIsNone(candidate["housing_whatif"]["official_total_brl"])
            self.assertEqual(candidate["missing"][0],
                             "Ida e volta real para os mesmos passeios")

    def test_only_housing_delta_is_comparable_given_two_manual_rents(self):
        result=self.study(alternatives=["offenburg"],
                          rents={"mulhouse":1400.,"offenburg":1100.})
        delta=result["candidates"][0]["financial_delta_brl"]
        self.assertEqual(delta,-3780.)
        self.assertFalse(result["candidates"][0]["total_difference_known"])
        base=result["candidates"][0]["housing_whatif"]
        self.assertEqual(
            round(base["candidate_total_brl"]-base["official_total_brl"],2),
            delta)
        self.assertFalse(result["candidates"][0]["return_or_hotel_verified"])

    def test_studies_do_not_infer_inaccessible_destinations_or_overnights(self):
        result=self.study(alternatives=["dijon"],dests=["basel"])
        row=result["candidates"][0]
        self.assertEqual(row["lost_destinations"],[])
        self.assertEqual(row["new_destinations_confirmed"],[])
        self.assertEqual(row["paired_route_times"],sum(r["delta_minutes"] is not None for r in row["routes"]))
        self.assertFalse(row["return_or_hotel_verified"])

    def test_invalid_research_inputs_rejected_without_change(self):
        plan=new_plan()
        original=deepcopy(plan)
        for other,dests,rents in [
            (["mulhouse"],["strasbourg"],{}),
            (["offenburg","offenburg"],["strasbourg"],{}),
            (["offenburg","strasbourg","metz"],["strasbourg"],{}),
            (["offenburg"],["unknown_city"],{}),
            (["offenburg"],["strasbourg","strasbourg"],{}),
            (["offenburg"],["strasbourg"],{"offenburg":-200.}),
        ]:
            with self.subTest(other=other,dests=dests,rents=rents):
                with self.assertRaises(ValueError):
                    compare_city_decisions(
                        plan,other,dests,rents,self.data,False,60,6.3)
        self.assertEqual(plan,original)

    def test_explicit_review_only_four_supported_bases(self):
        plan=new_plan()
        result=self.study(plan)
        before=deepcopy(plan)
        with self.assertRaises(ValueError):
            review_base_application(plan,result,"offenburg")
        review=review_base_application(plan,result,"strasbourg")
        self.assertEqual(plan,before)
        self.assertEqual(approve_settings(plan,review),before)
        applied=approve_settings(plan,review,confirmed=True)
        self.assertEqual(applied["base_city"],"strasbourg")
        self.assertEqual(applied["revision"],plan["revision"]+1)
        self.assertEqual(before,plan)
        with self.assertRaises(ValueError):
            review_base_application(applied,result,"strasbourg")


class DecisionDraftTests(unittest.TestCase):
    def test_portable_study_roundtrip_is_not_trip_plan(self):
        plan=new_plan()
        study=compare_city_decisions(
            plan,["offenburg"],["strasbourg"],
            {"mulhouse":None,"offenburg":1250.},load_data(),False,60,6.3)
        draft=make_city_draft("Meu teste",study,"Verificar aluguel real")
        content=export_city_draft(draft)
        restored=import_city_draft(content)
        self.assertEqual(restored,draft)
        self.assertEqual(restored["status"],"exploratory_only")
        self.assertNotIn("assignments",restored)
        self.assertNotIn("packages",restored)
        self.assertEqual(restored["rents_eur_month"]["mulhouse"],None)
        self.assertEqual(plan["revision"],0)

    def test_import_rejects_bad_schema_and_unsafe_values(self):
        with self.assertRaises(ValueError):
            import_city_draft(b"{bad json")
        with self.assertRaises(ValueError):
            import_city_draft(b"x"*(65536+1))
        plan=new_plan()
        result=compare_city_decisions(plan,["offenburg"],["colmar"],
               {},load_data(),False,60,6.3)
        draft=make_city_draft("Prova",result)
        draft["alternatives"]=["mulhouse"]
        with self.assertRaises(ValueError):
            export_city_draft(draft)


class DecisionUITests(unittest.TestCase):
    def test_two_city_simulation_never_changes_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        open_public(app,"Explorar","Comparar bases")
        app.button(key="ux125b_open_base_studies").click().run()
        app.segmented_control(key="ux_compare_mode").set_value("Estudos de troca").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux34_candidates",{x.key for x in app.multiselect})
        self.assertIn("ux34_destinations",{x.key for x in app.multiselect})
        app.multiselect(key="ux34_candidates").set_value(
            ["offenburg","strasbourg"]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.number_input(key="ux34_rent_mulhouse").set_value(1400.).run()
        app.number_input(key="ux34_rent_offenburg").set_value(1100.).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertIn("ux34_save_draft",{x.key for x in app.button})
        app.button(key="ux34_save_draft").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(app.session_state["ux34_drafts"])
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_review_and_reject_before_official_change(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        original=deepcopy(app.session_state["advisor_plan"])
        open_public(app,"Explorar","Comparar bases")
        app.button(key="ux125b_open_base_studies").click().run()
        app.segmented_control(key="ux_compare_mode").set_value("Estudos de troca").run()
        app.multiselect(key="ux34_candidates").set_value(["strasbourg"]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.button(key="ux34_open_review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(app.button(key="ux34_confirm_apply").disabled)
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="ux34_cancel_review").click().run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="ux34_open_review").click().run()
        app.checkbox(key="ux34_apply_ack").check().run()
        self.assertFalse(app.button(key="ux34_confirm_apply").disabled)
        app.button(key="ux34_confirm_apply").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],
                         "strasbourg")
        self.assertEqual(app.session_state["advisor_plan"]["revision"],
                         original["revision"]+1)


if __name__=="__main__":
    unittest.main()
