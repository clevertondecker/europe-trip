"""Profile cards expose actual preselected destinations and attractions."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest
from attractions_model import load_attractions

ROOT=Path(__file__).resolve().parents[1]


class PreselectedOutingsVisibleTests(unittest.TestCase):
    def test_styles_show_destinations_and_attractions_without_extra_click(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=95).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Simular roteiros").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        catalog=load_attractions()
        names={d["id"]:d["name"] for d in catalog["destinations"]}
        attractions={a["id"]:a["name"] for a in catalog["attractions"]}
        text="\n".join(item.value for item in app.markdown)
        self.assertIn("Passeios pré-selecionados neste estilo",text)
        for key in ("economy","balanced","experience"):
            scenario=app.session_state.get("scenario_edit_"+key)
            if scenario is not None:
                packages=scenario["packages"]
            else:
                from travel_profile_scenarios import build_profile_scenarios
                from attractions_model import load_base_routes
                from data_model import load_data
                current=app.session_state["advisor_plan"]
                scenarios=build_profile_scenarios(current,catalog,load_base_routes(),
                                                  load_data(),False,6.3,7.1)
                packages=next(s["proposal_packages"] for s in scenarios if s["profile"]==key)
            for destination,ids in packages.items():
                self.assertIn(names[destination],text)
                for attraction in ids:
                    self.assertIn(attractions[attraction],text)
        self.assertEqual(app.session_state["advisor_plan"]["packages"],{})


if __name__=="__main__":
    unittest.main()
