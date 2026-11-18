import unittest
from data8_local_access_model import (
    load_access_dataset, local_access_scenario, access_research_summary,
    validate_access_dataset
)

class DATA8AccessTests(unittest.TestCase):
    def test_14_directional_records_for_7_attractions(self):
        evidence=load_access_dataset()
        summary=access_research_summary(evidence)
        self.assertEqual(summary["direction_observations"],14)
        self.assertEqual(summary["attractions_with_walk_estimates"],7)
        self.assertEqual(summary["verified_2027_service_connections"],0)
        self.assertFalse(evidence["joinable_to_rail_service"])

    def test_directional_asymmetry_does_not_become_schedule(self):
        data=load_access_dataset()
        walk=local_access_scenario("dq32_aachen_07",station_id="aachen_hbf",evidence=data)
        self.assertEqual(walk["to_attraction_range_min"],[18,30])
        self.assertEqual(walk["to_station_range_min"],[20,35])
        self.assertEqual(walk["roundtrip_range_min"],[38,65])
        self.assertFalse(walk["ready_for_rail_2027"])
        other=local_access_scenario("dq32_aachen_07",station_id="other_station",evidence=data)
        self.assertIsNone(other["roundtrip_range_min"])

    def test_structured_source_role_not_method_phrase(self):
        from copy import deepcopy
        dataset=load_access_dataset()
        sample={"schema_version":1,"scope":"editorial_local_access_not_a_verified_route",
                "checked_at":"2026-11-18","observations":deepcopy(dataset["observations"])}
        # The method is explanatory prose, not a validation sentinel.
        sample["observations"][0]["method"]="Estimativa manual ainda não verificada."
        validate_access_dataset(sample)
        for key,bad in (("source_scope","verified_map_route"),
                        ("duration_basis","measured_minutes"),
                        ("route_evidence_source_url","https://example.org/map")):
            altered=deepcopy(sample)
            altered["observations"][0][key]=bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_access_dataset(altered)
        del sample["observations"][0]["source_scope"]
        with self.assertRaises(ValueError):
            validate_access_dataset(sample)

    def test_cannot_turn_editorial_into_verified_duration(self):
        from copy import deepcopy
        data=load_access_dataset()
        baseline={"schema_version":1,"scope":"editorial_local_access_not_a_verified_route",
            "checked_at":"2026-11-18","observations":deepcopy(data["observations"])}
        for field,value in (("valid_for_2027",True),("joinable_to_rail_service",True),
                            ("distance_m",980),("min_minutes",0),
                            ("source_url","http://example.org")):
            x=deepcopy(baseline)
            x["observations"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                validate_access_dataset(x)

if __name__=="__main__":
    unittest.main()
