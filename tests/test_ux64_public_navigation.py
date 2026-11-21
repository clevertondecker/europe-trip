"""Legacy route identities survive 3-area visual migration."""
import unittest
from ux64_navigation_model import (
    PUBLIC_AREAS, PUBLIC_TASKS, TARGETS,
    public_area, public_task, select_public_area, select_public_task,
)


class PublicNavigationTests(unittest.TestCase):
    def test_three_areas_cover_all_public_tasks(self):
        self.assertEqual(PUBLIC_AREAS,("Explorar","Planejar","Orçamento"))
        self.assertEqual(len(TARGETS),sum(len(v) for v in PUBLIC_TASKS.values()))

    def test_legacy_areas_map_to_plan(self):
        self.assertEqual(public_area("Minha viagem"),"Planejar")
        self.assertEqual(public_area("Meu roteiro"),"Planejar")
        self.assertEqual(public_task("Meu roteiro","Organizar viagem"),"Organizar")

    def test_wishlist_and_discovery_share_one_legacy_tool(self):
        state={}
        select_public_task(state,"Explorar","Minha lista")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Explorar","Passeios"))
        self.assertEqual(state["ux502_view"],"Minha lista")
        select_public_task(state,"Explorar","Descobrir")
        self.assertEqual(state["ux502_view"],"Descobrir lugares")

    def test_plan_area_home_still_routes_to_old_authoritative_screen(self):
        state={}
        select_public_area(state,"Planejar")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Minha viagem","Resumo"))
        select_public_task(state,"Planejar","Meus destinos")
        self.assertEqual((state["ux_area"],state["ux_section"]),
                         ("Meu roteiro","Meu planejamento"))

    def test_unknown_task_fails_closed(self):
        with self.assertRaises(ValueError):
            select_public_task({},"Planejar","Delete all plans")


if __name__=="__main__":
    unittest.main()
