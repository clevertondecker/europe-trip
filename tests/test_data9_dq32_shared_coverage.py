"""DATA 9.1: DQ 3.2 / Comparar consistent-source integration tests."""
import unittest
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from dq32_macro_opportunities_model import opportunity_overview
from rail_gap_coverage_audit_model import (
    build_rail_coverage_inventory, research_backlog, audit_summary,
)
from routes7_comparison_projection import decorate_comparison
from trip_plan_model import new_plan

ROOT = Path(__file__).resolve().parents[1]


class SharedRailEvidenceTests(unittest.TestCase):
    def test_dq32_uses_comparison_precedence_for_new_gap(self):
        for base, destination in (
            ("mulhouse","aachen"),("strasbourg","karlsruhe"),
            ("lille","interlaken"),("aachen","amsterdam"),
        ):
            with self.subTest(base=base,destination=destination):
                view=opportunity_overview(base)
                entry=next(r for r in view["destinations"] if
                           r["destination_id"]==destination)
                projected=decorate_comparison({"rows":[{
                    "base_id":base,"destination_id":destination,
                    "evidence_status":"not_researched",
                    "minimum_oneway_min":None,"source_url":None,
                    "divergent_sources":False,
                }]})["cells"][(base,destination)]
                if entry["status"]=="indicative_rail_reference_only":
                    self.assertEqual(entry["indicative_train_oneway_min"],
                                     projected["display_min"])
                    self.assertEqual(entry["indicative_train_label"],
                                     projected["label"])
                    self.assertTrue(entry["indicative_source_url"].startswith("https://"))
                else:
                    # A documented historical service can supersede DATA 9.
                    self.assertEqual(entry["status"],"historical_train_time_only")
                    self.assertIsNotNone(entry["minimum_train_oneway_min"])

    def test_partitions_are_mutually_exclusive_and_cover_the_universe(self):
        for base in ("mulhouse","strasbourg","aachen","karlsruhe","lille"):
            with self.subTest(base=base):
                r=opportunity_overview(base)
                sets=[
                    {x["destination_id"] for x in r[key]}
                    for key in ("local_destinations","historical_rail_destinations",
                                "indicative_rail_destinations","unresearched_destinations")
                ]
                self.assertEqual(sum(map(len,sets)),r["registry_destinations"])
                self.assertEqual(len(set.union(*sets)),r["registry_destinations"])
                self.assertEqual(r["rail_reference_total_count"],
                    r["rail_time_documented_count"]+r["indicative_rail_reference_count"])
                self.assertTrue(all(len(a&b)==0 for i,a in enumerate(sets)
                                    for b in sets[i+1:]))
                self.assertFalse(r["official_plan_modified"])

    def test_missing_destinations_remain_unknown(self):
        r=opportunity_overview("mulhouse")
        self.assertTrue(r["unresearched_destinations"])
        for row in r["unresearched_destinations"]:
            self.assertIsNone(row["indicative_train_oneway_min"])
            self.assertIsNone(row["minimum_train_oneway_min"])
            self.assertFalse(row["reachable_confirmed"])

    def test_audit_30_bases_and_research_backlog(self):
        snapshot=build_rail_coverage_inventory()
        self.assertEqual(snapshot["base_count"],30)
        self.assertEqual(snapshot["total_pairs"],
                         snapshot["base_count"]*snapshot["destination_count"])
        self.assertEqual(snapshot["total_pairs"],sum(snapshot[k] for k in (
            "historical_pairs","indicative_pairs","local_pairs","missing_pairs")))
        self.assertEqual(len(research_backlog(snapshot)),snapshot["missing_pairs"])
        self.assertEqual(len(snapshot["per_destination"]),snapshot["destination_count"])
        self.assertEqual(sum(x["missing_bases"] for x in snapshot["per_destination"]),
                         snapshot["missing_pairs"])
        self.assertEqual(snapshot["local_pairs"],30)
        self.assertFalse(snapshot["fare_and_return_verified_2027"])
        self.assertFalse(snapshot["mutates_tripplan"])
        self.assertEqual(audit_summary(snapshot)["total_pairs"],snapshot["total_pairs"])
        print("DATA9_DQ32_COVERAGE="+str(audit_summary(snapshot)))
        print("DATA9_DQ32_TOP_GAPS="+str(snapshot["per_destination"][:20]))


class SharedRailAppTests(unittest.TestCase):
    def test_audit_cli_executes_and_writes_backlog(self):
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.run(
                [sys.executable, str(ROOT/"scripts/audit_data9_rail_coverage.py"),
                 "--output",temp],cwd=ROOT,capture_output=True,text=True,
                timeout=120,check=True)
            summary=json.loads(result.stdout.strip())
            self.assertEqual(summary["base_count"],30)
            self.assertEqual(summary["total_pairs"],1380)
            output=Path(temp)
            inventory=json.loads((output/"inventory.json").read_text(encoding="utf-8"))
            backlog=json.loads((output/"backlog.json").read_text(encoding="utf-8"))
            self.assertEqual(len(backlog),summary["missing_pairs"])
            components=json.loads((output/"component_backlog.json").read_text(encoding="utf-8"))
            component_summary=json.loads((output/"component_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(len(components),summary["total_pairs"])
            self.assertEqual(component_summary["missing_components"]["independent_return_service"],1350)
            self.assertEqual(len(inventory["per_base"]),30)
            self.assertEqual(len(inventory["per_destination"]),46)
            self.assertIn("Lacunas ferroviárias",(output/"summary.md").read_text(encoding="utf-8"))

    def test_dq32_indicative_group_and_canonical_wishlist_intact(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        before=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.selectbox(key="attractions_scenario_base").set_value("mulhouse").run()
        app.selectbox(key="ux_dq32_opportunity_group").set_value(
            "Referências indicativas de ida").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],before)
        table=next(df.value for df in app.dataframe if
                   "Passeio confirmado" in df.value.columns)
        self.assertTrue((table["Transporte"].str.contains(
            "mínimo publicado|mínimo indicativo|amostra datada|referência secundária")).all())
        self.assertTrue((table["Passeio confirmado"]=="Não").all())
        self.assertTrue(any("Destinos com tempo ou referência" in m.label
                            for m in app.metric))
        app.selectbox(key="ux_dq32_opportunity_group").set_value(
            "Outros destinos, transporte não pesquisado").run()
        table=next(df.value for df in app.dataframe if
                   "Passeio confirmado" in df.value.columns)
        self.assertTrue((table["Transporte"]=="Transporte não pesquisado").all())
        self.assertEqual(app.session_state["advisor_plan"],before)

    def test_strasbourg_preserves_historical_and_exposes_indicative(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        before=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.selectbox(key="attractions_scenario_base").set_value("strasbourg").run()
        app.selectbox(key="ux_dq32_opportunity_group").set_value(
            "Referências indicativas de ida").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        table=next(df.value for df in app.dataframe if
                   "Passeio confirmado" in df.value.columns)
        self.assertTrue(any("Karlsruhe" in x for x in table["Destino"]))
        self.assertEqual(app.session_state["advisor_plan"],before)


if __name__=="__main__":
    unittest.main()
