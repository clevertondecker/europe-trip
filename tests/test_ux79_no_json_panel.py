"""The normal itinerary save UI is cloud-first and has no manual JSON controls.

Keep the archive/import implementations elsewhere for disaster recovery, but
they must not appear as parallel write paths in the itinerary save panel.
"""
import inspect
import unittest
from itinerary_flow_ui import _save_panel


class CloudOnlyItineraryPanelTests(unittest.TestCase):
    def test_manual_json_backup_controls_are_absent(self):
        source=inspect.getsource(_save_panel)
        self.assertNotIn("file_uploader(", source)
        self.assertNotIn("flow_backup_download", source)
        self.assertNotIn("flow_import_json", source)
        self.assertNotIn("Confirmar recuperação nesta sessão", source)

    def test_private_save_is_primary(self):
        source=inspect.getsource(_save_panel)
        self.assertIn("render_primary_private_save(plan, catalog)", source)
        self.assertIn("Avançado · publicar no GitHub público", source)
        self.assertNotIn("backup JSON (opcional)", source)


if __name__=="__main__":
    unittest.main()
