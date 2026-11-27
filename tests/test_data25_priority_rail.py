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
        self.assertEqual({key for key in data["by_pair"] if key[1]=="annecy"},
                         {(b, "annecy") for b in RESEARCH_BASE_IDS})
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

    def test_batch_two_additive_only_and_global_parity(self):
        expected = (("lille","angers",197),("metz","angers",245),("mulhouse","angers",294),("nancy","angers",238),("strasbourg","angers",257),("lille","rennes",205),("metz","rennes",251),("mulhouse","rennes",310),("nancy","rennes",243),("strasbourg","rennes",243),("metz","selestat",83))
        data=load_data25()
        keys={(b,d) for b,d,_ in expected}
        self.assertEqual(set(data["by_pair"]),keys | {(b,"annecy") for b in RESEARCH_BASE_IDS})
        discovery=build_exploration_discovery()
        research=load_research(include_candidates=True)
        matrix=build_destination_matrix(list(RESEARCH_BASE_IDS),
            ["annecy","angers","rennes","selestat"],discovery=discovery,research=research)
        before=deepcopy(matrix)
        old=decorate_comparison(matrix,data25_overlay={"by_pair":{
            k:v for k,v in data["by_pair"].items() if k not in keys}})
        new=decorate_comparison(matrix)
        audit=build_audit()
        pairs={(p["base_id"],p["destination_id"]):p for p in audit["rail_pairs"]}
        for b,d,minutes in expected:
            key=b,d
            self.assertEqual(old["cells"][key]["category"],"no_time")
            cell=new["cells"][key]
            self.assertEqual(cell["category"],"reference_only")
            self.assertEqual(cell["display_min"],minutes)
            self.assertEqual(cell["source_url"],data["by_pair"][key]["source_url"])
            self.assertFalse(cell["valid_for_2027"])
            self.assertFalse(cell["weekend_return_known"])
            self.assertEqual(pairs[key]["display_basis"],"data25_priority_reference")
            self.assertFalse(pairs[key]["return_2027_verified"])
            self.assertIsNone(pairs[key]["full_door_to_door_min"])
        for key in set(new["cells"])-keys:
            self.assertEqual(old["cells"][key],new["cells"][key])
        self.assertEqual(matrix,before)
