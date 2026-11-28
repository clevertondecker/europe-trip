"""Prevent independent reimplementation of shared presentation/evidence helpers."""
import ast
import unittest
from pathlib import Path

from formatting import brl, eur, chf, amount, minutes, html_safe, REQUIRED

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"_safe", "_https", "_money", "money", "_currency", "_eur",
         "_format_brl", "_format_eur", "compact_money", "_duration"}
# These functions parse/validate data rather than format presentation values.
ALLOW = {
    ("quote_research_model.py", "_money"),
    ("data8_couple_cost_model.py", "_money"),
    ("ux44_finance_comparison_model.py", "_money"),
    ("data8_attraction_evidence_model.py", "_duration"),
}
SHARED = {"formatting": {"brl", "eur", "chf", "amount", "minutes", "html_safe"},
          "evidence_validation": {"is_https_url"}}


def delegates(node, imports):
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return False
    expression = body[0].value
    calls = [part for part in ast.walk(expression) if isinstance(part, ast.Call)]
    if not calls or any(not isinstance(call.func, ast.Name) or call.func.id not in imports for call in calls):
        return False
    # Permit direct calls, concatenation of delegated currencies, and URL-or-None.
    return not any(isinstance(part, (ast.JoinedStr, ast.Attribute, ast.Lambda))
                   for part in ast.walk(expression))


class FormattingContractTests(unittest.TestCase):
    def test_no_duplicate_helpers(self):
        failures = []
        paths = sorted(ROOT.glob("*.py"))
        for directory in ("scripts", "tools"):
            paths.extend(sorted((ROOT / directory).rglob("*.py")))
        for path in paths:
            if path.name in SHARED or path.name in ("formatting.py", "evidence_validation.py"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = {alias.asname or alias.name
                       for node in tree.body if isinstance(node, ast.ImportFrom)
                       for alias in node.names if alias.name in SHARED.get(node.module, set())}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in NAMES:
                    if (path.name, node.name) not in ALLOW and not delegates(node, imports):
                        failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: {node.name}")
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Lambda):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id in NAMES:
                            failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: {target.id}")
        self.assertFalse(failures, "\n".join(failures))

    def test_shared_currency_contract(self):
        for fn, symbol in ((brl, "R$"), (eur, "€"), (chf, "CHF")):
            with self.subTest(symbol=symbol):
                self.assertEqual(fn(1234.56, missing="missing"), symbol + " 1.234,56")
                self.assertEqual(fn(-1234.56, missing="missing"), symbol + " -1.234,56")
                self.assertEqual(fn(0, missing="missing"), symbol + " 0,00")
                self.assertEqual(fn(1234, decimals=0, missing="missing"), symbol + " 1.234")
                self.assertEqual(fn(None, missing="missing"), "missing")
                with self.assertRaises(TypeError):
                    fn(None, missing=REQUIRED)
                with self.assertRaises(TypeError):
                    fn(1)
        self.assertEqual(amount(1000, missing=None), "1.000,00")

    def test_minutes_and_escape(self):
        for value, expected in ((0, "0 min"), (59, "59 min"), (60, "1h00"),
                                (61, "1h01"), (None, "missing")):
            self.assertEqual(minutes(value, missing="missing"), expected)
        self.assertEqual(html_safe("<>&\"'"), "&lt;&gt;&amp;&quot;&#x27;")
