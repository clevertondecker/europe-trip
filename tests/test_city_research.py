import copy
import unittest
from city_research import city_readiness, load_audit, validate_audit

class ResearchAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_audit()

    def test_four_cities_follow_same_schema_and_gates(self):
        self.assertEqual({c["id"] for c in self.audit["cities"]},
                         {"mulhouse", "strasbourg", "metz", "nancy"})
        for city in self.audit["cities"]:
            self.assertEqual(city_readiness(city)["total"], len(self.audit["standards"]))

    def test_no_unverified_city_ready(self):
        self.assertTrue(all(not city_readiness(c)["decision_ready"] for c in self.audit["cities"]))
        self.assertTrue(all(c["eligible_2027_quotes"] == 0 for c in self.audit["cities"]))

    def test_missing_evidence_for_new_city_is_rejected(self):
        modified = copy.deepcopy(self.audit)
        modified["cities"].append({"id": "colmar", "name": "Colmar"})
        with self.assertRaises(ValueError):
            validate_audit(modified)

    def test_duplicate_city_is_rejected(self):
        modified = copy.deepcopy(self.audit)
        modified["cities"].append(copy.deepcopy(modified["cities"][0]))
        with self.assertRaises(ValueError):
            validate_audit(modified)

    def test_fake_decision_ready_is_rejected(self):
        modified = copy.deepcopy(self.audit)
        modified["cities"][0]["audit_status"] = "decision_ready"
        with self.assertRaises(ValueError):
            validate_audit(modified)

    def test_unaudited_gates_fail(self):
        modified = copy.deepcopy(self.audit)
        modified["cities"][0]["pending_gates"].remove("eligibility")
        with self.assertRaises(ValueError):
            validate_audit(modified)

if __name__ == "__main__":
    unittest.main()
