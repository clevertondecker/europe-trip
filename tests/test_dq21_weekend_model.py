import unittest
from copy import deepcopy
from dq21_weekend_model import load_weekend_details,paired_day_trip,weekend_research_matrix,combined_belgian_weekend,weekend_hypotheses

class DQ21Weekends(unittest.TestCase):
    def test_fixed_15_and_nonverified_returns(self):
        rows=weekend_research_matrix()
        self.assertEqual(len(rows),15)
        self.assertTrue(all(r["same_weekend_full_itinerary_verified"] is False for r in rows))
        self.assertTrue(all(r["bookable_2027"] is False for r in rows))
        self.assertIsNone(rows[0]["overnight_required"])

    def test_dated_saturday_outbound_not_return(self):
        x=paired_day_trip("strasbourg","luxembourg_city","2026-11-21")
        self.assertEqual(x["status"],"falta_retorno")
        y=paired_day_trip("luxembourg_city","strasbourg","2026-11-17")
        self.assertEqual(y["status"],"dia_util_nao_comprova_fim_de_semana")

    def test_genuine_synthetic_timing_works_but_not_2027(self):
        j=load_weekend_details()
        row={"origin_id":"strasbourg","destination_id":"luxembourg_city",
             "travel_date":"2026-11-21","depart_local":"07:00","arrive_local":"09:00",
             "changes":1,"source_url":"https://example.org/train","source_type":"test"}
        back={**row,"origin_id":"luxembourg_city","destination_id":"strasbourg",
              "depart_local":"19:00","arrive_local":"21:00"}
        j["dated_services"]=[row,back]
        self.assertEqual(paired_day_trip("strasbourg","luxembourg_city","2026-11-21",
                        evidence=j)["status"],"ultima_milha_pendente")
        v=paired_day_trip("strasbourg","luxembourg_city","2026-11-21",
                          evidence=j,last_mile_minutes_each_way=30)
        self.assertEqual(v["status"],"bate_volta_historico_amostrado")
        self.assertEqual(v["visit_hours"],9)
        self.assertFalse(v["confirmed_2027"])

    def test_bruges_leg_not_whole_base_journey(self):
        x=combined_belgian_weekend()
        self.assertTrue(x["weekend_segment_pattern"])
        self.assertFalse(x["2027_confirmed"])
        self.assertTrue(all(v is False for v in x["from_each_base_verified"].values()))

    def test_hypotheses_rest_days(self):
        for n in (8,9):
            rows=weekend_hypotheses(n)
            self.assertEqual(len(rows),n)
            self.assertTrue(any(w["status"]=="descanso" for w in rows))
            self.assertTrue(all(w["travel_total_minutes"] is None for w in rows))

if __name__=="__main__": unittest.main()
