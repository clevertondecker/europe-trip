"""Audit snapshot contract: reproduce generated CSVs without changing production data.

The nine-row example and decision-readiness matrices are intentionally manual
curations, not outputs of the original audit generator.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import scripts.audit_rail_and_attraction_gaps as audit

SOURCE_BLOBS = {
    "data/attractions_2027.json": "6354e3c837bd0bf181e3fca7537b58509707bd43",
    "data/dq32_macro_tourism_2026_11.json": "6ed2fe387901374e608937d701140bd6442b1e01",
    "data/base_city_research_expanded_2026_11.json": "9c5a8bdf3343a64eeb3188c6ec4fbea8e1101ddf",
    "data/five_base_comparison_evidence_2026_11.json": "ad2cf963feb4efca67d356a7df6317d2336388f6",
    "data/dq30_mobility_pilot_2026_11.json": "33b36c7b6b6c98235ae00a30a24d0349f6cab01c",
    "data/exploration_bases_2027.json": "142a34e8482f7bff5684f161c8242785aa9d20da",
    "data/base_city_rail_evidence_expanded_2026_11.json": "8ef2743dee9c03a5aa9f80499568bee2e0f3f782",
    "data/base_destination_routes_2027.json": "b72e6109224775920c335137f7c2b96e2de711d6",
}
GENERATED = (
    "README.md",
    "city_base_destination_matrix.csv",
    "city_base_summary.csv",
    "attraction_access_gaps.csv",
    "city_base_attraction_matrix.csv",
    "summary.json",
)
AUDIT_DIR = audit.ROOT / "docs/audits/2026-11-17-rail-attraction-gaps"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class AuditReproducibilityTests(unittest.TestCase):
    def test_source_versions_frozen_for_snapshot(self):
        for name, expected in SOURCE_BLOBS.items():
            with self.subTest(source=name):
                self.assertEqual(
                    git_blob_sha((audit.ROOT / name).read_bytes()), expected,
                    "Historical audit inputs changed: refresh audit in a new versioned snapshot",
                )

    def test_generated_files_are_deterministic_and_match_committed(self):
        original = audit.OUT
        try:
            with TemporaryDirectory() as root:
                saved = []
                for i in (1, 2):
                    target = Path(root) / f"run{i}"
                    audit.OUT = target
                    with contextlib.redirect_stdout(io.StringIO()):
                        audit.main()
                    one = {
                        filename: (target / filename).read_bytes()
                        for filename in GENERATED
                    }
                    saved.append(one)
                    for name, payload in one.items():
                        with self.subTest(run=i, artifact=name):
                            self.assertEqual(
                                payload, (AUDIT_DIR / name).read_bytes(),
                                f"{name}: generated artifact differs from committed snapshot",
                            )
                self.assertEqual(saved[0], saved[1])
        finally:
            audit.OUT = original

    def test_identities_uniqueness_and_partition(self):
        bases = rows(AUDIT_DIR / "city_base_summary.csv")
        pairs = rows(AUDIT_DIR / "city_base_destination_matrix.csv")
        attractions = rows(AUDIT_DIR / "attraction_access_gaps.csv")
        joined = rows(AUDIT_DIR / "city_base_attraction_matrix.csv")
        self.assertEqual(len(bases), len({x["base_id"] for x in bases}))
        self.assertEqual(
            len(pairs), len({(x["base_id"], x["destination_id"]) for x in pairs}))
        self.assertEqual(
            len(attractions), len({x["attraction_id"] for x in attractions}))
        self.assertEqual(
            len(joined), len({(x["base_id"], x["attraction_id"]) for x in joined}))
        self.assertEqual(len(pairs), len(bases) * len({x["destination_id"] for x in pairs}))
        self.assertEqual(len(joined), len(bases) * len(attractions))
        self.assertEqual(
            {(x["base_id"], x["destination_id"]) for x in pairs},
            {(b["base_id"], d["destination_id"])
             for b in bases for d in {x["destination_id"]: x for x in pairs}.values()},
        )
        self.assertEqual(
            {(x["base_id"], x["attraction_id"]) for x in joined},
            {(b["base_id"], a["attraction_id"]) for b in bases for a in attractions},
        )
        summary = json.loads((AUDIT_DIR / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(len(pairs), summary["base_destination_pairs"])
        self.assertEqual(len(joined), summary["base_attraction_pairs"])
        self.assertEqual(len(attractions), summary["distinct_attractions"])
        status_counts = {x: sum(r["rail_status"] == x for r in pairs)
                         for x in ("not_researched", "partial", "historical_time", "local")}
        self.assertEqual(status_counts, summary["rail_status_counts"])
        self.assertTrue(all(x["verified_base_to_attraction_total_minutes"] in ("", "None")
                            for x in joined))

    def test_manual_example_is_exact_subset_of_generated_pairs(self):
        example = rows(AUDIT_DIR / "example_3bases_3destinations.csv")
        pairs = {(x["base_id"], x["destination_id"]): x for x in
                 rows(AUDIT_DIR / "city_base_destination_matrix.csv")}
        self.assertEqual(len(example), 9)
        self.assertEqual(len({(x["base_id"], x["destination_id"]) for x in example}), 9)
        for row in example:
            orig = pairs[(row["base_id"], row["destination_id"])]
            self.assertEqual(row["evidence_status"], orig["rail_status"])
            self.assertEqual(row["historical_oneway_min"],
                             orig["historical_train_oneway_min"])
            self.assertEqual(row["rail_source_url"], orig["source_url"])
            self.assertEqual(row["source_date"], orig["source_date"])


if __name__ == "__main__":
    unittest.main()
