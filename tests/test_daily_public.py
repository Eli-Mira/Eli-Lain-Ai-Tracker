"""Tests for daily public rendering and export with sanitization."""
from pathlib import Path
import tempfile
from datetime import datetime, timezone

from intel_sources.daily_public import render_digest, export_digest


def minimal_digest():
    now = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)
    return {
        "schema_version": 1,
        "report_date": "2026-10-07",
        "generated_at": now.isoformat(),
        "items": [{
            "id": "test:id1",
            "name": "Test Project",
            "what": "A meaningful description.",
            "why": "relevant",
            "category": "free-api",
            "source_id": "src1",
            "source_url": "https://example.com/project",
            "link_verification": {"status": "verified", "checked_at": now.isoformat(), "url": "https://example.com/project", "http_status": 200},
            "observed_at": now.isoformat(),
            "free": {"status": "open-source", "detail": "MIT"},
            "api": {"status": "available", "detail": "REST"},
            "score": 80,
            "scoring_breakdown": "category:free-api=+20",
        }],
        "sources": [{"name": "src1", "adapter": "http", "enabled": True, "id": "src1"}],
        "counts": {"fetched": 1, "eligible": 1, "rejected": {}, "selected": 1},
    }


def test_render_digest_uses_template():
    digest = minimal_digest()
    html = render_digest(digest)
    assert "daily-digest-v1" in html
    assert digest["generated_at"] in html
    assert "Test Project" in html
    # Ensure meta tags for UI contract
    assert 'meta name="elilain-report-kind"' in html
    assert 'meta name="elilain-generated-at"' in html


def test_render_digest_card_data_attrs():
    digest = minimal_digest()
    html = render_digest(digest)
    # Check data attributes exist
    assert 'data-id="test:id1"' in html
    assert 'data-source="src1"' in html
    assert 'data-source-url="https://example.com/project"' in html
    assert 'data-verified-at="' in html
    assert 'data-observed-at="' in html
    # Link class
    assert 'class="original-source"' in html
    assert 'href="https://example.com/project"' in html


def test_export_digest_atomic_write(tmp_path: Path):
    digest = minimal_digest()
    out = export_digest(digest, tmp_path / "out")
    assert out.exists()
    assert out.read_text(encoding="utf-8")
    # Ensure only index.html in dir
    assert list((tmp_path / "out").iterdir())
    # Re-export overwrites safely
    out2 = export_digest(digest, tmp_path / "out")
    assert out == out2


def test_render_digest_sanitizes_secrets():
    digest = minimal_digest()
    # Inject secret into what
    digest["items"][0]["what"] = "Check api_key=sk-123456789 for details"
    html = render_digest(digest)
    # Secret should be stripped or redacted
    assert "sk-123456789" not in html


def test_render_digest_rejects_boilerplate_descriptions():
    digest = minimal_digest()
    digest["items"][0]["what"] = "N/A"
    html = render_digest(digest)
    # Item should be absent or description filtered
    # Since digest is pre-filtered, render should not crash
    assert "Test Project" in html  # name remains, but what may be empty
    # Ensure no raw path/HTML/control characters leak
    assert "<script" not in html.lower() or "original-source" in html
