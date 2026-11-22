"""UX: visual state, WCAG contrast and native Streamlit flow contracts."""
import re
import unittest
from copy import deepcopy
from pathlib import Path

from ux_planning_journey_presentation import (
    project_visual_state, header_html, metric_html, next_html, step_html,
)

ROOT = Path(__file__).resolve().parents[1]


def view(*, wished=6, planned=0, organized=0, eligible=5, action="build", saved=False):
    return {
        "counts": {"wished": wished, "planned": planned, "organized": organized},
        "eligible_count": eligible, "next": action, "private_saved": saved,
    }


def selected(visual):
    return [metric["id"] for metric in visual["metrics"] if metric["highlight"]]


def step(visual, name):
    return next(item for item in visual["steps"] if item["id"] == name)


class PlanningVisualProjectionTests(unittest.TestCase):
    def test_empty_wishlist_and_no_draft(self):
        state = view(wished=0, planned=0, eligible=0, action="choose")
        before = deepcopy(state)
        visual = project_visual_state(state, "Rascunho nesta sessão")
        self.assertEqual(state, before)
        self.assertEqual(visual["action"], "choose")
        self.assertEqual(selected(visual), ["wished"])
        self.assertEqual(step(visual, "choose")["status"], "Disponível")
        self.assertTrue(step(visual, "build")["disabled"])
        self.assertIn("Indisponível", step(visual, "build")["status"])
        self.assertFalse(step(visual, "review")["disabled"])

    def test_wishlist_eligible_stresses_inclusion_even_before_first_included(self):
        visual = project_visual_state(view(), "Rascunho nesta sessão")
        self.assertEqual(selected(visual), ["planned"])
        self.assertEqual(visual["metrics"][0]["value"], 6)
        self.assertEqual(visual["metrics"][1]["value"], 0)
        self.assertIn("5 destino(s)", visual["headline"])
        self.assertEqual([item["id"] for item in visual["steps"]],
                         ["choose", "build", "organize", "review"])
        self.assertTrue(step(visual, "build")["active"])
        self.assertFalse(step(visual, "build")["disabled"])
        self.assertIn('aria-current="step"', step_html(step(visual, "build")))

    def test_exploratory_only_disables_build_without_blocking_review(self):
        visual = project_visual_state(
            view(wished=2, eligible=0, action="exploratory"), "Rascunho nesta sessão")
        self.assertEqual(visual["current_step"], "choose")
        self.assertEqual(selected(visual), ["wished"])
        self.assertTrue(step(visual, "build")["disabled"])
        self.assertFalse(step(visual, "review")["disabled"])
        self.assertIn("pesquisa", visual["headline"])
        self.assertIn('aria-disabled="true"', step_html(step(visual, "build")))

    def test_revise_undated_draft_prioritizes_included_not_organized(self):
        visual = project_visual_state(
            view(wished=0, planned=2, organized=0, eligible=0, action="review"),
            "Rascunho nesta sessão")
        self.assertEqual(selected(visual), ["planned"])
        self.assertEqual(step(visual, "review")["status"], "Rascunho local a revisar")
        self.assertIn("opcional", step(visual, "organize")["status"])
        self.assertIn("não confirma", visual["explanation"])

    def test_partially_organized_draft_highlights_organizer_only_when_focused(self):
        state = view(wished=3, planned=4, organized=2, eligible=0, action="review")
        review = project_visual_state(state, "Rascunho nesta sessão")
        organizing = project_visual_state(state, "Rascunho nesta sessão",
                                          focused="organize")
        self.assertEqual(selected(review), ["planned"])
        self.assertEqual(selected(organizing), ["organized"])
        self.assertTrue(step(organizing, "organize")["active"])
        self.assertIn("Visitas organizadas", step(organizing, "organize")["status"])

    def test_pending_eligible_destinations_prioritize_included_during_review(self):
        visual = project_visual_state(
            view(wished=5, planned=2, organized=0, eligible=3, action="build"),
            "Rascunho nesta sessão", focused="review")
        self.assertEqual(selected(visual), ["planned"])
        self.assertIn("3 ainda compatíveis", step(visual, "build")["detail"])
        self.assertTrue(step(visual, "review")["active"])

    def test_saved_and_focused_states_coexist_and_header_is_truthful(self):
        raw = view(planned=2, organized=1, eligible=0, action="review", saved=True)
        visual = project_visual_state(raw, "Salvo em espaço privado")
        review = step(visual, "review")
        self.assertEqual(selected(visual), ["planned"])
        self.assertEqual(review["status"], "Salvo em espaço privado")
        self.assertTrue(review["active"])
        self.assertEqual(review["button"], "Revisar")
        self.assertIn("Em foco", step_html(review))
        self.assertIn("Salvo em espaço privado", step_html(review))
        self.assertEqual(visual["primary_label"], "Continuar planejamento")
        self.assertIn("journey-header__dot--saved",
                      header_html("Salvo em espaço privado", "Recuperável", saved=True))
        self.assertIn("journey-header__dot--local",
                      header_html("Rascunho nesta sessão", "Local"))
        stale = project_visual_state(raw, "Alterações apenas nesta sessão")
        self.assertFalse(stale["saved"])
        self.assertIn("Alterações não salvas", step(stale, "review")["status"])
        self.assertIn("Alterações apenas nesta sessão", step(stale, "review")["detail"])

    def test_in_focus_optional_organize_still_allows_review(self):
        visual = project_visual_state(
            view(wished=1, planned=1, organized=0, eligible=0, action="review"),
            "Rascunho nesta sessão", focused="organize")
        self.assertEqual(selected(visual), ["organized"])
        self.assertIn("opcional", visual["explanation"])
        self.assertFalse(step(visual, "review")["disabled"])
        self.assertTrue(step(visual, "organize")["active"])
        self.assertIn("Ainda sem datas", step(visual, "organize")["status"])

    def test_escape_html_status_and_markup(self):
        h = header_html("<script>alert(1)</script>", "Aguardando <salvar>")
        self.assertNotIn("<script>", h)
        self.assertIn("&lt;script&gt;", h)
        self.assertIn("&lt;salvar&gt;", h)
        visual = project_visual_state(view(), "Rascunho nesta sessão")
        self.assertIn("journey-stat--highlight", metric_html(visual["metrics"][1]))
        self.assertIn("PRÓXIMA AÇÃO", next_html(visual))
        evil = step(visual, "review").copy()
        evil["status"] = "<script>bad</script>"
        html = step_html(evil)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("journey-step__states", html)

    def test_not_persisting_fake_progress(self):
        visual = project_visual_state(view(), "Rascunho nesta sessão")
        self.assertNotIn("percent", visual)
        self.assertNotIn("progress", visual)
        self.assertNotIn("100%", str(visual))


