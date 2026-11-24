"""REC03B handoff contracts tested against real catalogs and REC02 evidence."""
import unittest
from copy import deepcopy
from rec03b_handoffs import (PENDING,CONTEXT,PREVIOUS,queue_handoff,apply_handoff,
                            queue_restore_manual,contextual_points)
from rec03a_session import clear_recommendation_context,SCOPE,sync_identity
from recommendation_scope_model import confirm_scope
from ux502_destination_interests_model import empty_interests,set_interest,remove_interest
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research
from base_recommendation_model import recommend_bases
from ux503_destination_base_comparison_model import compare_wishlist_bases
from routes7_comparison_projection import decorate_comparison
from trip_plan_model import new_plan

class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.research=load_research(include_candidates=True)

    def state(self):
        items=empty_interests()
        for d,p in (("paris","must_visit"),("colmar","interested"),("strasbourg","maybe"),
                    ("basel","must_visit"),("lucerne","interested"),("interlaken","maybe"),
                    ("angers","interested")):
            items=set_interest(items,d,p,self.discovery)
        ids=[x["destination_id"] for x in items["items"]]
        return {"ux502_interests":items,SCOPE:confirm_scope(items,ids,self.discovery),
                "advisor_plan":new_plan(),"scenario_base_selected":"metz","ux_mode":"Simulação",
                "ux41_favorites":["metz"],"ux36_cloud_dirty":False,
                "ux504_bases_shadow":["metz","nancy"],"ux504_visible_destinations_shadow":["paris"]}

    def apply(self,state):
        return apply_handoff(state,discovery=self.discovery,research=self.research)

    def test_transfer_whole_scope_and_restore_previous(self):
        state=self.state()
        before=deepcopy(state)
        queue_handoff(state,"manual",["strasbourg","angers","mulhouse"])
        self.assertEqual(self.apply(state),"manual")
        self.assertNotIn(PENDING,state)
        self.assertEqual(state["ux503_visible_destinations"],before[SCOPE]["destination_ids"])
        self.assertEqual(len(state["ux503_visible_destinations"]),7)
        self.assertEqual(state["ux503_bases"],["strasbourg","angers","mulhouse"])
        rec=recommend_bases(state["ux502_interests"],state[SCOPE],discovery=self.discovery,research=self.research)
        raw=compare_wishlist_bases(state["ux502_interests"],state["ux503_bases"],
                                   visible_destination_ids=state["ux503_visible_destinations"],
                                   discovery=self.discovery,research=self.research)
        manual=decorate_comparison(raw)
        for c in rec["candidates"]:
            if c["base_id"] in state["ux503_bases"]:
                for d,cell in c["evidence"].items():
                    self.assertEqual(cell,manual["cells"][c["base_id"],d])
        queue_restore_manual(state)
        self.assertEqual(self.apply(state),"restore_manual")
        self.assertEqual(state["ux503_bases"],["metz","nancy"])
        self.assertEqual(state["ux503_visible_destinations"],["paris"])
        self.assertNotIn(PREVIOUS,state)
        for k in ("advisor_plan","scenario_base_selected","ux_mode","ux502_interests","ux41_favorites","ux36_cloud_dirty"):
            self.assertEqual(state[k],before[k])

    def test_reject_stale_and_invalid_intents(self):
        for ids in (["angers"],["metz","metz"],["unknown","nancy"]):
            state=self.state()
            queue_handoff(state,"manual",ids)
            self.assertIsNone(self.apply(state))
            self.assertEqual(state["ux504_bases_shadow"],["metz","nancy"])
            self.assertNotIn(PENDING,state)
        state=self.state()
        queue_handoff(state,"manual",["angers","metz"])
        state["ux502_interests"]=remove_interest(state["ux502_interests"],"paris",self.discovery)
        self.assertIsNone(self.apply(state))
        self.assertNotIn(CONTEXT,state)

    def test_profile_and_map_never_choose_scenario_or_official(self):
        state=self.state()
        before=deepcopy(state)
        queue_handoff(state,"profile",["angers"])
        self.assertEqual(self.apply(state),"profile")
        self.assertEqual(state["ux40_selected_city"],"angers")
        self.assertEqual(state["ux_section"],"Cidades-base")
        queue_handoff(state,"map",["angers"])
        self.assertEqual(self.apply(state),"map")
        from attractions_model import load_attractions
        from base_explorer_model import load_exploration
        pins,missing=contextual_points(state[CONTEXT],state["advisor_plan"],discovery=self.discovery,
                                       research=self.research,exploration=load_exploration(),catalog=load_attractions())
        self.assertEqual(len({p["id"] for p in pins}),len(pins))
        self.assertTrue(any(p["id"]=="angers" and "Base candidata" in p["role"] for p in pins))
        self.assertTrue(any(p["id"]=="mulhouse" and "Base oficial" in p["role"] for p in pins))
        for k in ("advisor_plan","scenario_base_selected","ux_mode","ux502_interests","ux41_favorites","ux36_cloud_dirty"):
            self.assertEqual(state[k],before[k])
        sync_identity(state,"new-account")
        self.assertNotIn(CONTEXT,state)
        self.assertNotIn(SCOPE,state)

    def test_planning_handoff_uses_canonical_intent_without_including(self):
        from ux_planning_journey_ui import apply_planning_request
        state=self.state()
        before=deepcopy(state)
        queue_handoff(state,"planning",[])
        self.assertEqual(self.apply(state),"planning")
        self.assertEqual(state["flow_journey_intent"]["action"],"build")
        self.assertEqual(state["flow_journey_intent"]["stage"],"França")
        apply_planning_request(state)
        # UX83: inclusion/review has a dedicated public destination.
        self.assertEqual(state["ux_section"],"Meu planejamento")
        self.assertEqual(state["flow_journey_view"],"build")
        for key in ("advisor_plan","ux502_interests","scenario_base_selected","ux41_favorites","ux36_cloud_dirty",SCOPE):
            self.assertEqual(state[key],before[key])

    def test_exploratory_scope_does_not_open_empty_build(self):
        state=self.state()
        state[SCOPE]=confirm_scope(state["ux502_interests"],["paris","angers"],self.discovery)
        before=deepcopy(state)
        queue_handoff(state,"planning",[])
        self.assertEqual(self.apply(state),"planning")
        self.assertEqual(state["ux_area"],"Explorar")
        self.assertEqual(state["ux502_view"],"Minha lista")
        self.assertNotIn("flow_journey_intent",state)
        self.assertEqual(state["advisor_plan"],before["advisor_plan"])
        self.assertEqual(state["ux502_interests"],before["ux502_interests"])

    def test_reset_discards_pending_and_prior_context(self):
        state=self.state()
        queue_handoff(state,"manual",["angers","metz"])
        self.apply(state)
        queue_handoff(state,"map",["angers"])
        clear_recommendation_context(state)
        for key in (SCOPE,PENDING,CONTEXT,PREVIOUS):
            self.assertNotIn(key,state)
        self.assertEqual(state["scenario_base_selected"],"metz")


