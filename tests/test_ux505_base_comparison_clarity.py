"""UX 5.0.5 — interpretation without modifying the comparison engine."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ux505_base_comparison_presentation import (
    comparison_overview, matrix_cell, known_findings, missing_research,
)
from ux502_destination_interests_model import empty_interests, set_interest

ROOT = Path(__file__).resolve().parents[1]


def sample_result():
    return {
        "base_ids":["strasbourg", "mulhouse"],
        "destinations":[
            {"id":"colmar","name":"Colmar","priority_label":"Imperdível"},
            {"id":"strasbourg","name":"Strasbourg",
             "priority_label":"Quero conhecer"}],
        "rows":[
            {"base_id":"strasbourg","destination_id":"colmar",
             "destination_name":"Colmar","minimum_oneway_min":35,
             "evidence_status":"historical_time","observations":[
                 {"minimum_oneway_min":35}],
             "divergent_sources":False},
            {"base_id":"strasbourg","destination_id":"strasbourg",
             "destination_name":"Strasbourg","minimum_oneway_min":None,
             "evidence_status":"local","observations":[],
             "divergent_sources":False},
            {"base_id":"mulhouse","destination_id":"colmar",
             "destination_name":"Colmar","minimum_oneway_min":None,
             "evidence_status":"partial","observations":[{"source_url":"https://example.com"}],
             "divergent_sources":True},
            {"base_id":"mulhouse","destination_id":"strasbourg",
             "destination_name":"Strasbourg","minimum_oneway_min":None,
             "evidence_status":"not_researched","observations":[],
             "divergent_sources":False},
        ],
        "summaries":[
            {"base_id":"strasbourg","base_name":"Strasbourg"},
            {"base_id":"mulhouse","base_name":"Mulhouse"},
        ],
    }


class InterpretiveComparisonTests(TestCase):
    def test_counts_describe_coverage_not_ranking_and_inputs_unchanged(self):
        result=sample_result()
        old=deepcopy(result)
        view=comparison_overview(result)
        self.assertEqual((view["total"],view["documented"],view["missing"],view["local"]),
                         (4,1,2,1))
        self.assertIn("1 possuem tempo histórico",view["description"])
        self.assertIn("não temos informações suficientes",view["description"])
        self.assertNotIn("melhor é",view["description"])
        self.assertEqual(result,old)

    def test_no_documented_time_does_not_mean_disconnected(self):
        result=sample_result()
        result["rows"][0]["minimum_oneway_min"]=None
        result["rows"][0]["evidence_status"]="not_researched"
        result["rows"][0]["observations"]=[]
        view=comparison_overview(result)
        self.assertEqual((view["documented"],view["missing"],view["local"]),(0,3,1))
        self.assertIn("não significa ausência de conexão",view["description"])
        self.assertIn("não podemos comparar com segurança",view["description"])

    def test_matrix_keeps_local_partial_unknown_and_conflicts_distinct(self):
        result=sample_result()
        self.assertEqual(matrix_cell(result["rows"][0]),"35 min · ida histórica")
        self.assertEqual(matrix_cell(result["rows"][1]),"Local — acesso a verificar")
        self.assertEqual(matrix_cell(result["rows"][2]),
                         "Pesquisa parcial · tempo não identificado · fontes divergentes")
        self.assertEqual(matrix_cell(result["rows"][3]),"Tempo não pesquisado")
        self.assertIn("tempos divergentes"," ".join(missing_research(result)))
        self.assertIn("acesso local"," ".join(missing_research(result)).lower())

    def test_findings_describe_observations_without_electing_base(self):
        result=sample_result()
        findings=known_findings(result)
        self.assertIn("Colmar (35 min)",findings[0])
        self.assertIn("ainda sem tempos históricos",findings[1])
        self.assertIn("não qual cidade-base",findings[-1])


class ComparisonPresentationAppTests(TestCase):
    def _open(self, interests=None):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        before=deepcopy(app.session_state["advisor_plan"])
        app.radio(key="ux_area").set_value("Explorar").run()
        if interests is not None:
            app.session_state["ux502_interests"]=interests
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        return app,before

    def test_empty_list_explains_need_for_destinations_and_preserves_plan(self):
        app,plan=self._open(empty_interests())
        self.assertTrue(any("Sua lista está vazia" in i.value for i in app.info))
        self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_selected_wishes_summary_matrix_and_navigation(self):
        wishes=set_interest(empty_interests(),"colmar","must_visit")
        app,plan=self._open(wishes)
        values=" ".join(x.value for x in app.markdown)
        self.assertIn("Como seria visitar nossos destinos a partir de cada cidade?",values)
        self.assertIn("O que podemos concluir com os dados atuais?",values)
        self.assertIn("O que ainda precisamos pesquisar?",values)
        self.assertTrue(any("Trajetos com tempo pesquisado" in x.label for x in app.metric))
        self.assertTrue(app.dataframe)
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        app.button(key="ux503_back_to_wishes").click().run()
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
            app.multiselect(key="ux503_bases").set_value(["mulhouse","strasbourg"]).run()
            matrix=next(f.value for f in app.dataframe
                        if "Destino · prioridade" in f.value.columns)
            cells=" ".join(str(x) for x in matrix.to_numpy().flatten())
            self.assertIn("Local — acesso a verificar",cells)
            self.assertIn("fontes divergentes",cells)
            self.assertIn("Tempo não pesquisado",cells)
            self.assertEqual(app.session_state["advisor_plan"],plan)
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            self.assertFalse(app.exception,[e.message for e in app.exception])
