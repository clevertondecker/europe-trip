"""Guard against importing retired exploration callbacks from any production module."""
import ast
from pathlib import Path
import unittest


class RetiredCallbackTests(unittest.TestCase):
    def test_no_retired_discovery_imports(self):
        root=Path(__file__).resolve().parents[1]
        retired={"_discover_eligible","_ordered_matches"}
        violations=[]
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node,ast.ImportFrom) and node.module in (
                    "ux502_destination_interests_ui","ux501_destination_discovery_ui"):
                    for alias in node.names:
                        if alias.name in retired:
                            violations.append(f"{path.name}:{node.lineno}: {alias.name}")
                if isinstance(node,ast.Attribute) and node.attr in retired:
                    violations.append(f"{path.name}:{node.lineno}: {node.attr}")
        self.assertEqual(violations,[])
