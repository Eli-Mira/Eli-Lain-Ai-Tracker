"""Browser verification of the built project-shortlist artifacts (real Chromium, offline)."""
from __future__ import annotations

from pathlib import Path
import json
import sys

from playwright.sync_api import sync_playwright

CHROME = "C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe"


def verify(path: Path, width: int, javascript: bool = True) -> dict:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=CHROME)
        try:
            context = browser.new_context(viewport={"width": width, "height": 900},
                                          offline=True, java_script_enabled=javascript)
            page = context.new_page()
            requests, errors = [], []
            page.on("request", lambda request: requests.append(request.url))
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(path.as_uri(), wait_until="load")
            body = page.locator("body").inner_text()
            result = {
                "width": width, "javascript": javascript,
                "discovery_rows": page.locator("#discoveries .discovery-item:visible").count(),
                "project_groups": page.locator("#project-shortlists .project-group").count(),
                "recommendation_cards": page.locator("#project-shortlists .recommendation-item").count(),
                "first_card_id": page.locator("#project-shortlists .recommendation-item").first.get_attribute("data-id"),
                "coverage_text": page.locator("#recommendation-coverage").inner_text(),
                "no_horizontal_overflow": page.evaluate("document.documentElement.scrollWidth <= innerWidth"),
                "requests": requests, "page_errors": errors,
                "body_chars": len(body),
                "leaks_localhost": "localhost" in body.lower(),
                "leaks_windows_path": ":\\" in body,
            }
            context.close()
            return result
        finally:
            browser.close()


def main(paths: list[str]) -> int:
    reports = []
    for raw in paths:
        path = Path(raw)
        for width in (360, 1440):
            reports.append(verify(path, width))
        reports.append(verify(path, 1440, javascript=False))
    print(json.dumps(reports, indent=2, sort_keys=True))
    failed = [r for r in reports if r["page_errors"] or r["leaks_localhost"] or r["leaks_windows_path"]
              or not r["no_horizontal_overflow"] or len(r["requests"]) != 1
              or r["project_groups"] != 4 or r["recommendation_cards"] == 0
              or (r["javascript"] and r["discovery_rows"] == 0)]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
