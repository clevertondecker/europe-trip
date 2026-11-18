"""Country flags always derive from catalog metadata, never from city names."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
from destination_labels import country_flag,place_label,destination_names
from attractions_model import load_attractions

ROOT=Path(__file__).resolve().parents[1]


class DestinationLabelsTests(unittest.TestCase):
    def test_flags_by_country_and_safe_fallback(self):
        self.assertEqual(place_label("Colmar","França"),"🇫🇷 Colmar")
        self.assertEqual(place_label("Basel","Suíça",show_country=True),
                         "🇨🇭 Basel · Suíça")
        self.assertEqual(country_flag("Alemanha"),"🇩🇪")
        self.assertEqual(country_flag("Luxemburgo"),"🇱🇺")
        self.assertEqual(country_flag("Desconhecido"),"")
        self.assertEqual(place_label("Outra cidade","Desconhecido"),"Outra cidade")

    def test_every_catalog_destination_uses_its_country(self):
        catalog=load_attractions()
        names=destination_names(catalog)
        for dest in catalog["destinations"]:
            self.assertEqual(names[dest["id"]],place_label(dest["name"],dest["country"]))

    def test_active_profile_shows_country_flags_on_preset(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Meu roteiro"))).click().run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Temporada europeia").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        display=" ".join(x.value for x in list(app.markdown)+list(app.caption))
        self.assertIn("🇫🇷",display)
        self.assertIn("🇨🇭",display)


if __name__=="__main__":
    unittest.main()
