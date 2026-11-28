"""ARCH15A: prevent deprecated widget width arguments and smoke-test public navigation."""
import logging
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WidthContractTests(unittest.TestCase):
    def test_no_deprecated_width_in_production_python(self):
        paths = sorted(ROOT.glob("*.py"))
        for directory in ("scripts", "tools"):
            paths.extend(sorted((ROOT / directory).rglob("*.py")))
        violations = []
        for path in paths:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "use_container_width" in line:
                    violations.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
        self.assertFalse(violations, "\n".join(violations))

    def test_public_screens_without_width_deprecation(self):
        from streamlit.testing.v1 import AppTest

        messages = []
        class Capture(logging.Handler):
            def emit(self, record):
                messages.append(record.getMessage())

        handler = Capture()
        logger = logging.getLogger("streamlit")
        logger.addHandler(handler)
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
                self.assertFalse(app.exception, [x.message for x in app.exception])
                for index, tasks in (
                    (1, ("Descobrir", "Minha lista", "Comparar bases", "Cobertura dos dados", "Mapa")),
                    (2, ("Visão geral", "Meus destinos", "Organizar")),
                    (3, ("Visão financeira", "Simulações")),
                ):
                    app.button(key=f"ux_sidebar_nav_{index}").click().run()
                    self.assertFalse(app.exception, [x.message for x in app.exception])
                    for task in tasks:
                        with self.subTest(task=task):
                            app.segmented_control(key="ux64_public_task").set_value(task).run()
                            self.assertFalse(app.exception, [x.message for x in app.exception])
                messages.extend(str(item.message) for item in caught)
        finally:
            logger.removeHandler(handler)
        self.assertFalse([m for m in messages if "use_container_width" in m], messages)
