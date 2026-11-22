"""UX93: map only projects existing wishlist/plan decisions; it never writes them."""
import unittest
from copy import deepcopy

from ux93_map_projection import annotate_map_places,filter_map_places
from trip_plan_model import new_plan


class MapDecisionProjectionTests(unittest.TestCase):
    def test_wishlist_itinerary_and_candidates_without_mutation(self):
        places=[
            {"id":"colmar","name":"Colmar","country":"França","phase":"france",
             "role":"Cidade","status":"opcional"},
            {"id":"metz","name":"Metz","country":"França","phase":"france",
             "role":"Base","status":"candidata"},
            {"id":"rome","name":"Roma","country":"Itália","phase":"italy",
             "role":"Roteiro","status":"opcional"},
        ]
        plan=new_plan()
        plan["flexible_visits"]=[{"destination_id":"colmar","stage":"França",
                                  "attractions":[],"period":"Não definido"}]
        wishes={"items":[{"destination_id":"colmar","priority":"must_visit"},
                         {"destination_id":"metz","priority":"discarded"},
                         {"destination_id":"rome","priority":"interested"}]}
        original=deepcopy((places,plan,wishes))
        output=annotate_map_places(places,wishes,plan)
        self.assertEqual([p["ux93_group"] for p in output],
                         ["No roteiro","Base candidata","Na minha lista"])
        self.assertIn("No roteiro",output[0]["role"])
        self.assertEqual((places,plan,wishes),original)
        self.assertEqual([p["id"] for p in
            filter_map_places(output,group="Na minha lista")],["rome"])
        self.assertEqual([p["id"] for p in
            filter_map_places(output,stage="Itália")],["rome"])

    def test_invalid_group_rejected_and_empty_selection_is_safe(self):
        with self.assertRaises(ValueError):
            filter_map_places([],group="Reservados")
        with self.assertRaises(ValueError):
            filter_map_places([],stage="Outros")
        self.assertEqual(filter_map_places([]),[])


if __name__=="__main__":
    unittest.main()
