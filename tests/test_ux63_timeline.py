"""Timeline must distinguish grouping from temporal organization."""
import unittest
from ux63_timeline_model import project_timeline,timeline_metrics
from trip_plan_model import new_plan
from attractions_model import load_attractions
from planning_store import add_assignment


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.plan = new_plan()
        self.catalog = load_attractions()
        a=self.catalog["attractions"][0]
        self.destination=a["destination_id"]
        self.plan["packages"]={self.destination:[a["id"]]}
        self.plan["flexible_visits"]=[{
            "destination_id":self.destination, "stage":"França",
            "attractions":[a["id"]],"period":"Ainda não definido"}]

    def test_group_without_date_is_not_organized(self):
        groups={"groups":[{"name":"Fim de semana na Suíça",
                           "destinations":[self.destination],
                           "start_date":None,"period":"Ainda não definido"}]}
        rows=project_timeline(self.plan,self.catalog,groups,stage="França")
        self.assertEqual(timeline_metrics(rows)["grouped"],1)
        self.assertEqual(timeline_metrics(rows)["organized"],0)
        self.assertEqual(timeline_metrics(rows)["dated"],0)

    def test_group_period_has_no_fictitious_date(self):
        groups={"groups":[{"name":"Estadia","destinations":[self.destination],
                           "start_date":None,"period":"Trabalho remoto · fim de semana"}]}
        rows=project_timeline(self.plan,self.catalog,groups,stage="França")
        self.assertEqual(timeline_metrics(rows)["organized"],1)
        self.assertEqual(timeline_metrics(rows)["dated"],0)

    def test_no_cross_stage_visits(self):
        rows=project_timeline(self.plan,self.catalog,stage="Itália")
        self.assertEqual(rows,[])


if __name__=="__main__":
    unittest.main()
