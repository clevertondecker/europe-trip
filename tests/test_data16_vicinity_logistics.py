import unittest
from data16_vicinity_logistics_model import HUBS,hub_references,attraction_references,all_base_hubs
from data16_commons_photo_model import parse_metadata
class DATA16LogisticsTests(unittest.TestCase):
    def test_all_30_bases_to_three_hubs_and_no_invented_total(self):
        rows=all_base_hubs()
        self.assertEqual(len(rows),90)
        self.assertEqual(len({(r["origin_id"],r["hub_id"]) for r in rows}),90)
        for row in rows:
            self.assertIsNone(row["total_oneway_min"])
            self.assertFalse(row["return_verified_2027"])
    def test_all_15_attractions_from_multiple_bases(self):
        for city in ("mulhouse","strasbourg","selestat","offenburg","dijon","lille"):
            rows=attraction_references(city)
            self.assertEqual(len(rows),15)
            self.assertTrue(all(r["total_oneway_min"] is None and
                                r["feasibility"]=="unknown" for r in rows))
        self.assertIsNone(hub_references("selestat")["selestat"]["rail_to_hub_min"])
        with self.assertRaises(ValueError):hub_references("not_a_city")
    def test_streamlit_interactions_reset_pagination_and_preserve_plan(self):
        from copy import deepcopy
        from pathlib import Path
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        import attractions_ui
        app=Path(__file__).resolve().parents[1]/"app.py"
        with patch.object(attractions_ui,"_data16_photo",return_value=None):
            at=AppTest.from_file(str(app),default_timeout=120).run()
            baseline=deepcopy(at.session_state["advisor_plan"])
            at.button(key="ux_sidebar_nav_1").click().run()
            at.button(key="ux64_sidebar_nav_1").click().run()
            at.button(key="ux125b_home_base_outings").click().run()
            at.toggle(key="data16_show_research").set_value(True).run()
            self.assertFalse(at.exception,[e.message for e in at.exception])
            at.selectbox(key="data16_cards_page").set_value(3).run()
            self.assertEqual(at.session_state["data16_cards_page"],3)
            at.selectbox(key="data16_region").set_value("offenburg").run()
            self.assertEqual(at.session_state["data16_cards_page"],1)
            at.selectbox(key="data16_cards_page").set_value(2).run()
            at.selectbox(key="data16_source_base").set_value("metz").run()
            self.assertEqual(at.session_state["data16_cards_page"],1)
            self.assertFalse(at.exception,[e.message for e in at.exception])
            self.assertEqual(at.session_state["advisor_plan"],baseline)

    def test_invalid_license_rejected(self):
        p={"query":{"pages":{"1":{"title":"File:A.jpg","imageinfo":[{
            "thumburl":"https://upload.wikimedia.org/x.jpg","extmetadata":{
            "Artist":{"value":"A"},"LicenseShortName":{"value":"All rights reserved"},
            "LicenseUrl":{"value":"https://example.com"}}}]}}}}
        self.assertIsNone(parse_metadata(p,"A.jpg"))
        m=p["query"]["pages"]["1"]["imageinfo"][0]["extmetadata"]
        m["LicenseShortName"]["value"]="CC BY-SA 4.0"
        m["LicenseUrl"]["value"]="https://creativecommons.org/licenses/by-sa/4.0/"
        self.assertIsNotNone(parse_metadata(p,"A.jpg"))
        m["LicenseShortName"]["value"]="CC BY-NC 4.0"
        self.assertIsNone(parse_metadata(p,"A.jpg"))
        m["LicenseShortName"]["value"]="CC BY-ND 4.0"
        self.assertIsNone(parse_metadata(p,"A.jpg"))
