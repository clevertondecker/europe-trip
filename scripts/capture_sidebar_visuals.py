"""Optional real-browser screenshot capture for UX sidebar visual review.

Requires playwright installed locally and chromium:
  pip install playwright
  playwright install chromium
  python scripts/capture_sidebar_visuals.py --url https://YOUR-APP.streamlit.app

Creates screenshots in /tmp by default; never commits user information.
This script is not a substitute for reviewing screenshots.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Deployed Streamlit URL")
    parser.add_argument("--output", type=Path, default=Path("/tmp/europe-sidebar-visual"))
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Install playwright and run 'playwright install chromium' first"
        ) from exc
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height},
                                    device_scale_factor=1)
            page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
            page.locator('[data-testid="stSidebar"]').wait_for(timeout=60000)
            # Mobile Streamlit may collapse sidebar until explicitly opened.
            if name == "mobile":
                trigger = page.get_by_role("button", name="Open sidebar")
                if trigger.count():
                    trigger.first.click()
            page.wait_for_timeout(1500)
            for label in ("Minha viagem", "Explorar destinos", "Meu roteiro", "Orçamento"):
                button = page.get_by_role("button", name=label, exact=True)
                if name == "desktop" and not button.count():
                    raise AssertionError(f"Sidebar navigation missing: {label}")
            output = args.output / f"sidebar-{name}.png"
            page.screenshot(path=str(output), full_page=False)
            print(f"Screenshot: {output}")
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
