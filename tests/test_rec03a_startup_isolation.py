"""Production regression: a stale module must not prevent global app startup."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StartupIsolationTests(unittest.TestCase):
    def run_fresh(self, script):
        completed = subprocess.run(
            [sys.executable, "-c", script], cwd=ROOT, capture_output=True,
            text=True, timeout=180,
        )
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + "\n" + completed.stderr)

    def test_fresh_process_import_contract(self):
        # Clean interpreter, independent of unittest discovery import order.
        self.run_fresh("""
from ux503_destination_base_comparison_model import build_wishlist_matrix
from base_recommendation_evidence_model import build_recommendation_matrix
from base_recommendation_model import recommend_bases
assert all(callable(x) for x in (build_wishlist_matrix,build_recommendation_matrix,recommend_bases))
from rec03a_suggestions_ui import render_recommendation_activity
assert callable(render_recommendation_activity)
""")

    def test_stale_ux503_module_does_not_crash_app_or_reuse_results(self):
        self.run_fresh("""
import sys
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from ux502_destination_interests_model import empty_interests, set_interest
from trip01_supplemental_discovery import build_exploration_discovery
import ux503_destination_base_comparison_model as legacy
# Faithful reproduction of the missing export in the production traceback.
original = legacy.build_wishlist_matrix
# Preserve old manual API behavior, as in the old module, while removing
# the new symbol from the imported module's namespace.
def legacy_compare(*args, **kwargs):
    return original(*args, **kwargs)
legacy.compare_wishlist_bases = legacy_compare
del legacy.build_wishlist_matrix
assert "base_recommendation_model" not in sys.modules
a=AppTest.from_file("app.py",default_timeout=120).run()
assert not a.exception, str(a.exception)
assert "base_recommendation_model" not in sys.modules
before=deepcopy(a.session_state["advisor_plan"])
a.button(key="ux_sidebar_nav_1").click().run()
a.segmented_control(key="ux_section").set_value("Comparar").run()
assert not a.exception, str(a.exception)
discovery=build_exploration_discovery()
wishes=set_interest(empty_interests(),"paris","must_visit",discovery)
a.session_state["ux502_interests"]=wishes
a.radio(key="rec03a_activity_widget").set_value("Cidades sugeridas").run()
assert not a.exception, str(a.exception)
a.button(key="rec03a_confirm_all").click().run()
assert not a.exception, str(a.exception)
assert any("temporariamente indisponíveis" in e.value for e in a.error), str(a.error)
assert not any("Todas as cidades-base" in m.value for m in a.markdown)
assert a.session_state["advisor_plan"] == before
assert a.session_state["ux502_interests"] == wishes
a.button(key="rec03a_manual_fallback").click().run()
assert not a.exception, str(a.exception)
assert a.session_state["rec03a_activity"] == "Comparação personalizada"
assert a.multiselect(key="ux503_bases")
assert a.session_state["advisor_plan"] == before
assert a.session_state["ux502_interests"] == wishes
# Simulate a coherent module version becoming available; a retry must use
# the real implementation, no synthetic fallback or permanent disablement.
legacy.build_wishlist_matrix=original
a.radio(key="rec03a_activity_widget").set_value("Cidades sugeridas").run()
assert not a.exception, str(a.exception)
assert not a.error, str(a.error)
assert any("Todas as cidades-base" in m.value for m in a.markdown)
assert a.session_state["advisor_plan"] == before
""")


if __name__=="__main__":
    unittest.main()
