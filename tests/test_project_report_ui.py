"""Project report UI and fail-closed public evaluation contract."""
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

from intel_sources.recommendations import evaluate_projects
from tracker_core.reporter_html import LainReporter

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
CHECKED = "2026-10-01T11:00:00+00:00"
TDD = "skills:obra/superpowers/test-driven-development"


def discovery(identifier=TDD):
    kind, slug = identifier.split(":", 1)
    return {"id": identifier, "headline": slug, "source": "skills-sh" if kind == "skills" else "github-trending",
            "url": ("https://skills.sh/" if kind == "skills" else "https://github.com/") + slug,
            "checked_at": CHECKED, "evidence": {}, "summary": "Original inventory retained"}


def test_lain_render_accepts_evaluated_groups_and_preserves_inventory(tmp_path):
    items = [discovery(), discovery("github:pytorch/pytorch")]
    result = evaluate_projects(items, now=NOW)
    html = LainReporter().render(api_items=[], tool_items=items,
        recommendation_groups=result["groups"], recommendation_coverage={
            **result["coverage"], "inventory_count": result["inventory_count"], "reviewed_count": 2})
    soup = BeautifulSoup(html, "html.parser")
    assert len(soup.select("#discoveries .discovery-item")) == 2
    assert len(soup.select("#project-shortlists .project-group")) == 4
    assert "2 reviewed / 2 discovery candidates" in soup.select_one("#recommendation-coverage").text
    card = soup.select_one(".recommendation-item[data-id='" + TDD + "']")
    for expected in ("Reason:", "Constraints:", "Confidence: low", "Discovery: fresh", "Official metadata: unverified",
                     "Cost: unknown", "License: unknown", "Support: unknown", "Next validation:", "metadata-only", "not integration-tested"):
        assert expected in card.text
    assert "Decimal totals" in soup.select_one(".project-group[data-project='hearth-pos']").text
    assert "No installed integration tests" in soup.select_one("#project-shortlists").text
    saved = LainReporter().save(tmp_path / "report.html", api_items=[], tool_items=items,
        recommendation_groups=result["groups"], recommendation_coverage={"reviewed_count": 2, "discovery_count": 2})
    assert "Decimal totals" in saved.read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    assert (root / "src/templates/report_template_lain.html").read_bytes() == (root / "src/tracker-core/templates/report_template_lain.html").read_bytes()


def test_public_shortlists_review_full_validated_inventory_not_display_cap():
    import copy
    from intel_sources.public_report import build_public_payload
    first = discovery("skills:aaa/public/unreviewed")
    reviewed = discovery()
    reviewed.update(summary="PRIVATE_DESCRIPTION_CANARY", constraints=["PRIVATE_CONSTRAINT_CANARY"],
                    source_urls=["http://localhost/PRIVATE_URL_CANARY"],
                    evidence={"description": "PRIVATE_EVIDENCE_CANARY", "error": "PRIVATE_ERROR_CANARY"})
    private = discovery("github:Eli-Mira/Eli-Lain-Ai-Tracker")
    state = {"items": [first, reviewed, private], "sources": [{"name": "skills-sh", "status": "ok", "checked_at": CHECKED}]}
    before = copy.deepcopy(state)
    payload = build_public_payload(state, now=NOW, max_items_per_source=1)
    assert [item["id"] for item in payload["tool_items"]] == [first["id"]]
    assert "recommendation_groups" in payload, "public project shortlists are missing"
    shortlist = payload["recommendation_groups"]["hearth-pos"]["shortlist"]
    assert [item["id"] for item in shortlist] == [TDD]
    assert "evidence" not in shortlist[0], "raw evaluation evidence must never reach public renderer"
    assert "PRIVATE_" not in str(payload) and "localhost" not in str(payload)
    assert "Eli-Lain-Ai-Tracker" not in str(payload)
    assert payload["recommendation_coverage"] == {"reviewed_count": 1, "discovery_count": 2,
        "inventory_count": 2, "shortlist_limit_per_project": 4, "exported_count": 1,
        "max_items_per_source": 1, "inventory_replaced": False}
    assert state == before
    soup = BeautifulSoup(LainReporter().render(**payload), "html.parser")
    assert "Decimal totals" in soup.select_one("#project-shortlists").text
    assert len(soup.select("#discoveries .discovery-item")) == 1
    for anchor in soup.select("#project-shortlists a[href]"):
        assert anchor["href"].startswith("https://skills.sh/") or anchor["href"].startswith("https://github.com/")
    for entry in payload["recommendation_groups"]["hearth-pos"]["shortlist"]:
        assert set(entry) >= {"id", "reason", "constraints", "next_validation", "freshness", "confidence",
                              "license", "cost", "support", "source_urls"}
        assert "evidence" not in entry and "summary" not in entry


def test_real_saved_inventory_renders_advisory_shortlists_in_internal_and_public_chromium(tmp_path):
    import json
    import os
    from collections import Counter
    from playwright.sync_api import sync_playwright
    from intel_sources.public_report import build_public_payload
    from intel_sources.recommendations import evaluate_projects
    root = Path(__file__).resolve().parents[1]
    state = json.loads((root / "data/intel_state.json").read_text(encoding="utf-8"))
    evaluated = evaluate_projects(state["items"], now=NOW)
    groups = evaluated["groups"]
    coverage = {**evaluated["coverage"], "inventory_count": evaluated["inventory_count"],
        "reviewed_count": len({entry["id"] for group in groups.values()
                               for category in ("shortlist", "deferred", "excluded")
                               for entry in group[category]})}
    internal = tmp_path / "internal" / "report.html"
    LainReporter().save(internal, api_items=[], tool_items=state["items"], report_date="2026-10-01",
        generated_at="12:00 UTC", runtime_source="Local verification render from saved inventory",
        recommendation_groups=groups, recommendation_coverage=coverage)
    payload = build_public_payload(state, now=NOW, max_items_per_source=25)
    public = tmp_path / "public" / "index.html"
    public.parent.mkdir()
    public.write_text(LainReporter().render(**payload), encoding="utf-8")
    shortlists = {project: len(group["shortlist"]) for project, group in groups.items()}
    assert sum(shortlists.values()) > 0, "real inventory produced no reviewed shortlist candidates"
    assert shortlists["fruit-slicer"] > 0, "fruit-slicer shortlist is empty from real saved data"
    assert coverage["reviewed_count"] > 0 and coverage["discovery_count"] > 100
    assert payload["recommendation_coverage"]["discovery_count"] > payload["recommendation_coverage"]["exported_count"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=os.environ.get("PLAYWRIGHT_EXECUTABLE_PATH"))
        try:
            for path, exported, expected in ((internal, len(state["items"]), coverage["reviewed_count"]),
                                             (public, len(payload["tool_items"]), payload["recommendation_coverage"]["reviewed_count"])):
                context = browser.new_context(viewport={"width": 1440, "height": 900}, offline=True)
                page = context.new_page()
                requests, errors = [], []
                page.on("request", lambda request: requests.append(request.url))
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(path.as_uri(), wait_until="load")
                assert page.locator("#discoveries .discovery-item:visible").count() == exported
                assert page.locator("#project-shortlists .project-group").count() == 4
                assert page.locator("#recommendation-coverage").text_content().startswith(f"{expected} reviewed / ")
                cards = page.locator("#project-shortlists .recommendation-item")
                assert cards.count() > 0
                assert cards.first.get_attribute("data-id")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                assert requests == [path.as_uri()] and not errors
                if exported != len(state["items"]):
                    assert "PRIVATE" not in page.locator("body").inner_text()
                context.close()
        finally:
            browser.close()


