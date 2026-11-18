import unittest

from data8_attraction_evidence_model import coverage_report, card_projection
from data8_priority_tourism_model import load_priority_lot


class PriorityTourismPilotTests(unittest.TestCase):
    def test_18_verified_identifiers_and_two_noncanonical_candidates(self):
        result = load_priority_lot()
        self.assertEqual(len(result["entries"]), 18)
        self.assertEqual(len(result["by_id"]), 18)
        self.assertEqual(len(result["unreconciled_candidates"]), 2)
        self.assertEqual({x["destination_id"] for x in result["unreconciled_candidates"]},
                         {"cologne","ghent"})
        self.assertTrue(all(x["canonical_attraction_id"] is None
                            for x in result["unreconciled_candidates"]))
        self.assertFalse(result["mutates_catalog"])

    def test_unknown_price_not_free_and_visit_estimate_is_editorial(self):
        r = load_priority_lot()
        summary = coverage_report(r)
        self.assertEqual(summary["selected_attractions"], 18)
        self.assertEqual(summary["duration_range"], 18)
        self.assertEqual(summary["experience_sourced"], 18)
        self.assertEqual(summary["general_hours_documented"], 3)
        self.assertEqual(summary["2027_verified"], 0)
        self.assertEqual(r["by_id"]["dq32_aachen_07"]["admission"]["amount"], 0)
        self.assertIsNone(r["by_id"]["brussels_eu_quarter"]["admission"]["amount"])
        self.assertEqual(r["by_id"]["brussels_eu_quarter"]["admission"]["state"], "unknown")
        self.assertEqual(r["by_id"]["strasbourg_vauban"]["admission"]["state"], "unknown")

    def test_admission_requires_proven_scope(self):
        result=load_priority_lot()
        from collections import Counter
        states=Counter(x["admission"]["state"] for x in result["entries"])
        self.assertEqual(states,{"free_general_entry":2,"external_no_ticket":4,"unknown":12})
        for row in result["entries"]:
            adm=row["admission"]
            if adm["state"]=="external_no_ticket":
                self.assertEqual(adm["external_access_basis"],"documented_public_outdoor_area")
                self.assertIsNone(adm["amount"])
                self.assertTrue(adm["scope_note"])
                self.assertTrue(adm["source_url"])
                self.assertTrue(adm["checked_at"])
        self.assertEqual(result["by_id"]["brussels_atomium"]["admission"]["state"],"unknown")
        self.assertEqual(result["by_id"]["brussels_grand_place"]["admission"]["state"],"unknown")
        self.assertEqual(coverage_report(result)["general_entry_known"],2)

    def test_18_records_retain_provenance_and_candidate_identity(self):
        result=load_priority_lot()
        self.assertEqual(len({x["attraction_id"] for x in result["entries"]}),18)
        for row in result["entries"]:
            self.assertTrue(row["experience"]["source_url"].startswith("https://"))
            self.assertTrue(row["experience"]["checked_at"])
            self.assertFalse(row["valid_for_2027"])
            if row["duration"]["state"]=="editorial_estimate":
                self.assertTrue(row["duration"]["method"])
        self.assertEqual(len(result["unreconciled_candidates"]),2)

    def test_does_not_mutate_discovery(self):
        from ux501_destination_discovery_model import build_destination_discovery
        d = build_destination_discovery()
        from copy import deepcopy
        old = deepcopy(d)
        r = load_priority_lot(discovery=d)
        card = d["destinations"][0]["attractions"][0] if d["destinations"][0]["attractions"] else {"id":"missing"}
        card_projection(card, research=r)
        self.assertEqual(d, old)

if __name__ == "__main__":
    unittest.main()
