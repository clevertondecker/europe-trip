"""Temporary ARCH15A repository inventory; remove after recording evidence."""
import inspect
import subprocess
import unittest
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
class Arch15AInventory(unittest.TestCase):
    def test_inventory(self):
        names = (
            "over" + "line", "show_" + "place", "mini_" + "budget",
            "navigate_" + "page", "navigate_to_" + "attractions",
            "_ux_area_" + "changed", "_ux_legacy_itinerary_" + "changed",
            "_ux_legacy_guide_" + "changed", "_ux_return_to_" + "official",
        )
        for name in names:
            result = subprocess.run(["grep", "-rnI", "--exclude-dir=.git",
                "--exclude-dir=__pycache__", name, "."], cwd=ROOT,
                text=True, capture_output=True)
            print("ARCH15A_FUNCTION", name, result.returncode, result.stdout, sep="\n", flush=True)
            self.assertIn(result.returncode, (0, 1), result.stderr)
        token = "use_container_" + "width"
        result = subprocess.run(["git", "grep", "-n", token, "--", "*.py"],
                                cwd=ROOT, text=True, capture_output=True)
        print("ARCH15A_WIDTH", result.stdout, sep="\n", flush=True)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        for name in ("button", "link_button", "dataframe", "image", "download_button", "data_editor"):
            print("ARCH15A_API", st.__version__, name, inspect.signature(getattr(st, name)), flush=True)
        for path in ROOT.glob("*.md"):
            if path.stem.startswith(("PROMPT_", "PESQUISA_", "RELATORIO_")):
                result = subprocess.run(["git", "grep", "-n", "-F", path.stem, "--", "*.py", "*.md", ":(exclude)" + path.name],
                                        cwd=ROOT, text=True, capture_output=True)
                print("ARCH15A_DOC", path.name, result.returncode, result.stdout, sep="\n", flush=True)
                self.assertIn(result.returncode, (0, 1), result.stderr)
