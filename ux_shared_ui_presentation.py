"""Pure shared presentation for the three public application areas.

UX81 reuses the existing #196 journey classes and CSS tokens rather than
starting a competing component library. These functions NEVER query application
state, perform navigation, persist changes or create interactive HTML controls.
Callers provide projected data and use native Streamlit widgets for actions.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
from typing import Literal

HeaderVariant = Literal["standard", "compact"]
ActionVariant = Literal["strong", "compact"]
StatusKind = Literal["neutral", "saved", "warning", "disabled"]


def _safe(value: object) -> str:
    """Escape text AND attribute data, including quotation marks."""
    return escape(str(value), quote=True)


def page_header(
    title: str,
    eyebrow: str,
    description: str = "",
    *,
    status_label: str = "",
    status_hint: str = "",
    saved: bool = False,
    tag: str = "",
    variant: HeaderVariant = "standard",
) -> str:
    """Read-only page context; saved is an explicit, already-verified fact."""
    if variant not in ("standard", "compact"):
        raise ValueError("Unknown header variant")
    status = ""
    if status_label:
        dot_kind = "saved" if saved else "local"
        suffix = (f'<span aria-hidden="true"> · </span>{_safe(status_hint)}'
                  if status_hint else "")
        status = (
            '<p class="journey-header__save ui-page-header__status">'
            f'<span class="journey-header__dot journey-header__dot--{dot_kind}" '
            f'aria-hidden="true"></span>{_safe(status_label)}{suffix}</p>'
        )
    summary = (f'<p class="ui-page-header__description">{_safe(description)}</p>'
               if description else "")
    tag_html = (f'<span class="journey-header__tag">{_safe(tag)}</span>'
                if tag else "")
    return (
        f'<header class="journey-header ui-page-header ui-page-header--{variant}" '
        f'aria-label="{_safe(title)}">'
        f'<div><span class="journey-header__eyebrow">{_safe(eyebrow)}</span>'
        f'<h1>{_safe(title)}</h1>{summary}{status}</div>'
        f'{tag_html}</header>'
    )


def kpi_cards(metrics: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    """Return each card separately for native st.columns and responsive wrapping.

    Metrics MUST come from the caller's existing canonical projections.
    Required fields: name, value. Optional: hint, icon, highlight.
    """
    rendered = []
    for metric in metrics:
        name = metric["name"]
        value = metric["value"]
        icon = metric.get("icon", "•")
        hint = metric.get("hint", "")
        highlighted = bool(metric.get("highlight", False))
        modifier = " journey-stat--highlight" if highlighted else ""
        rendered.append(
            f'<div class="journey-stat ui-kpi-card{modifier}" '
            f'aria-label="{_safe(name)}: {_safe(value)}">'
            f'<div class="journey-stat__icon" aria-hidden="true">{_safe(icon)}</div>'
            '<div class="journey-stat__content">'
            f'<span class="journey-stat__label">{_safe(name)}</span>'
            f'<strong class="journey-stat__value">{_safe(value)}</strong>'
            f'<small>{_safe(hint)}</small></div></div>'
        )
    return tuple(rendered)


def next_action(
    headline: str,
    explanation: str,
    *,
    variant: ActionVariant = "strong",
    eyebrow: str = "PRÓXIMA AÇÃO",
) -> str:
    """Informational text ONLY. Native Streamlit renders the actual CTA."""
    if variant not in ("strong", "compact"):
        raise ValueError("Unknown action variant")
    return (
        f'<div class="journey-next__content ui-next-action ui-next-action--{variant}">'
        '<span class="journey-next__eyebrow">'
        f'<span aria-hidden="true">✦</span> {_safe(eyebrow)}</span>'
        f'<h2>{_safe(headline)}</h2>'
        f'<p>{_safe(explanation)}</p></div>'
    )


def section_heading(
    eyebrow: str,
    title: str,
    description: str = "",
    *,
    variant: HeaderVariant = "standard",
) -> str:
    """Heading for a section, not a second h1/page title."""
    if variant not in ("standard", "compact"):
        raise ValueError("Unknown section variant")
    details = f'<p>{_safe(description)}</p>' if description else ""
    return (
        f'<div class="journey-section-title ui-section-heading '
        f'ui-section-heading--{variant}">'
        f'<span>{_safe(eyebrow)}</span><h2>{_safe(title)}</h2>'
        f'{details}</div>'
    )


def status_indicator(
    status: str,
    *,
    active: bool = False,
    kind: StatusKind = "neutral",
) -> str:
    """Separate domain status from current navigation focus, with text for both."""
    if kind not in ("neutral", "saved", "warning", "disabled"):
        raise ValueError("Unknown status kind")
    focus = ('<span class="journey-step__focus">Em foco</span>' if active else "")
    return (
        '<div class="journey-step__states ui-status-group">'
        f'<span class="journey-step__status ui-status-indicator '
        f'ui-status-indicator--{kind}">{_safe(status)}</span>'
        f'{focus}</div>'
    )
