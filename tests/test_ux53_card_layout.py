"""UX 5.3: opt-in card layout and native interaction source contracts.

These are structural checks, not a substitute for browser screenshot geometry.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class UnifiedCardLayoutTests(unittest.TestCase):
    def test_scoped_css(self):
        css = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        for token in ('st-key-ux53_row_', 'align-items: stretch',
                      'margin-top: auto', '[data-testid="stColumn"]',
                      '> :last-child', 'aspect-ratio: 16 / 9'):
            self.assertIn(token, css)

    def test_grid_scopes(self):
        cases = (
            ("ux501_destination_discovery_ui.py", "destinations", "destination"),
            ("attractions_ui.py", "dq32", "dq32"),
            ("base_research_expanded_ui.py", "bases", "base"),
        )
        for path, row, card in cases:
            with self.subTest(path=path):
                code = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("ux53_row_" + row, code)
                self.assertNotIn("ux53_card_" + card, code)
                self.assertIn("border=True", code)
                self.assertIn("ux53_footer_" + card, code)
                self.assertIn("st.columns(", code)

    def test_native_border_is_the_card_not_a_nested_container(self):
        discovery = (ROOT / "ux501_destination_discovery_ui.py").read_text(encoding="utf-8")
        rail = (ROOT / "attractions_ui.py").read_text(encoding="utf-8")
        bases = (ROOT / "base_research_expanded_ui.py").read_text(encoding="utf-8")
        self.assertIn("st.columns(len(row_items), border=True)", discovery)
        self.assertIn('st.columns(2, gap="medium", border=True)', rail)
        self.assertIn("st.columns(2, border=True)", bases)
        self.assertNotIn("ux53_card_destination_", discovery)
        self.assertNotIn("ux53_card_dq32_", rail)
        self.assertNotIn("ux53_card_base_", bases)

    def test_discovery_callbacks_and_attributions_preserved(self):
        code = (ROOT / "ux501_destination_discovery_ui.py").read_text(encoding="utf-8")
        for term in ("Fonte original", "Fonte e licença", "Foto a pesquisar",
                     "Consultar fonte turística", "Ver atrações e fontes",
                     "Salvar na lista", "on_click=add_destination", "Adicionar ao roteiro", "commit_outing(",
                     'key="ux501_page"'):
            self.assertIn(term, code)

    def test_existing_callback_contracts(self):
        rail = (ROOT / "attractions_ui.py").read_text(encoding="utf-8")
        bases = (ROOT / "base_research_expanded_ui.py").read_text(encoding="utf-8")
        self.assertIn("on_click=_dq32_choose_destination", rail)
        self.assertIn("on_click=_open_city", bases)
        self.assertIn("Duração ainda não pesquisada", rail)

if __name__ == "__main__":
    unittest.main()
