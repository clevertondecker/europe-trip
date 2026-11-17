import copy
import unittest
from datetime import date
from attractions_model import (
    load_attractions, load_base_routes, route_for, places_for_base,
    package_cost, attraction_cost, approximate_feasibility, schedule_visit,
    excursions_overage_brl, validate_attractions, validate_routes)
from calendar_model import calendar_plan

class AdaptiveAttractionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.attractions=load_attractions()
        cls.routes=load_base_routes()

    def test_four_base_coverage_and_attraction_count(self):
        self.assertEqual(len(self.attractions["destinations"]),14)
        self.assertGreaterEqual(len(self.attractions["attractions"]),50)
        self.assertEqual(len(self.routes["routes"]),56)
        for base in ["mulhouse","strasbourg","metz","nancy"]:
            self.assertGreaterEqual(sum(a["destination_id"]==base
                for a in self.attractions["attractions"]),5)
            self.assertEqual(len(places_for_base(self.attractions,self.routes,base)),14)

    def test_colmar_depends_on_selected_base(self):
        mul=route_for(self.routes,"mulhouse","colmar")
        stras=route_for(self.routes,"strasbourg","colmar")
        self.assertEqual((mul["train_minutes_one_way"],mul["fare_eur_person_oneway"]),(18,5.4))
        self.assertEqual((stras["train_minutes_one_way"],stras["fare_eur_person_oneway"]),(32,7.9))
        chosen=["colmar_venise","colmar_tanners"]
        first=package_cost(self.attractions,self.routes,"mulhouse",chosen)
        second=package_cost(self.attractions,self.routes,"strasbourg",chosen)
        self.assertAlmostEqual(first["known_by_currency"]["EUR"],21.6)
        self.assertAlmostEqual(second["known_by_currency"]["EUR"],31.6)
        self.assertTrue(first["conditional"])

    def test_metz_nancy_ter(self):
        for left,right in [("metz","nancy"),("nancy","metz")]:
            self.assertEqual(route_for(self.routes,left,right)["train_minutes_one_way"],38)
            self.assertEqual(route_for(self.routes,left,right)["fare_eur_person_oneway"],7)

    def test_unknown_route_never_guessed_or_zero(self):
        r=route_for(self.routes,"nancy","interlaken")
        self.assertIsNone(r["train_minutes_one_way"])
        self.assertIsNone(r["fare_eur_person_oneway"])
        self.assertIn("pernoite",approximate_feasibility(
            next(x for x in self.attractions["destinations"] if x["id"]=="interlaken"),r).lower())

    def test_paid_site_in_eur_and_couple(self):
        r=package_cost(self.attractions,self.routes,"mulhouse",["mulhouse_train","mulhouse_reunion"])
        self.assertEqual(r["known_by_currency"]["EUR"],32)
        self.assertEqual(r["by_destination"]["mulhouse"],["mulhouse_train","mulhouse_reunion"])
        self.assertTrue(any("Transporte urbano" in m for m in r["missing"]))

    def test_chf_never_combined_with_eur(self):
        r=package_cost(self.attractions,self.routes,"mulhouse",["oesch_cable","colmar_venise"])
        self.assertEqual(r["known_by_currency"],{"EUR":21.6,"CHF":72})
        self.assertTrue(any("Transporte entre" in m for m in r["missing"]))

    def test_does_not_double_count_same_destination_transport(self):
        r=package_cost(self.attractions,self.routes,"mulhouse",
                       ["colmar_venise","colmar_tanners","colmar_pfister"])
        self.assertEqual(r["known_by_currency"]["EUR"],21.6)
        self.assertEqual(len([x for x in r["breakdown"] if "Transporte" in x["item"]]),1)

    def test_unknown_ticket_is_not_free(self):
        t=next(a["ticket"] for a in self.attractions["attractions"]
               if a["id"]=="metz_pompidou")
        self.assertIsNone(attraction_cost(t))
        free_public=next(a["ticket"] for a in self.attractions["attractions"]
               if a["id"]=="metz_lake")
        self.assertEqual(attraction_cost(free_public),0)
        self.assertEqual(free_public["status"],"not_applicable")

    def test_duplicate_selected_raises(self):
        with self.assertRaises(ValueError):
            package_cost(self.attractions,self.routes,"mulhouse",
                         ["colmar_venise","colmar_venise"])

    def test_route_missing_scope_protected(self):
        changed=copy.deepcopy(self.routes)
        row=route_for(changed,"mulhouse","colmar")
        row["minutes_scope"]="door_to_door"
        with self.assertRaises(ValueError): validate_routes(changed)

    def test_attraction_requires_source(self):
        changed=copy.deepcopy(self.attractions)
        changed["attractions"][0]["source_urls"]=[]
        with self.assertRaises(ValueError): validate_attractions(changed)

    def test_assign_only_eligible_calendar_day_and_no_duplicate(self):
        days=calendar_plan(date(2027,9,9),70,10,25,4)
        good=next(x for x in days if x["activity"]=="Férias · excursões possíveis")
        assignments=schedule_visit(days,{},good["date"],"colmar")
        self.assertEqual(assignments[good["date"]],"colmar")
        with self.assertRaises(ValueError):
            schedule_visit(days,assignments,good["date"],"basel")
        work=next(x for x in days if "Trabalho remoto" in x["activity"])
        with self.assertRaises(ValueError):
            schedule_visit(days,{},work["date"],"basel",full_day=True)
        with self.assertRaises(ValueError):
            schedule_visit(days,{},days[0]["date"],"colmar")

    def test_budget_only_counts_known_overage_above_allowance(self):
        self.assertEqual(excursions_overage_brl(60,0,6.3,7,500),0)
        self.assertEqual(excursions_overage_brl(200,30,6.3,7,500),970)
        with self.assertRaises(ValueError): excursions_overage_brl(-1,0,6,7,100)

if __name__=="__main__":
    unittest.main()
