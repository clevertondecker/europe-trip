"""UX55 regression tests for ticket semantics and read-only visual discovery."""
from copy import deepcopy
import unittest
from unittest.mock import MagicMock, patch

from attractions_model import load_attractions
from itinerary_flow_model import destinations, FRANCE_STAGE, ITALY_STAGE
from ux55_visual_outing_ui import ticket_presentation, destination_preview, render_destination_preview


class VisualOutingPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_attractions()
        cls.choices = destinations(cls.catalog)

    def test_ticket_adult_return_retains_return_and_currency(self):
        ticket = {"status": "operator_published", "amount": 36,
                  "currency": "CHF", "per": "adult_return",
                  "validity": "outono 2026", "notes": "subida e descida; não duplicar"}
        result = ticket_presentation(ticket)
        self.assertIn("CHF 36.00", result["price"])
        self.assertIn("ida e volta", result["price"])
        self.assertEqual(result["validity"], "outono 2026")
        self.assertIn("não duplicar", result["notes"])

    def test_ticket_single_adult_and_missing_unknown_fields(self):
        result = ticket_presentation({"status": "operator_published", "amount": 16,
                                      "currency": "EUR", "per": "adult"})
        self.assertIn("EUR 16.00", result["price"])
        self.assertNotIn("ida e volta", result["price"])
        self.assertIsNone(result["notes"])
        for ticket in (None, {}, {"status": "operator_published", "amount": 40,
                                   "currency": None, "per": "adult"},
                       {"status": "operator_published", "amount": 20,
                        "currency": "EUR", "per": "group"}):
            self.assertIn("verificar", ticket_presentation(ticket)["price"])

    def test_not_applicable_does_not_imply_free_paid_interiors(self):
        result = ticket_presentation({"status": "not_applicable", "per": "none",
                                      "notes": "Interior pago em dias especiais"})
        self.assertIn("sem bilhete cadastrado", result["price"])
        self.assertIn("Interior pago", result["notes"])

    def test_canonical_sample_return_ticket_does_not_double_count(self):
        record = next(a for a in self.catalog["attractions"] if a["ticket"]["per"] == "adult_return")
        place = next(d for d in self.choices if d["stage"] == FRANCE_STAGE
                     and any(a["id"] == record["id"] for a in d["attractions"]))
        preview = destination_preview(place, self.catalog)
        ticket = next(a for a in preview["details"] if a["id"] == record["id"])
        self.assertIn("ida e volta", ticket["price"])
        self.assertIn(record["ticket"]["validity"], ticket["ticket_validity"])

    def test_canonical_details_and_sources(self):
        dest = next(d for d in self.choices if d["id"] == "colmar")
        view = destination_preview(dest, self.catalog)
        self.assertEqual(len(view["details"]), len(dest["attractions"]))
        by_id = {a["id"]: a for a in self.catalog["attractions"]}
        for item in view["details"]:
            self.assertEqual(item["summary"], by_id[item["id"]]["summary"])
            self.assertEqual(item["source"], by_id[item["id"]]["source_urls"][0])

    def test_italy_does_not_inherit_french_photo_or_ticket(self):
        dest = next(d for d in self.choices if d["id"] == "italy_amalfi")
        self.assertEqual(dest["stage"], ITALY_STAGE)
        view = destination_preview(dest, self.catalog)
        self.assertEqual(view["country"], "Itália")
        self.assertIsNone(view["photo"])
        self.assertTrue(all(a["minutes"] is None for a in view["details"]))

    def test_preview_does_not_change_plan_or_catalog(self):
        dest = next(d for d in self.choices if d["id"] == "colmar")
        original_catalog, original_dest = deepcopy(self.catalog), deepcopy(dest)
        fake = MagicMock()
        fake.columns.return_value = (MagicMock(), MagicMock())
        with patch("ux55_visual_outing_ui.st", fake), patch(
            "ux55_visual_outing_ui.photo_markup", return_value="<div>visual</div>"
        ), patch("ux55_visual_outing_ui.photo_credit", return_value=None):
            render_destination_preview(dest, self.catalog, [])
        self.assertTrue(fake.html.called)
        self.assertEqual(fake.expander.call_count, len(dest["attractions"]))
        self.assertFalse(fake.button.called)
        self.assertEqual(self.catalog, original_catalog)
        self.assertEqual(dest, original_dest)


if __name__ == "__main__":
    unittest.main()
