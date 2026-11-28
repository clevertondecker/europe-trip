import copy
import unittest
from data26b1_fare_reference_model import (
    load_fare_references, validate_fare_references, fare_reference_coverage, official_source,
)

class FareReferencesTest(unittest.TestCase):
    def setUp(self):
        self.data = load_fare_references()

    def test_production_contract(self):
        result = fare_reference_coverage(data=self.data)
        for counts in (result["scope"], result["batch"], *result["by_base"].values(), *result["by_destination"].values()):
            self.assertLessEqual(counts["legacy"], counts["with_references"])
            self.assertLessEqual(counts["with_references"], counts["total"])
            self.assertEqual(counts["with_references"], counts["legacy"] + counts["net_new_references"])
            self.assertEqual(counts["batch_references"], counts["legacy_overlap"] + counts["net_new_references"])
            self.assertEqual(counts["legacy"], counts["legacy_overlap"] + counts["legacy_only"])

    def test_sources(self):
        for domain in ("www.bahn.de", "www.sbb.ch", "www.cfl.lu", "www.belgiantrain.be", "www.nsinternational.com", "www.eurostar.com"):
            self.assertTrue(official_source("https://" + domain + "/tickets"))
        for url in ("https://bahn.de.evil.org", "http://bahn.de", "https://bahn.de@evil.org", "https://bahn.de:444"):
            self.assertFalse(official_source(url))

    def test_duplicate_alias_scope(self):
        data = copy.deepcopy(self.data)
        data["scope"]["destinations"].append("brussels")
        with self.assertRaises(ValueError):
            validate_fare_references(data)

    def test_duplicate_alias_observation(self):
        data = copy.deepcopy(self.data)
        row = copy.deepcopy(next(r for r in data["references"] if r["destination_id"] == "bruxelles"))
        row["destination_id"] = "brussels"
        data["references"].append(row)
        with self.assertRaises(ValueError):
            validate_fare_references(data)

    def test_same_capture_changed_price_is_conflict_not_new_observation(self):
        data = copy.deepcopy(self.data)
        row = copy.deepcopy(next(r for r in data["references"] if r["status"] == "observed_calendar"))
        row["amount_minor"] += 100
        data["references"].append(row)
        with self.assertRaisesRegex(ValueError, "Conflito de preço"):
            validate_fare_references(data)

    def test_distinct_capture_can_have_another_price(self):
        data = copy.deepcopy(self.data)
        row = copy.deepcopy(next(r for r in data["references"] if r["status"] == "observed_calendar"
                                 and r["travel_date"] > data["checked_at"]))
        row["source_capture_date"] = row["researched_at"]
        row["amount_minor"] += 100
        data["references"].append(row)
        validate_fare_references(data)

    def test_revision_requires_matching_currency_units_direction_and_date(self):
        for field, value in (("currency", "GBP"), ("passengers", 2),
                             ("direction", "roundtrip"), ("kind", "quote"),
                             ("travel_date", "2026-12-06"), ("destination_id", "reims")):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                row = next(r for r in data["references"] if r["status"] == "corroborated_price")
                row["review"][field] = value
                with self.assertRaises(ValueError):
                    validate_fare_references(data)

    def test_unknown_mode_cannot_corroborate_even_equal_price(self):
        data = copy.deepcopy(self.data)
        row = next(r for r in data["references"] if r["status"] == "corroborated_price")
        row["review"].update(transport_mode="unknown", currency=None, passengers=None,
                             direction=None, kind=None, unit_provenance="not_documented")
        with self.assertRaisesRegex(ValueError, "revisão inconsistente"):
            validate_fare_references(data)
        row["status"] = "not_reproduced"
        validate_fare_references(data)

    def test_review_must_have_independent_matching_calendar(self):
        data = copy.deepcopy(self.data)
        row = next(r for r in data["references"] if r["status"] == "corroborated_price")
        row["review"]["commercial_brand"] = "unsupported"
        with self.assertRaisesRegex(ValueError, "calendário correspondente"):
            validate_fare_references(data)

    def test_legitimate_date_difference(self):
        data = copy.deepcopy(self.data)
        row = copy.deepcopy(next(r for r in data["references"] if r["status"] == "observed_calendar"))
        row["travel_date"] = "2027-01-09"
        data["references"].append(row)
        validate_fare_references(data)

    def test_wrong_country_and_date(self):
        for field, value in (("destination_country", "XX"), ("researched_at", "2028-01-01"), ("source_capture_date", "2028-01-01")):
            data = copy.deepcopy(self.data)
            data["references"][0][field] = value
            with self.assertRaises(ValueError):
                validate_fare_references(data)

    def test_historical_price_preserved(self):
        historical = next(r for r in self.data["references"] if r["status"] == "divergent_price")
        self.assertNotEqual(historical["amount_minor"], historical["review"]["amount_minor"])
        self.assertIsNone(historical["source_capture_date"])

    def test_gap_classification(self):
        data = copy.deepcopy(self.data)
        gap = next(r for r in data["gaps"] if r["reason"] == "research_pending")
        gap["researched_at"] = data["checked_at"]
        with self.assertRaises(ValueError):
            validate_fare_references(data)

    def test_distinct_pair_union(self):
        data = {"scope": {"bases": ["mulhouse", "lille"], "destinations": ["paris"],
                          "batch_destinations": ["paris"]},
                "references": [{"origin_id": "mulhouse", "destination_id": "paris", "status": "observed_calendar"},
                               {"origin_id": "lille", "destination_id": "paris", "status": "not_reproduced"}]}
        row = {"origin_id": "mulhouse", "destination_id": "paris",
               "fare_from_eur_person_oneway": 20, "source_url": "https://www.sncf-connect.com/train",
               "mode": "rail", "fare_conditions": "advertised", "evidence_date": "2026-11-27"}
        legacy = {"observations": [row, {**row, "origin_id": "lille", "mode": "bus"}]}
        result = fare_reference_coverage(data, legacy, {"records": []})["scope"]
        self.assertEqual(result["legacy"], 1)
        self.assertEqual(result["with_references"], 1)
        self.assertEqual(result["legacy_overlap"], 1)
        self.assertEqual(result["net_new_references"], 0)
        self.assertEqual(result["legacy_only"], 0)
        self.assertEqual(result["batch_references"], 1)
        self.assertEqual(result["complete_roundtrip"], 0)

    def test_data24_parity(self):
        from data24_coverage_model import rail_coverage
        before = rail_coverage()
        fare_reference_coverage(data=self.data)
        after = rail_coverage()
        self.assertEqual(before, after)

    def test_fare_panel_filters_and_nonempty_tables(self):
        from streamlit.testing.v1 import AppTest
        script = (
            "from ux132_research_coverage_ui import render_fare_evidence\n"
            "render_fare_evidence({'bases': [], 'destinations': []})\n"
        )
        app = AppTest.from_string(script, default_timeout=30).run()
        def table(columns):
            matches = [e.value for e in app.dataframe if set(columns) <= set(e.value.columns)]
            self.assertEqual(len(matches), 1)
            return matches[0]
        self.assertFalse(app.exception)
        self.assertFalse(app.warning)
        recent = table(("Origem", "Destino", "Valor", "Estado"))
        self.assertGreater(len(recent), 0)
        self.assertTrue(all(recent["Estado"] == "Calendário observado"))
        app.selectbox(key="ux132_fare_reference_status").select("Histórico").run()
        self.assertFalse(app.exception)
        self.assertFalse(app.warning)
        historical = table(("Origem", "Destino", "Valor", "Estado"))
        self.assertGreater(len(historical), 0)
        self.assertTrue(all(historical["Estado"].str.startswith("Histórico:")))
        app.selectbox(key="ux132_fare_reference_status").select("Lacunas").run()
        app.selectbox(key="ux132_fare_reference_base").select("metz").run()
        self.assertFalse(app.exception)
        self.assertFalse(app.warning)
        gaps = table(("Origem", "Destino", "Motivo"))
        self.assertGreater(len(gaps), 0)
        self.assertTrue(all(gaps["Origem"] == "Metz"))

    def test_review_must_match_historical_status(self):
        data = copy.deepcopy(self.data)
        row = next(r for r in data["references"] if r["status"] == "divergent_price")
        row["review"]["amount_minor"] = row["amount_minor"]
        with self.assertRaisesRegex(ValueError, "revisão inconsistente"):
            validate_fare_references(data)

    def test_catalog_detects_wrong_country(self):
        from unittest.mock import patch
        from data26b1_fare_reference_model import validate_catalog_scope
        with patch("base_research_expanded_model.load_research", return_value={"cities":[{"id":"metz","country":"França"}]}), patch("trip01_supplemental_discovery.build_exploration_discovery", return_value={"destinations":[{"id":"bruges_be","country":"França"}]}):
            with self.assertRaisesRegex(ValueError, "catálogo"):
                validate_catalog_scope({"metz"}, {"bruges_be"})

    def test_bern_is_research_only_without_catalog_mutation(self):
        from unittest.mock import patch
        from data26b1_fare_reference_model import validate_catalog_scope
        bases = {"cities": [{"id":"metz","country":"França"}]}
        destinations = {"destinations": []}
        with patch("base_research_expanded_model.load_research", return_value=bases), patch("trip01_supplemental_discovery.build_exploration_discovery", return_value=destinations):
            validate_catalog_scope({"metz"}, {"bern"})
            with self.assertRaisesRegex(ValueError, "destino paris"):
                validate_catalog_scope({"metz"}, {"paris"})
        self.assertEqual(destinations, {"destinations": []})
        with patch("base_research_expanded_model.load_research", return_value=bases), patch("trip01_supplemental_discovery.build_exploration_discovery", return_value={"destinations":[{"id":"bern","country":"França"}]}):
            with self.assertRaisesRegex(ValueError, "destino bern"):
                validate_catalog_scope({"metz"}, {"bern"})


    def test_return_and_product_references_do_not_expand_outbound_coverage(self):
        result = fare_reference_coverage(data=self.data)
        stripped = copy.deepcopy(self.data)
        returns = stripped.pop("return_references")
        products = stripped.pop("regional_products")
        self.assertEqual(len(returns), 5)
        self.assertEqual(len(products), 12)
        self.assertEqual(result["scope"]["total"], 60)
        self.assertEqual(result, fare_reference_coverage(data=stripped))
        for r in returns:
            self.assertEqual(r["origin_id"], "paris")
            self.assertEqual(r["travel_date"], "2026-12-06")
            self.assertIsNone(r["service_id"])
            self.assertIsNone(r["availability"])
        indexed = {p["id"]: p for p in products}
        self.assertEqual(indexed["dual_2_family"]["couple_use"], "requires_children")
        self.assertEqual(indexed["fluo_group_weekend"]["price_unit"], "group_day")
        self.assertIsNone(indexed["saar_lor_lux"]["amount_minor"])

    def test_invalid_return_or_product_rejected(self):
        for kind, key, changes in (
            ("return_references", "lille", {"origin_id": "lille"}),
            ("return_references", "lille", {"passengers": 2}),
            ("return_references", "lille", {"service_id": "7014"}),
            ("return_references", "lille", {"availability": True}),
            ("regional_products", "dual_2_family", {"couple_use": "group_allowed"}),
            ("regional_products", "sbb_saver_day_no_card", {"valid_for_2027": True}),
            ("regional_products", "saar_lor_lux", {"amount_minor": 1000}),
            ("regional_products", "fluo_group_weekend", {"group_max": 1}),
        ):
            with self.subTest(kind=kind, key=key, changes=changes):
                data = copy.deepcopy(self.data)
                row = next(r for r in data[kind]
                           if r.get("id", r.get("destination_id")) == key)
                row.update(changes)
                with self.assertRaises(ValueError):
                    validate_fare_references(data)

    def test_regional_product_and_return_tables_in_existing_panel(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string(
            "from ux132_research_coverage_ui import render_fare_evidence\n"
            "render_fare_evidence({'bases': [], 'destinations': []})\n"
        ).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertFalse(app.warning)
        returns = [e.value for e in app.dataframe
                   if {"Origem", "Destino", "Preço indicativo"} <= set(e.value.columns)]
        products = [e.value for e in app.dataframe
                    if {"Produto", "Preço publicado", "Uso"} <= set(e.value.columns)]
        self.assertEqual(len(returns), 1)
        self.assertEqual(len(returns[0]), 5)
        self.assertEqual(len(products), 1)
        self.assertEqual(len(products[0]), 12)
        app.selectbox(key="ux132_regional_product").select("dual_2_family").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("exige crianças" in str(x.value) for x in app.markdown))
