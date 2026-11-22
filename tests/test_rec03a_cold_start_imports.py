"""Regression guard for the REC03A/REC01 startup import failure."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import base_recommendation_evidence_model as evidence


class SharedMatrixImportTests(unittest.TestCase):
    def test_existing_builder_is_used_without_reloading(self):
        def original():
            return "original"
        with patch.object(evidence, "import_module",
                          return_value=SimpleNamespace(build_wishlist_matrix=original)):
            self.assertIs(evidence._wishlist_matrix_builder(), original)

    def test_incompatible_module_fails_closed_only_when_requested(self):
        old = SimpleNamespace(compare_wishlist_bases=object())
        with patch.object(evidence, "import_module", return_value=old):
            with self.assertRaisesRegex(ImportError, "REC01/UX503"):
                evidence._wishlist_matrix_builder()

    def run_child(self, script):
        repo = Path(__file__).resolve().parents[1]
        process = subprocess.run(
            [sys.executable, "-c", script], cwd=repo, capture_output=True,
            text=True, timeout=90, check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout + "\n" + process.stderr)

    def test_cold_imports_match_actual_app_module_order(self):
        self.run_child("""
import ast
from pathlib import Path
tree=ast.parse(Path('app.py').read_text(encoding='utf-8'))
nodes=[x for x in tree.body if isinstance(x,(ast.Import,ast.ImportFrom))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'app.py','exec'), {})
from ux503_destination_base_comparison_model import build_wishlist_matrix
from base_recommendation_evidence_model import _wishlist_matrix_builder
assert _wishlist_matrix_builder() is build_wishlist_matrix
""")

    def test_startup_imports_survive_cached_old_ux503_module(self):
        # A fresh subprocess deliberately models an old UX503 module retained
        # in a worker while REC03A is loaded for the first time.
        self.run_child("""
import ast
from pathlib import Path
import ux503_destination_base_comparison_model as old
del old.build_wishlist_matrix
tree=ast.parse(Path('app.py').read_text(encoding='utf-8'))
nodes=[x for x in tree.body if isinstance(x,(ast.Import,ast.ImportFrom))]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'app.py','exec'), {})
from base_recommendation_evidence_model import _wishlist_matrix_builder
try:
    _wishlist_matrix_builder()
except ImportError as exc:
    assert 'REC01/UX503' in str(exc)
else:
    raise AssertionError('Missing shared matrix should fail closed')
""")


if __name__ == "__main__":
    unittest.main()
