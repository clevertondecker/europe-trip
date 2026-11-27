"""UX132C3: independent public task and one-time session migration."""
import unittest
from copy import deepcopy

from ux_navigation import bootstrap, route, from_legacy
from ux64_navigation_model import PUBLIC_TASKS, select_public_task, public_task


class CoverageRouteTests(unittest.TestCase):
    def test_independent_route_and_return_preserve_state(self):
        state = {"ux_area": "Explorar", "ux_section": "Comparar",
                 "ux112_active_view": "Minha comparação",
                 "ux112_active_view_shadow": "Minha comparação",
                 "ux132_domain_shadow": "Morar e trabalhar",
                 "ux132c2_scope_shadow": "all",
                 "rec03a_scope": {"confirmed": True},
                 "rec03a_draft": ["paris"], "advisor_plan": {"revision": 3}}
        before = deepcopy(state)
        self.assertIn("Cobertura dos dados", PUBLIC_TASKS["Explorar"])
        select_public_task(state, "Explorar", "Cobertura dos dados")
        self.assertEqual(bootstrap(state), ("Cobertura dos dados", None, None, None))
        self.assertEqual(public_task(state["ux_area"], state["ux_section"]), "Cobertura dos dados")
        select_public_task(state, "Explorar", "Comparar bases")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")
        for key in before:
            self.assertEqual(state[key], before[key])

    def test_migrate_old_coverage_session_once(self):
        state = {"ux_area": "Explorar", "ux_section": "Comparar",
                 "ux112_active_view_shadow": "Cobertura dos dados",
                 "ux112_active_view": "Cobertura dos dados",
                 "ux132_domain_shadow": "Atrações turísticas"}
        self.assertEqual(bootstrap(state)[0], "Cobertura dos dados")
        self.assertEqual(state["ux112_active_view_shadow"], "Explorar alternativas")
        self.assertEqual(state["ux132_domain_shadow"], "Atrações turísticas")
        select_public_task(state, "Explorar", "Comparar bases")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")

    def test_explicit_comparison_request_beats_stale_coverage(self):
        state = {"ux_area": "Explorar", "ux_section": "Passeios",
                 "ux112_active_view_shadow": "Cobertura dos dados"}
        select_public_task(state, "Explorar", "Comparar bases")
        self.assertEqual(bootstrap(state)[0], "Comparar cidades")

    def test_legacy_routes(self):
        self.assertEqual(from_legacy("Comparar cidades"), ("Explorar", "Comparar"))
        self.assertEqual(from_legacy("Cobertura dos dados"), ("Explorar", "Cobertura dos dados"))
        self.assertEqual(route("Explorar", "Mapa")[0], "Mapa & destinos")


if __name__ == "__main__":
    unittest.main()
