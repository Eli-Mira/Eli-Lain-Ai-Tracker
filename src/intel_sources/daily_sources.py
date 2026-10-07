"""Daily source fetching and link verification.

Each source listed in settings is queried asynchronously; results can be
replayed from cache in offline/CI conditions.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourceStatus:
    source_id: str
    status: str
    checked_at: str
    returned: int = 0
    accepted: int = 0
    error_code: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_aware() -> datetime:
    return datetime.now(timezone.utc)


def _build_candidate(raw: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw source record into the contract shape."""
    return {
        'id': raw.get('id', ''),
        'name': raw.get('name', ''),
        'what': raw.get('what', ''),
        'category': raw.get('category', ''),
        'source_id': source.get('id', ''),
        'source_url': raw.get('url', ''),
        'published_at': raw.get('published_at'),
        'date_kind': raw.get('date_kind', 'unknown'),
        'observed_at': raw.get('observed_at', _now_iso()),
        'free': raw.get('free', {'status': 'unknown', 'detail': '', 'evidence_url': ''}),
        'api': raw.get('api', {'status': 'unknown', 'detail': '', 'evidence_url': ''}),
        'topics': raw.get('topics', []),
    }


async def fetch_candidates(settings: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Return mock candidates for now with enforced status bookkeeping.

    Real implementation would query the sources described in settings. This
    version returns a deterministic shape for tests and keeps the contract.
    """
    sources_cfg = settings.get('sources', [])
    statuses: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    now = now or _now_aware()
    now_iso = now.isoformat()

    # Build deterministic mock data keyed by first enabled source
    enabled = [s for s in sources_cfg if s.get('enabled')]
    # Always process skipped sources even if no enabled
    skipped = [s for s in sources_cfg if not s.get('enabled')]
    if not enabled and not skipped:
        return {'candidates': [], 'sources': [{'id': 'no sources', 'name': 'no sources', 'status': 'skipped', 'checked_at': now_iso, 'returned': 0, 'accepted': 0}]}

    # Produce two mock candidates matching contract fields
    mock_raw = [
        {
            'id': 'demo-1',
            'name': 'Demo free API launch',
            'what': 'A new free tier API for model inference',
            'category': 'free-api',
            'url': 'https://example.com/demo',
            'published_at': now.isoformat(),
            'date_kind': 'release',
            'observed_at': now_iso,
            'free': {'status': 'open-source', 'detail': 'MIT', 'evidence_url': 'https://example.com/license'},
            'api': {'status': 'available', 'detail': 'REST', 'evidence_url': 'https://example.com/api'},
            'topics': ['free-api'],
        },
        {
            'id': 'demo-2',
            'name': 'Open skill catalog update',
            'what': 'A public catalog of skills with free tier',
            'category': 'skills',
            'url': 'https://example.com/skill',
            'published_at': now.isoformat(),
            'date_kind': 'catalog-created',
            'observed_at': now_iso,
            'free': {'status': 'free-tier', 'detail': 'limited', 'evidence_url': ''},
            'api': {'status': 'none', 'detail': 'no API', 'evidence_url': ''},
            'topics': ['skills'],
        },
    ]

    for src in enabled:
        status = SourceStatus(source_id=src.get('id', ''), status='ok', checked_at=now_iso)
        try:
            await asyncio.sleep(0)
            cand_set = [_build_candidate(r, src) for r in mock_raw]
            candidates.extend(cand_set)
            status.returned = len(cand_set)
            status.accepted = len(cand_set)
        except Exception as exc:
            logger.warning(f"Source {src.get('id')} failed: {exc}")
            status.status = 'error'
            status.error_code = 'fetch_error'
        statuses.append({
            'id': status.source_id,
            'name': src.get('name', status.source_id),
            'status': status.status,
            'checked_at': status.checked_at,
            'returned': status.returned,
            'accepted': status.accepted,
            'error_code': status.error_code,
        })

    # Always include a skipped source for contract completeness
    skipped_sources = [s for s in sources_cfg if not s.get('enabled')]
    for s in skipped_sources:
        statuses.append({
            'id': s.get('id'),
            'name': s.get('name', s.get('id')),
            'status': 'skipped',
            'checked_at': now_iso,
            'returned': 0,
            'accepted': 0,
            'error_code': None,
        })

    return {'candidates': candidates, 'sources': statuses}


async def verify_candidates(candidates: list[dict[str, Any]], settings: dict[str, Any], now: datetime | None = None) -> list[dict[str, Any]]:
    """Attach link_verification to each candidate using safe mock verification.

    The contract requires fields status/checked_at/url/http_status. This
    implementation uses http_status=200 for the demo URLs.
    """
    now = now or _now_aware()
    now_iso = now.isoformat()
    verified = []
    for cand in candidates:
        url = cand.get('source_url', '')
        verification = {'status': 'verified', 'checked_at': now_iso, 'url': url, 'http_status': 200}
        # Mock failure for non-example domains
        if not url.startswith('https://example.com/'):
            verification = {'status': 'unverified', 'checked_at': now_iso, 'url': url, 'http_status': None}
        out = dict(cand)
        out['link_verification'] = verification
        verified.append(out)
    return verified
