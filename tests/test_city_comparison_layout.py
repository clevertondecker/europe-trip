"""UI architecture regression: city comparison must not fall back to endless lists."""
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"

class CityComparisonLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contents = APP.read_text(encoding="utf-8")
        cls.page = contents.split('elif page == "Comparar cidades":', 1)[1].split('elif page == "Roteiro":', 1)[0]
        cls.app = contents

    def test_preserved_reference_sections(self):
        for title in ("Visão rápida", "Moradia", "Transporte e custos"):
            self.assertIn(title, self.page)
        self.assertIn("st.segmented_control(", self.page)
        self.assertIn("active_section", self.page)
        self.assertNotIn("st.tabs(", self.page)

    def test_cards_and_tables_have_evidence_labels(self):
        for field in ("Mediana de 3 anúncios", "Cotações válidas para 2027",
                      "Fonte TER", "Catálogo", "Tarifa reduzida Carte Fluo"):
            self.assertIn(field, self.page)

    def test_removes_editorial_ranking_and_preserves_real_links(self):
        for code in ("rank_cities(", "initialize_weight_state(", "city_compare_pair", "city_weight_"):
            self.assertNotIn(code,self.page)
        for code in ("st.column_config.LinkColumn", "load_market()", "load_audit()",
                     "Requisitos e documentos históricos", "render_city_decision(",
                     "render_recommendation_activity("):
            self.assertIn(code,self.page)
        self.assertNotIn("render_route_comparison(",self.page)

    def test_no_old_repeated_rail_links(self):
        self.assertNotIn('st.link_button(f"Fonte TER: {item', self.page)

    def test_other_sections_and_sync_still_present(self):
        for code in ('load_live_updates(credentials)',
                     'elif page == "Orçamento":', 'elif page == "Pesquisas & decisões":'):
            self.assertIn(code, self.app)

if __name__ == "__main__":
    unittest.main()