def luminance(color):
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(part * 2 for part in value)
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                for v in channels]
    return sum(v * w for v, w in zip(channels, (.2126, .7152, .0722)))


def contrast(fg, bg):
    a, b = sorted([luminance(fg), luminance(bg)], reverse=True)
    return (a + .05) / (b + .05)


def color_for(source, selector):
    pattern = rf"{re.escape(selector)}\s*\{{([^}}]*)\}}"
    section = re.search(pattern, source, re.S)
    if not section:
        raise AssertionError(f"Selector not found: {selector}")
    match = re.search(r"(?<![-\w])color\s*:\s*(#[0-9A-Fa-f]{3,6})", section[1])
    if not match:
        raise AssertionError(f"No foreground color for: {selector}")
    return match[1]


def over(fg, bg, fraction):
    a, b = fg.lstrip("#"), bg.lstrip("#")
    channels = [round(int(a[i:i + 2], 16) * fraction +
                      int(b[i:i + 2], 16) * (1 - fraction))
                for i in (0, 2, 4)]
    return "#" + "".join(f"{v:02x}" for v in channels)


class JourneyWCAGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")

    def test_small_text_aa_on_white_and_highlight_gradients(self):
        cases = [
            (".journey-header__eyebrow", ["#F0F7F8", "#FAFCFE"]),
            (".journey-stat small", ["#FFFFFF", "#E7F5FA", "#F5FCFF"]),
            (".journey-section-title p", ["#FFFFFF", "#FAFCFE"]),
            (".journey-step__copy small", ["#FFFFFF", "#EAF7FB", "#F8FCFE"]),
            (".journey-step__status", ["#FFFFFF"]),
            (".journey-step__focus", ["#DCF0F5"]),
        ]
        for selector, backgrounds in cases:
            with self.subTest(selector=selector):
                foreground = color_for(self.css, selector)
                for bg in backgrounds:
                    self.assertGreaterEqual(contrast(foreground, bg), 4.5,
                                            (selector, foreground, bg))

    def test_banner_text_aa_including_radial_overlay(self):
        lightest = over("#55B8C5", "#124D60", .18)
        for selector in (".journey-next__eyebrow",
                         ".journey-next__content h2",
                         ".journey-next__content p"):
            with self.subTest(selector=selector):
                fg = color_for(self.css, selector)
                self.assertGreaterEqual(contrast(fg, lightest), 4.5,
                                        (selector, fg, lightest))

    def test_focus_and_narrow_viewport_layout_contracts(self):
        self.assertIn(".journey-next__anchor:focus-visible", self.css)
        self.assertIn("flow_journey_metrics", self.css)
        self.assertIn("flex-wrap:wrap !important", self.css)
        self.assertIn("st-key-flow_journey_step_card_", self.css)
        self.assertIn("min-height:44px !important", self.css)
        self.assertIn("button:disabled", self.css)
        self.assertIn("opacity:1 !important", self.css)


if __name__ == "__main__":
    unittest.main()
