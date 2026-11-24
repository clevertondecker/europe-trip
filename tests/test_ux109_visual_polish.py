"""UX109: city identity and research presentation with shared contracts preserved."""
import unittest
from streamlit.testing.v1 import AppTest
from base_research_expanded_model import load_research,find_city
from base_research_expanded_ui import _profile_summary_facts
from ux100_base_card_photos import base_card_photo_record


def load_view(base):
    return AppTest.from_string(
        'from base_research_expanded_ui import render_expanded_research\n'
        f'render_expanded_research(activity_override="Explorar uma cidade",'
        f'compact=True,fixed_city={base!r})',
        default_timeout=120,
    ).run()


class UX109ProfileTests(unittest.TestCase):
    def test_distinct_evidence_categories_and_verified_source_urls(self):
        research=load_research(include_candidates=True)
        for base in ("mulhouse","strasbourg","angers","annecy"):
            with self.subTest(base=base):
                rows=_profile_summary_facts(find_city(research,base),research)
                self.assertLessEqual(len(rows),2)
                self.assertEqual(len({r["section"] for r in rows}),len(rows))
                for row in rows:
                    self.assertTrue(row["source_url"].startswith("https://"))
                    self.assertTrue(row["summary"])

    def test_documented_photo_has_provenance_without_new_catalog(self):
        for base in ("mulhouse","strasbourg"):
            record=base_card_photo_record(base)
            self.assertIsNotNone(record)
            for field in ("author","license","license_url","source_page"):
                self.assertTrue(record.get(field),field)

    def test_fixed_city_compact_details_without_repeated_headings(self):
        app=load_view("mulhouse")
        self.assertFalse(app.exception,[e.message for e in app.exception])
        labels=[x.value for x in app.markdown]
        self.assertNotIn("### Investigue por assunto",labels)
        self.assertNotIn("#### Moradia e custo observado",labels)
        self.assertFalse(any("#### Trens, logística e passeios" in x for x in labels))
        self.assertIn("Moradia",app.segmented_control(key="ux124_topic_mulhouse").options)
        self.assertIn("Logística",app.segmented_control(key="ux124_topic_mulhouse").options)
        self.assertTrue(any("Fontes e pendências" in e.label for e in app.expander))
        self.assertTrue(any("Pontos fortes documentados" in x for x in labels))
        self.assertEqual(len(app.metric),2)

    def test_city_without_optional_pack_still_displays_canonical_summary(self):
        from city_profiles_model import load_profiles,profile_by_id
        from base_research_expanded_model import load_research
        research=load_research(include_candidates=True)
        expected=profile_by_id(load_profiles(canonical=research),"mulhouse")["summary"]
        app=AppTest.from_string(
            'from unittest.mock import patch\n'
            'from base_research_expanded_ui import render_expanded_research\n'
            'with patch("ux124_city_profile_model.pack_for_city",return_value=None):\n'
            '    render_expanded_research(activity_override="Explorar uma cidade",'
            'compact=True,fixed_city="mulhouse")',
            default_timeout=120,
        ).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        from collections import Counter
        from ux124b_profile_presentation import city_intro
        details=next(e for e in app.expander if "Fontes e pendências" in e.label)
        summaries=Counter(str(x.value) for x in app.markdown)
        summaries.subtract(str(x.value) for x in details.markdown)
        self.assertEqual(sum(n for item,n in summaries.items() if city_intro({"summary":expected}) in item),1)
        self.assertTrue(any(expected in item.value for item in details.caption))

    def test_independent_explorer_preserves_existing_headings(self):
        app=AppTest.from_string(
            'from base_research_expanded_ui import render_expanded_research\n'
            'render_expanded_research(activity_override="Explorar uma cidade",'
            'compact=True,fixed_city=None)',default_timeout=120,
        ).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        labels=[x.value for x in app.markdown]
        self.assertIn("### Explorar cidades",labels)
        self.assertIn("#### Explore uma cidade",labels)
        self.assertTrue(any(x.key=="expanded_bases_detail_city" for x in app.selectbox))


if __name__=="__main__":
    unittest.main()
