"""UX120 mode compatibility and smart calendar protection."""
import unittest
from copy import deepcopy
from ux120_organizer_navigation import organizer_mode,legacy_mode
from trip_plan_model import new_plan
from attractions_model import load_attractions,load_base_routes
from itinerary_flow_model import add_undated_choices, FRANCE_STAGE
from ux48_weekend_groups_model import empty_groups,create_group,available_weekends,set_rest_weekend
from smart_calendar_model import suggest_calendar


class OrganizerTests(unittest.TestCase):
    def test_legacy_routes_roundtrip(self):
        for mode,legacy in (("Visitas","Por período ou data"),
                            ("Calendário","Calendário inteligente"),
                            ("Viagens agrupadas","Viagens agrupadas")):
            self.assertEqual(legacy_mode(mode,FRANCE_STAGE),legacy)
            self.assertEqual(organizer_mode(legacy,FRANCE_STAGE),mode)
        self.assertEqual(legacy_mode("Calendário",FRANCE_STAGE,"Completo"),"Calendário completo")
        self.assertEqual(organizer_mode("Viagens agrupadas","Itália"),"Visitas")

    def test_suggestions_do_not_schedule_group_members_or_reserved_days(self):
        catalog=load_attractions()
        plan=add_undated_choices(new_plan(),catalog,["colmar","basel"],FRANCE_STAGE)
        state=empty_groups(plan)
        dates=[r["start"] for r in available_weekends(state,plan,catalog)
               if r["status"]=="livre · não reservado"]
        state=create_group(state,plan,catalog,name="Grupo",destinations=["basel"],start_date=dates[0])
        state=set_rest_weekend(state,plan,catalog,dates[1],True)
        before=deepcopy((plan,state))
        proposals=suggest_calendar(plan,catalog,load_base_routes(),weekend_groups=state,stage=FRANCE_STAGE)
        from ux48_weekend_groups_model import _trip_days
        forbidden=set(_trip_days(dates[0],0)+_trip_days(dates[1],1))
        self.assertTrue(proposals)
        for proposal in proposals:
            self.assertFalse(set(proposal["assignments"]) & forbidden)
            self.assertNotIn("basel",proposal["assignments"].values())
        self.assertEqual((plan,state),before)
