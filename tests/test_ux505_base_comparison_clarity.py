"""UX 5.0.5 — interpretation without modifying the comparison engine."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ux502_destination_interests_model import empty_interests, set_interest

ROOT = Path(__file__).resolve().parents[1]


class ComparisonPresentationAppTests(TestCase):
    def _open(self, interests=None):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        before=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        if interests is not None:
            app.session_state["ux502_interests"]=interests
        app.session_state["rec03a_activity"]="Comparação personalizada"
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        if interests and interests.get("items"):
            app.button(key="rec03a_confirm_subset").click().run()
            app.session_state["rec03a_handoff_base_selection"]=["mulhouse","strasbourg"]
            app.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        return app,before

    def test_empty_list_explains_need_for_destinations_and_preserves_plan(self):
        app,plan=self._open(empty_interests())
        self.assertTrue(any("Nenhum destino ativo" in i.value for i in app.info))
        self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_selected_wishes_summary_matrix_and_navigation(self):
        wishes=set_interest(empty_interests(),"colmar","must_visit")
        app,plan=self._open(wishes)
        values=" ".join(x.value for x in app.markdown)
        self.assertIn("Comparar cidades-base",values)
        self.assertIn("Tempos de ida por destino",values)
        self.assertIn("Resumo da comparação",values)
        self.assertIn("ux97-table",values)
        self.assertTrue(any(x.key=="rec03a_inline_sources" for x in app.checkbox))
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        app.button(key="rec03a_back_wishlist").click().run()
        self.assertEqual(app.session_state["ux_section"],"Passeios")
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_no_time_partial_divergent_and_local_remain_visible(self):
        wishes=set_interest(empty_interests(),"strasbourg","must_visit")
        wishes=set_interest(wishes,"colmar","interested")
        # Oeschinensee has no station-to-attraction duration: it remains an
        # intentionally unresearched cell after additive DATA11 coverage.
        wishes=set_interest(wishes,"oeschinen","interested")
        def mock_evidence(base_id,destination_id,**kwargs):
            if base_id==destination_id:
                status,minutes,observations="local",None,[]
            elif base_id=="mulhouse" and destination_id=="colmar":
                status,minutes="partial",None
                observations=[{"source_url":"https://example.org/one"},
                              {"source_url":"https://example.org/two"}]
            else:
                status,minutes,observations="not_researched",None,[]
            if base_id=="mulhouse" and destination_id=="colmar":
                observations=[{"minimum_oneway_min":30,"source_url":"https://example.org/one"},
                              {"minimum_oneway_min":45,"source_url":"https://example.org/two"}]
                status,minutes="historical_time",30
            return {"status":status,"minimum_oneway_min":minutes,
                    "typical_oneway_min":None,
                    "source_url":observations[0].get("source_url") if observations else None,
                    "source_date":"2026-11-14" if observations else None,
                    "source_dataset":"fixture" if observations else None,
                    "observations":observations}
        with patch("ux503_destination_base_comparison_model.get_rail_evidence",
                   side_effect=mock_evidence):
            app,plan=self._open(wishes)
            cells=next(m.value for m in app.markdown if 'class="ux97-table"' in m.value)
            self.assertIn("Acesso local pendente",cells)
            self.assertIn("tempos publicados diferentes",cells)
            self.assertIn("Sem tempo",cells)
            self.assertEqual(app.session_state["advisor_plan"],plan)
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            self.assertFalse(app.exception,[e.message for e in app.exception])
