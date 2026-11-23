"""UX98: insights must reflect REC02 evidence, not an invented ranking."""
import unittest
from copy import deepcopy
from ux98_base_insights_presentation import project_base_insights


class BaseInsightsTests(unittest.TestCase):
    def candidate(self, **changes):
        value = {"base_id": "metz", "reasons": [],
                 "missing_destination_ids": [], "local_destination_ids": []}
        value.update(changes)
        return value

    def test_complete_scope_pros_are_source_coded_and_read_only(self):
        source = self.candidate(must_visit={"known":["paris"],"local":[],"missing":[]},reasons=[
            "imperdiveis_identificados", "comparacao_condicional_disponivel",
            "menor_minimo_ponderado_no_mesmo_subconjunto"])
        before = deepcopy(source)
        projection = project_base_insights(source)
        self.assertEqual(source, before)
        self.assertEqual(projection["base_id"], "metz")
        self.assertEqual([x["code"] for x in projection["documented"]],
            ["imperdiveis_identificados", "comparacao_condicional_disponivel"])
        self.assertEqual([x["code"] for x in projection["advantages"]],
            ["menor_minimo_ponderado_no_mesmo_subconjunto"])
        self.assertNotIn("hospedagem", str(projection).lower())
        self.assertNotIn("melhor cidade", str(projection).lower())

    def test_partial_references_and_local_cautions(self):
        result = project_base_insights(self.candidate(
            reasons=["imperdiveis_com_evidencia_pendente",
                     "destinos_com_tempo_pendente"],
            missing_destination_ids=["basel"], local_destination_ids=["colmar"]))
        codes = [x["code"] for x in result["cautions"]]
        self.assertIn("imperdiveis_com_evidencia_pendente", codes)
        self.assertEqual(codes.count("destinos_com_tempo_pendente"), 1)
        self.assertIn("local_destination_ids", codes)
        self.assertIn("rec02_limitations", codes)

    def test_no_evidence_is_neutral_not_fabricated(self):
        result = project_base_insights(self.candidate())
        self.assertEqual(result["advantages"], [])
        self.assertEqual(result["neutral"][0]["code"], "no_proven_advantage")
        self.assertEqual(result["cautions"][-1]["code"], "rec02_limitations")

    def test_no_must_visit_scope_does_not_claim_must_visit_coverage(self):
        result=project_base_insights(self.candidate(
            reasons=["imperdiveis_identificados"],
            must_visit={"known":[],"local":[],"missing":[]}))
        self.assertFalse(any(item["code"]=="imperdiveis_identificados"
                             for item in result["advantages"]))
        self.assertTrue(result["neutral"])
        result_with_must=project_base_insights(self.candidate(
            reasons=["imperdiveis_identificados"],
            must_visit={"known":["paris"],"local":[],"missing":[]}))
        self.assertIn("imperdiveis_identificados",
                      [x["code"] for x in result_with_must["documented"]])
        self.assertNotIn("imperdiveis_identificados",
                         [x["code"] for x in result_with_must["advantages"]])

    def test_research_coverage_is_not_fabricated_as_comparative_benefit(self):
        source=self.candidate(
            must_visit={"known":["paris"],"local":[],"missing":[]},
            reasons=["imperdiveis_identificados",
                     "comparacao_condicional_disponivel"])
        result=project_base_insights(source)
        self.assertEqual(result["advantages"],[])
        self.assertEqual([item["code"] for item in result["documented"]],
                         ["imperdiveis_identificados",
                          "comparacao_condicional_disponivel"])
        self.assertFalse(result["neutral"])
        self.assertEqual(result["cautions"][-1]["code"],"rec02_limitations")

    def test_unknown_reasons_are_never_turn_into_claims(self):
        result = project_base_insights(self.candidate(reasons=["unknown", "fronteira_documental_do_escopo"]))
        self.assertEqual(result["advantages"], [])
        self.assertEqual(result["neutral"][0]["code"], "no_proven_advantage")

if __name__ == "__main__":
    unittest.main()
