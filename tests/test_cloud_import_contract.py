"""Fail fast if the Streamlit Cloud entrypoint's module imports regress.

A syntax-only compile check is insufficient: the app previously crashed with
ImportError at the very top of app.py despite passing source-level checks.
"""
import importlib
import unittest


class CloudImportContractTests(unittest.TestCase):
    def test_selection_module_is_independent_of_presentation(self):
        m = importlib.import_module("exploratory_selection")
        self.assertTrue(callable(m.sync_city_widget))
        self.assertTrue(callable(m.set_city_from_widget))

    def test_impact_module_remains_importable_and_preserves_old_api(self):
        m = importlib.import_module("base_scenario_ui")
        self.assertTrue(callable(m.render_scenario_impact))
        self.assertTrue(callable(m.sync_city_widget))
        self.assertTrue(callable(m.set_city_from_widget))

    def test_all_app_import_dependencies_exist(self):
        # Execute all imports used by app.py *without* instantiating its UI.
        components = [
            ("base_explorer_ui", "render_base_explorer"),
            ("base_research_expanded_ui", "render_expanded_research"),
            ("attractions_ui", "render_explorer"),
            ("travel_advisor_ui", "render_advisor"),
            ("exploratory_selection", "sync_city_widget"),
            ("base_scenario_ui", "render_scenario_impact"),
            ("ux_navigation", "bootstrap"),
        ]
        for module_name, member in components:
            with self.subTest(module=module_name, member=member):
                obj = importlib.import_module(module_name)
                self.assertTrue(callable(getattr(obj, member)))


if __name__ == "__main__":
    unittest.main()
