"""UX 3.6: private storage never silently overwrites or publishes drafts."""
import unittest
from unittest.mock import Mock, patch

from private_continuity_store import (
    PrivateArchiveStore, StorageConflict, StorageUnavailable,
    object_key, validate_private_config,
)


class OwnerPrivateStorageTests(unittest.TestCase):
    def test_object_key_is_owner_scoped_and_does_not_expose_email(self):
        first = object_key("Owner@Example.com")
        self.assertEqual(first, object_key(" owner@example.com "))
        self.assertNotEqual(first, object_key("other@example.com"))
        self.assertNotIn("example.com", first)

    def test_configuration_fails_closed(self):
        with self.assertRaises(StorageUnavailable):
            validate_private_config("", {})
        with self.assertRaises(StorageUnavailable):
            validate_private_config("bucket-name", {"client_email": "a"})
        with self.assertRaises(ValueError):
            object_key("not-an-email")

    @patch("private_continuity_store.AuthorizedSession")
    @patch("private_continuity_store.Credentials.from_service_account_info")
    def test_initial_write_uses_generation_zero_and_no_public_repo(self, creds, session):
        http = session.return_value
        http.post.return_value = Mock(status_code=200, json=lambda: {"generation": "3"})
        store = PrivateArchiveStore("my-private-bucket",
                                    {"client_email": "a", "private_key": "secret"},
                                    "owner@example.com")
        self.assertEqual(store.save(b'{"ok":true}', None), 3)
        url = http.post.call_args.args[0]
        self.assertIn("storage.googleapis.com", url)
        self.assertNotIn("api.github.com", url)
        self.assertEqual(http.post.call_args.kwargs["params"]["ifGenerationMatch"], "0")
        self.assertNotIn("owner@example.com", http.post.call_args.kwargs["params"]["name"])

    @patch("private_continuity_store.AuthorizedSession")
    @patch("private_continuity_store.Credentials.from_service_account_info")
    def test_update_requires_matching_generation(self, creds, session):
        http = session.return_value
        http.post.return_value = Mock(status_code=412)
        store = PrivateArchiveStore("my-private-bucket",
                                    {"client_email": "a", "private_key": "secret"},
                                    "owner@example.com")
        with self.assertRaises(StorageConflict):
            store.save(b'{"ok":true}', 42)
        self.assertEqual(http.post.call_args.kwargs["params"]["ifGenerationMatch"], "42")

    @patch("private_continuity_store.AuthorizedSession")
    @patch("private_continuity_store.Credentials.from_service_account_info")
    def test_load_pins_read_to_metadata_generation(self, creds, session):
        http = session.return_value
        http.get.side_effect = [
            Mock(status_code=200, json=lambda: {"generation": "9"}),
            Mock(status_code=200, content=b'{"schema":1}'),
        ]
        store = PrivateArchiveStore("my-private-bucket",
                                    {"client_email": "a", "private_key": "secret"},
                                    "owner@example.com")
        self.assertEqual(store.load(), (b'{"schema":1}', 9))
        self.assertEqual(http.get.call_args.kwargs["params"]["generation"], 9)

    @patch("private_continuity_store.AuthorizedSession")
    @patch("private_continuity_store.Credentials.from_service_account_info")
    def test_missing_object_is_not_a_silent_overwrite(self, creds, session):
        http = session.return_value
        http.get.return_value = Mock(status_code=404)
        store = PrivateArchiveStore("my-private-bucket",
                                    {"client_email": "a", "private_key": "secret"},
                                    "owner@example.com")
        self.assertIsNone(store.load())


if __name__ == "__main__":
    unittest.main()
