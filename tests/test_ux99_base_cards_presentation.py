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
