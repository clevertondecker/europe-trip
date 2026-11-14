import unittest
from datetime import date
from calendar_model import calendar_plan
class CalendarTests(unittest.TestCase):
    def test_trip_after_wedding(self):
        with self.assertRaises(ValueError):
            calendar_plan(date(2027,9,4),70,10,25,4)
    def test_italy_first_and_france_later(self):
        days=calendar_plan(date(2027,9,9),70,10,25,4)
        self.assertEqual(len(days),70)
        self.assertEqual(days[0]["stage"],"Itália")
        self.assertEqual(days[10]["activity"],"Instalação")
        self.assertEqual(days[14]["activity"],"Férias · excursões possíveis")
        self.assertTrue(all(not r["confirmed"] for r in days))
    def test_remote_weekdays_weekend_pois(self):
        days=calendar_plan(date(2027,9,9),70,10,25,4)
        for day in days[25:]:
            if date.fromisoformat(day["date"]).weekday()<5:
                self.assertIn("Trabalho remoto",day["activity"])
            else:
                self.assertIn("Fim de semana",day["activity"])
    def test_bad_vacation_assumptions(self):
        with self.assertRaises(ValueError):
            calendar_plan(date(2027,9,9),70,10,8,3)
if __name__=="__main__": unittest.main()
