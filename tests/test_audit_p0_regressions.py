"""Regression cases for independently confirmed P0 audit findings."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from datetime import date

from money_units import known_eur_equivalent,known_brl
from destination_recommender import recommend_destinations
from attractions_model import load_attractions,load_base_routes
from trip_plan_model import new_plan,apply_proposal
from planning_store import change_plan,add_assignment,remove_package
from recommended_itineraries import approve_profile_scenario
from unified_budget import scenario_total,resolve_french_budget
from calendar_model import calendar_plan
from public_plan_safety import ensure_public_plan_is_minimal
from catalog_plan_validation import validate_catalog_packages


class MoneyRegression(unittest.TestCase):
    def test_mixed_curreny_never_uses_plain_numeric_sum(self):
        self.assertAlmostEqual(known_eur_equivalent({"EUR":10,"CHF":10},6,12),30)
        self.assertEqual(known_brl({"EUR":10,"CHF":10},6,12),180)
        with self.assertRaises(ValueError):
            known_eur_equivalent({"EUR":10,"CHF":5},0,6)
        with self.assertRaises(ValueError):
            known_eur_equivalent({"EUR":-1,"CHF":5},6,6)

    def test_destination_score_uses_fx_normalization(self):
        p=new_plan()
        cat=load_attractions()
        routes=load_base_routes()
        cost={"known_by_currency":{"EUR":0,"CHF":10},"complete":True,
              "missing":[],"conditional":[]}
        with patch("destination_recommender.package_cost",return_value=cost):
            a=recommend_destinations(p,cat,routes,eur_fx=6,chf_fx=6)
            b=recommend_destinations(p,cat,routes,eur_fx=6,chf_fx=12)
        index_a={r["destination_id"]:r for r in a}
        index_b={r["destination_id"]:r for r in b}
        self.assertTrue(set(index_a)&set(index_b))
        key=next(iter(set(index_a)&set(index_b)))
        self.assertAlmostEqual(index_a[key]["cost_score_eur_equivalent"],10)
        self.assertAlmostEqual(index_b[key]["cost_score_eur_equivalent"],20)
        self.assertGreater(index_a[key]["score"],index_b[key]["score"])
        self.assertEqual(index_a[key]["known_costs"],cost["known_by_currency"])

    def test_budget_negative_delta_is_valid_only_for_existing_expense(self):
        base={"id":"70k","days":70,"cap_brl":70000,
              "reported_total_brl":69683,"emergency_reserve_brl":5000,
              "components":[
                  {"name":"França · aluguel mobiliado","amount":10000},
                  {"name":"França · supermercado","amount":8000},
                  {"name":"França · bares e restaurantes","amount":4500},
                  {"name":"França · transporte urbano","amount":1000},
                  {"name":"França · passeios e viagens","amount":3000}]}
        french=resolve_french_budget(base,True)
        kwargs=dict(french_days=60,outings_weekly=2,
                    outing_couple_eur=60,fx_brl_per_eur=6)
        prior=scenario_total(base,french,**kwargs)
        cheaper=scenario_total(base,french,**kwargs,flight_delta_brl=-500,
                               excursions_delta_brl=-200,local_transport_delta_brl=-100,
                               rent_delta_brl=-300)
        self.assertAlmostEqual(prior["total"]-cheaper["total"],1100)
        self.assertEqual(cheaper["new_components"]["excursions"],2800)
        with self.assertRaises(ValueError):
            scenario_total(base,french,**kwargs,excursions_delta_brl=-5000)
        with self.assertRaises(ValueError):
            scenario_total(base,french,**kwargs,flight_delta_brl=-100000)
        with self.assertRaises(ValueError):
            scenario_total(base,french,**kwargs,flight_delta_brl="100")
        with self.assertRaises(ValueError):
            scenario_total(base,french,**kwargs,flight_delta_brl=float("nan"))


class CalendarIntegrity(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan()
        self.plan["packages"]={"colmar":["sample_attraction"]}
        days=calendar_plan(date.fromisoformat(self.plan["departure_date"]),
                           self.plan["total_days"],self.plan["italy_days"],
                           self.plan["vacation_days"],self.plan["setup_days"])
        self.allowed=next(x["date"] for x in days
                          if x["stage"]=="França" and "Fim de semana" in x["activity"])
        self.workday=next(x["date"] for x in days
                          if "Trabalho remoto" in x["activity"])
        self.setup=next(x["date"] for x in days if x["activity"]=="Instalação")
        self.italy=next(x["date"] for x in days if x["stage"]=="Itália")

    def test_workday_italy_setup_and_outside_trip_rejected(self):
        for day in (self.workday,self.italy,self.setup,"2028-01-01"):
            with self.subTest(day=day),self.assertRaises(ValueError):
                add_assignment(self.plan,day,"colmar")
        ok=add_assignment(self.plan,self.allowed,"colmar")
        self.assertEqual(ok["assignments"],{self.allowed:"colmar"})
        self.assertEqual(ok["revision"],self.plan["revision"]+1)
        removed=remove_package(ok,"colmar")
        self.assertEqual(removed["assignments"],{})

    def test_no_destination_missing_and_proposal_cannot_bypass_date_rules(self):
        with self.assertRaises(ValueError):
            change_plan(self.plan,{"assignments":{self.allowed:"ghost"}})
        prop={"plan_id":self.plan["plan_id"],"base_city":self.plan["base_city"],
              "base_revision":self.plan["revision"],
              "profile":self.plan["profile"],
              "proposal_packages":deepcopy(self.plan["packages"]),
              "preview_assignments":{self.workday:"colmar"}}
        with self.assertRaises(ValueError):
            approve_profile_scenario(self.plan,prop,approved=True)
        optimizer={"base_revision":self.plan["revision"],"base_city":self.plan["base_city"],
                   "proposal_id":"test","assignments":{self.setup:"colmar"}}
        with self.assertRaises(ValueError):
            apply_proposal(self.plan,optimizer,approved=True)

    def test_unmodified_old_dates_can_be_kept_without_migration(self):
        old=deepcopy(self.plan)
        old["assignments"]={self.workday:"colmar"}
        # The historical approved entry remains loadable; no new invalid date.
        new=change_plan(old,{"assignments":{
            self.workday:"colmar",self.allowed:"colmar"}})
        self.assertEqual(len(new["assignments"]),2)


class CatalogIntegrity(unittest.TestCase):
    def test_catalog_rejects_misplaced_attraction_ids(self):
        catalog=load_attractions()
        plan=new_plan()
        colmar=next(a["id"] for a in catalog["attractions"]
                    if a["destination_id"]=="colmar")
        basel=next(a["id"] for a in catalog["attractions"]
                   if a["destination_id"]=="basel")
        plan["packages"]={"colmar":[colmar]}
        validate_catalog_packages(plan,catalog)
        plan["packages"]={"colmar":[basel]}
        with self.assertRaises(ValueError):
            validate_catalog_packages(plan,catalog)


class PrivacyGuard(unittest.TestCase):
    def test_public_plan_rejects_unexpected_data_or_email(self):
        plan=new_plan()
        ensure_public_plan_is_minimal(plan)
        extra={**plan,"personal_notes":"my secret"}
        with self.assertRaises(ValueError):
            ensure_public_plan_is_minimal(extra)
        with_email=deepcopy(plan)
        with_email["accepted_recommendations"]=["contact personal@example.com"]
        with self.assertRaises(ValueError):
            ensure_public_plan_is_minimal(with_email)


if __name__=="__main__":
    unittest.main()
