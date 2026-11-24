"""Planning journey must permit direct wishlist -> draft review without comparison."""
import unittest
from copy import deepcopy
from ux_planning_journey_model import project_planning
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from attractions_model import load_attractions
from itinerary_flow_model import add_undated_choices,FRANCE_STAGE,ITALY_STAGE

class PlanningJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.catalog=load_attractions()

    def test_filled_wishlist_prioritizes_build_not_compare(self):
        plan=new_plan()
        wishes=empty_interests()
        for d in ("strasbourg","colmar","angers"):
            wishes=set_interest(wishes,d,"must_visit",self.discovery)
        before=deepcopy((plan,wishes))
        view=project_planning(plan,wishes,self.discovery,self.catalog)
        self.assertEqual(view["next"],"build")
        self.assertEqual(view["counts"]["wished"],3)
        self.assertEqual(view["eligible_count"],2)
        self.assertEqual([r["id"] for r in view["unsupported"]],["angers"])
        self.assertEqual((plan,wishes),before)
        added=add_undated_choices(plan,self.catalog,["strasbourg","colmar"],FRANCE_STAGE)
        review=project_planning(added,wishes,self.discovery,self.catalog)
        self.assertEqual(review["next"],"organize")
        self.assertEqual(review["counts"]["planned"],2)
        self.assertEqual(review["counts"]["organized"],0)
        self.assertEqual(len(review["pending"]),2)
        self.assertFalse(review["private_saved"])

    def test_empty_wishlist_existing_draft_is_reviewable(self):
        plan=add_undated_choices(new_plan(),self.catalog,["strasbourg"],FRANCE_STAGE)
        self.assertEqual(project_planning(plan,empty_interests(),self.discovery,self.catalog)["next"],"organize")

    def test_navigation_intent_preserves_plan_and_rejects_account_change(self):
        from ux_planning_journey_ui import request_planning,apply_planning_request
        state={"advisor_plan":new_plan(),"rec03a_identity":"owner"}
        before=deepcopy(state["advisor_plan"])
        request_planning(state,"build",FRANCE_STAGE)
        apply_planning_request(state)
        self.assertEqual(state["ux_section"],"Meu planejamento")
        self.assertEqual(state["flow_journey_stage_hint"],FRANCE_STAGE)
        self.assertEqual(state["advisor_plan"],before)
        request_planning(state,"review")
        state["rec03a_identity"]="other"
        apply_planning_request(state)
        self.assertEqual(state["flow_journey_view"],"build")
        self.assertEqual(state["advisor_plan"],before)

    def test_all_eligibility_states(self):
        plan=new_plan()
        draft=add_undated_choices(plan,self.catalog,["colmar"],FRANCE_STAGE)
        cases=[
            (plan,[],"choose","empty",0),
            (plan,["colmar"],"build","eligible_wishes",1),
            (plan,["angers","paris"],"exploratory","exploratory_only",0),
            (draft,[],"organize","draft_without_wishes",0),
            (draft,["colmar","strasbourg","angers"],"build","draft_with_pending",1),
            (draft,["colmar","angers"],"organize","draft_with_no_eligible_pending",0),
            (draft,["angers"],"organize","draft_with_no_eligible_pending",0),
        ]
        for p,ids,action,phase,count in cases:
            with self.subTest(phase=phase,ids=ids):
                w=empty_interests()
                for d in ids:
                    w=set_interest(w,d,"interested",self.discovery)
                before=deepcopy((p,w))
                view=project_planning(p,w,self.discovery,self.catalog)
                self.assertEqual((view["next"],view["phase"],view["eligible_count"]),(action,phase,count))
                self.assertEqual((p,w),before)
                self.assertEqual(view["next"]=="build",count>0)

    def test_empty_plan_and_wishlist(self):
        view=project_planning(new_plan(),empty_interests(),self.discovery,self.catalog)
        self.assertEqual(view["next"],"choose")
        self.assertEqual(view["counts"]["planned"],0)

