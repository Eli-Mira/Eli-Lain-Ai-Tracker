"""Daily public export helpers.

Produces a file on disk suitable for serving; atomic writes and safety checks
are kept minimal but sufficient for tests.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from .daily_digest import render_digest

logger = logging.getLogger(__name__)


def export_digest(digest: dict[str, Any], export_dir: str | Path) -> Path:
    """Render digest to a standalone HTML file in export_dir.

    The file is written atomically; a temporary file is renamed into place.
    """
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    html = render_digest(digest)
    target = export_dir / 'index.html'
    temporary = target.with_suffix('.tmp')
    try:
        temporary.write_text(html, encoding='utf-8')
        temporary.replace(target)
    except Exception as exc:
        logger.error(f"Export failed: {exc}")
        raise
    logger.info(f"Exported digest to {target}")
    return target


def export_state(state: dict[str, Any], export_dir: str | Path) -> Path:
    """Write private raw evidence JSON for debugging/local use."""
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    target = export_dir / 'digest_state.json'
    temporary = target.with_suffix('.tmp')
    try:
        temporary.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
        temporary.replace(target)
    except Exception as exc:
        logger.error(f"State export failed: {exc}")
        raise
    return target
