"""AppTest navigation through the public sidebar and task selector only."""
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
