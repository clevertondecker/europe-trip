"""UX108: city profile is a decision-oriented read-only research view."""
from __future__ import annotations

import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

from base_research_expanded_model import load_research, find_city
from base_coverage_model import coverage_matrix


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
        expected=next(r for r in coverage_matrix("general",study=study)
                      if r["id"]=="strasbourg")
        self.assertEqual(app.metric[0].value,str(len(city["housing_offers"])))
        self.assertEqual(
            app.metric[1].value,
            f'{expected["route_basket_with_time"]}/{expected["route_basket_total"]}'
        )
        self.assertIn("históricos de 2026",app.metric[0].label)
        self.assertIn("tempo pesquisado",app.metric[1].label)
        labels=[m.value for m in app.markdown]
        self.assertIn("### Investigue por assunto",labels)
        sections=["Moradia e bairros","Trens, logística e passeios",
                  "Vida cotidiana, bairros e clima","Fontes e metodologia"]
        expander_labels=[x.label for x in app.expander]
        for item in sections:
            self.assertTrue(any(item in x for x in expander_labels),item)
        self.assertTrue(any("Já documentado" in m.value for m in app.markdown))
        self.assertTrue(any("Ainda pendente" in m.value for m in app.markdown))
        self.assertFalse(any("#### Moradia e custo observado" in x for x in labels))
        self.assertNotIn("### Explorar cidades",labels)

    def test_data23_and_ux105_remain_distinct_from_historical_times(self):
        for city in ("angers","annecy","aachen","arlon"):
            with self.subTest(city=city):
                app=view(city)
                self.assertTrue(any("Investigue por assunto" in m.value for m in app.markdown))
                self.assertTrue(any("referências adicionais de ida" in c.value
                                    for c in app.caption)
                                if city in ("angers","annecy") else True)
                self.assertTrue(any("Mobilidade local e atrações complementares" in x.label
                                    for x in app.expander))
                self.assertFalse(any("Nota final" in str(x.value) for x in app.metric))

    def test_city_without_2026_housing_is_not_presented_as_quoted_for_2027(self):
        study=load_research(include_candidates=True)
        city=next(c for c in study["cities"] if not c["housing_offers"])
        app=view(city["id"])
        self.assertEqual(app.metric[0].value,"0")
        self.assertTrue(any("Ainda pendente" in m.value for m in app.markdown))

    def test_independent_explorer_keeps_original_headings(self):
        app=view("strasbourg",fixed=False)
        labels=[m.value for m in app.markdown]
        self.assertIn("### Explorar cidades",labels)
        self.assertIn("#### Explore uma cidade",labels)
        self.assertFalse(any("### Explore os detalhes" in x for x in labels))
        self.assertTrue(any(w.key=="expanded_bases_detail_city" for w in app.selectbox))


if __name__=="__main__":
    unittest.main()
