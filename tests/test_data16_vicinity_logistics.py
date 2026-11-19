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
    def test_photo_cards_are_opt_in_and_no_nested_expanders(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"attractions_ui.py").read_text(encoding="utf-8")
        self.assertIn('key="data16_show_research"',source)
        self.assertIn('key="data16_cards_page"',source)
        self.assertIn('key="data16_show_matrix"',source)
        self.assertNotIn('with st.expander("Comparar as 30 cidades-base',source)
        self.assertIn('photo=_data16_photo(photo_ref["file_title"])',source)
        self.assertIn('st.link_button("Fonte turística"',source)

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
