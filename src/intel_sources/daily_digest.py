"""Daily digest builder with strict gates.

Implements the digest shape required by the contract and exposes helpers for
scoring and selection.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def build_digest(collection: dict[str, Any], settings: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Build a daily digest from verified candidates.

    The contract requires:
      {schema_version, report_date, generated_at, items, sources, counts}
    """
    now = now or datetime.now(timezone.utc)
    candidates = collection.get('candidates', [])
    sources_info = collection.get('sources', [])

    # Basic gates
    eligible = []
    rejected = []
    categories_allowed = set(settings.get('categories', []))
    max_age_days = settings.get('max_age_days', 7)
    min_score = settings.get('min_score', 60)

    for cand in candidates:
        reason = None
        # Category gate
        if cand.get('category') not in categories_allowed:
            reason = 'unsupported category'
        else:
            # Date kind must be actual, not observed only
            date_kind = cand.get('date_kind')
            if date_kind == 'unknown':
                reason = 'observed only date'
            else:
                # Link verification gate
                lv = cand.get('link_verification', {})
                if lv.get('status') != 'verified':
                    reason = 'link not verified'
                else:
                    # Age gate
                    published = _parse_iso(cand.get('published_at'))
                    if published:
                        age_days = (now - published).days
                        if age_days < 0:
                            reason = 'future date'
                        elif age_days > max_age_days:
                            reason = 'too old'
                    elif not published:
                        reason = 'missing published_at'
                    # Description non-empty and not boilerplate
                    what = cand.get('what') or ''
                    if not what.strip() or len(what.strip()) < 20:
                        reason = 'empty description'
                    else:
                        # Secret detection in free/api fields
                        free_detail = (cand.get('free') or {}).get('detail', '')
                        api_detail = (cand.get('api') or {}).get('detail', '')
                        if 'api_key' in free_detail.lower() or 'sk-' in free_detail or 'api_key' in api_detail.lower() or 'sk-' in api_detail:
                            reason = 'secret evidence'
        if reason:
            rejected.append({'id': cand.get('id'), 'reason': reason})
        else:
            eligible.append(cand)

    # Score items (simple heuristic for now)
    def score_item(cand: dict[str, Any]) -> int:
        score = 60
        if cand.get('free', {}).get('status') in ('open-source', 'free-tier'):
            score += 10
        if cand.get('api', {}).get('status') == 'available':
            score += 10
        if cand.get('topics'):
            score += 5
        return min(score, 100)

    scored = []
    seen_ids = set()
    for cand in eligible:
        s = score_item(cand)
        if s >= min_score:
            # Project to six-field digest shape
            projected = {
                "id": cand.get("id"),
                "name": cand.get("name"),
                "what": cand.get("what"),
                "why": cand.get("why", "relevant"),
                "category": cand.get("category"),
                "source_id": cand.get("source_id"),
                "source_url": cand.get("source_url"),
                "link_verification": cand.get("link_verification", {}),
                "observed_at": cand.get("observed_at"),
                "free": cand.get("free", {}),
                "api": cand.get("api", {}),
            }
            projected["score"] = s
            breakdown = {'base': 60, 'free_bonus': 10 if cand.get('free', {}).get('status') in ('open-source', 'free-tier') else 0, 'api_bonus': 10 if cand.get('api', {}).get('status') == 'available' else 0}
            projected['scoring_breakdown'] = str(breakdown)
            # Identity-safe dedup by exact id+source_url
            ident_key = f"{projected.get('id')}|{projected.get('source_url')}"
            if ident_key in seen_ids:
                rejected.append({'id': projected.get('id'), 'reason': 'duplicate identity'})
                continue
            seen_ids.add(ident_key)
            scored.append(projected)
        else:
            rejected.append({'id': cand.get('id'), 'reason': 'score below threshold'})

    # Selection limit
    max_items = settings.get('max_items', 5)
    selected = scored[:max_items]

    counts = {
        'fetched': len(candidates),
        'eligible': len(eligible),
        'rejected': len(rejected),
        'selected': len(selected),
    }

    report_date = now.date().isoformat()
    digest = {
        'schema_version': 1,
        'report_date': report_date,
        'generated_at': now.isoformat(),
        'items': selected,
        'sources': sources_info,
        'counts': counts,
    }
    logger.info(f"Digest built: {counts}")
    return digest


