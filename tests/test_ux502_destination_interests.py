"""UX 5.0.2 — destinations are not attractions or confirmed outings."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import (
    empty_interests, validate_interests, set_interest, remove_interest,
    reconcile_transient, selected_destinations_for_comparison,
    export_interests, import_interests,
)
from attractions_model import load_attractions
from continuity_archive_model import make_archive,export_archive,import_archive

ROOT=Path(__file__).resolve().parents[1]


class DestinationInterestsModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_destination_discovery()

    def test_priorities_order_immutable_and_removal(self):
        initial=empty_interests()
        a=set_interest(initial,"bruges_be","interested",self.discovery)
        a=set_interest(a,"colmar","must_visit",self.discovery)
        a=set_interest(a,"lille","discarded",self.discovery)
        a=set_interest(a,"basel","maybe",self.discovery)
        self.assertEqual(initial,empty_interests())
        self.assertEqual(selected_destinations_for_comparison(a,self.discovery),
                         ["colmar","bruges_be","basel"])
        self.assertEqual(set_interest(a,"colmar","must_visit",self.discovery),a)
        self.assertEqual(len(a["items"]),4)
        self.assertEqual(len(remove_interest(a,"lille",self.discovery)["items"]),3)

    def test_invalid_destination_duplicate_schema_and_attraction(self):
        with self.assertRaises(ValueError):
            set_interest(empty_interests(),"lux_bock","interested",self.discovery)
        with self.assertRaises(ValueError):
            set_interest(empty_interests(),"unknown","interested",self.discovery)
        bad=empty_interests()
        bad["items"]=[{"destination_id":"colmar","priority":"maybe"}]*2
        with self.assertRaises(ValueError):
            validate_interests(bad,self.discovery)
        bad["schema_version"]=99
        with self.assertRaises(ValueError):
            validate_interests(bad,self.discovery)

    def test_round_trip_and_transient_reconciliation(self):
        a=set_interest(empty_interests(),"colmar","must_visit",self.discovery)
        b=import_interests(export_interests(a,self.discovery),self.discovery)
        self.assertEqual(b,a)
        existing,missing=reconcile_transient(b,["colmar","bruges_be"],self.discovery)
        self.assertEqual(existing,a)
        self.assertEqual(missing,["bruges_be"])

    def test_legacy_archive_and_new_optional_field(self):
        from trip_plan_model import new_plan
        plan=new_plan()
        catalog=load_attractions()
        old=make_archive(plan,catalog)
        old.pop("destination_interests")
        legacy=import_archive(__import__("json").dumps(old).encode(),catalog)
        self.assertEqual(legacy["destination_interests"],empty_interests())
        new=set_interest(empty_interests(),"colmar","must_visit",self.discovery)
        doc=make_archive(plan,catalog,destination_interests=new)
        self.assertEqual(import_archive(export_archive(doc,catalog),catalog)["destination_interests"],new)


class DestinationInterestsAppTests(unittest.TestCase):
    def test_list_filter_priority_and_tripplan_isolation(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.radio(key="ux502_view").set_value("Minha lista").run()
        app.session_state["ux502_interests"]=set_interest(
            set_interest(empty_interests(),"colmar","must_visit"),
            "bruges_be","interested")
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(selected_destinations_for_comparison(
            app.session_state["ux502_interests"]),["colmar","bruges_be"])
        app.radio(key="ux502_view").set_value("Descobrir lugares").run()
        app.selectbox(key="ux501_country").set_value("Bélgica").run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(len(app.session_state["ux502_interests"]["items"]),2)


    def test_selectboxes_rebind_after_replacement_same_revision(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.radio(key="ux502_view").set_value("Minha lista").run()
        first=set_interest(empty_interests(),"colmar","must_visit")
        app.session_state["ux502_interests"]=first
        app.run()
        before=[x for x in app.selectbox if x.key and x.key.startswith("ux502_priority_colmar_")]
        self.assertEqual(len(before),1)
        self.assertEqual(before[0].value,"must_visit")
        # Simulate imported JSON or restored private archive: same revision,
        # different priority. The former Streamlit widget must not win.
        restored=set_interest(empty_interests(),"colmar","maybe")
        self.assertEqual(first["revision"],restored["revision"])
        app.session_state["ux502_interests"]=restored
        app.run()
        after=[x for x in app.selectbox if x.key and x.key.startswith("ux502_priority_colmar_")]
        self.assertEqual(len(after),1)
        self.assertNotEqual(before[0].key,after[0].key)
        self.assertEqual(after[0].value,"maybe")
        self.assertEqual(app.session_state["ux502_interests"],restored)
        self.assertFalse(app.exception,[x.message for x in app.exception])


class PrivateWishlistPersistenceTests(unittest.TestCase):
    def setUp(self):
        from trip_plan_model import new_plan
        self.plan=new_plan()
        self.catalog=load_attractions()
        self.interests=set_interest(empty_interests(),"colmar","must_visit")

    def test_confirmed_private_save_and_archive_roundtrip(self):
        from unittest.mock import Mock,patch
        import continuity_ui
        state={"advisor_plan":deepcopy(self.plan),
               "ux502_interests":deepcopy(self.interests),
               "ux36_cloud_generation":7,"ux36_cloud_dirty":True}
        storage=Mock()
        storage.save.return_value=8
        with patch.object(continuity_ui.st,"session_state",state), \
             patch.object(continuity_ui,"_private_store",return_value=storage):
            continuity_ui.save_private_now(self.plan,self.catalog)
        args=storage.save.call_args.args
        self.assertEqual(args[1],7)
        archived=import_archive(args[0],self.catalog)
        self.assertEqual(archived["destination_interests"],self.interests)
        self.assertEqual(state["ux36_cloud_generation"],8)
        self.assertEqual(state["ux502_private_saved_revision"],self.interests["revision"])
        self.assertFalse(state["ux36_cloud_dirty"])
        self.assertEqual(state["ux36_cloud_status"],"Salvo em espaço privado")

    def test_network_failure_and_generation_conflict_do_not_claim_saved(self):
        from unittest.mock import Mock,patch
        import continuity_ui
        from private_continuity_store import StorageUnavailable,StorageConflict
        for failure in (StorageUnavailable("offline"),StorageConflict("generation")):
            with self.subTest(failure=type(failure).__name__):
                state={"advisor_plan":deepcopy(self.plan),
                       "ux502_interests":deepcopy(self.interests),
                       "ux36_cloud_generation":7,"ux36_cloud_dirty":True}
                storage=Mock()
                storage.save.side_effect=failure
                with patch.object(continuity_ui.st,"session_state",state), \
                     patch.object(continuity_ui,"_private_store",return_value=storage):
                    with self.assertRaises(type(failure)):
                        continuity_ui.save_private_now(self.plan,self.catalog)
                self.assertTrue(state["ux36_cloud_dirty"])
                self.assertNotIn("ux502_private_saved_revision",state)
                self.assertNotIn("Salvo",state.get("ux36_cloud_status",""))
                self.assertEqual(state["ux36_cloud_generation"],7)

    def test_restore_private_recovers_wishes_only_after_validated_load(self):
        from unittest.mock import Mock,patch
        import continuity_ui
        archive=make_archive(self.plan,self.catalog,destination_interests=self.interests)
        storage=Mock()
        storage.load.return_value=(export_archive(archive,self.catalog),23)
        state={}
        with patch.object(continuity_ui.st,"session_state",state), \
             patch.object(continuity_ui,"_private_store",return_value=storage), \
             patch.object(continuity_ui,"sync_legacy_view"):
            continuity_ui.restore_private_on_start(self.catalog)
        self.assertEqual(state["ux502_interests"],self.interests)
        self.assertEqual(state["ux502_private_saved_revision"],self.interests["revision"])
        self.assertEqual(state["ux36_cloud_generation"],23)
        self.assertFalse(state["ux36_cloud_dirty"])
        self.assertEqual(state["advisor_plan"],self.plan)

    def test_ui_shows_saved_only_after_storage_confirmation(self):
        from unittest.mock import Mock,patch
        import continuity_ui
        from private_continuity_store import StorageConflict
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.session_state["ux502_interests"]=deepcopy(self.interests)
        fake=Mock()
        fake.save.side_effect=StorageConflict("stale")
        with patch.object(continuity_ui,"_private_store",return_value=fake):
            app.run()
            # A configured private store owns routine wishlist saves; no
            # duplicate JSON transfer controls in the everyday journey.
            self.assertNotIn("ux502_upload", app.session_state)
            self.assertNotIn("ux502_import_pending", app.session_state)
            self.assertFalse(any("Lista salva no armazenamento privado" in x.value for x in app.success))
            app.button(key="ux502_cloud_save").click().run()
        self.assertFalse(any("Lista salva no armazenamento privado" in x.value for x in app.success))
        self.assertTrue(app.session_state.get("ux36_cloud_dirty",False))
        fake.save.side_effect=None
        fake.save.return_value=8
        with patch.object(continuity_ui,"_private_store",return_value=fake):
            app.button(key="ux502_cloud_save").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux502_private_saved_revision"],self.interests["revision"])
        self.assertFalse(app.session_state["ux36_cloud_dirty"])
        self.assertEqual(app.session_state["ux502_status"], "Salvo no armazenamento privado")


if __name__=="__main__":
    unittest.main()
