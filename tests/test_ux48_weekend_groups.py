"""UX 4.8: weekend draft model, conflict validation and Streamlit smoke."""
import unittest
from copy import deepcopy
from json import loads
from streamlit.testing.v1 import AppTest
from pathlib import Path
from attractions_model import load_attractions
from trip_plan_model import new_plan
from ux45_outing_contract import apply_outing,remove_outing
from ux48_weekend_groups_model import (
    empty_groups,create_group,update_group,remove_group,
    reconcile_removed_outings,ungrouped_outings,
    available_weekends,set_rest_weekend,export_groups,import_groups,
)

ROOT=Path(__file__).resolve().parents[1]

class WeekendGroupModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()

    def setUp(self):
        self.plan=new_plan()
        for key in ("brussels","bruges_be","rotterdam"):
            ids=[a["id"] for a in self.catalog["attractions"]
                 if a["destination_id"]==key][:2]
            self.plan,_=apply_outing(self.plan,self.catalog,key,ids,confirmed=True)
        self.draft=empty_groups(self.plan)

    def test_group_single_and_two_destinations_order_without_duplicate_cost(self):
        groups=create_group(self.draft,self.plan,self.catalog,name="Bruxelas + Bruges",
                            destinations=["brussels","bruges_be"],
                            period="Férias restantes",nights=1,
                            notes="Retorno e hotel a pesquisar")
        g=groups["groups"][0]
        self.assertEqual(g["destinations"],["brussels","bruges_be"])
        self.assertIsNone(g["start_date"])
        self.assertEqual(g["nights"],1)
        self.assertEqual(g["status"],"estudo")
        self.assertEqual(self.plan["packages"]["brussels"],self.plan["packages"]["brussels"])
        self.assertEqual([r["id"] for r in ungrouped_outings(groups,self.plan,self.catalog)],
                         ["rotterdam"])
        self.assertTrue(all(r["group"] is None for r in
                            available_weekends(groups,self.plan,self.catalog)))
        another=create_group(groups,self.plan,self.catalog,name="Rotterdam",
                             destinations=["rotterdam"],status="planejado")
        self.assertEqual(len(another["groups"]),2)
        self.assertEqual(self.plan["assignments"],{})
        self.assertNotIn("weekend_groups",self.plan)

    def test_edit_order_name_and_unlink_preserves_canonical(self):
        groups=create_group(self.draft,self.plan,self.catalog,name="Original",
                            destinations=["brussels","bruges_be"])
        g=groups["groups"][0]
        new=update_group(groups,self.plan,self.catalog,g["id"],
                         name="Troquei a ordem",destinations=["bruges_be","brussels"],
                         period="Trabalho remoto · fim de semana",nights=1)
        self.assertEqual(new["groups"][0]["destinations"],["bruges_be","brussels"])
        reduced=update_group(new,self.plan,self.catalog,g["id"],
                             destinations=["brussels"])
        self.assertIn("bruges_be",self.plan["packages"])
        self.assertIn("bruges_be",[r["id"] for r in
                                  ungrouped_outings(reduced,self.plan,self.catalog)])
        deleted=remove_group(reduced,self.plan,self.catalog,g["id"])
        self.assertFalse(deleted["groups"])
        self.assertEqual(len(self.plan["packages"]),3)

    def test_weekend_dates_rest_conflict_and_assignment_conflict(self):
        saturday=next(r["start"] for r in
                      available_weekends(self.draft,self.plan,self.catalog)
                      if r["status"]=="livre · não reservado")
        g=create_group(self.draft,self.plan,self.catalog,name="Bélgica",
                       destinations=["brussels","bruges_be"],
                       start_date=saturday,nights=1)
        self.assertIn("pernoite",next(x["status"] for x in
                                     available_weekends(g,self.plan,self.catalog)
                                     if x["start"]==saturday))
        with self.assertRaises(ValueError):
            set_rest_weekend(g,self.plan,self.catalog,saturday,True)
        with self.assertRaises(ValueError):
            create_group(g,self.plan,self.catalog,name="Duplica",destinations=["brussels"])
        with self.assertRaises(ValueError):
            create_group(g,self.plan,self.catalog,name="Mesmo sábado",
                         destinations=["rotterdam"],start_date=saturday)
        plan=deepcopy(self.plan)
        plan["assignments"][saturday]="rotterdam"
        with self.assertRaises(ValueError):
            create_group(self.draft,plan,self.catalog,name="Bélgica",
                         destinations=["brussels","bruges_be"],start_date=saturday)
        with self.assertRaises(ValueError):
            create_group(self.draft,self.plan,self.catalog,name="Data inválida",
                         destinations=["rotterdam"],start_date="2027-09-05")
        rest=set_rest_weekend(self.draft,self.plan,self.catalog,saturday,True)
        self.assertIn(saturday,rest["rest_weekends"])
        self.assertEqual(set_rest_weekend(rest,self.plan,self.catalog,saturday,False)["rest_weekends"],[])

    def test_reconcile_deleted_canonical_outing_no_orphan_or_plan_changes(self):
        g=create_group(self.draft,self.plan,self.catalog,name="Bélgica",
                       destinations=["brussels","bruges_be"])
        trimmed,_=remove_outing(self.plan,self.catalog,"bruges_be",confirmed=True)
        result=reconcile_removed_outings(g,trimmed,self.catalog)
        self.assertEqual(result["groups"][0]["destinations"],["brussels"])
        last,_=remove_outing(trimmed,self.catalog,"brussels",confirmed=True)
        self.assertFalse(reconcile_removed_outings(result,last,self.catalog)["groups"])

    def test_portable_json_plan_scoping_and_invalid_import(self):
        g=create_group(self.draft,self.plan,self.catalog,name="Bélgica",
                       destinations=["brussels","bruges_be"])
        encoded=export_groups(g,self.plan,self.catalog)
        self.assertEqual(import_groups(encoded,self.plan,self.catalog),g)
        other=new_plan()
        with self.assertRaises(ValueError):import_groups(encoded,other,self.catalog)
        corrupted=loads(encoded)
        corrupted["groups"][0]["destinations"]=["unknown"]
        import json
        with self.assertRaises(ValueError):
            import_groups(json.dumps(corrupted),self.plan,self.catalog)

    def test_rest_rejects_official_sunday_assignment(self):
        saturday=next(r["start"] for r in
                      available_weekends(self.draft,self.plan,self.catalog)
                      if r["status"]=="livre · não reservado")
        from datetime import date,timedelta
        sunday=(date.fromisoformat(saturday)+timedelta(days=1)).isoformat()
        plan=deepcopy(self.plan)
        plan["assignments"][sunday]="rotterdam"
        with self.assertRaises(ValueError):
            set_rest_weekend(self.draft,plan,self.catalog,saturday,True)

    def test_three_nights_occupy_following_weekdays(self):
        saturday=next(r["start"] for r in
                      available_weekends(self.draft,self.plan,self.catalog)
                      if r["status"]=="livre · não reservado")
        group=create_group(self.draft,self.plan,self.catalog,name="Bélgica",
                           destinations=["brussels"],start_date=saturday,nights=3)
        from datetime import date,timedelta
        monday=(date.fromisoformat(saturday)+timedelta(days=2)).isoformat()
        plan=deepcopy(self.plan)
        plan["assignments"][monday]="rotterdam"
        with self.assertRaises(ValueError):
            from ux48_weekend_groups_model import validate_groups
            validate_groups(group,plan,self.catalog)

    def test_reconciliation_preserves_groups_when_old_dates_conflict(self):
        saturday=next(r["start"] for r in
                      available_weekends(self.draft,self.plan,self.catalog)
                      if r["status"]=="livre · não reservado")
        group=create_group(self.draft,self.plan,self.catalog,name="Bélgica",
                           destinations=["brussels"],start_date=saturday)
        other=create_group(group,self.plan,self.catalog,name="Holanda",
                           destinations=["rotterdam"])
        from ux48_weekend_groups_model import validate_groups
        changed=deepcopy(other)
        changed["groups"][1]["start_date"]=saturday
        corrected=reconcile_removed_outings(changed,self.plan,self.catalog)
        self.assertEqual(len(corrected["groups"]),2)
        self.assertEqual(corrected["groups"][0]["start_date"],saturday)
        self.assertIsNone(corrected["groups"][1]["start_date"])
        validate_groups(corrected,self.plan,self.catalog)

