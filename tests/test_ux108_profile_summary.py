"""UX108: city profile is a decision-oriented read-only research view."""
from __future__ import annotations

import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

from base_research_expanded_model import load_research, find_city
from ux124_city_profile_model import city_profile,TOPICS


def view(city_id: str, *, fixed=True):
    code=(
        "from base_research_expanded_ui import render_expanded_research\n"
        "render_expanded_research(activity_override='Explorar uma cidade',"
        f"compact=True,fixed_city={city_id!r})"
    ) if fixed else (
        "from base_research_expanded_ui import render_expanded_research\n"
        "render_expanded_research(activity_override='Explorar uma cidade',"
        "compact=True,fixed_city=None)"
    )
    app=AppTest.from_string(code,default_timeout=120).run()
    assert not app.exception, [x.message for x in app.exception]
    return app


class ProfileResearchTests(unittest.TestCase):
    def test_historical_values_are_derived_from_the_research_model(self):
        study=load_research(include_candidates=True)
        app=view("strasbourg")
        city=find_city(study,"strasbourg")
        expected=city_profile("strasbourg",research=study)
        timed=expected["counts"].get("historical",0)+expected["counts"].get("reference_only",0)
        total=expected["catalog_destination_count"]-expected["counts"].get("local",0)
        from ux124b_profile_presentation import compact_money
        self.assertEqual(app.metric[0].value,compact_money(expected["housing"]["median_eur_month"]))
        self.assertEqual(app.metric[1].value,"—")
        self.assertIn("mediana histórica",app.metric[0].label)
        self.assertIn("destinos desejados",app.metric[1].label.lower())
        labels=[m.value for m in app.markdown]
        self.assertNotIn("### Investigue por assunto",labels)
        self.assertEqual(tuple(app.segmented_control(key="ux124_topic_strasbourg").options),TOPICS)
        self.assertTrue(any("Fontes e pendências" in x.label for x in app.expander))
        self.assertTrue(any("Pontos de atenção" in m.value for m in app.markdown))
        self.assertTrue(any("Ainda pendente" in m.value for m in app.caption))
        self.assertFalse(any("#### Moradia e custo observado" in x for x in labels))
        self.assertNotIn("### Explorar cidades",labels)

    def test_data23_and_ux105_remain_distinct_from_historical_times(self):
        for city in ("angers","annecy","aachen","arlon"):
            with self.subTest(city=city):
                app=view(city)
                self.assertEqual(tuple(app.segmented_control(key="ux124_topic_"+city).options),TOPICS)
                app.segmented_control(key="ux124_topic_"+city).set_value("Logística").run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
                self.assertTrue(any("Transporte urbano e última milha" in m.value for m in app.markdown))
                self.assertTrue(any("Conexões fora do catálogo" in x.label for x in app.expander)
                                if city in ("angers","annecy") else True)
                self.assertFalse(any("Nota final" in str(x.value) for x in app.metric))

    def test_city_without_2026_housing_is_not_presented_as_quoted_for_2027(self):
        study=load_research(include_candidates=True)
        city=next(c for c in study["cities"] if not c["housing_offers"])
        app=view(city["id"])
        self.assertEqual(app.metric[0].value,"Não pesquisado")
        self.assertTrue(any("Ainda pendente" in m.value for m in app.caption))

    def test_independent_explorer_keeps_original_headings(self):
        app=view("strasbourg",fixed=False)
        labels=[m.value for m in app.markdown]
        self.assertIn("### Explorar cidades",labels)
        self.assertIn("#### Explore uma cidade",labels)
        self.assertFalse(any("### Explore os detalhes" in x for x in labels))
        self.assertTrue(any(w.key=="expanded_bases_detail_city" for w in app.selectbox))


if __name__=="__main__":
    unittest.main()
