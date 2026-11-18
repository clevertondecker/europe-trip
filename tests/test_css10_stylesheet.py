"""CSS 1.0: design token and Streamlit UI regression contracts.

These tests check structural invariants, not rendered pixel equality. Keep
browser screenshots as a separate acceptance step.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
CSS=ROOT/"assets"/"styles.css"
APP=ROOT/"app.py"

def _strip_comments(source: str)->str:
    return re.sub(r"/\*.*?\*/","",source,flags=re.S)

class StylesheetContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css=CSS.read_text(encoding="utf-8")
        cls.raw=_strip_comments(cls.css)

    def test_single_palette_and_active_typography(self):
        self.assertEqual(len(re.findall(r":root\s*\{",self.raw)),1)
        for token in ("--petrol","--green","--sand","--muted",
                      "--ui-heading","--ui-selected","--ui-page-bg",
                      "--ui-link","--ui-focus"):
            self.assertRegex(self.raw,re.escape(token)+r"\s*:")
        self.assertIn("font-family:'DM Sans',system-ui,sans-serif !important",self.raw)
        self.assertIn("h1{font-size:2.65rem !important;}",self.raw)
        self.assertIn("font-family:'Playfair Display',serif",self.raw)

    def test_global_overrides_only_have_one_active_declaration(self):
        self.assertEqual(self.raw.count('[data-testid="stAppViewContainer"]{background:'),1)
        self.assertEqual(self.raw.count('[data-testid="stSidebar"]{background:'),1)
        self.assertNotIn('background: #F8F6F1;',self.raw)
        self.assertNotIn("h1,h2,h3{color:#163A4D",self.raw)

    def test_focus_tabs_and_mobile_contracts(self):
        for selector in (
            '[data-testid="stTabs"] button[role="tab"]:focus-visible',
            '[data-testid="stSegmentedControl"] button:focus-visible',
            ':where([data-testid="stAppViewContainer"]) :is(button,input,textarea):focus-visible',
            '[data-testid="stSegmentedControl"] button[aria-checked="true"]',
            '@media (prefers-reduced-motion: reduce)',
            '@media (max-width: 680px)',
            'overflow-x:auto',
        ):
            self.assertIn(selector,self.raw)
        self.assertIn("var(--ui-selected)",self.raw)
        self.assertIn("var(--ui-focus)",self.raw)
        self.assertIn("min-height: 44px !important",self.raw)

    def test_loader_and_css_syntax_structure(self):
        app=APP.read_text(encoding="utf-8")
        self.assertIn('assets" / "styles.css"',app)
        self.assertIn("unsafe_allow_html=True",app)
        self.assertEqual(self.raw.count("{"),self.raw.count("}"))
        self.assertEqual(self.raw.count("/*"),0)
        self.assertNotIn("var(--ui-heading):",self.raw)

    def test_streamlit_app_still_renders(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(APP),default_timeout=120).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])

if __name__=="__main__":
    unittest.main()
