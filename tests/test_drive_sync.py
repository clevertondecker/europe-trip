import unittest
from drive_sync import parse_decisions, parse_tasks

class SyncTests(unittest.TestCase):
    def test_decisions(self):
        result = parse_decisions("D-001 | Vigente | Casamento\nD-002 | Não decidida | Cidade")
        self.assertEqual(result[0]["id"], "D-001")
        self.assertEqual(result[1]["status"], "Não decidida")

    def test_tasks(self):
        result = parse_tasks("P0 — TESTE\n[ ] Verificar voos\nP1 — TESTE\n[x] Apartamento\nREGISTRO DE PROGRESSO\n[ ] Ignorar")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["status"], "concluído")

if __name__ == "__main__":
    unittest.main()
