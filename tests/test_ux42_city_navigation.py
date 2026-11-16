"""UX 4.2: route contracts and preserved research activities."""
from pathlib import Path
import unittest

from ux42_city_navigation import ACTIVITIES,normalize_activity
from ux_navigation import route

ROOT=Path(__file__).resolve().parents[1]

class CityNavigationTests(unittest.TestCase):
    def test_single_task_selection(self):
        self.assertEqual(len(ACTIVITIES),3)
        self.assertEqual(len(set(ACTIVITIES)),3)
        self.assertEqual(normalize_activity(None),ACTIVITIES[0])
        self.assertEqual(normalize_activity("Pesquisa ampliada"),ACTIVITIES[0])
        self.assertEqual(normalize_activity("Comparar cidades"),ACTIVITIES[1])
        self.assertEqual(normalize_activity("Comparar mesmas viagens"),ACTIVITIES[2])

    def test_city_route_still_uses_legacy_adapter(self):
        self.assertEqual(route("Explorar","Cidades-base")[0],"Roteiro")
        self.assertEqual(route("Explorar","Cidades-base")[1],"Explorar bases")

    def test_no_new_business_data_or_trip_mutation(self):
        source=(ROOT/"ux42_city_navigation.py").read_text()
        self.assertNotIn("update_fields(",source)
        self.assertNotIn("trip_plan_repository",source)

    def test_streamlit_city_page_smoke(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        before=app.session_state["advisor_plan"].copy()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux42_city_activity"],ACTIVITIES[0])
        app.segmented_control(key="ux42_city_activity").set_value(ACTIVITIES[1]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],before)
        app.segmented_control(key="ux42_city_activity").set_value(ACTIVITIES[2]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],before)

if __name__=="__main__":
    unittest.main()
