import unittest
from pathlib import Path
from drive_sync import parse_decisions, parse_tasks, parse_workbook, model_budget, model_timeline, chosen_city, update_map_places

class SyncV03Tests(unittest.TestCase):
    def test_decisions_require_explicit(self):
        self.assertIsNone(chosen_city(parse_decisions('D-001 | Vigente | Casamento\nD-004 | Não decidida | Mulhouse ou Strasbourg')))
        d=parse_decisions('D-001 | Vigente | Casamento\nD-004 | Vigente | Cidade-base francesa: Strasbourg')
        self.assertEqual(chosen_city(d),'strasbourg')
        places=[{'id':'strasbourg','status':'candidata','description':'Teste','source':'knowledge'}]
        self.assertEqual(update_map_places(places,d)[0]['status'],'roteiro_proposto')
        self.assertEqual(places[0]['status'],'candidata')

    def test_tasks_validate(self):
        with self.assertRaises(ValueError): parse_tasks('P0 — TESTE\nSem marcação')
        self.assertEqual(len(parse_tasks('P0 — TESTE\n[ ] Testar\nREGISTRO DE PROGRESSO\n[ ] Não incluir')),1)

    def test_actual_finance_model(self):
        # Source workbook is used only in the developer environment; no network is required.
        source=Path('/mnt/data/Europa_2027_COMPLETO_ORGANIZADO.xlsm')
        if not source.exists():self.skipTest('Original workbook not mounted')
        b,a,i=parse_workbook(source.read_bytes())
        x=model_budget(a,b)
        self.assertAlmostEqual(x['budget_scenarios'][0]['reported_total_brl'],59974.50969,places=2)
        self.assertAlmostEqual(x['budget_scenarios'][1]['reported_total_brl'],69683.17526,places=2)
        self.assertEqual(x['metadata']['wedding_date'],'2027-09-04')
        self.assertEqual(x['metadata']['departure_candidate'],'2027-09-10')
        self.assertEqual(len(model_timeline(i)),8)

    def test_detect_modified_budget_without_cached_recalc(self):
        source=Path('/mnt/data/Europa_2027_COMPLETO_ORGANIZADO.xlsm')
        if not source.exists():self.skipTest('Original workbook not mounted')
        b,a,_=parse_workbook(source.read_bytes())
        a['B18']=900.0
        x=model_budget(a,b)
        self.assertGreater(x['budget_scenarios'][0]['reported_total_brl'],59975)
        self.assertTrue(any('cache' in issue.lower() for issue in x['issues']))

if __name__=='__main__':unittest.main()