"""Tests for daily digest selection with strict gates and explainable scoring."""
from datetime import datetime, timezone, timedelta
import pytest

from intel_sources.daily_digest import build_digest


NOW = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)


def settings():
    return {
        "schema_version": 1,
        "sources": [],
        "categories": ["free-api", "models", "agents", "mcp", "skills", "devtools", "news"],
        "max_items": 5,
        "max_age_days": 7,
        "min_score": 60,
        "priorities": {"free-api": 5, "models": 4, "agents": 3, "mcp": 2, "skills": 2, "devtools": 1, "news": 1},
    }


def candidate(base=None):
    base = base or {}
    return {
        "id": "test:id1",
        "name": "Test Project",
        "what": "A meaningful description of the project with enough detail to be useful to the user.",
        "category": "free-api",
        "source_id": "src1",
        "source_url": "https://example.com/project",
        "published_at": (NOW - timedelta(days=2)).isoformat(),
        "date_kind": "release",
        "observed_at": NOW.isoformat(),
        "free": {"status": "open-source", "detail": "MIT", "evidence_url": "https://example.com/license"},
        "api": {"status": "available", "detail": "REST", "evidence_url": "https://example.com/api"},
        "topics": ["free-api"],
        "link_verification": {"status": "verified", "checked_at": NOW.isoformat(), "url": "https://example.com/project", "http_status": 200},
        **base,
    }


def collection(candidates):
    return {"candidates": candidates, "sources": []}


def test_gates_reject_unverified_link():
    cand = candidate({"link_verification": {"status": "unverified", "checked_at": NOW.isoformat(), "url": "https://example.com/project", "http_status": None}})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0
    assert digest["counts"]["fetched"] == 1


def test_gates_reject_stale_date():
    cand = candidate({"published_at": (NOW - timedelta(days=30)).isoformat()})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0


def test_gates_reject_future_date():
    cand = candidate({"published_at": (NOW + timedelta(days=1)).isoformat()})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0


def test_gates_reject_observed_only_date():
    cand = candidate({"published_at": None, "date_kind": "unknown", "observed_at": NOW.isoformat()})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0


def test_gates_reject_weak_description():
    cand = candidate({"what": "N/A"})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0


def test_gates_reject_secret_evidence():
    cand = candidate({"free": {"status": "open-source", "detail": "api_key=sk-123456", "evidence_url": "https://example.com"}})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0


def test_identity_safe_dedup_does_not_merge_distinct_owners():
    c1 = candidate({"id": "skill:owner1/proj", "source_url": "https://skills.sh/owner1/proj", "source_id": "skills"})
    c2 = candidate({"id": "skill:owner2/proj", "source_url": "https://skills.sh/owner2/proj", "source_id": "skills"})
    digest = build_digest(collection([c1, c2]), settings(), now=NOW)
    ids = [i["id"] for i in digest["items"]]
    assert len(ids) == 2
    assert c1["id"] in ids and c2["id"] in ids


def test_dedup_exact_identity():
    c1 = candidate({"id": "test:id1", "source_url": "https://example.com/project"})
    c2 = candidate({"id": "test:id1", "source_url": "https://example.com/project"})
    digest = build_digest(collection([c1, c2]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 1


def test_explainable_scoring_breakdown_present():
    cand = candidate()
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert len(digest["items"]) == 1
    item = digest["items"][0]
    assert "scoring_breakdown" in item
    assert isinstance(item["scoring_breakdown"], str)
    assert len(item["scoring_breakdown"]) > 0


def test_no_hard_minimum_items():
    # Only weak candidates, should select zero not pad to min
    cand = candidate({"what": "short"})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    assert digest["counts"]["selected"] == 0
    assert digest["items"] == []


def test_counts_consistency():
    c1 = candidate()
    c2 = candidate({"link_verification": {"status": "failed", "checked_at": NOW.isoformat(), "url": "", "http_status": 0}})
    c3 = candidate({"published_at": (NOW - timedelta(days=30)).isoformat()})
    digest = build_digest(collection([c1, c2, c3]), settings(), now=NOW)
    assert digest["counts"]["fetched"] == 3
    assert digest["counts"]["selected"] == 1


def test_raw_inventory_not_exposed():
    cand = candidate({"what": "Good description of the project with enough detail for evaluation.", "free": {"status": "open-source", "detail": "MIT", "evidence_url": "https://example.com/license"}})
    digest = build_digest(collection([cand]), settings(), now=NOW)
    item = digest["items"][0]
    # Ensure only six-field digest structure plus metadata
    for key in item:
        assert key in {"id", "name", "what", "why", "category", "source_id", "source_url", "link_verification", "observed_at", "free", "api", "score", "scoring_breakdown"}
