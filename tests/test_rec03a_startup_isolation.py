"""REC03A: recovery after a coherent module becomes available."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import base_recommendation_evidence_model as evidence


class StartupRecoveryTests(TestCase):
    def test_incompatible_builder_does_not_poison_subsequent_request(self):
        module = SimpleNamespace()
        with patch.object(evidence, "import_module", return_value=module):
            with self.assertRaisesRegex(ImportError, "REC01/UX503"):
                evidence._wishlist_matrix_builder()
            module.build_wishlist_matrix = lambda: "coherent"
            self.assertIs(evidence._wishlist_matrix_builder(), module.build_wishlist_matrix)
            self.assertEqual(evidence._wishlist_matrix_builder()(), "coherent")

    def test_noncallable_builder_fails_closed(self):
        with patch.object(evidence, "import_module",
                          return_value=SimpleNamespace(build_wishlist_matrix=42)):
            with self.assertRaisesRegex(ImportError, "REC01/UX503"):
                evidence._wishlist_matrix_builder()
