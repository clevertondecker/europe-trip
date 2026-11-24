"""UX122: a single private save, explicit recovery and full decisions fingerprint."""
import unittest
from copy import deepcopy
from unittest.mock import Mock,patch
from pathlib import Path
from attractions_model import load_attractions
from trip_plan_model import new_plan
from itinerary_flow_model import add_undated_choices,FRANCE_STAGE
from ux48_weekend_groups_model import empty_groups,create_group
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from continuity_archive_model import make_archive,import_archive,preview_restore,persisted_data_fingerprint
import continuity_ui as ui
from private_continuity_store import StorageConflict,StorageUnavailable


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_attractions()
        self.plan=add_undated_choices(new_plan(),self.catalog,["colmar","strasbourg"],FRANCE_STAGE)
        self.wishes=set_interest(empty_interests(),"colmar","must_visit",build_exploration_discovery())
        self.groups=create_group(empty_groups(self.plan),self.plan,self.catalog,
                                 name="Alsácia",destinations=["colmar","strasbourg"])
        self.state={"advisor_plan":deepcopy(self.plan),"ux502_interests":deepcopy(self.wishes),
                    "ux48_weekend_groups":deepcopy(self.groups),"ux_area":"Meu roteiro",
                    "ux_section":"Organizar viagem","flow_active_stage":FRANCE_STAGE,
                    "ux_organize_view":"Viagens agrupadas","rec03a_identity":"owner-test"}
        self.store=Mock()
        self.store.save.return_value=11

    def test_complete_decisions_saved_and_recovered_in_another_session(self):
        with patch.object(ui.st,"session_state",self.state),patch.object(ui,"_private_store",return_value=self.store):
            ui.save_private_now(self.plan,self.catalog)
            self.assertTrue(ui.resolve_private_status(self.plan,self.catalog,store_available=True)["saved"])
            self.state["ux_area"]="Explorar"
            self.state["ux_section"]="Passeios"
            self.assertTrue(ui.resolve_private_status(self.plan,self.catalog,store_available=True)["saved"])
            self.state["ux502_interests"]["items"][0]["priority"]="interested"
            self.assertFalse(ui.resolve_private_status(self.plan,self.catalog,store_available=True)["saved"])
            self.assertFalse(ui.resolve_private_status(self.plan,self.catalog,store_available=False)["saved"])
        body,generation=self.store.save.call_args.args
        archived=import_archive(body,self.catalog)
        self.assertEqual(archived["continuation"]["organize_view"],"Viagens agrupadas")
        self.assertEqual(archived["weekend_groups"],self.groups)
        self.assertEqual(archived["destination_interests"],self.wishes)
        self.store.load.return_value=(body,11)
        fresh={"advisor_plan":new_plan(),"rec03a_identity":"owner-test"}
        with patch.object(ui.st,"session_state",fresh),patch.object(ui,"_private_store",return_value=self.store):
            ui.restore_private_on_start(self.catalog)
            self.assertTrue(ui.resolve_private_status(fresh["advisor_plan"],self.catalog,store_available=True)["saved"])
            self.assertEqual(fresh["ux48_weekend_groups"],self.groups)
            self.assertEqual(fresh["ux502_interests"],self.wishes)
            ui.autosave_private_if_requested(self.catalog)
        self.assertEqual(self.store.save.call_count,1)

    def test_invalid_confirmation_cannot_mark_saved(self):
        self.store.save.return_value=None
        with patch.object(ui.st,"session_state",self.state),patch.object(ui,"_private_store",return_value=self.store):
            with self.assertRaises(StorageUnavailable):
                ui.save_private_now(self.plan,self.catalog)
            self.assertFalse(ui.resolve_private_status(self.plan,self.catalog,store_available=True)["saved"])

    def test_restore_requires_current_identity_and_remains_local(self):
        with patch.object(ui.st,"session_state",self.state),patch.object(ui,"_private_store",return_value=self.store),patch.object(ui,"bootstrap",side_effect=lambda:self.state["advisor_plan"]),patch.object(ui,"sync_legacy_view"):
            archive=ui._private_archive(self.plan,self.catalog)
            preview=preview_restore(self.plan,archive,self.catalog,current_archive=archive)
            self.state["ux36_pending_restore"]={"archive":archive,"preview":preview,"identity":"other"}
            ui.apply_pending_restore(self.catalog)
            self.assertIn("ux36_error",self.state)
            self.assertEqual(self.state["advisor_plan"],self.plan)
            self.state["ux36_pending_restore"]={"archive":archive,"preview":preview,"identity":"owner-test"}
            self.state["ux36_private_autosave"]=True
            ui.apply_pending_restore(self.catalog)
            self.assertFalse(self.state["ux36_private_autosave"])
            self.assertTrue(self.state["ux36_cloud_dirty"])
            ui.autosave_private_if_requested(self.catalog)
        self.store.save.assert_not_called()

    def test_conflict_and_failure_override_matching_hash(self):
        with patch.object(ui.st,"session_state",self.state),patch.object(ui,"_private_store",return_value=self.store):
            ui.save_private_now(self.plan,self.catalog)
            for status,kind in (("Conflito de versão","conflict"),("Erro ao salvar","error")):
                self.state["ux36_cloud_status"]=status
                before=deepcopy(self.state)
                resolved=ui.resolve_private_status(self.plan,self.catalog,store_available=True)
                self.assertEqual(resolved["kind"],kind)
                self.assertFalse(resolved["saved"])
                self.assertTrue(resolved["can_save"])
                self.assertEqual(self.state,before)


class ContinuityAppTests(unittest.TestCase):
    def test_single_save_on_all_public_tasks_and_no_duplicate_after_ack(self):
        from streamlit.testing.v1 import AppTest
        root=Path(__file__).resolve().parents[1]
        store=Mock()
        store.load.return_value=None
        store.save.return_value=10
        with patch("continuity_ui._private_store",return_value=store):
            app=AppTest.from_file(str(root/"app.py"),default_timeout=120).run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            for task in ("Visão geral","Meus destinos","Organizar"):
                app.segmented_control(key="ux64_public_task").set_value(task).run()
                self.assertFalse(app.exception,[e.message for e in app.exception])
                self.assertEqual(sum(b.label=="Salvar minha viagem" for b in app.button),1)
                self.assertEqual(sum(x.label=="Cópia e recuperação" for x in app.expander),1)
                self.assertFalse(any(x.label=="Ferramentas complementares" for x in app.expander))
            store.save.assert_not_called()
            app.button(key="ux75_private_save_now").click().run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            self.assertNotIn("ux75_private_save_now",{b.key for b in app.button})
            self.assertTrue(any("Tudo salvo" in x.value for x in app.success))
            self.assertEqual(store.save.call_count,1)
            app.run()
            self.assertEqual(store.save.call_count,1)
