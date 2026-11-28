"""Execute all major Streamlit pages headlessly to catch runtime errors.

AppTest does not render a browser image or interactive maps; manual visual
verification remains necessary after deployment.
"""
import unittest
from nav_helpers import open_public
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
from ux64_navigation_model import PUBLIC_TASKS
class AppSmokeTests(unittest.TestCase):
    def test_all_public_tasks_and_research_entry_render_without_exceptions(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=40).run()
        self.assertEqual(len(at.exception),0, [e.message for e in at.exception])
        for area,tasks in PUBLIC_TASKS.items():
            for task in tasks:
                with self.subTest(area=area,task=task):
                    open_public(at,area,task)
                    self.assertEqual(len(at.exception),0,[e.message for e in at.exception])
        open_public(at,"Planejar","Visão geral")
        at.button(key="home_next_tasks").click().run()
        self.assertEqual(len(at.exception),0,[e.message for e in at.exception])
if __name__=="__main__":unittest.main()
