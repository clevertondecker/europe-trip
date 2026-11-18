"""UX3.8 researched-quotation invariants, no payments or baseline writes."""
import unittest
from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal
from unittest.mock import Mock

from quote_research_model import (
    new_quote,empty_collection,upsert_quote,remove_quote,
    encode_collection,decode_collection,comparable_quotes,quote_difference,
    housing_budget_whatif,cloud_load,cloud_save
)
from private_continuity_store import StorageConflict
from trip_plan_model import new_plan


class QuoteResearchTests(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan()
        self.before=deepcopy(self.plan)
        start=date.fromisoformat(self.plan["departure_date"])+timedelta(days=self.plan["italy_days"])
        end=date.fromisoformat(self.plan["departure_date"])+timedelta(days=self.plan["total_days"])
        self.start,self.end=start.isoformat(),end.isoformat()

    def quote(self,**changes):
        kw=dict(plan_id=self.plan["plan_id"],name="Apartamento mobiliado",category="housing",
                amount="2850.00",currency="EUR",unit="stay",city_id=self.plan["base_city"],
                quantity=1,travelers=2,start_date=self.start,end_date=self.end,
                researched_at="2026-11-16")
        kw.update(changes)
        return new_quote(**kw)

    def test_crud_independent_and_exportable(self):
        a=self.quote()
        b=self.quote(name="Outra opção",amount="3100.00")
        source=empty_collection()
        after=upsert_quote(upsert_quote(source,a),b)
        self.assertEqual(len(source["quotes"]),0)
        self.assertEqual(after["revision"],2)
        self.assertEqual(len(decode_collection(encode_collection(after))["quotes"]),2)
        revised=deepcopy(a);revised["favorite"]=True
        after=upsert_quote(after,revised)
        self.assertEqual(after["revision"],3)
        self.assertTrue(after["quotes"][0]["favorite"])
        result=remove_quote(after,a["id"])
        self.assertEqual(len(result["quotes"]),1)
        self.assertEqual(self.plan,self.before)

    def test_only_exact_scope_is_comparable(self):
        a=self.quote()
        b=self.quote(amount="2650.00")
        self.assertTrue(comparable_quotes(a,b))
        self.assertEqual(quote_difference(a,b),Decimal("-200.00"))
        self.assertIsNone(quote_difference(a,self.quote(currency="CHF")))
        self.assertIsNone(quote_difference(a,self.quote(unit="month")))
        self.assertIsNone(quote_difference(a,self.quote(start_date="2027-10-01")))
        self.assertIsNone(quote_difference(a,self.quote(city_id="strasbourg")))

    def test_housing_replaces_not_adds_allowance(self):
        quote=self.quote(amount="2850.00")
        result=housing_budget_whatif(quote,self.plan,Decimal("20000.00"),
                                     fx_brl_per_unit="6.30")
        self.assertEqual(result["delta_brl"],"-2045.00")
        self.assertIn("Substituição",result["reason"])
        self.assertEqual(self.plan,self.before)

    def test_housing_requires_exact_france_period_and_official_base(self):
        for change in (dict(city_id="strasbourg"),dict(end_date="2027-12-01"),
                       dict(unit="month"),dict(travelers=1),
                       dict(quantity=2),dict(category="flight")):
            with self.subTest(change=change):
                r=housing_budget_whatif(self.quote(**change),self.plan,20000,
                                        fx_brl_per_unit="6.30")
                self.assertIsNone(r["delta_brl"])

    def test_unknown_fx_never_becomes_zero(self):
        self.assertIsNone(housing_budget_whatif(
            self.quote(),self.plan,20000)["delta_brl"])
        self.assertIsNone(housing_budget_whatif(
            self.quote(currency="CHF"),self.plan,20000)["delta_brl"])

    def test_rejects_invalid_amounts_and_untrusted_inputs(self):
        for value in ("NaN","Infinity","-1","0","none","1e999"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.quote(amount=value)
        with self.assertRaises(ValueError):self.quote(source_url="javascript:evil")
        with self.assertRaises(ValueError):self.quote(start_date="2027-12-01")
        with self.assertRaises(ValueError):self.quote(travelers=0)
        with self.assertRaises(ValueError):decode_collection(b'{"schema_version":100}')
        with self.assertRaises(ValueError):decode_collection(b"x"*350001)

    def test_cas_uses_generation_without_mutating_local(self):
        store=Mock()
        coll=upsert_quote(empty_collection(),self.quote())
        before=deepcopy(coll)
        store.save.side_effect=StorageConflict("old")
        with self.assertRaises(StorageConflict):cloud_save(store,coll,123)
        self.assertEqual(store.save.call_args.args[1],123)
        self.assertEqual(coll,before)
        store.load.return_value=(encode_collection(coll),15)
        self.assertEqual(cloud_load(store),(coll,15))

    def test_no_auto_payment_or_reservation_status(self):
        quote=self.quote()
        self.assertNotIn("paid",quote)
        self.assertNotIn("reserved",quote)
        self.assertNotIn("payment",quote)
        self.assertEqual(self.plan,self.before)


class QuoteUIAppTest(unittest.TestCase):
    def test_budget_sections_render_without_cloud_and_preserve_plan(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=110).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        previous=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Orçamento"))).click().run()
        app.segmented_control(key="ux_section").set_value("Detalhamento").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],previous)
        app.segmented_control(key="ux_section").set_value("Resumo financeiro").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],previous)


if __name__=="__main__":
    unittest.main()
