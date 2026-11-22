"""UX93: map only projects existing wishlist/plan decisions; it never writes them."""
import unittest
from copy import deepcopy

from ux93_map_projection import annotate_map_places,filter_map_places,map_identity,unmapped_wishes,unmapped_planned_places,ITALY_TO_MAP
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

    def test_real_catalog_italy_identifiers_and_missing_geometry(self):
        from data_model import load_data
        from itinerary_planner import load_itinerary
        from attractions_model import load_attractions
        from catalog import build_catalog
        from italy_honeymoon_model import load_honeymoon
        from trip01_supplemental_discovery import build_exploration_discovery
        from ux502_destination_interests_model import empty_interests,set_interest

        real_places=build_catalog(load_data()["places"],load_itinerary(),
                                  load_attractions()["destinations"])
        geometry={map_identity(p["id"]) for p in real_places}
        italy={r["id"] for r in load_honeymoon()["itinerary_places"]}
        self.assertTrue(set(ITALY_TO_MAP)<=italy)
        self.assertTrue(set(ITALY_TO_MAP.values())<=geometry)
        self.assertEqual(map_identity("roma"),map_identity("italy_rome"))
        self.assertEqual(map_identity("napoles"),map_identity("italy_naples"))
        self.assertNotIn(map_identity("italy_ravello"),geometry)
        self.assertNotIn(map_identity("italy_pompeii"),geometry)

        plan=new_plan()
        plan["flexible_visits"]=[
            {"destination_id":"italy_rome","stage":"Itália",
             "attractions":[],"period":"Ainda não definido"},
            {"destination_id":"colmar","stage":"França",
             "attractions":[],"period":"Ainda não definido"},
        ]
        # The packages mapping uses destination IDs as keys and attraction
        # IDs as values. Attraction IDs must never become map locations.
        plan["packages"]={"strasbourg":["strasbourg_cathedral"]}
        wishes=empty_interests()
        discovery=build_exploration_discovery()
        wishes=set_interest(wishes,"obernai","must_visit",discovery)
        wishes=set_interest(wishes,"colmar","interested",discovery)
        original=deepcopy((real_places,plan,wishes))
        rows=annotate_map_places(real_places,wishes,plan)
        by_id={map_identity(p["id"]):p for p in rows}
        self.assertEqual(by_id["rome"]["ux93_group"],"No roteiro")
        self.assertEqual(by_id["colmar"]["ux93_group"],"No roteiro")
        self.assertEqual(by_id["strasbourg"]["ux93_group"],"No roteiro")
        self.assertEqual((real_places,plan,wishes),original)
        self.assertIn("obernai",unmapped_wishes(real_places,wishes))
        self.assertNotIn("colmar",unmapped_wishes(real_places,wishes))
        self.assertFalse(unmapped_wishes(real_places,empty_interests()))
        self.assertFalse(unmapped_planned_places(real_places,plan))
        plan_with_unmapped=deepcopy(plan)
        plan_with_unmapped["flexible_visits"].append({
            "destination_id":"italy_ravello","stage":"Itália",
            "attractions":[],"period":"Ainda não definido"})
        self.assertEqual(unmapped_planned_places(real_places,plan_with_unmapped),
                         {"italy_ravello"})

    def test_invalid_group_rejected_and_empty_selection_is_safe(self):
        with self.assertRaises(ValueError):
            filter_map_places([],group="Reservados")
        with self.assertRaises(ValueError):
            filter_map_places([],stage="Outros")
        self.assertEqual(filter_map_places([]),[])


if __name__=="__main__":
    unittest.main()
