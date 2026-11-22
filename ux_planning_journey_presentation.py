"""Read-only, presentation-only view of the existing planning projection.

No new progress state is persisted, and no score or save success is inferred.
All user-visible dynamic text is HTML-escaped at the rendering boundary.
"""
from __future__ import annotations

from html import escape
from ux_shared_ui_presentation import page_header, kpi_cards, next_action, status_indicator


def project_visual_state(view: dict, storage_label: str, focused: str | None = None) -> dict:
    """Derive hierarchy from canonical journey counts, not widget guesses."""
    counts = view["counts"]
    wished, planned, organized = (
        int(counts[key]) for key in ("wished", "planned", "organized")
    )
    eligible = int(view["eligible_count"])
    action = focused if focused in ("build", "organize", "review") else view["next"]
    current_step = "choose" if action in ("choose", "exploratory") else action
    saved = storage_label == "Salvo em espaço privado" and bool(view["private_saved"])

    descriptions = {
        "choose": (
            "Escolha os lugares que deseja conhecer.",
            "Comece pela lista de desejos. Nenhuma reserva é feita nesta etapa.",
        ),
        "exploratory": (
            "Seus desejos ainda estão disponíveis somente para pesquisa.",
            "Eles permanecem na lista; ainda não podem entrar como passeios no roteiro.",
        ),
        "build": (
            f"{eligible} destino(s) compatíveis ainda podem entrar no roteiro.",
            "Confirme quais deseja incluir. Você não precisa definir datas agora.",
        ),
        "organize": (
            "Organize as visitas por período ou data, se desejar.",
            "Essa etapa é opcional: rascunhos sem datas também podem ser salvos.",
        ),
        "review": (
            "Revise o que está no roteiro e suas alterações.",
            "Salvar registra suas escolhas; não confirma bilhetes, hospedagem ou reservas.",
        ),
    }
    headline, explanation = descriptions[action]
    if saved and action == "review":
        headline = "Seu rascunho está salvo em espaço privado."
        explanation = ("Continue planejando quando quiser. Salvar o roteiro "
                       "não confirma viagens ou reservas.")
    # Inclusion is primary when eligible wishes are pending; organizing is
    # emphasized only while the user explicitly works on dated visits.
    # Reviewing an undated draft must never highlight an empty organizer.
    if eligible:
        highlight = "planned"
    elif action == "organize" and planned:
        highlight = "organized"
    elif not planned or action in ("choose", "exploratory"):
        highlight = "wished"
    else:
        highlight = "planned"
    metrics = [
        {"id": "wished", "icon": "◎", "name": "Desejados", "value": wished,
         "hint": "Na minha lista", "highlight": highlight == "wished"},
        {"id": "planned", "icon": "▣", "name": "Incluídos", "value": planned,
         "hint": "No roteiro", "highlight": highlight == "planned"},
        {"id": "organized", "icon": "▤", "name": "Organizados", "value": organized,
         "hint": "Com período ou data", "highlight": highlight == "organized"},
    ]
    if saved:
        review_detail = "Salvo em espaço privado"
    elif storage_label.startswith("Alterações"):
        review_detail = storage_label
    elif planned:
        review_detail = "Rascunho pode ser salvo"
    else:
        review_detail = "Nenhum destino incluído"

    step_info = [
        ("choose", "Escolher destinos", f"{wished} desejados", "Ver destinos", False),
        ("build", "Montar roteiro", f"{planned} incluídos · {eligible} ainda compatíveis",
         "Montar roteiro", eligible == 0),
        ("organize", "Organizar visitas", f"{organized} com período ou data · opcional",
         "Organizar", False),
        ("review", "Revisar e salvar", review_detail,
         "Revisar" if saved else "Revisar e salvar", False),
    ]
    steps = []
    for number, (step, title, detail, button, disabled) in enumerate(step_info, 1):
        # The persistent/derived state and the open panel are independent:
        # e.g. "Salvo em espaço privado" AND "Em foco" are both displayed.
        if step == "choose":
            status = "Lista iniciada" if wished else "Disponível"
        elif step == "build":
            status = ("Indisponível · sem novos destinos compatíveis" if disabled else
                      "Rascunho iniciado" if planned else "Disponível para incluir")
        elif step == "organize":
            status = ("Visitas organizadas · opcional" if organized else
                      "Ainda sem datas · opcional" if planned else
                      "Opcional · sem visitas incluídas")
        elif saved:
            status = "Salvo em espaço privado"
        elif storage_label.startswith("Alterações"):
            status = "Alterações não salvas"
        elif planned:
            status = "Rascunho local a revisar"
        else:
            status = "Disponível · sem destinos incluídos"
        steps.append({
            "id": step, "number": number, "title": title, "detail": detail,
            "button": button, "disabled": disabled, "status": status,
            "active": step == current_step,
            "status_kind": ("disabled" if disabled else
                            "saved" if step == "review" and saved else
                            "warning" if step == "review" and storage_label.startswith("Alterações")
                            else "neutral"),
        })
    return {
        "action": action, "current_step": current_step,
        "headline": headline, "explanation": explanation,
        "metrics": metrics, "steps": steps, "saved": saved,
        "primary_label": "Continuar planejamento" if saved and action == "review" else None,
    }



# Existing UX81 integration wrappers retain legacy public names and selectors.
# All generic markup is owned by ux_shared_ui_presentation (one library).
def header_html(storage_label: str, storage_hint: str, *, saved: bool = False,
                title: str = "Meu roteiro", tag: str = "Da lista ao roteiro revisado") -> str:
    return page_header(
        title, "NOSSA EUROPA 2027 · PLANEJAMENTO",
        status_label=storage_label, status_hint=storage_hint, saved=saved,
        tag=tag,
    )


def metric_html(metric: dict) -> str:
    return kpi_cards((metric,))[0]


def next_html(visual: dict) -> str:
    return next_action(visual["headline"], visual["explanation"])


def step_html(step: dict) -> str:
    current = ' aria-current="step"' if step["active"] else ""
    unavailable = ' aria-disabled="true"' if step["disabled"] else ""
    return (
        f'<div class="journey-step"{current}{unavailable}>'
        f'<span class="journey-step__number" aria-hidden="true">{step["number"]}</span>'
        '<div class="journey-step__copy">'
        f'<strong>{escape(step["title"])}</strong>'
        f'<small>{escape(step["detail"])}</small>'
        f'{status_indicator(step["status"], active=step["active"], kind=step.get("status_kind", "neutral"))}'
        '</div></div>'
    )
