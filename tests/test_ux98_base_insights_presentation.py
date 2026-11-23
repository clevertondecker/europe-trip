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
        source = self.candidate(reasons=[
            "imperdiveis_identificados", "comparacao_condicional_disponivel",
            "menor_minimo_ponderado_no_mesmo_subconjunto"])
        before = deepcopy(source)
        projection = project_base_insights(source)
        self.assertEqual(source, before)
        self.assertEqual(projection["base_id"], "metz")
        self.assertEqual([x["code"] for x in projection["advantages"]],
            ["imperdiveis_identificados", "comparacao_condicional_disponivel",
             "menor_minimo_ponderado_no_mesmo_subconjunto"])
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
        self.assertEqual(result["advantages"][0]["code"], "no_proven_advantage")
        self.assertEqual(len(result["advantages"]), 1)
        self.assertEqual(result["cautions"][-1]["code"], "rec02_limitations")

    def test_unknown_reasons_are_never_turn_into_claims(self):
        result = project_base_insights(self.candidate(reasons=["unknown", "fronteira_documental_do_escopo"]))
        self.assertEqual(result["advantages"][0]["code"], "no_proven_advantage")

if __name__ == "__main__":
    unittest.main()
