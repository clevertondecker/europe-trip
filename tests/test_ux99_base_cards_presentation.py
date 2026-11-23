"""UX99 fragments must remain escaped, passive and evidence-only."""
import unittest
from ux99_base_cards_presentation import scope_chips, insight_panels


class BaseCardPresentationTests(unittest.TestCase):
    def test_scope_is_escaped_and_read_only(self):
        html=scope_chips(["x"], {"x": "<script>alert(1)</script>"})
        self.assertIn("&lt;script&gt;",html)
        self.assertNotIn("<script>",html)
        self.assertNotIn("<button",html)
        self.assertIn("Seus destinos",html)

    def test_neutral_state_is_not_painted_as_positive_and_cards_are_concise(self):
        html=insight_panels({
            "advantages":[],
            "neutral":[{"text":"Nenhuma vantagem comprovada"}],
            "cautions":[{"text":"Cuidado A"},{"text":"Cuidado B"},{"text":"Cuidado C"}]})
        self.assertIn("ux99-insight--neutral",html)
        self.assertNotIn("ux99-insight--pros",html)
        self.assertIn("Nenhuma vantagem comprovada",html)
        self.assertIn("Cuidado A",html)
        self.assertIn("Cuidado B",html)
        self.assertNotIn("Cuidado C",html)

    def test_research_documentation_uses_neutral_not_green(self):
        html=insight_panels({
            "advantages":[],
            "documented":[{"text":"Há referências de ida para alguns destinos"}],
            "cautions":[{"text":"Retorno não verificado"}]})
        self.assertIn("O que já foi pesquisado",html)
        self.assertIn("ux99-insight--neutral",html)
        self.assertNotIn("ux99-insight--pros",html)
        self.assertNotIn("Vantagens comparativas",html)

    def test_pro_and_caution_panels_have_no_fake_interactivity(self):
        html=insight_panels({"advantages":[{"text":"Referências para imperdíveis"}],
                             "cautions":[{"text":"<b>Tempo pendente</b>"}]})
        self.assertIn("ux99-insight--pros",html)
        self.assertIn("ux99-insight--cons",html)
        self.assertIn("&lt;b&gt;Tempo pendente&lt;/b&gt;",html)
        self.assertNotIn("<input",html)
        self.assertNotIn("<button",html)

if __name__ == "__main__":
    unittest.main()
