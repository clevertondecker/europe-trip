"""DATA25: directional reference precedence and parity across the shared audit."""
import unittest
from copy import deepcopy

from data25_priority_rail_model import load_data25, RESEARCH_BASE_IDS
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research
from data24_audit_model import build_audit
from ux503_destination_base_comparison_model import build_destination_matrix
from rail_reference_projection_model import decorate_comparison


class Data25Tests(unittest.TestCase):
    def test_exact_five_previously_missing_pairs_and_source(self):
        data = load_data25()
        expected = {"lille": 342, "metz": 363, "mulhouse": 352,
                    "nancy": 373, "strasbourg": 397}
        self.assertEqual(set(data["by_pair"]), {(b, "annecy") for b in RESEARCH_BASE_IDS})
        matrix = build_destination_matrix(
            list(RESEARCH_BASE_IDS), ["annecy"],
            discovery=build_exploration_discovery(),
            research=load_research(include_candidates=True))
        before = deepcopy(matrix)
        old = decorate_comparison(matrix, data25_overlay={"by_pair": {}})
        new = decorate_comparison(matrix)
        self.assertEqual(matrix, before)
        for b, duration in expected.items():
            key = b, "annecy"
            self.assertEqual(old["cells"][key]["category"], "no_time")
            cell = new["cells"][key]
            self.assertEqual(cell["category"], "reference_only")
            self.assertEqual(cell["display_min"], duration)
            self.assertEqual(cell["source_url"], data["by_pair"][key]["source_url"])
            self.assertFalse(cell["valid_for_2027"])
            self.assertFalse(cell["weekend_return_known"])
            self.assertTrue(cell["data25_connectivity_applied"])

    def test_audit_parity_and_no_official_decision(self):
        audit = build_audit()
        self.assertEqual(audit["d004"]["scope"]["approved_research_base_ids"], list(RESEARCH_BASE_IDS))
        self.assertIsNone(audit["d004"]["scope"]["official_finalist_ids"])
        pairs = {(p["base_id"], p["destination_id"]): p for p in audit["rail_pairs"]}
        for base in RESEARCH_BASE_IDS:
            p = pairs[(base, "annecy")]
            self.assertEqual(p["display_basis"], "data25_priority_reference")
            self.assertFalse(p["return_2027_verified"])
            self.assertIsNone(p["full_door_to_door_min"])
        self.assertFalse(audit["official_plan_modified"])
