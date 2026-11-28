"""AppTest navigation via public tabs and explicit contextual CTAs."""
from ux64_navigation_model import PUBLIC_AREAS, PUBLIC_TASKS


def open_public(app, area, task):
    """Open a public task using actual widgets, never injected route state."""
    if area not in PUBLIC_TASKS or task not in PUBLIC_TASKS[area]:
        raise ValueError(f"Not a public task: {area!r}/{task!r}")
    app.sidebar.button(key=f"ux64_sidebar_nav_{PUBLIC_AREAS.index(area)}").click().run()
    if app.exception:
        raise AssertionError([error.message for error in app.exception])
    tabs = app.segmented_control(key="ux64_public_task")
    if tabs.value != task:
        tabs.set_value(task).run()
    if app.exception:
        raise AssertionError([error.message for error in app.exception])
    if app.segmented_control(key="ux64_public_task").value != task:
        raise AssertionError(f"Public navigation did not reach {area!r}/{task!r}")
    return app


def open_support(app, tool):
    """Open an existing planning tool via its user-facing overview CTA."""
    open_public(app, "Planejar", "Visão geral")
    app.button(key="home_open_consultor").click().run()
    if app.exception:
        raise AssertionError([error.message for error in app.exception])
    selector = app.selectbox(key="ux_improve_view")
    if selector.value != tool:
        selector.set_value(tool).run()
    if app.exception:
        raise AssertionError([error.message for error in app.exception])
    if app.selectbox(key="ux_improve_view").value != tool:
        raise AssertionError(f"Planning tool did not open: {tool!r}")
    return app
