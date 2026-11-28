import unittest
from streamlit.testing.v1 import AppTest
from rec03a_suggestions_ui import catalog_filter_options

CITIES = {"metz":{"name":"Metz","country":"França"},
          "nancy":{"name":"Nancy","country":"França"},
          "trier":{"name":"Trier","country":"Alemanha"},
          "lille":{"name":"Lille","country":"França"},
          "colmar":{"name":"Colmar","country":"França"},
          "reims":{"name":"Reims","country":"França"}}
CANDIDATES = [{"base_id":b,"group":"conditional" if b=="nancy" else "comparable"} for b in CITIES]

APP = """
import streamlit as st
from rec03a_suggestions_ui import render_catalog_filters, catalog_page
from rec03b_handoffs import CHOICE
cities = %s
candidates = %s
if CHOICE not in st.session_state:
    st.session_state[CHOICE] = ["metz", "trier"]
if st.checkbox("Retirar candidatos", key="shrink"):
    candidates = [c for c in candidates if c["base_id"] not in ("nancy","trier","reims")]
if st.checkbox("Mostrar filtros", value=True, key="show_filters"):
    browsing, rows = render_catalog_filters(candidates, cities)
    st.write("RESULT:" + ",".join(c["base_id"] for c in rows) if browsing else "SUGGESTIONS")
    if browsing and rows:
        st.write("PAGE:" + ",".join(c["base_id"] for c in catalog_page(rows)))
st.write("CHOICE:" + ",".join(st.session_state[CHOICE]))
""" % (repr(CITIES), repr(CANDIDATES))

class CatalogFiltersTest(unittest.TestCase):
    def test_options_from_candidates(self):
        self.assertEqual(catalog_filter_options(CANDIDATES, CITIES, "França"),
                         (["Alemanha","França"], ["colmar","lille","metz","nancy","reims"]))
        self.assertEqual(catalog_filter_options(CANDIDATES[:1], CITIES),
                         (["França"], ["metz"]))

    def test_select_filter_clear_and_preserve_choice(self):
        app = AppTest.from_string(APP).run()
        def has(text):
            return any(text == m.value for m in app.markdown)
        self.assertFalse(app.exception)
        self.assertTrue(has("SUGGESTIONS"))
        self.assertNotIn("rec03a_country", {w.key for w in app.selectbox})
        app.segmented_control(key="rec03a_catalog_mode").set_value("Todas as cidades").run()
        self.assertTrue(has("RESULT:metz,nancy,trier,lille,colmar,reims"))
        app.number_input(key="rec03a_page").set_value(2).run()
        self.assertTrue(has("PAGE:colmar,reims"))
        app.selectbox(key="rec03a_country").select("França").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.number_input(key="rec03a_page").value, 1)
        self.assertTrue(has("RESULT:metz,nancy,lille,colmar,reims"))
        app.number_input(key="rec03a_page").set_value(2).run()
        app.selectbox(key="rec03a_category").select("Comparáveis").run()
        self.assertEqual(app.number_input(key="rec03a_page").value, 1)
        self.assertTrue(has("RESULT:metz,lille,colmar,reims"))
        app.selectbox(key="rec03a_city").select("nancy").run()
        self.assertTrue(has("RESULT:nancy"))
        self.assertEqual(app.session_state["rec03a_category_shadow"], "Todas")
        self.assertNotIn("rec03a_category", {w.key for w in app.selectbox})
        app.selectbox(key="rec03a_country").select("Alemanha").run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.selectbox(key="rec03a_city").value)
        self.assertEqual(app.number_input(key="rec03a_page").value, 1)
        self.assertTrue(has("RESULT:trier"))
        app.checkbox(key="show_filters").uncheck().run()
        app.checkbox(key="show_filters").check().run()
        self.assertTrue(has("RESULT:trier"))
        app.button(key="rec03a_clear_filters").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(has("SUGGESTIONS"))
        self.assertTrue(has("CHOICE:metz,trier"))

    def test_dynamic_candidates_reconcile_removed_options(self):
        app = AppTest.from_string(APP).run()
        app.segmented_control(key="rec03a_catalog_mode").set_value("Todas as cidades").run()
        app.selectbox(key="rec03a_country").select("Alemanha").run()
        app.selectbox(key="rec03a_city").select("trier").run()
        app.checkbox(key="shrink").check().run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.selectbox(key="rec03a_country").value)
        self.assertIsNone(app.selectbox(key="rec03a_city").value)
        self.assertEqual(app.number_input(key="rec03a_page").value, 1)
        self.assertTrue(any(m.value == "CHOICE:metz,trier" for m in app.markdown))