class PlanningJourneyAppTests(unittest.TestCase):
    def test_bulk_confirm_and_review_without_navigation(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        discovery=build_exploration_discovery()
        wishes=empty_interests()
        for d in ("strasbourg","colmar","angers"):
            wishes=set_interest(wishes,d,"must_visit",discovery)
        script="""
import streamlit as st
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions())
"""
        app=AppTest.from_string(script,default_timeout=90)
        plan=new_plan()
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.session_state["ux_area"]="Meu roteiro"
        app.session_state["ux_section"]="Meu planejamento"
        # No real cloud write; test the existing canonical review/save surface.
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.button(key="flow_journey_primary").label,"Montar meu roteiro")
            app.button(key="flow_journey_primary").click().run()
            self.assertFalse(app.exception,str(app.exception))
            key="flow_journey_batch_"+FRANCE_STAGE
            app.button(key=key+"_all").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["advisor_plan"],plan)
            self.assertEqual(set(app.multiselect(key=key).value),{"strasbourg","colmar"})
            app.button(key="flow_journey_cancel_batch").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["advisor_plan"],plan)
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            app.button(key="flow_journey_review_build").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.multiselect(key=key).value,[])
            app.button(key=key+"_all").click().run()
            app.button(key=key+"_confirm").click().run()
            self.assertFalse(app.exception,str(app.exception))
            current=app.session_state["advisor_plan"]
            self.assertEqual(current["revision"],plan["revision"]+1)
            self.assertEqual(current["base_city"],plan["base_city"])
            self.assertEqual(current["assignments"],{})
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            self.assertEqual(app.session_state["flow_journey_view"],"review")
            self.assertEqual(app.session_state["ux_area"],"Meu roteiro")
            self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
            self.assertTrue(any("Revisar e salvar meu rascunho" in x.value for x in app.markdown))
            self.assertTrue(any("Nuvem privada" in x.value for x in app.warning))
        # Run the existing persistence adapter using only a mock store.
        from unittest.mock import MagicMock
        from private_continuity_store import StorageConflict
        store=MagicMock()
        store.save.side_effect=StorageConflict("conflito simulado")
        with patch("continuity_ui._private_store",return_value=store):
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            app.button(key="ux75_private_save_now").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertTrue(app.session_state["ux36_cloud_status"].startswith("Conflito"))
            self.assertEqual(app.session_state["advisor_plan"],current)
            self.assertTrue(app.session_state["ux36_cloud_dirty"])
            store.save.side_effect=None
            store.save.return_value=123
            app.button(key="ux75_private_save_now").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["ux36_cloud_status"],"Salvo em espaço privado")
            self.assertFalse(app.session_state["ux36_cloud_dirty"])
            self.assertEqual(app.session_state["advisor_plan"],current)
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            self.assertEqual(store.save.call_count,2)

    def test_bulk_confirmation_with_public_tabs_does_not_mutate_rendered_widget(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        discovery=build_exploration_discovery()
        wishes=empty_interests()
        for destination in ("basel","colmar","interlaken","obernai","strasbourg"):
            wishes=set_interest(wishes,destination,"interested",discovery)
        script="""
import streamlit as st
from ux64_navigation_ui import render_public_task_tabs
from ux_planning_journey_ui import render_planning_journey
from attractions_model import load_attractions
from planning_session import active_plan
render_public_task_tabs()
render_planning_journey(active_plan(),load_attractions())
"""
        app=AppTest.from_string(script,default_timeout=90)
        plan=new_plan()
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.session_state["ux_area"]="Meu roteiro"
        app.session_state["ux_section"]="Meu planejamento"
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            app.button(key="flow_journey_primary").click().run()
            self.assertFalse(app.exception,str(app.exception))
            batch="flow_journey_batch_"+FRANCE_STAGE
            app.button(key=batch+"_all").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertTrue(app.multiselect(key=batch).value)
            app.button(key=batch+"_confirm").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["flow_journey_view"],"review")
            self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
            self.assertEqual(app.session_state["advisor_plan"]["base_city"],plan["base_city"])
            self.assertEqual(app.session_state["ux502_interests"],wishes)

    def test_exploratory_only_and_stale_build_have_no_empty_form(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        script="""
import streamlit as st
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions(),summary_only=st.session_state.get("summary",False))
"""
        app=AppTest.from_string(script,default_timeout=90)
        plan=new_plan()
        wishes=set_interest(empty_interests(),"angers","must_visit")
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.session_state["summary"]=True
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.button(key="flow_journey_primary").label,"Revisar minha lista")
            app.session_state["summary"]=False
            app.session_state["flow_journey_view"]="build"
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.button(key="flow_journey_primary").label,"Revisar minha lista")
            self.assertTrue(app.button(key="flow_journey_step_build").disabled)
            self.assertFalse(any(w.key.startswith("flow_journey_batch_") for w in app.multiselect if w.key))
            self.assertEqual(app.session_state["advisor_plan"],plan)
            self.assertEqual(app.session_state["ux502_interests"],wishes)


    def test_visual_journey_retains_canonical_navigation_and_compact_summary(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        script = """
import streamlit as st
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions(),
                        summary_only=st.session_state.get("summary",False))
"""
        app=AppTest.from_string(script,default_timeout=90)
        app.session_state["advisor_plan"]=new_plan()
        app.session_state["ux502_interests"]=set_interest(
            empty_interests(),"strasbourg","must_visit",build_exploration_discovery())
        with patch("continuity_ui._private_store",return_value=None):
            app.session_state["summary"]=True
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertTrue(any("Nossa viagem" in x.value for x in app.markdown))
            self.assertEqual(len(app.metric),3)
            self.assertEqual({x.label for x in app.metric},{"Incluídos","Organizados","A organizar"})
            app.session_state["summary"]=False
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertTrue(any("journey-header__eyebrow" in x.value
                                for x in app.markdown))
            self.assertIn("flow_journey_step_review",{x.key for x in app.button})
            self.assertIn("flow_journey_step_build",{x.key for x in app.button})
            original=deepcopy(app.session_state["advisor_plan"])
            app.button(key="flow_journey_step_review").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["flow_journey_view"],"review")
            self.assertEqual(app.session_state["advisor_plan"],original)
            self.assertTrue(any('href="#journey-review-anchor"' in x.value
                                for x in app.markdown))
            self.assertTrue(any('id="journey-review-anchor"' in x.value
                                for x in app.markdown))
            app.button(key="flow_journey_step_build").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["flow_journey_view"],"build")
            self.assertTrue(any('href="#journey-build-anchor"' in x.value
                                for x in app.markdown))
            self.assertEqual(app.session_state["advisor_plan"],original)



    def test_save_without_dates_and_recovery_panel_are_directly_accessible(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch,MagicMock
        catalog=load_attractions()
        plan=add_undated_choices(new_plan(),catalog,["strasbourg"],FRANCE_STAGE)
        script="""
import streamlit as st
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions())
"""
        app=AppTest.from_string(script,default_timeout=90)
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=empty_interests()
        app.session_state["ux_area"]="Meu roteiro"
        app.session_state["ux_section"]="Meu planejamento"
        store=MagicMock()
        store.save.return_value=17
        with patch("continuity_ui._private_store",return_value=store):
            app.run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            app.button(key="flow_journey_primary").click().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            self.assertIn("ux75_private_save_now",{x.key for x in app.button})
            self.assertIn("flow_journey_review_organize",{x.key for x in app.button})
            self.assertEqual(
                sum(x.label=="Recuperar ou guardar uma cópia privada"
                    for x in app.expander),1)
            self.assertEqual(app.session_state["advisor_plan"]["assignments"],{})
            app.button(key="ux75_private_save_now").click().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            self.assertEqual(app.session_state["ux36_cloud_status"],
                             "Salvo em espaço privado")
            self.assertEqual(app.session_state["advisor_plan"],plan)
            app.button(key="flow_journey_review_organize").click().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            self.assertEqual(app.session_state["flow_journey_view"],"organize")
            self.assertEqual(app.session_state["advisor_plan"],plan)


class PlanningUx83NavigationTests(unittest.TestCase):
    def test_public_tasks_target_only_their_own_canonical_activity(self):
        from ux64_navigation_model import select_public_task
        from ux_planning_journey_ui import request_planning,apply_planning_request
        state={"advisor_plan":new_plan(),"rec03a_identity":"owner"}
        plan=deepcopy(state["advisor_plan"])
        for action,expected in (
                ("build","Meu planejamento"),("review","Meu planejamento"),
                ("organize","Organizar viagem")):
            with self.subTest(action=action):
                request_planning(state,action)
                apply_planning_request(state)
                self.assertEqual(state["ux_area"],"Meu roteiro")
                self.assertEqual(state["ux_section"],expected)
                self.assertEqual(state["flow_journey_view"],action)
                self.assertEqual(state["advisor_plan"],plan)
        # Clicking public task tabs changes focus without touching the plan.
        select_public_task(state,"Planejar","Meus destinos")
        self.assertIsNone(state["flow_journey_view"])
        select_public_task(state,"Planejar","Organizar")
        self.assertEqual(state["flow_journey_view"],"organize")
        self.assertEqual(state["advisor_plan"],plan)

    def test_app_renders_full_editor_only_in_meus_destinos_not_summary(self):
        from pathlib import Path
        code=(Path(__file__).resolve().parents[1]/"app.py").read_text()
        start=code.index('if itinerary_section == "Visão geral":')
        end=code.index('    elif itinerary_section == "Itália":',start)
        section=code[start:end]
        branch=section.split('elif (ux_area,ux_section)==("Meu roteiro","Organizar viagem")')[0]
        self.assertIn('("Meu roteiro","Meu planejamento")',branch)
        self.assertNotIn('summary_only=True',branch)
        self.assertIn('summary_only=True',code[code.index('if page == "Visão geral":'):code.index('elif page == "Roteiro":')])
        self.assertIn('st.session_state["flow_journey_view"]="organize"',code)

    def test_organizer_header_and_review_are_same_shared_component(self):
        from ux_planning_journey_presentation import header_html
        self.assertIn("Organizar nossa viagem",
            header_html("Rascunho", "Local",title="Organizar nossa viagem",
                        tag="Visitas por período ou data"))
        self.assertIn("journey-header",header_html("Rascunho","Local"))
        from ux_planning_journey_ui import _show
        from unittest.mock import patch
        with patch("ux_planning_journey_ui.st.session_state",{
                "ux_area":"Meu roteiro","ux_section":"Organizar viagem"}) as state:
            _show("review")
            self.assertEqual(state["ux_section"],"Meu planejamento")
            self.assertEqual(state["flow_journey_view"],"review")
            _show("organize")
            self.assertEqual(state["ux_section"],"Organizar viagem")
            self.assertEqual(state["flow_journey_view"],"organize")

if __name__=="__main__":
    unittest.main()
