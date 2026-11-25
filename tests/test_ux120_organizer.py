"""UX120 mode compatibility and smart calendar protection."""
import unittest
from copy import deepcopy
from ux120_organizer_navigation import organizer_mode,legacy_mode
from trip_plan_model import new_plan
from attractions_model import load_attractions,load_base_routes
from itinerary_flow_model import add_undated_choices, FRANCE_STAGE
from ux48_weekend_groups_model import empty_groups,create_group,available_weekends,set_rest_weekend
from smart_calendar_model import suggest_calendar


class OrganizerTests(unittest.TestCase):
    def test_legacy_routes_roundtrip(self):
        for mode,legacy in (("Visitas","Por período ou data"),
                            ("Calendário","Calendário inteligente"),
                            ("Viagens agrupadas","Viagens agrupadas")):
            self.assertEqual(legacy_mode(mode,FRANCE_STAGE),legacy)
            self.assertEqual(organizer_mode(legacy,FRANCE_STAGE),mode)
        self.assertEqual(legacy_mode("Calendário",FRANCE_STAGE,"Completo"),"Calendário completo")
        self.assertEqual(organizer_mode("Viagens agrupadas","Itália"),"Visitas")

    def test_suggestions_do_not_schedule_group_members_or_reserved_days(self):
        catalog=load_attractions()
        plan=add_undated_choices(new_plan(),catalog,["colmar","basel"],FRANCE_STAGE)
        state=empty_groups(plan)
        dates=[r["start"] for r in available_weekends(state,plan,catalog)
               if r["status"]=="livre · não reservado"]
        state=create_group(state,plan,catalog,name="Grupo",destinations=["basel"],start_date=dates[0])
        state=set_rest_weekend(state,plan,catalog,dates[1],True)
        before=deepcopy((plan,state))
        proposals=suggest_calendar(plan,catalog,load_base_routes(),weekend_groups=state,stage=FRANCE_STAGE)
        from ux48_weekend_groups_model import _trip_days
        forbidden=set(_trip_days(dates[0],0)+_trip_days(dates[1],1))
        self.assertTrue(proposals)
        for proposal in proposals:
            self.assertFalse(set(proposal["assignments"]) & forbidden)
            self.assertNotIn("basel",proposal["assignments"].values())
        self.assertEqual((plan,state),before)


    def test_timeline_visit_click_replaces_add_form_with_correct_organizer(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        from ux502_destination_interests_model import empty_interests, set_interest

        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        plan=add_undated_choices(app.session_state["advisor_plan"],load_attractions(),
                                 ["colmar","basel"],FRANCE_STAGE)
        wishes=set_interest(empty_interests(),"colmar","must_visit")
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.button(key="ux64_sidebar_nav_1").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Organizar").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.segmented_control(key="flow_active_stage").set_value(FRANCE_STAGE).run()
        app.segmented_control(key="ux120_mode").set_value("Visitas").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn("flow_organize_destination",{w.key for w in app.selectbox})
        app.button(key="ux120_visit_colmar").click().run()
        self.assertEqual(app.session_state["flow_organize_destination"],"colmar")
        app.button(key="flow_add_open_button").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(app.session_state["flow_add_open"])
        self.assertIn("flow_add_close",{b.key for b in app.button})

        app.button(key="ux120_visit_basel").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertFalse(app.session_state["flow_add_open"])
        self.assertTrue(app.session_state["flow_organize_open"])
        self.assertFalse(app.session_state["flow_save_open"])
        self.assertNotIn("flow_add_close",{b.key for b in app.button})
        self.assertEqual(app.session_state["flow_organize_destination"],"basel")
        self.assertIn("flow_organize_mode",{w.key for w in app.segmented_control})
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)

        # The same CTA must still work when the organizer is already open.
        app.button(key="ux120_visit_colmar").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertFalse(app.session_state["flow_add_open"])
        self.assertEqual(app.session_state["flow_organize_destination"],"colmar")
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)

        # A changed period cannot be silently discarded when opening another card.
        from itinerary_flow_model import period_options,UNASSIGNED
        option=next(x for x in period_options(FRANCE_STAGE) if x!=UNASSIGNED)
        app.selectbox(key="flow_organize_period").set_value(option).run()
        app.button(key="ux120_visit_basel").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("ux129_discard",{b.key for b in app.button})
        self.assertEqual(app.session_state["flow_journey_visit_focus"],(FRANCE_STAGE,"colmar"))
        app.button(key="ux129_keep_editing").click().run()
        self.assertEqual(app.selectbox(key="flow_organize_period").value,option)
        app.button(key="ux120_visit_basel").click().run()
        app.button(key="ux129_discard").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["flow_journey_visit_focus"],(FRANCE_STAGE,"basel"))
        self.assertEqual(app.selectbox(key="flow_organize_period").value,UNASSIGNED)
        app.button(key="ux129_cancel_visit").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn("flow_organize_mode",{w.key for w in app.segmented_control})
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)

        # Explicit writes inside the card, and closing with a dirty draft.
        from datetime import date
        from itinerary_flow_model import selected_rows_for_stage
        from ux129_visit_focus import DRAFTS,ORDER
        app.button(key="ux120_visit_basel").click().run()
        self.assertEqual(app.button(key="flow_organize_close").label,"Fechar")
        app.selectbox(key="flow_organize_period").set_value(option).run()
        app.button(key="flow_organize_close").click().run()
        self.assertIn("ux129_discard",{b.key for b in app.button})
        self.assertEqual(app.session_state["advisor_plan"],plan)
        app.button(key="ux129_keep_editing").click().run()
        original_order=deepcopy(app.session_state[ORDER])
        app.button(key="flow_organize_save_period").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        updated=app.session_state["advisor_plan"]
        self.assertEqual(next(r for r in selected_rows_for_stage(updated,load_attractions(),FRANCE_STAGE)
                              if r["id"]=="basel")["period"],option)
        self.assertEqual(app.session_state[ORDER],original_order)
        self.assertNotIn((FRANCE_STAGE,"basel"),app.session_state[DRAFTS])
        self.assertTrue(any("Período de Basel atualizado" in x.value for x in app.success))
        self.assertEqual(app.session_state["flow_journey_visit_focus"],(FRANCE_STAGE,"basel"))
        app.segmented_control(key="flow_organize_mode").set_value("Definir data").run()
        chosen=date(2027,10,16)
        app.date_input(key="flow_organize_date_"+FRANCE_STAGE).set_value(chosen).run()
        app.button(key="flow_organize_save_date").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any("Data proposta registrada para Basel" in x.value for x in app.success))
        self.assertEqual(app.session_state["advisor_plan"]["assignments"].get(chosen.isoformat()),"basel")
        self.assertNotIn((FRANCE_STAGE,"basel"),app.session_state[DRAFTS])
        self.assertEqual(app.session_state[ORDER],original_order)
        app.button(key="flow_organize_remove_date").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn(chosen.isoformat(),app.session_state["advisor_plan"]["assignments"])
        self.assertTrue(any("Data removida" in x.value for x in app.success))
        self.assertNotIn((FRANCE_STAGE,"basel"),app.session_state[DRAFTS])
        app.button(key="flow_organize_close").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertNotIn("flow_organize_mode",{w.key for w in app.segmented_control})
        self.assertEqual(app.session_state["ux502_interests"],wishes)
