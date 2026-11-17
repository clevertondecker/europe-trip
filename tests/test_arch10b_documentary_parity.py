import unittest
from arch10b_documentary_parity import documentary_rail_parity
from base_coverage_model import coverage_matrix


class DocumentaryParityTests(unittest.TestCase):
    def test_30_by_15_audit_without_mutation_or_false_equivalence(self):
        before=coverage_matrix("general")
        result=documentary_rail_parity()
        self.assertEqual(result["pairs"],450)
        self.assertEqual(len(result["rows"]),450)
        self.assertEqual(result["pairs"],result["identical_pairs"]+
                         sum(not row["same_evidence"] for row in result["rows"]))
        self.assertEqual(result["time_differences"],
                         sum(not row["same_time"] for row in result["rows"]))
        self.assertEqual(result["source_differences"],
                         sum(not row["same_source"] for row in result["rows"]))
        self.assertEqual(coverage_matrix("general"),before)
        self.assertFalse(result["documentary_model_modified"])
        self.assertTrue(all("difference_reason" in row for row in result["rows"]))

    def test_only_one_base_retains_same_15_denominator(self):
        result=documentary_rail_parity(cities=[{"id":"lille"}])
        self.assertEqual(result["pairs"],15)
        self.assertTrue(all(row["base_id"]=="lille" for row in result["rows"]))
        self.assertTrue(all(row["shared_observations_count"]>=0
                            for row in result["rows"]))
