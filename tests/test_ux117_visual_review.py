"""UX117: accessible, read-only visual projection and safe aggregate semantics."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from base_change_model import SIMILARITY_THRESHOLD_MINUTES,destination_impact
from ux117_review_visual import comparable_subtotals,impact_html,subtotals_html,housing_html,city_identity_html
from city_decision_ui import contextual_impact_projection
from city_decision_model import compare_city_decisions
from trip_plan_model import new_plan
from data_model import load_data

def row(before,after,basis,status,delta,**extra):
    return dict(before=before,after=after,comparison_basis=basis,status=status,
                delta_minutes=delta,name="Destino",priority="must_visit",
                priority_label="Imperdível",official_category="historical",
                candidate_category="historical",official_confidence="medium",
                candidate_confidence="medium",**extra)

class VisualReviewTests(unittest.TestCase):
    def test_subtotals_are_separate_and_exclude_unpaired(self):
        rows=[row(137,20,"fastest_reference","Melhorou",-117),
              row(83,162,"fastest_reference","Piorou",79),
              row(100,100,"representative","Semelhante",0),
              row(80,90,"representative","Semelhante",10),
              row(104,69,"indicative_only","Referência insuficiente",None),
              row(None,20,"local","Local",None),
              row(None,134,"unavailable","Não pesquisado",None)]
        totals=comparable_subtotals({"rows":rows})
        self.assertEqual(totals["fastest_reference"],dict(before=220,after=182,count=2,delta=-38))
        self.assertEqual(totals["representative"],dict(before=180,after=190,count=2,delta=10))
        self.assertEqual(comparable_subtotals({"rows":rows[4:]}),{})
        self.assertEqual(subtotals_html({"rows":[]}),"")
    def test_real_projection_and_escape(self):
        plan=new_plan()
        plan["base_city"]="metz"
        original=deepcopy(plan)
        c=compare_city_decisions(plan,["mulhouse"],["basel","colmar","paris","interlaken","obernai","strasbourg"],{},load_data(),False,60,6.3)
        view=contextual_impact_projection(c,{"obernai":"must_visit"})
        self.assertEqual(len(view["rows"]),6)
        self.assertEqual(sum(x["count"] for x in comparable_subtotals(view).values()),view["comparable"])
        self.assertIn("Atenção: imperdível",impact_html(view))
        self.assertIn('scope="col"',impact_html(view))
        self.assertIn('role="progressbar"',impact_html(view))
        self.assertIn("Não cotado",housing_html(c,view))
        view["rows"][0]["name"]="<script>alert(1)</script>"
        self.assertNotIn("<script>",impact_html(view))
        self.assertIn("&lt;script&gt;",impact_html(view))
        self.assertNotIn("<button",impact_html(view))
        self.assertNotIn("<img",city_identity_html({"name":"<img>","country":"França"},"Base atual"))
        self.assertEqual(plan,original)

    def test_housing_hypotheses_use_existing_finance_result(self):
        plan=new_plan()
        plan["base_city"]="metz"
        c=compare_city_decisions(plan,["mulhouse"],["paris"],
                                 {"metz":1000,"mulhouse":900},load_data(),False,60,6.3)
        view=contextual_impact_projection(c)
        self.assertTrue(view["housing_known"])
        self.assertLess(view["housing_delta_brl"],0)
        html=housing_html(c,view)
        self.assertIn("€ 1.000/mês",html)
        self.assertIn("€ 900/mês",html)
        self.assertIn("Somente moradia",html)
        self.assertNotIn("Não cotado",html)

    def test_zero_comparable_and_local_remain_distinct(self):
        rows=[row(None,45,"local","Local",None)]
        rows[0]["official_category"]="local"
        groups={k:[] for k in ("Melhorou","Piorou","Semelhante","Local","Não pesquisado","Referência insuficiente")}
        groups["Local"]=rows
        view=dict(rows=rows,groups=groups,comparable=0,total=1,
                  official_name="Metz",candidate_name="Nancy")
        self.assertIn("Local · acesso a verificar",impact_html(view))
        self.assertIn("0 de 1 destinos comparáveis",impact_html(view))
        self.assertEqual(subtotals_html(view),"")

    def test_domain_threshold_and_explanation(self):
        plan=new_plan()
        plan["base_city"]="metz"
        route=dict(minutes=100,fare=None,source=None,fare_condition=None,basis=None,
                   note="",category="historical",confidence="medium",provenance="sample",
                   representative_minutes=None)
        limit=SIMILARITY_THRESHOLD_MINUTES
        for delta,status in ((-limit,"Melhorou"),(-limit+1,"Semelhante"),
                             (limit-1,"Semelhante"),(limit,"Piorou"),(0,"Semelhante")):
            with self.subTest(delta=delta):
                with patch("base_change_model.known_route",side_effect=[route,dict(route,minutes=100+delta)]):
                    impact=destination_impact(plan,"nancy",["paris"])[0]
                self.assertEqual(impact["status"],status)

    def test_priority_notices_are_conditional(self):
        groups={k:[] for k in ("Melhorou","Piorou","Semelhante","Local","Não pesquisado","Referência insuficiente")}
        rows=[row(100,120,"fastest_reference","Piorou",20),
              row(None,69,"unavailable","Não pesquisado",None)]
        for item in rows:groups[item["status"]].append(item)
        view=dict(rows=rows,groups=groups,comparable=1,total=2,
                  official_name="Metz",candidate_name="Nancy")
        html=impact_html(view)
        self.assertIn(f"inferiores a {SIMILARITY_THRESHOLD_MINUTES} minutos",html)
        self.assertIn("1 destino imperdível terá uma ida mais longa.",html)
        self.assertIn("1 destino imperdível ainda precisa de validação.",html)
        for item in rows:item["priority"]="maybe"
        self.assertNotIn("ux117-priority-note",impact_html(view))

    def test_subtotal_prose_for_positive_negative_and_zero(self):
        for delta,expected in ((20,"20 min a mais"),(-20,"20 min a menos"),
                               (0,"Mesmo tempo acumulado")):
            status="Piorou" if delta>0 else "Melhorou" if delta<0 else "Semelhante"
            view=dict(rows=[row(100,100+delta,"fastest_reference",status,delta)],
                      total=2,official_name="Metz",candidate_name="Nancy")
            html=subtotals_html(view)
            self.assertIn(expected,html)
            self.assertIn("1/2 destinos",html)

    def test_financial_fraction_and_zero_preserved(self):
        comparison=dict(official_base="metz",rents_eur_month={"metz":1000.25,"nancy":999.75},
                        french_days=60,eur_fx=6.3)
        view=dict(candidate="nancy",official_name="Metz",candidate_name="Nancy",
                  housing_known=True,housing_delta_brl=-6.3)
        html=housing_html(comparison,view)
        self.assertIn("€ 1.000,25/mês",html)
        self.assertIn("€ 999,75/mês",html)
        self.assertIn("−R$ 6,30",html)
        self.assertIn("R$ 6,30/€",html)
        view["housing_delta_brl"]=0
        self.assertIn("moradia: R$ 0",housing_html(comparison,view))
        view["housing_delta_brl"]=6.3
        self.assertIn("+R$ 6,30",housing_html(comparison,view))
