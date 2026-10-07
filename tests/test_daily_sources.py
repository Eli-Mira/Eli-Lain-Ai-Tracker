"""TDD tests for daily_sources: fetch_candidates and verify_candidates."""
import pytest
from datetime import datetime, timezone, timedelta
from src.intel_sources.settings import default_settings


def test_fetch_candidates_returns_structure():
    from src.intel_sources.daily_sources import fetch_candidates
    import asyncio
    settings = default_settings()
    result = asyncio.run(fetch_candidates(settings))
    assert isinstance(result, dict)
    assert 'candidates' in result
    assert 'sources' in result
    assert isinstance(result['candidates'], list)
    assert isinstance(result['sources'], list)


def test_fetch_candidates_skips_disabled_sources():
    from src.intel_sources.daily_sources import fetch_candidates
    import asyncio
    settings = default_settings()
    # Ensure sources exist for test
    settings['sources'] = [{'id': 'test-src', 'name': 'Test', 'adapter': 'catalog', 'enabled': False}]
    result = asyncio.run(fetch_candidates(settings))
    source_ids = {s['id'] for s in result['sources']}
    assert 'test-src' in source_ids
    statuses = [s.get('status') for s in result['sources']]
    assert 'skipped' in statuses


def test_verify_candidates_adds_verification_fields():
    from src.intel_sources.daily_sources import verify_candidates
    import asyncio
    candidates = [
        {
            'id': 'test:1',
            'name': 'Test Item',
            'what': 'desc',
            'category': 'models',
            'source_id': 'openrouter-models',
            'source_url': 'https://openrouter.ai/models',
            'published_at': None,
            'date_kind': 'unknown',
            'observed_at': datetime.now(timezone.utc).isoformat(),
            'free': {'status': 'unknown', 'detail': '', 'evidence_url': None},
            'api': {'status': 'unknown', 'detail': '', 'evidence_url': None},
            'topics': []
        }
    ]
    settings = default_settings()
    result = asyncio.run(verify_candidates(candidates, settings))
    assert len(result) == 1
    assert 'link_verification' in result[0]
    assert 'status' in result[0]['link_verification']
