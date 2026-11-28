#!/usr/bin/env python3
"""Audit root-module reachability and produce reproducible ARCH15E evidence.

Static AST imports include imports inside functions. Literal dynamic imports
are included; nonliteral dynamic imports require explicit review.
Tests are deliberately not production entry points.
"""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
# Temporary review exceptions. Do not expand without a documented reason.
ALLOWLIST = {
    "arch10b_documentary_parity": "Documentary rail audit; pending offline relocation",
    "arch14_macro_coverage_cache": "Macro opportunity projection differs from UX132; pending decision",
    "calendar_visit_model": "Repeated-visit prototype; pending reference audit",
    "corridor_priority_pilot_model": "Research pilot with versioned data; pending offline relocation",
    "geographic_base_screening_model": "Exploratory geographic study; pending reference audit",
    "regional_opportunity_research_model": "Regional proposals with versioned data; pending offline relocation",
    "route_research_evidence_model": "Research validation contract; pending offline relocation",
    "rec02_diagnostics": "Standalone recommendation diagnostics; pending offline relocation",
    "rec01_feasibility": "Standalone recommendation benchmark; pending offline relocation",
}
SYMBOLS = (
    "upsert_flexible_choice", "remove_flexible_choice", "delete_package",
    "active_plan_view", "PrivateQuoteStore", "validate_predefined_budget",
    "close_overlays", "_draft_all", "lot_coverage", "_by_city", "_format_brl",
    "MANUAL_KEYS", "DEPARTURE_MIN_DATE", "SOURCE_URL", "RECHECK", "LEGACY",
    "OFFICIAL_FARE_BASES", "VALID_DISTANCE_KINDS", "VALID_MODES",
)


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0]
        elif isinstance(node, ast.Call) and node.args:
            fn = node.func
            dynamic = (isinstance(fn, ast.Name) and fn.id in ("import_module", "__import__")
                       or isinstance(fn, ast.Attribute) and fn.attr == "import_module")
            arg = node.args[0]
            if dynamic and isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                yield arg.value.split(".")[0]


def unreachable(root=ROOT):
    modules = {p.stem: p for p in root.glob("*.py")}
    entries = [root / "app.py", *sorted((root / "scripts").rglob("*.py")),
               *sorted((root / "tools").rglob("*.py"))]
    reached = set()
    queue = list(entries)
    while queue:
        path = queue.pop()
        if path in reached:
            continue
        reached.add(path)
        queue.extend(modules[name] for name in imports(path) if name in modules)
    return sorted(name for name, path in modules.items() if path not in reached)


def evidence():
    for name in ALLOWLIST:
        path = name + ".py"
        print("\nORIGIN", path, flush=True)
        subprocess.run(["git", "log", "--diff-filter=A", "--format=%H %s", "--", path],
                       cwd=ROOT, check=True)
    for name in SYMBOLS:
        print("\nREFERENCES", name, flush=True)
        result = subprocess.run(["git", "grep", "-n", "-w", name, "--", "."], cwd=ROOT)
        if result.returncode not in (0, 1):
            raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args()
    if args.evidence:
        evidence()
    missing = set(unreachable())
    for name in sorted(missing):
        print(name, ALLOWLIST.get(name, "UNEXPLAINED"))
    unexpected = missing - ALLOWLIST.keys()
    if unexpected:
        raise SystemExit("Unexpected unreachable root modules: " + ", ".join(sorted(unexpected)))


if __name__ == "__main__":
    main()
