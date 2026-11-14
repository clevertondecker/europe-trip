"""Execute all major Streamlit pages headlessly to catch runtime errors.

AppTest does not render a browser image or interactive maps; manual visual
verification remains necessary after deployment.
"""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
PAGES=["Visão geral","Mapa & destinos","Comparar cidades",
       "Roteiro","Orçamento","Pesquisas & decisões"]
class AppSmokeTests(unittest.TestCase):
    def test_all_six_pages_render_without_exceptions(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=40).run()
        self.assertEqual(len(at.exception),0, [e.message for e in at.exception])
        for page in PAGES[1:]:
            with self.subTest(page=page):
                at.radio(key="main_navigation").set_value(page).run()
                self.assertEqual(len(at.exception),0,[e.message for e in at.exception])
if __name__=="__main__":unittest.main()