def render_digest(digest: dict[str, Any]) -> str:
    """Render digest to HTML using the daily_digest template.

    Uses Jinja2 to render src/templates/daily_digest.html with strict public projection.
    """
    from pathlib import Path
    from jinja2 import Template
    import re

    template_path = Path(__file__).parent.parent / 'templates' / 'daily_digest.html'
    if not template_path.exists():
        raise ValueError('daily digest template not found')
    
    template_source = template_path.read_text(encoding='utf-8')
    tmpl = Template(template_source)
    
    # Sanitize helper
    _secret_pattern = re.compile(r'(?i)(api[_-]?key|sk-[A-Za-z0-9_-]{6,}|gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}|bearer\s+[A-Za-z0-9._~+/=-]{12,}|password\s*[=:]?\s*\S+)')
    _path_pattern = re.compile(r'([a-zA-Z]:[/\\]|[/~].*[/~]|(/home/|/tmp/|/var/|/etc/))')
    _html_control = re.compile(r'[<>`\"\'&=]')
    
    def sanitize_text(value):
        if not isinstance(value, str):
            return ''
        # Reject paths
        if _path_pattern.search(value):
            return ''
        # Strip secrets
        value = _secret_pattern.sub('[REDACTED]', value)
        # Reject HTML/control chars
        if _html_control.search(value):
            # Strip tags and control chars
            value = re.sub(r'<[^>]+>', '', value)
            value = ''.join(c for c in value if ord(c) >= 32 or c == '\n')
        # Trim boilerplate
        v = value.strip()
        if len(v) < 5:
            return ''
        return v
    
    # Sanitize digest items in-place making explicit projection
    items = digest.get('items', [])
    sanitized_items = []
    for it in items:
        if not isinstance(it, dict):
            continue
        # Only allow six-field digest + metadata
        safe = {
            'id': str(it.get('id', '')) if isinstance(it.get('id'), (str, int)) else '',
            'name': sanitize_text(str(it.get('name', ''))),
            'what': sanitize_text(str(it.get('what', ''))),
            'why': sanitize_text(str(it.get('why', ''))),
            'category': str(it.get('category', '')),
            'source_id': str(it.get('source_id', '')),
            'source_url': str(it.get('source_url', '')),
            'link_verification': it.get('link_verification', {}),
            'observed_at': str(it.get('observed_at', '')),
            'free': {
                'status': str(it.get('free', {}).get('status', '')),
                'detail': sanitize_text(str(it.get('free', {}).get('detail', '')))
            },
            'api': {
                'status': str(it.get('api', {}).get('status', '')),
                'detail': sanitize_text(str(it.get('api', {}).get('detail', '')))
            },
            'score': it.get('score'),
            'scoring_breakdown': sanitize_text(str(it.get('scoring_breakdown', '')))
        }
        sanitized_items.append(safe)
    
    # Build sanitized digest copy
    safe_digest = dict(digest)
    safe_digest['items'] = sanitized_items
    safe_digest['sources'] = digest.get('sources', [])
    safe_digest['report_date'] = sanitize_text(str(digest.get('report_date', '')))
    safe_digest['generated_at'] = sanitize_text(str(digest.get('generated_at', '')))
    
    # Wrapper to avoid dict.items method collision in Jinja
    class _DictWrapper:
        def __init__(self, d): self._d = d
        def __getattr__(self, name):
            if name in self._d:
                return self._d[name]
            raise AttributeError(name)
        def __getitem__(self, key):
            return self._d[key]
    
    # Build render context with explicit projection, no raw dict leakage
    history = {"reports": []}
    render_context = {
        "digest": _DictWrapper(safe_digest),
        "history": _DictWrapper(history)
    }
    
    html = tmpl.render(**render_context)
    return html
