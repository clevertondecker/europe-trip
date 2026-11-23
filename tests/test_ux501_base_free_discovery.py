"""UX 5.0.1 — base-independent catalog and no official mutations."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from ux501_destination_discovery_model import (
    build_destination_discovery, filter_destinations,
)
from attractions_model import load_attractions
from dq32_macro_opportunities_model import load_macro_tourism

ROOT=Path(__file__).resolve().parents[1]


class BaseFreeDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory=build_destination_discovery()

    def test_no_base_required_and_all_known_places_present(self):
        model=self.inventory
        self.assertFalse(model["base_required"])
        self.assertTrue(model["read_only"])
        self.assertGreaterEqual(model["destination_count"],30)
        ids={row["id"] for row in model["destinations"]}
        self.assertTrue({"mulhouse","strasbourg","lille","colmar",
                         "brussels","luxembourg_city","bruges_be"}<=ids)
        self.assertEqual(len(ids),model["destination_count"])
        self.assertEqual(model["canonical_attractions_count"],65)
        self.assertEqual(model["dq32_source_records_count"],30)

    def test_identity_dedup_preserves_canonical_bock_source(self):
        model=self.inventory
        lux=next(row for row in model["destinations"]
                 if row["id"]=="luxembourg_city")
        bock=[x for x in lux["attractions"] if x["id"]=="lux_bock"]
        self.assertEqual(len(bock),1)
        self.assertEqual(bock[0]["reconciled_source_ids"],
                         ["dq32_luxembourg_city_22"])
        self.assertEqual(sum(item["id"]=="lux_bock"
                             for row in model["destinations"]
                             for item in row["attractions"]),1)
        self.assertEqual(len(model["reconciled_aliases"]),1)

    def test_search_country_experience_and_attraction(self):
        all_countries=self.inventory["countries"]
        self.assertIn("Bélgica",all_countries)
        belgian=filter_destinations(self.inventory,country="Bélgica")
        self.assertTrue(belgian)
        self.assertTrue(all(row["country"]=="Bélgica" for row in belgian))
        colmar=filter_destinations(self.inventory,query="colmar")
        self.assertTrue(any(row["id"]=="colmar" for row in colmar))
        bock=filter_destinations(self.inventory,query="casemates")
        self.assertTrue(any(row["id"]=="luxembourg_city" for row in bock))
        museums=filter_destinations(self.inventory,categories=("Museus",))
        self.assertTrue(museums)
        self.assertTrue(all("Museus" in row["categories"] for row in museums))

    def test_destinations_without_attractions_remain_explorable(self):
        empty=[x for x in self.inventory["destinations"]
               if not x["attractions"]]
        self.assertTrue(empty)
        self.assertTrue(all(
            x["research_status"]=="destination_known_attractions_not_indexed"
            and x["feasible_from_base"] is None
            and not x["verified_weekend_return"]
            for x in empty))
        result=filter_destinations(self.inventory,query=empty[0]["name"])
        self.assertTrue(any(x["id"]==empty[0]["id"] for x in result))

    def test_interest_selection_does_not_change_catalog_or_claim_trip(self):
        initial=deepcopy(self.inventory)
        selected=filter_destinations(self.inventory,selected=("lille","colmar"))
        self.assertEqual([row["id"] for row in selected[:2]],["lille","colmar"])
        self.assertEqual(self.inventory,initial)
        self.assertTrue(all(row["feasible_from_base"] is None
                            and not row["officially_selected"]
                            for row in selected))

    def test_invalid_filters_rejected_and_source_provenance(self):
        with self.assertRaises(ValueError):
            filter_destinations(self.inventory,country="Atlantis")
        with self.assertRaises(ValueError):
            filter_destinations(self.inventory,selected=("lille","lille"))
        for row in self.inventory["destinations"]:
            for attr in row["attractions"]:
                self.assertTrue(attr["source_url"].startswith("https://"))
                self.assertIn(attr["kind"],("legacy_catalog","dq32_sourced_local"))
                self.assertTrue(attr["id"])


class LegacySelectionRecoveryTests(unittest.TestCase):
    def test_widget_state_is_mirrored_before_cleanup_and_restored_after(self):
        from ux502_destination_interests_ui import _recover_previous_session_interests
        state={"ux501_interest_session":["colmar","lille"]}
        _recover_previous_session_interests(state)
        self.assertEqual(state["ux502_transient_shadow"],["colmar","lille"])
        # Simulate Streamlit cleanup when the obsolete multiselect is unmounted.
        state.pop("ux501_interest_session")
        _recover_previous_session_interests(state)
        self.assertEqual(state["ux501_interest_session"],["colmar","lille"])

    def test_empty_old_widget_does_not_erase_recoverable_selection(self):
        from ux502_destination_interests_ui import _recover_previous_session_interests
        state={"ux501_interest_session":[],
               "ux502_transient_shadow":["colmar"]}
        _recover_previous_session_interests(state)
        self.assertEqual(state["ux502_transient_shadow"],["colmar"])

class BaseFreeDiscoveryAppTests(unittest.TestCase):
    def test_discover_without_switching_base_and_leave_tripplan_untouched(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        initial=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Descobrir destinos" in x.value for x in app.markdown))
        self.assertFalse(any(x.key=="ux501_interest_session" for x in app.multiselect))
        self.assertFalse(any("Pesquisa do catálogo e seleção anterior" in x.label
                             for x in app.expander))
        # Other legacy itinerary widgets belong to a separate compatibility path.
        self.assertTrue(any(x.key=="attractions_scenario_base" for x in app.selectbox))
        app.selectbox(key="ux501_country").set_value("Bélgica").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],initial)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))

    def test_previous_interests_survive_navigation_and_reconcile_in_wishlist(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        initial=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        chosen=["colmar","lille","brussels","basel","bruges_be"]
        # Previously saved session-only choices must remain recoverable
        # even though the obsolete editor is no longer rendered.
        app.session_state["ux501_interest_session"]=list(chosen)
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertFalse(any(x.key=="ux501_interest_session" for x in app.multiselect))
        app.selectbox(key="ux501_page").set_value(2).run()
        app.selectbox(key="ux501_country").set_value("Bélgica").run()
        app.selectbox(key="ux501_country").set_value("Todos os países").run()
        app.text_input(key="ux501_search").set_value("casemates").run()
        app.text_input(key="ux501_search").set_value("").run()
        self.assertEqual(app.session_state["ux501_interest_session"],chosen)
        self.assertEqual(app.session_state["ux502_transient_shadow"],chosen)
        app.radio(key="ux502_view").set_value("Minha lista").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux502_migrate",{x.key for x in app.button})
        app.button(key="ux502_migrate").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(
            {x["destination_id"] for x in app.session_state["ux502_interests"]["items"]},
            set(chosen))
        self.assertEqual(app.session_state["advisor_plan"],initial)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))

    def test_empty_filter_results_preserve_legacy_session_choices(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.session_state["ux501_interest_session"]=["colmar"]
        app.run()
        app.text_input(key="ux501_search").set_value("inexistente-ux90-999").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertFalse(any(x.key=="ux501_interest_session" for x in app.multiselect))
        self.assertEqual(app.session_state["ux501_interest_session"],["colmar"])
        app.text_input(key="ux501_search").set_value("").run()
        self.assertEqual(app.session_state["ux501_interest_session"],["colmar"])

    def test_discarded_card_reconsideration_without_plan_mutation(self):
        from ux502_destination_interests_model import empty_interests,set_interest
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.button(key="ux64_sidebar_nav_0").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Descobrir").run()
        app.text_input(key="ux501_search").set_value("colmar").run()
        plan=deepcopy(app.session_state["advisor_plan"])
        self.assertIn("ux502_add_colmar",{x.key for x in app.button})
        self.assertNotIn("ux502_restore_colmar",{x.key for x in app.button})
        for priority in ("must_visit","interested","maybe"):
            app.session_state["ux502_interests"]=set_interest(
                empty_interests(),"colmar",priority)
            app.run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            self.assertNotIn("ux502_add_colmar",{x.key for x in app.button})
            self.assertNotIn("ux502_restore_colmar",{x.key for x in app.button})
        app.session_state["ux502_interests"]=set_interest(
            empty_interests(),"colmar","discarded")
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux502_restore_colmar",{x.key for x in app.button})
        self.assertNotIn("ux502_add_colmar",{x.key for x in app.button})
        app.button(key="ux502_restore_colmar").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux502_interests"]["items"],
                         [{"destination_id":"colmar","priority":"interested"}])
        self.assertEqual(app.session_state["advisor_plan"],plan)

    def test_first_discovery_does_not_require_exploratory_base(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Descobrir destinos" in x.value for x in app.markdown))
        self.assertFalse(any("Destinos para descobrir" in x.value
                             and "ui-kpi-card" in x.value
                             for x in app.markdown))
        self.assertTrue(any(x.key=="ux501_search" for x in app.text_input))
        self.assertTrue(any(x.key=="ux501_country" for x in app.selectbox))


if __name__=="__main__":
    unittest.main()
