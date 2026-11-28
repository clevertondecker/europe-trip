import unittest
from streamlit.testing.v1 import AppTest
from rec03a_suggestions_ui import catalog_filter_options

CITIES = {"metz":{"name":"Metz","country":"França"},
          "nancy":{"name":"Nancy","country":"França"},
          "trier":{"name":"Trier","country":"Alemanha"}}
CANDIDATES = [{"base_id":b,"group":"comparable"} for b in CITIES]

APP = """
import streamlit as st
from rec03a_suggestions_ui import render_catalog_filters
from rec03b_handoffs import CHOICE
cities = %s
candidates = %s
if CHOICE not in st.session_state:
    st.session_state[CHOICE] = ["metz", "trier"]
if st.checkbox("Mostrar filtros", value=True, key="show_filters"):
    browsing, rows = render_catalog_filters(candidates, cities)
    st.write("RESULT:" + ",".join(c["base_id"] for c in rows) if browsing else "SUGGESTIONS")
st.write("CHOICE:" + ",".join(st.session_state[CHOICE]))
""" % (repr(CITIES), repr(CANDIDATES))

class CatalogFiltersTest(unittest.TestCase):
    def test_options_from_candidates(self):
        self.assertEqual(catalog_filter_options(CANDIDATES, CITIES, "França"),
                         (["Alemanha","França"], ["metz","nancy"]))
        self.assertEqual(catalog_filter_options(CANDIDATES[:1], CITIES),
                         (["França"], ["metz"]))

    def test_select_filter_clear_and_preserve_choice(self):
        app = AppTest.from_string(APP).run()
        def has(text):
            return any(text == m.value for m in app.markdown)
        self.assertFalse(app.exception)
        self.assertTrue(has("SUGGESTIONS"))
        app.selectbox(key="rec03a_country").select("França").run()
        self.assertFalse(app.exception)
        self.assertTrue(has("RESULT:metz,nancy"))
        app.selectbox(key="rec03a_city").select("nancy").run()
        self.assertTrue(has("RESULT:nancy"))
        app.session_state["rec03a_page_shadow"] = 3
        app.selectbox(key="rec03a_country").select("Alemanha").run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.selectbox(key="rec03a_city").value)
        self.assertEqual(app.session_state["rec03a_page_shadow"], 1)
        self.assertTrue(has("RESULT:trier"))
        app.checkbox(key="show_filters").uncheck().run()
        app.checkbox(key="show_filters").check().run()
        self.assertTrue(has("RESULT:trier"))
        app.button(key="rec03a_clear_filters").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(has("SUGGESTIONS"))
        self.assertTrue(has("CHOICE:metz,trier"))
