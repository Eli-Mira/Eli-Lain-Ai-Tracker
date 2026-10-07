"""Tests for the daily automation module."""
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path('C:/tmp/eli-lain-tracker/src')))

from intel_sources import settings
from intel_sources.daily_automation import run_daily, _intended_cairo_slot


def test_default_settings_load():
    s = settings.default_settings()
    assert s['schema_version'] == 1
    assert s['schedule']['timezone'] == 'Africa/Cairo'
    assert s['schedule']['hour'] == 10
    assert s['schedule']['minute'] == 0
    assert len(s['sources']) >= 1


def test_intended_slot_does_not_drop_late_job():
    sched = {'hour': 10, 'minute': 0}
    # 11:30 UTC approximates late run
    now = datetime(2026, 10, 7, 11, 30, tzinfo=timezone.utc)
    slot = _intended_cairo_slot(now, sched)
    # Slot should be today at 10:00, not tomorrow or dropped
    assert slot.hour == 10
    assert slot.minute == 0
    # Ensure we still return a slot even though it's late
    delta = now - slot
    assert delta.total_seconds() > 0


def test_run_daily_creates_artifacts(tmp_path_factory):
    # Use a temporary data dir
    data_dir = Path(tmp_path_factory.mktemp('daily'))
    async def _run():
        res = await run_daily(settings_path=None, data_dir=data_dir)
        return res
    res = asyncio.run(_run())
    assert res['report_date'] is not None
    assert Path(res['public_path']).exists()
    assert Path(res['evidence_path']).exists()
    assert res['counts']['fetched'] >= 0
    # History file exists
    hist = data_dir / 'daily_state' / 'history.jsonl'
    assert hist.exists()
    # Delayed flag is bool
    assert isinstance(res['delayed_start'], bool)


def test_link_verification_shape():
    from intel_sources.daily_sources import fetch_candidates, verify_candidates
    cfg = settings.default_settings()
    fetched = asyncio.run(fetch_candidates(cfg))
    verified = asyncio.run(verify_candidates(fetched['candidates'], cfg))
    for cand in verified:
        lv = cand.get('link_verification', {})
        assert 'status' in lv
        assert 'checked_at' in lv
        assert 'url' in lv
        assert 'http_status' in lv
