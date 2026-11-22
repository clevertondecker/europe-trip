"""UX81: a single pure, reusable accessible UI contract for all public tabs."""
from pathlib import Path
import unittest

from ux_shared_ui_presentation import (
    page_header, kpi_cards, next_action, section_heading, status_indicator,
)
from ux_planning_journey_presentation import (
    header_html, metric_html, next_html, step_html, project_visual_state,
)


class SharedPresentationTests(unittest.TestCase):
    def test_page_header_escapes_every_dynamic_field_and_preserves_save_truth(self):
        markup = page_header('<Trip "2027">', '<X>', 'A & B',
                             status_label='<saved?>', status_hint='"really"',
                             saved=False, tag='<Tag>')
        self.assertNotIn('<Trip', markup)
        for token in ('&lt;Trip &quot;2027&quot;&gt;', '&lt;X&gt;',
                      'A &amp; B', '&lt;saved?&gt;', '&quot;really&quot;', '&lt;Tag&gt;'):
            self.assertIn(token, markup)
        self.assertIn('journey-header__dot--local', markup)
        self.assertNotIn('journey-header__dot--saved', markup)
        self.assertIn('journey-header__dot--saved',
                      page_header('P', 'E', status_label='Salvo', saved=True))
        self.assertIn('ui-page-header--compact',
                      page_header('P', 'E', variant='compact'))

    def test_kpis_preserve_numbers_and_escape_monetary_values_and_attributes(self):
        metrics = [{"name": '<N>"', "value": 'R$ <1.000 & 2>',
                    "hint": '<span>X</span>', "icon": '"&',
                    "highlight": True}]
        markup = kpi_cards(metrics)[0]
        self.assertIn('journey-stat--highlight', markup)
        self.assertIn('aria-label="&lt;N&gt;&quot;: R$ &lt;1.000 &amp; 2&gt;"', markup)
        self.assertNotIn('<span>X</span>', markup)
        self.assertIn('R$ &lt;1.000 &amp; 2&gt;', markup)
        self.assertEqual(kpi_cards([]), ())
        self.assertIn('ui-kpi-card', markup)

    def test_next_action_has_no_fake_html_button_and_supports_density(self):
        html = next_action('<script>', '<bad & value>', variant='compact')
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&lt;bad &amp; value&gt;', html)
        self.assertIn('ui-next-action--compact', html)
        self.assertNotIn('<button', html)
        self.assertIn('journey-next__content', next_action('A', 'B'))

    def test_status_and_section_maintain_focus_separate_from_persistence(self):
        markup = status_indicator('<salvo>', active=True, kind='saved')
        self.assertIn('&lt;salvo&gt;', markup)
        self.assertIn('Em foco', markup)
        self.assertIn('ui-status-indicator--saved', markup)
        self.assertNotIn('Em foco', status_indicator('Disponível'))
        heading = section_heading('P&D', 'Seção <b>', 'Texto "X"', variant='compact')
        self.assertIn('P&amp;D', heading)
        self.assertIn('Seção &lt;b&gt;', heading)
        self.assertIn('&quot;X&quot;', heading)
        self.assertIn('ui-section-heading--compact', heading)

    def test_variants_reject_unknown_values(self):
        for fn in (lambda: page_header('X', 'Y', variant='huge'),
                   lambda: next_action('X', 'Y', variant='huge'),
                   lambda: section_heading('X', 'Y', variant='huge'),
                   lambda: status_indicator('X', kind='unknown')):
            with self.subTest(fn=fn):
                with self.assertRaises(ValueError):
                    fn()

    def test_existing_journey_delegates_and_keeps_public_html_contract(self):
        view = {
            "counts": {"wished": 3, "planned": 1, "organized": 0},
            "eligible_count": 1, "next": "build", "private_saved": False
        }
        visual = project_visual_state(view, "Rascunho nesta sessão")
        self.assertIn('journey-header', header_html('Rascunho nesta sessão', 'Local'))
        self.assertIn('journey-stat', metric_html(visual["metrics"][0]))
        self.assertIn('PRÓXIMA AÇÃO', next_html(visual))
        review = visual["steps"][-1]
        self.assertIn('journey-step__states', step_html(review))
        self.assertIn('ui-status-indicator', step_html(review))
        self.assertIn('journey-step__focus', step_html({
            **review, "active": True
        }))

    def test_css_single_source_and_scoped_variants(self):
        css = (Path(__file__).resolve().parents[1] / "assets" / "styles.css").read_text()
        self.assertEqual(css.count(":root {"), 1)
        self.assertIn(".ui-page-header--compact", css)
        self.assertIn(".ui-next-action--compact", css)
        self.assertIn(".ui-kpi-card", css)
        self.assertIn(".journey-next__anchor:focus-visible", css)
        self.assertNotIn(".ui-page-header *:focus {", css)


if __name__ == "__main__":
    unittest.main()
