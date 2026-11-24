"""UX107 regression: individual profile does not change the independent explorer."""
import unittest
from streamlit.testing.v1 import AppTest


class ProfileHierarchyTests(unittest.TestCase):
    def test_independent_compact_explorer_keeps_heading_and_selector(self):
        app=AppTest.from_string(
            'from base_research_expanded_ui import render_expanded_research\n'
            'render_expanded_research(activity_override="Explorar uma cidade",'
            'compact=True,fixed_city=None)',
            default_timeout=90,
        ).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("### Explorar cidades" in m.value
                            for m in app.markdown))
        self.assertTrue(any("#### Explore uma cidade" in m.value
                            for m in app.markdown))
        self.assertTrue(any(x.key=="expanded_bases_detail_city"
                            for x in app.selectbox))

    def test_fixed_city_mode_omits_redundant_headings_without_losing_data(self):
        app=AppTest.from_string(
            'from base_research_expanded_ui import render_expanded_research\n'
            'render_expanded_research(activity_override="Explorar uma cidade",'
            'compact=True,fixed_city="strasbourg")',
            default_timeout=90,
        ).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertFalse(any("### Explorar cidades" in m.value or
                             "#### Explore uma cidade" in m.value
                             for m in app.markdown))
        self.assertFalse(any(x.key=="expanded_bases_detail_city"
                             for x in app.selectbox))
        self.assertIn("Aluguel mensal",app.metric[0].label)
        self.assertEqual(app.metric[1].value,"—")



if __name__=="__main__":
    unittest.main()
