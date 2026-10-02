"""Receipt-state durability: a lost write must mean a duplicate announcement.

`save_receipts` records that an artifact was delivered so an identical artifact
is not announced twice. Two ways that record can be lost, both of which silently
re-open the door to a duplicate customer message:

  * concurrency: the read-modify-write has no lock, so two runs racing each
    other each write a snapshot taken before the other's record existed, and one
    record is clobbered;
  * durability: `os.replace` is atomic but the temp file and the directory entry
    were never fsynced, so a crash (or a CI runner being torn down) can leave the
    receipt file empty or truncated, which then fails to load.
"""
import builtins
import json
import threading
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from intel_sources import report_delivery as rd
from intel_sources.report_delivery import DeliveryConfig, DeliveryResult


def _config(**overrides):
    base = dict(TELEGRAM_BOT_TOKEN="t-token", TELEGRAM_CHAT_ID="123456",
                DISCORD_BOT_TOKEN="d-token", DISCORD_CHANNEL_ID="123456789012345678",
                PUBLIC_REPORT_URL=rd.PAGES_PUBLIC_URL)
    base.update(overrides)
    return DeliveryConfig.from_env(base)


def _result(url=None):
    return DeliveryResult(
        hosted=rd.HostedReport(url=url or rd.PAGES_PUBLIC_URL, sha256="a" * 64, deploy_id="d1"),
        brief="brief",
        telegram=rd.ChannelReceipt("telegram", "123456/111", "receipt-confirmed", ""),
        discord=rd.ChannelReceipt("discord", "123456789012345678", "independently-read-back", ""),
    )


def _artifact(sha):
    return rd.ReportArtifact(data=b"<html></html>", sha1="a" * 40, sha256=sha,
                             rendered_at="2026-10-02T00:00:00+00:00",
                             observations=(), source_counts=())


def test_concurrent_writers_do_not_clobber_each_others_receipt(tmp_path):
    """Real threads, real racing writes. Every record must survive.

    A previous version of this test monkeypatched the loader to hand back a
    stale snapshot, which passed even with the lock deleted - it asserted the
    mock, not the behaviour. This one starts genuine threads that all read and
    write the same file with no artificial delay, so a lockless
    read-modify-write really does lose records.
    """
    state = tmp_path / "receipts.json"
    # Only hex digests: load_receipts rejects any non-hex digest key, and a
    # non-hex key here would fail the validator for an unrelated reason.
    hex_alphabet = "0123456789abcdef"
    digests = [hex_alphabet[i // 4] * 64 for i in range(12)]
    barrier = threading.Barrier(len(digests))

    def writer(digest):
        barrier.wait()  # maximize the overlap window
        rd.save_receipts(state, _artifact(digest), _result(), _config())

    errors = []

    def guarded(digest):
        try:
            writer(digest)
        except BaseException as exc:  # noqa: BLE001 - reported, not swallowed
            errors.append(exc)

    threads = [threading.Thread(target=guarded, args=(d,)) for d in digests]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not any(t.is_alive() for t in threads), "a writer deadlocked on the lock"
    assert not errors, f"writers failed: {errors!r}"

    saved = rd.load_receipts(state)
    missing = [d[:8] for d in digests if d not in saved]
    assert not missing, f"lost receipts would re-announce already delivered reports: {missing}"
    assert not list(tmp_path.glob("*.lock")), "lock file leaked"


def test_lock_is_released_even_when_the_write_fails(tmp_path, monkeypatch):
    """A crashed write must not wedge every later run on the lock file."""
    state = tmp_path / "receipts.json"
    rd.save_receipts(state, _artifact("a" * 64), _result(), _config())

    real_open = builtins.open

    def exploding_open(*args, **kwargs):
        path = str(args[0])
        if path.endswith(".tmp") or (args[1] if len(args) > 1 else kwargs.get("mode", "r")) not in ("r", "rb"):
            raise OSError("disk full")
        return real_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", exploding_open)
    with pytest.raises(OSError):
        rd.save_receipts(state, _artifact("d" * 64), _result(), _config())
    monkeypatch.undo()

    assert not list(tmp_path.glob("*.lock")), "lock file leaked after a failed write"
    assert not list(tmp_path.glob("*.tmp")), "temp file leaked after a failed write"
    rd.save_receipts(state, _artifact("e" * 64), _result(), _config())
    assert "e" * 64 in rd.load_receipts(state)


def test_receipt_is_fsynced_before_the_atomic_rename(tmp_path, monkeypatch):
    """A rename that was never fsynced can be lost on crash."""
    state = tmp_path / "receipts.json"
    synced = []
    real_replace, real_fsync = os.replace, os.fsync

    def spy_fsync(fd):
        synced.append(Path(state.name) if False else fd)
        return real_fsync(fd)

    monkeypatch.setattr(rd.os, "fsync", spy_fsync)
    rd.save_receipts(state, _artifact("a" * 64), _result(), _config())
    monkeypatch.undo()
    assert synced, "no fsync: a crash could lose the receipt and cause a duplicate send"


def test_truncated_receipt_file_is_refused_rather_than_resending(tmp_path):
    """A corrupt state file must fail closed, not read as 'nothing sent'."""
    state = tmp_path / "receipts.json"
    state.write_text('{"artifacts": {"a": ', encoding="utf-8")
    with pytest.raises(rd.DeliveryError) as excinfo:
        rd.load_receipts(state)
    assert excinfo.value.code == "invalid_receipt_state"


def test_empty_receipt_file_is_refused(tmp_path):
    state = tmp_path / "receipts.json"
    state.write_bytes(b"")
    with pytest.raises(rd.DeliveryError) as excinfo:
        rd.load_receipts(state)
    assert excinfo.value.code == "invalid_receipt_state"


def test_missing_state_file_is_the_only_silent_empty_case(tmp_path):
    assert rd.load_receipts(tmp_path / "absent.json") == {}
