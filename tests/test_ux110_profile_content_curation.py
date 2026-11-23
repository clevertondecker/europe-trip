"""UX110: concise editorial research without changing coverage or planning data."""
import unittest
from streamlit.testing.v1 import AppTest
from base_research_expanded_model import load_research,find_city
from base_research_expanded_ui import _profile_summary_facts
from city_profiles_model import load_profiles,profile_by_id
from ux100_base_card_photos import base_card_photo_record


class UX110CurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research=load_research(include_candidates=True)

    def test_colmar_demographics_remain_in_sources_not_lead_summary(self):
        city=find_city(self.research,"colmar")
        lead=_profile_summary_facts(city,self.research)
        self.assertFalse(any("população" in item["summary"].casefold() for item in lead))
        full=profile_by_id(load_profiles(canonical=self.research),"colmar")
        self.assertTrue(any("População" in item["summary"] for item in full["evidence"]))

    def test_relevant_documented_sources_are_retained(self):
        for name in ("mulhouse","strasbourg","colmar","angers","annecy"):
            with self.subTest(name=name):
                city=find_city(self.research,name)
                lead=_profile_summary_facts(city,self.research)
                self.assertLessEqual(len(lead),2)
                self.assertEqual(len({item["section"] for item in lead}),len(lead))
                for item in lead:
                    self.assertTrue(item["source_url"].startswith("https://"))

    def test_colmar_photo_is_verified_city_specific_source(self):
        photo=base_card_photo_record("colmar")
        self.assertIn("Colmar_Petite_Venise_01.jpg",photo.get("source_page",""))
        self.assertEqual(photo["author"],"Zairon")
        self.assertEqual(photo["license"],"CC BY-SA 4.0")

    def test_zero_counts_are_explicitly_unknown_not_unavailable(self):
        app=AppTest.from_string(
            'from base_research_expanded_ui import render_expanded_research\n'
            'render_expanded_research(activity_override="Explorar uma cidade",'
            'compact=True,fixed_city="colmar")',
            default_timeout=120,
        ).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.metric[0].value,"0")
        self.assertEqual(app.metric[1].value,"0/15")
        captions=[str(item.value) for item in app.caption]
        self.assertTrue(any("não significa falta de imóveis" in x for x in captions))
        self.assertTrue(any("não significa falta de trens" in x for x in captions))
        self.assertTrue(any("Pesquisa e documentação" in str(x.value)
                            for x in app.markdown))
        self.assertTrue(any("Ainda faltam referências práticas" in x for x in captions))

    def test_independent_mode_keeps_its_existing_metrics(self):
        app=AppTest.from_string(
            'from base_research_expanded_ui import render_expanded_research\n'
            'render_expanded_research(activity_override="Explorar uma cidade",'
            'compact=True,fixed_city=None)',
            default_timeout=120,
        ).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.metric[0].label,"Anúncios históricos de 2026")
        self.assertIn("cesta histórica",app.metric[1].label.lower())


if __name__=="__main__":
    unittest.main()
