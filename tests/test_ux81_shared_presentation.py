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


    def test_strong_variant_has_its_own_background_without_original_key(self):
        html = next_action('<Planning>', 'Check & save', variant='strong')
        self.assertIn('ui-next-action--strong', html)
        self.assertIn('&lt;Planning&gt;', html)
        self.assertIn('Check &amp; save', html)
        self.assertNotIn('flow_journey_next', html)
        self.assertNotIn('<button', html)
        css = (Path(__file__).resolve().parents[1] / "assets" / "styles.css").read_text()
        import re
        self.assertRegex(css, r'(?s):is\(\s*\.ui-next-action--strong,'
                              r'.*?\)\s*\{[^}]*background:radial-gradient')
        self.assertIn('.ui-next-action--strong {max-width:none;}', css)

    def test_strong_shared_and_legacy_cta_shells_never_nest_two_cards(self):
        css = (Path(__file__).resolve().parents[1] / "assets" / "styles.css").read_text()
        import re
        reset = re.search(r'(?s):is\(\s*\[class\*="st-key-ui_action_shell_strong_"\],'
                          r'\s*\[class\*="st-key-flow_journey_next"\]\s*\)'
                          r'\s*\.ui-next-action--strong\s*\{([^}]+)\}', css)
        self.assertIsNotNone(reset)
        for style in ('background:none', 'box-shadow:none', 'border:0',
                      'margin:0', 'padding:0', 'max-width:820px'):
            self.assertIn(style, reset[1])
        self.assertIn('[data-testid="stButton"] button:focus-visible', css)
        self.assertIn('[data-testid="stButton"] button:disabled', css)
        self.assertIn('button:hover:not(:disabled)', css)
        self.assertEqual(css.count('background:radial-gradient(circle at 98%'), 1)

    def test_compact_variant_and_aa_contrast_of_strong_compact_and_cta(self):
        css = (Path(__file__).resolve().parents[1] / "assets" / "styles.css").read_text()
        self.assertIn('ui-next-action--compact', next_action('A','B',variant='compact'))
        self.assertIn('background:#EEF6F7', css)
        self.assertIn('color:#163A4D', css)
        self.assertIn('color:#4B6572', css)
        def luminance(value):
            v = value.lstrip('#')
            channels = [int(v[n:n+2],16)/255 for n in (0,2,4)]
            linear = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4
                      for x in channels]
            return sum(x*y for x,y in zip(linear,(.2126,.7152,.0722)))
        def contrast(a,b):
            x,y=sorted((luminance(a),luminance(b)),reverse=True)
            return (x+.05)/(y+.05)
        def overlay(fg,bg,alpha):
            f=bytes.fromhex(fg.lstrip('#'))
            b=bytes.fromhex(bg.lstrip('#'))
            return '#'+''.join(f'{round(x*alpha+y*(1-alpha)):02x}'
                              for x,y in zip(f,b))
        brightest=overlay('#55B8C5','#124D60',.18)
        for foreground,background in (
            ('#BCE8E7',brightest),('#E3F1F3',brightest),
            ('#FFFFFF',brightest),('#245B6D','#EEF6F7'),
            ('#163A4D','#EEF6F7'),('#4B6572','#EEF6F7'),
            ('#15516B','#FFFFFF'),('#395565','#DDECF0')
        ):
            with self.subTest(foreground=foreground,background=background):
                self.assertGreaterEqual(contrast(foreground,background),4.5)

    def test_native_cta_in_shared_and_original_shells_is_not_fake_html_button(self):
        """AppTest checks callbacks/HTML structure; does NOT validate CSS pixels."""
        from streamlit.testing.v1 import AppTest
        script = '''
import streamlit as st
from ux_shared_ui_presentation import next_action
with st.container(key="ui_action_shell_strong_explorar"):
    st.markdown(next_action("Adicionar ao roteiro", "Escolha seus destinos"),
                unsafe_allow_html=True)
    st.button("Continuar", key="shared_native_cta", type="primary",
              on_click=lambda: st.session_state.update(shared_clicked=True))
with st.container(key="flow_journey_next"):
    st.markdown(next_action("Meu roteiro", "Revisar rascunho"),
                unsafe_allow_html=True)
    st.button("Revisar", key="flow_journey_primary", type="primary")
st.markdown(next_action("Resumo financeiro", "Comparar cenários", variant="compact"),
            unsafe_allow_html=True)
'''
        app=AppTest.from_string(script,default_timeout=30).run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertIn('shared_native_cta',{b.key for b in app.button})
        self.assertIn('flow_journey_primary',{b.key for b in app.button})
        self.assertEqual(sum('ui-next-action--strong' in m.value for m in app.markdown),2)
        self.assertEqual(sum('ui-next-action--compact' in m.value for m in app.markdown),1)
        app.button(key='shared_native_cta').click().run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertTrue(app.session_state['shared_clicked'])

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
