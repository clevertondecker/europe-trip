"""UX111: one CHOICE source for card feedback, removal and adjacent navigation."""
import unittest
from streamlit.testing.v1 import AppTest
from rec03b_handoffs import CHOICE


OPTIONS=("strasbourg","colmar","lille","mulhouse","metz","nancy")
CITIES={name:{"name":name.title()} for name in OPTIONS}
CODE=(
    'import streamlit as st\n'
    'from rec03b_handoff_ui import render_card_choice,render_selection_toolbar\n'
    'from rec03b_handoffs import CHOICE\n'
    'OPTIONS='+repr(OPTIONS)+'\n'
    'CITIES='+repr(CITIES)+'\n'
    'st.markdown(\'<div id="ux111-comparison"></div>\',unsafe_allow_html=True)\n'
    'for name in OPTIONS:\n'
    '    render_card_choice(name,OPTIONS,show_selection_hint=False)\n'
    'st.markdown(\'<div id="ux111-picker"></div>\',unsafe_allow_html=True)\n'
    'render_selection_toolbar(OPTIONS,CITIES)\n'
)


class UX111SelectionTests(unittest.TestCase):
    def app(self,chosen=()):
        app=AppTest.from_string(CODE,default_timeout=45)
        app.session_state[CHOICE]=list(chosen)
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        return app

    def test_add_third_city_updates_canonical_choice_and_visible_feedback(self):
        app=self.app(("strasbourg","colmar"))
        app.checkbox(key="rec03a_pick_lille").check().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state[CHOICE],["strasbourg","colmar","lille"])
        captions=[str(c.value) for c in app.caption]
        self.assertTrue(any("Adicionada" in x and "3 de 5" in x for x in captions))
        self.assertTrue(any("Cidades selecionadas · 3 de 5" in x.value
                            for x in app.markdown))
        self.assertTrue(any("href=\"#ux111-comparison\"" in x.value
                            for x in app.markdown))

    def test_remove_in_toolbar_unchecks_card_without_changing_plan(self):
        app=self.app(("strasbourg","colmar","lille"))
        app.session_state["advisor_plan"]={"base_city":"mulhouse"}
        app.button(key="ux111_remove_colmar").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state[CHOICE],["strasbourg","lille"])
        self.assertFalse(app.checkbox(key="rec03a_pick_colmar").value)
        self.assertEqual(app.session_state["advisor_plan"],{"base_city":"mulhouse"})

    def test_five_city_limit_blocks_sixth_until_removal(self):
        app=self.app(OPTIONS[:5])
        self.assertTrue(app.checkbox(key="rec03a_pick_nancy").disabled)
        app.button(key="ux111_remove_metz").click().run()
        self.assertFalse(app.checkbox(key="rec03a_pick_nancy").disabled)
        app.checkbox(key="rec03a_pick_nancy").check().run()
        self.assertEqual(app.session_state[CHOICE],["strasbourg","colmar","lille","mulhouse","nancy"])

    def test_single_city_has_no_comparison_link(self):
        app=self.app(("colmar",))
        html="\n".join(str(x.value) for x in app.markdown)
        self.assertIn("Escolha pelo menos duas cidades",str([x.value for x in app.info]))
        self.assertNotIn('class="ux111-primary-action"',html)

    def test_removed_or_invalid_ids_are_never_shown_in_projection(self):
        app=self.app(("strasbourg","unknown","strasbourg","colmar"))
        self.assertEqual(sum(b.key=="ux111_remove_strasbourg" for b in app.button),1)
        self.assertFalse(any(b.key=="ux111_remove_unknown" for b in app.button))


if __name__=="__main__":
    unittest.main()
