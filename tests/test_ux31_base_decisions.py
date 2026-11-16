"""UX 3.1: evidence-based decisions, equal weights and safe navigation."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from ux_navigation import SECTIONS,route,bootstrap
from base_change_model import destination_impact,impact_summary,comparable_rent_whatif
from base_research_expanded_model import PRESETS,normalized_score,load_research
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class CityBaseDecisionTests(unittest.TestCase):
    def test_15_tabs_across_four_areas(self):
        self.assertEqual(list(SECTIONS),["Minha viagem","Explorar","Meu roteiro","Orçamento"])
        self.assertEqual(sum(map(len,SECTIONS.values())),13)
        self.assertEqual(SECTIONS["Meu roteiro"],(
            "Meu planejamento","Organizar viagem","Melhorar meu roteiro"))
        self.assertEqual(route("Explorar","Comparar")[0],"Comparar cidades")
        self.assertEqual(route("Meu roteiro","Melhorar meu roteiro",
                                suggestion="Guias especializados",
                                guide_view="Transportes e custos")[2],
                         "Transportes e custos")
        self.assertEqual(route("Orçamento","Simulações")[0],"Orçamento")

    def test_offenburg_improves_documented_strasbourg_rail_but_unknown_is_not_lost(self):
        plan=new_plan()
        before=plan.copy()
        rows=destination_impact(plan,"offenburg",["strasbourg","colmar"])
        self.assertEqual(rows[0]["status"],"Melhorou")
        self.assertEqual(rows[0]["official_minutes"],53)
        self.assertEqual(rows[0]["candidate_minutes"],25)
        self.assertEqual(rows[1]["status"],"Não pesquisado")
        self.assertIsNone(rows[1]["candidate_minutes"])
        self.assertEqual(impact_summary(rows)["Não pesquisado"],1)
        self.assertEqual(before,plan)

    def test_missing_rent_cannot_create_false_saving(self):
        result=comparable_rent_whatif(new_plan(),{},False,None,800.,60,6.3)
        self.assertIsNone(result["delta_brl"])
        self.assertFalse(result["known"])

    def test_all_30_are_included_in_weight_coverage_without_fabricated_scores(self):
        self.assertEqual(len(load_research()["cities"]),30)
        for profile in PRESETS:
            result=normalized_score({},profile)
            self.assertIsNone(result["score_0_100"])
            self.assertEqual(result["evidence_weight"],0)


class CityDecisionPageSmokeTests(unittest.TestCase):
    def test_comparison_and_budget_tabs_never_mutate_official_plan(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        plan=at.session_state["advisor_plan"].copy()
        at.radio(key="ux_area").set_value("Explorar").run()
        at.segmented_control(key="ux_mode").set_value("Simulação").run()
        at.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        at.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertEqual(at.session_state["advisor_plan"],plan)
        at.segmented_control(key="ux_compare_mode").set_value("Pesos das 30 cidades").run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        at.radio(key="ux_area").set_value("Orçamento").run()
        for section in ("Resumo financeiro","Simulações","Detalhamento"):
            at.segmented_control(key="ux_section").set_value(section).run()
            self.assertFalse(at.exception,[e.message for e in at.exception])
            self.assertEqual(at.session_state["advisor_plan"]["base_city"],plan["base_city"])


if __name__=="__main__":
    unittest.main()
