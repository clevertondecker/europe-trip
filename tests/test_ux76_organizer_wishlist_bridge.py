"""Wishlist destinations are visible in organizer, never auto-confirmed."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from itinerary_flow_model import FRANCE_STAGE, ITALY_STAGE, UNASSIGNED, selected_rows_for_stage
from trip_plan_model import new_plan
from ux61_destination_board_model import organizer_wishlist_candidates
from ux502_destination_interests_model import empty_interests
from ux45_outing_contract import apply_outing


class WishlistOrganizerBridgeTests(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan()
        self.catalog={
            "destinations":[{"id":"colmar","name":"Colmar"}],
            "attractions":[{"id":"colmar_oldtown","name":"Centro histórico",
                            "destination_id":"colmar"}],
        }
        self.discovery={"destinations":[
            {"id":"colmar","name":"Colmar","country":"França"},
            {"id":"unmapped","name":"Destino sem passeio","country":"Bélgica"},
        ]}
        self.wishes=empty_interests()
        self.wishes["items"]=[
            {"destination_id":"colmar","priority":"must_visit"},
            {"destination_id":"unmapped","priority":"interested"},
        ]

    def test_wishes_are_visible_without_becoming_outings(self):
        original_plan=deepcopy(self.plan)
        original_wishes=deepcopy(self.wishes)
        result=organizer_wishlist_candidates(self.wishes,self.plan,self.discovery,
                                             self.catalog,FRANCE_STAGE)
        self.assertEqual([row["id"] for row in result["eligible"]],["colmar"])
        self.assertEqual([row["id"] for row in result["unsupported"]],["unmapped"])
        self.assertEqual(selected_rows_for_stage(self.plan,self.catalog,FRANCE_STAGE),[])
        self.assertEqual(self.plan,original_plan)
        self.assertEqual(self.wishes,original_wishes)

    def test_explicit_confirmation_creates_single_undated_visit(self):
        candidate=organizer_wishlist_candidates(self.wishes,self.plan,self.discovery,
                                               self.catalog,FRANCE_STAGE)["eligible"][0]
        updated,outcome=apply_outing(self.plan,self.catalog,candidate["id"],[],
                                     UNASSIGNED,confirmed=True)
        self.assertEqual(outcome.action,"added")
        self.assertEqual(outcome.attraction_count,0)
        self.assertEqual(len(selected_rows_for_stage(updated,self.catalog,FRANCE_STAGE)),1)
        self.assertEqual(selected_rows_for_stage(updated,self.catalog,FRANCE_STAGE)[0]["period"],
                         UNASSIGNED)
        self.assertEqual(updated["assignments"],{})
        self.assertEqual(self.plan["flexible_visits"],[])
        remaining=organizer_wishlist_candidates(self.wishes,updated,self.discovery,
                                                self.catalog,FRANCE_STAGE)
        self.assertEqual(remaining["eligible"],[])
        self.assertEqual(len(remaining["unsupported"]),1)

    def test_no_confirmation_never_mutates_tripplan(self):
        original=deepcopy(self.plan)
        with self.assertRaisesRegex(ValueError,"Confirme"):
            apply_outing(self.plan,self.catalog,"colmar",[],UNASSIGNED,confirmed=False)
        self.assertEqual(self.plan,original)

    def test_discarded_and_confirmed_wishes_are_not_reoffered(self):
        self.wishes["items"][1]["priority"]="discarded"
        updated,_=apply_outing(self.plan,self.catalog,"colmar",[],UNASSIGNED,confirmed=True)
        result=organizer_wishlist_candidates(self.wishes,updated,self.discovery,
                                             self.catalog,FRANCE_STAGE)
        self.assertEqual(result,{"eligible":[],"other_stage":[],"unsupported":[]})

    def test_wishlist_is_stage_specific_and_never_guesses_id_from_name(self):
        result=organizer_wishlist_candidates(self.wishes,self.plan,self.discovery,
                                             self.catalog,ITALY_STAGE)
        self.assertEqual(result["eligible"],[])
        self.assertEqual([row["id"] for row in result["other_stage"]],["colmar"])
        self.assertEqual([row["id"] for row in result["unsupported"]],["unmapped"])
        with self.assertRaises(ValueError):
            organizer_wishlist_candidates(self.wishes,self.plan,self.discovery,
                                          self.catalog,"Etapa inválida")


class OrganizerIntegrationSmokeTests(WishlistOrganizerBridgeTests):
    @patch("ux61_destination_board_ui._discovery")
    @patch("itinerary_flow_ui.st")
    def test_organizer_surfaces_wishlist_even_when_no_visits_confirmed(self, st, discovery):
        from itinerary_flow_ui import _render_organizer_wishlist
        discovery.return_value=self.discovery
        st.session_state={"ux502_interests":self.wishes}
        st.multiselect.return_value=["colmar"]
        st.button.return_value=False
        _render_organizer_wishlist(self.plan,self.catalog,FRANCE_STAGE)
        self.assertEqual(st.multiselect.call_args.args[0],"Destinos para incluir no roteiro")
        self.assertIn("colmar",st.multiselect.call_args.args[1])
        st.button.assert_any_call("Incluir selecionados no roteiro",
                                  type="primary",disabled=False,
                                  key="flow_wishlist_confirm_França")

    @patch("ux61_destination_board_ui._discovery")
    @patch("itinerary_flow_ui.st")
    def test_removed_wishlist_entry_clears_stale_widget_selection(self, st, discovery):
        from itinerary_flow_ui import _render_organizer_wishlist
        discovery.return_value=self.discovery
        st.session_state={
            "ux502_interests":self.wishes,
            "flow_wishlist_to_plan_França":["colmar","no-longer-eligible"],
        }
        st.multiselect.return_value=["colmar"]
        st.button.return_value=False
        _render_organizer_wishlist(self.plan,self.catalog,FRANCE_STAGE)
        self.assertEqual(st.session_state["flow_wishlist_to_plan_França"],["colmar"])
        self.assertEqual(st.multiselect.call_args.kwargs["key"],
                         "flow_wishlist_to_plan_França")

    @patch("ux61_destination_board_ui._discovery")
    @patch("itinerary_flow_ui.commit_undated_destinations")
    @patch("itinerary_flow_ui.active_plan")
    @patch("itinerary_flow_ui.st")
    def test_organizer_promotes_only_after_explicit_click(self, st, active, commit, discovery):
        from itinerary_flow_ui import _render_organizer_wishlist
        discovery.return_value=self.discovery
        active.return_value=self.plan
        st.session_state={"ux502_interests":self.wishes}
        st.multiselect.return_value=["colmar"]
        st.button.return_value=True
        _render_organizer_wishlist(self.plan,self.catalog,FRANCE_STAGE)
        commit.assert_called_once_with(["colmar"],FRANCE_STAGE,confirmed=True)
        st.rerun.assert_called_once()
        self.assertIn("incluído",st.session_state["flow_notice"])


if __name__=="__main__":
    unittest.main()
