"""UX: visual hierarchy is derived from canonical planning state, not new storage."""
import unittest

from ux_planning_journey_presentation import (
    project_visual_state, header_html, metric_html, next_html, step_html,
)


def view(*, wished=6, planned=0, organized=0, eligible=5, action="build", saved=False):
    return {
        "counts": {"wished": wished, "planned": planned, "organized": organized},
        "eligible_count": eligible, "next": action, "private_saved": saved,
    }


class PlanningVisualProjectionTests(unittest.TestCase):
    def test_next_action_and_metrics_use_real_counts(self):
        presentation = project_visual_state(view(), "Rascunho nesta sessão")
        self.assertEqual(presentation["current_step"], "build")
        self.assertEqual(presentation["metrics"][0]["value"], 6)
        self.assertEqual(presentation["metrics"][1]["value"], 0)
        self.assertIn("5 destino(s)", presentation["headline"])
        self.assertTrue(presentation["metrics"][0]["highlight"])
        self.assertEqual([x["id"] for x in presentation["steps"]],
                         ["choose", "build", "organize", "review"])
        self.assertEqual([x["active"] for x in presentation["steps"]],
                         [False, True, False, False])
        self.assertFalse(presentation["steps"][1]["disabled"])

    def test_exploratory_only_disables_build_without_blocking_review(self):
        presentation = project_visual_state(
            view(wished=2, eligible=0, action="exploratory"), "Rascunho nesta sessão")
        self.assertEqual(presentation["current_step"], "choose")
        self.assertTrue(presentation["steps"][1]["disabled"])
        self.assertFalse(presentation["steps"][3]["disabled"])
        self.assertIn("pesquisa", presentation["headline"])

    def test_organizing_is_optional_and_unsaved_draft_is_not_claimed_saved(self):
        presentation = project_visual_state(
            view(wished=0, planned=2, organized=0, eligible=0, action="review"),
            "Alterações apenas nesta sessão")
        self.assertEqual(presentation["steps"][3]["detail"], "Rascunho pode ser salvo")
        self.assertNotEqual(presentation["steps"][3]["status"], "Salvo")
        self.assertIn("não confirma", presentation["explanation"])
        self.assertIn("opcional", presentation["steps"][2]["detail"])

    def test_saved_state_only_uses_confirmed_private_label(self):
        raw = view(planned=2, organized=1, eligible=0, action="review", saved=True)
        saved = project_visual_state(raw, "Salvo em espaço privado")
        self.assertEqual(saved["steps"][3]["status"], "Etapa em foco")
        self.assertEqual(saved["steps"][3]["detail"], "Salvo em espaço privado")
        not_saved = project_visual_state(raw, "Alterações apenas nesta sessão")
        self.assertEqual(not_saved["steps"][3]["detail"], "Rascunho pode ser salvo")

    def test_explicit_focus_and_markup_escape(self):
        p = project_visual_state(view(planned=1, eligible=0), "Rascunho nesta sessão",
                                 focused="organize")
        self.assertEqual(p["current_step"], "organize")
        self.assertIn("opcional", p["explanation"])
        h = header_html("<script>alert(1)</script>", "Aguardando <salvar>")
        self.assertNotIn("<script>", h)
        self.assertIn("&lt;script&gt;", h)
        self.assertIn("&lt;salvar&gt;", h)
        self.assertIn("journey-stat--highlight", metric_html(p["metrics"][1]))
        self.assertIn("PRÓXIMA AÇÃO", next_html(p))
        self.assertIn("journey-step", step_html(p["steps"][2]))

    def test_no_persisted_progress_or_fake_percentage(self):
        result = project_visual_state(view(), "Rascunho nesta sessão")
        self.assertNotIn("percent", result)
        self.assertNotIn("progress", result)
        self.assertNotIn("100%", str(result))


if __name__ == "__main__":
    unittest.main()