class HandoffAppTests(unittest.TestCase):

    def test_manual_view_to_other_public_area_reopens_suggestions(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        self.assertFalse(app.exception,str(app.exception))
        app.button(key="ux_sidebar_nav_1").click().run()
        app.session_state["rec03a_activity"]="Comparação personalizada"
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(sum(b.key=="rec03a_handoff_back_manual"
                             for b in app.button),1)
        app.segmented_control(key="ux64_public_task").set_value("Mapa").run()
        self.assertFalse(app.exception,str(app.exception))
        app.segmented_control(key="ux64_public_task").set_value("Comparar bases").run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(app.session_state["rec03a_activity"],"Cidades sugeridas")
        self.assertFalse(any(b.key=="rec03a_handoff_back_manual" for b in app.button))

    def test_real_app_suggestions_manual_and_planning_return(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,str(app.exception))
        discovery=build_exploration_discovery()
        wishes=empty_interests()
        for d in ("paris","colmar","strasbourg","basel","lucerne","interlaken","angers"):
            wishes=set_interest(wishes,d,"interested",discovery)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        original=deepcopy(app.session_state["advisor_plan"])
        def click(key):
            app.button(key=key).click().run()
            self.assertFalse(app.exception,str(app.exception))
        click("ux_sidebar_nav_1")
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertFalse(app.exception,str(app.exception))
        click("rec03a_confirm_subset")
        scope=deepcopy(app.session_state[SCOPE])
        def choose_city(base):
            key="rec03a_pick_"+base
            if not any(x.key==key for x in app.checkbox):
                if not app.checkbox(key="rec03a_show_all").value:
                    app.checkbox(key="rec03a_show_all").check().run()
                app.text_input(key="rec03a_search").set_value(base).run()
            self.assertFalse(app.exception,str(app.exception))
            app.checkbox(key=key).check().run()
            self.assertFalse(app.exception,str(app.exception))
        choose_city("strasbourg")
        choose_city("angers")
        # UX87 uses the same CHOICE but renders in its dedicated view.
        self.assertFalse(any('class="ux97-table"' in m.value for m in app.markdown))
        app.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertTrue(any('class="ux97-table"' in m.value for m in app.markdown))
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self.assertTrue(any(x.key=="rec03a_inline_sources" for x in app.checkbox))
        self.assertFalse(any(b.key=="rec03a_handoff_compare" for b in app.button))
        # REC03B manual handoff remains supported as a legitimate legacy path.
        queue_handoff(app.session_state,"manual",["strasbourg","angers"])
        app.run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(sum(b.key=="rec03a_handoff_back_manual"
                             for b in app.button),1)
        self.assertFalse(any(b.key=="rec03a_manual_to_suggested" for b in app.button))
        self.assertEqual(app.multiselect(key="ux503_bases").value,["strasbourg","angers"])
        self.assertEqual(set(app.multiselect(key="ux503_visible_destinations").value),set(scope["destination_ids"]))
        click("rec03a_handoff_back_manual")
        self.assertEqual(app.session_state[SCOPE],scope)
        self.assertEqual(app.session_state["rec03a_handoff_base_selection"],["strasbourg","angers"])
        app.segmented_control(key="ux112_active_view").set_value("Explorar alternativas").run()
        # Open a real candidate profile and its map, with the same scope.
        buttons=[b for b in app.button if b.key and b.key.startswith("rec03a_handoff_profile_")]
        self.assertTrue(buttons)
        key=buttons[0].key
        base=next(x["id"] for x in load_research(include_candidates=True)["cities"]
                  if key.endswith("_"+x["id"]))
        click(key)
        self.assertEqual(app.session_state[CONTEXT]["base_ids"],[base])
        self.assertFalse(any(w.key=="expanded_bases_detail_city" for w in app.selectbox))
        profile_titles=[m.value for m in app.markdown]
        self.assertFalse(any("Explorar cidades-base" in x for x in profile_titles))
        self.assertTrue(any(base.title() in x and "## " in x for x in profile_titles))
        self.assertTrue(any("Como seria morar aqui por dois meses?" in x for x in profile_titles))
        self.assertFalse(any("Investigue por assunto" in x for x in profile_titles))
        self.assertEqual(len(app.segmented_control(key="ux124_topic_"+base).options),6)
        self.assertFalse(any("#### Explore uma cidade" in x for x in profile_titles))
        self.assertFalse(any("### Explorar cidades" in x for x in profile_titles))
        self.assertTrue(any(b.key=="rec04_simulate_profile" and not b.disabled
                            for b in app.button))
        self.assertTrue(any(b.key=="rec03a_handoff_favorite" for b in app.button))
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.segmented_control(key="ux124_topic_"+base).set_value("Logística").run()
        self.assertFalse(app.exception,str(app.exception))
        app.segmented_control(key="ux124_routes_"+base).set_value("Com tempo pesquisado").run()
        self.assertFalse(app.exception,str(app.exception))
        click("rec03a_profile_discover")
        self.assertEqual(app.session_state["ux_section"],"Passeios")
        click("rec03a_profile_discovery_back")
        self.assertEqual(app.segmented_control(key="ux124_topic_"+base).value,"Logística")
        self.assertEqual(app.segmented_control(key="ux124_routes_"+base).value,"Com tempo pesquisado")
        self.assertEqual(app.session_state[CONTEXT]["base_ids"],[base])
        self.assertEqual(app.session_state[SCOPE],scope)
        self.assertEqual(app.session_state["advisor_plan"],original)
        click("rec03a_handoff_profile_map")
        self.assertEqual(app.session_state[CONTEXT]["kind"],"map")
        # The sidebar reports missing optional Drive credentials in CI.
        # Assert the actual map body, not unrelated synchronization diagnostics.
        errors=[e.value for e in app.error]
        sidebar_errors=[e.value for e in app.sidebar.error]
        from collections import Counter
        body_errors=list((Counter(errors)-Counter(sidebar_errors)).elements())
        self.assertFalse(body_errors, str(errors))
        self.assertTrue(any("Mapa das alternativas" in m.value for m in app.markdown))
        self.assertTrue(app.get("deck_gl_json_chart"), "Contextual map not rendered")
        self.assertTrue(app.dataframe, "Rail evidence table not rendered")
        click("rec03a_handoff_back_map")
        self.assertEqual(app.session_state[SCOPE],scope)
        self.assertEqual(app.session_state[CONTEXT]["kind"],"profile")
        self.assertEqual(app.session_state[CONTEXT]["base_ids"],[base])
        selected=list(app.session_state["rec03a_handoff_base_selection"])
        click("rec03a_profile_compare")
        self.assertEqual(app.session_state["rec03a_handoff_base_selection"],
                         selected if base in selected else selected+[base])
        self.assertEqual(app.session_state["ux112_active_view"],"Minha comparação")
        self.assertEqual(app.session_state["advisor_plan"],original)
        # Continue from the existing comparison view into planning.
        app.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertNotIn("rec03a_planning_open",{x.key for x in app.checkbox})
        click("rec03a_handoff_planning")
        self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
        self.assertEqual(app.session_state["flow_journey_view"],"build")
        self.assertEqual(app.session_state["advisor_plan"],original)
        click("rec03a_handoff_back_planning")
        self.assertEqual(app.session_state[SCOPE],scope)
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(app.session_state["ux502_interests"],wishes)


if __name__=="__main__":
    unittest.main()