class WeekendGroupUITests(unittest.TestCase):
    def test_private_archive_roundtrip_includes_weekend_groups(self):
        from continuity_archive_model import make_archive,export_archive,import_archive
        from ux48_weekend_groups_model import empty_groups,create_group
        plan=new_plan()
        catalog=load_attractions()
        ids=[a["id"] for a in catalog["attractions"]
             if a["destination_id"]=="brussels"][:2]
        plan,_=apply_outing(plan,catalog,"brussels",ids,confirmed=True)
        groups=create_group(empty_groups(plan),plan,catalog,name="Bruxelas",
                            destinations=["brussels"],nights=1)
        archive=make_archive(plan,catalog,weekend_groups=groups)
        restored=import_archive(export_archive(archive,catalog),catalog)
        self.assertEqual(restored["weekend_groups"],groups)
        legacy=deepcopy(archive)
        del legacy["weekend_groups"]
        self.assertEqual(import_archive(export_archive(legacy,catalog),catalog)
                         ["weekend_groups"],empty_groups(plan))

    def test_workflow_uses_current_navigation_without_legacy_menu(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Organizar viagem").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertFalse(any("Acesso a ferramentas antigas" in e.label
                             for e in app.expander))
        self.assertTrue(any("Organizar viagens de fim de semana" in m.value
                             for m in app.markdown))

if __name__=="__main__":
    unittest.main()
