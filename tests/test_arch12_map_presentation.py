import unittest
from unittest.mock import patch
from map_presentation_ui import render_map_view


class MapPresentationTests(unittest.TestCase):
    def test_empty_map_is_explained_without_rendering_layers(self):
        with patch("map_presentation_ui.st.info") as notice, patch(
                "map_presentation_ui.st.pydeck_chart") as chart:
            render_map_view([])
        notice.assert_called_once()
        chart.assert_not_called()

    def test_map_preserves_scatter_labels_and_tooltip(self):
        place={"name":"Strasbourg","country":"França","role":"Destino",
               "status":"candidate","lat":48.5734,"lon":7.7521}
        # Existing style palette defines allowed status labels.
        from data_model import STATUS_COLORS
        place["status"]=next(iter(STATUS_COLORS))
        with patch("map_presentation_ui.st.pydeck_chart") as chart:
            render_map_view([place],height=350,center=(48.57,7.75),
                            zoom=7,show_labels=False)
        chart.assert_called_once()
        args, kwargs=chart.call_args
        deck=args[0]
        self.assertEqual(len(deck.layers),1)
        self.assertEqual(kwargs["height"],350)
        self.assertEqual(kwargs["width"],"stretch")

    def test_map_with_labels_keeps_two_layers_and_original_data(self):
        from copy import deepcopy
        from data_model import STATUS_COLORS
        place={"name":"Metz","country":"França","role":"Base",
               "status":next(iter(STATUS_COLORS)),"lat":49.1193,"lon":6.1757}
        original=deepcopy(place)
        with patch("map_presentation_ui.st.pydeck_chart") as chart:
            render_map_view([place],show_labels=True)
        chart.assert_called_once()
        deck=chart.call_args.args[0]
        self.assertEqual(len(deck.layers),2)
        self.assertIn("name",str(deck.layers[1].get_text))
        self.assertIn("name",deck.to_json())
        self.assertEqual(place,original)
