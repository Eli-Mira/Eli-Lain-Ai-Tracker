# Delivery continuity follow-up — October 1, 2026

## Status

**Local regression gate PASS; integrated release OPEN.** These changes are not yet committed/pushed or exercised by a new hosted CI run. Historical live attachment verification remains run `36820991710` at commit `dae3eba33a504c63894e858a6ea62a9f107a164d`; it does not verify these new continuity fixes.

## Independently reproduced defects and fixes

1. **Confirmed sibling lost on channel failure.** A realistic multipart protocol run confirmed Telegram and rejected Discord with HTTP403. A fresh invocation sent Telegram again because receipts were saved only after both channels succeeded. RED assertion expected `previously-confirmed` and got `receipt-confirmed`. Receipts now preserve confirmed channels even on a failed fan-out; an explicit later run only attempts its unconfirmed sibling. No side-effect request is automatically retried inside one invocation.
2. **Destination change reused someone else's confirmation.** After one successful run, changing only the Telegram chat produced `previously-confirmed` for a destination that had received nothing. RED→GREEN: each channel confirmation is now bound to SHA256(site ID, bot credential, destination ID). No raw credentials or destination IDs are stored. Changing one destination invalidates that channel only. Legacy unbound receipts are readable but cannot suppress a send.
3. **Corrupt state caused new sends or late failure.** Four RED cases: invalid JSON, list instead of artifacts mapping, a scalar artifact record, and a list instead of message ID. Invalid state is now rejected with `invalid_receipt_state` before any external request, preserving original bytes. Unreadable state reports `receipt_state_unreadable`. Reads are bounded to 1MiB. Missing state remains an honest first-run baseline.
4. **CI discarded confirmed receipts when a sibling failed.** The old `actions/cache@v4` declares `post-if: success()`, so a failed publish would discard the very receipts needed for restart. Its `save-always` input is explicitly deprecated as not working as intended. Replaced with separate `actions/cache/restore@v4` and final `actions/cache/save@v4`, guarded by `always()` and trusted step outcomes. It saves after a started refresh even when publish fails; it does not save merely because earlier setup/tests failed. Restore and save enumerate exactly the same eight runtime files. Existing tests now recognize explicit restore actions instead of requiring the combined action name.

Primary action definitions retrieved with credential-free HTTP GETs on October 1, 2026:
- `https://raw.githubusercontent.com/actions/cache/v4/action.yml` — `save-always` is explicitly deprecated and `post-if` is `success()`.
- `https://raw.githubusercontent.com/actions/cache/v4/save/action.yml` — standalone save-only entry point.

## Commands and actual output

Run from `C:/tmp/eli-lain-tracker`; all pytest temp directories are under Hermes scratch.

```bash
NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_release_delivery_continuity.py -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/receipt-red-1'
# RED: 1 failed; confirmed Telegram repeated after Discord failure.

NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_release_delivery_continuity.py::test_changed_telegram_destination_does_not_reuse_old_confirmation -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/receipt-red-2'
# RED: 1 failed; new destination incorrectly previously-confirmed.

NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_release_delivery_continuity.py -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/receipt-red-3' --tb=short
# RED: 4 failed, 2 passed; malformed receipt-state variants.

NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_release_delivery_continuity.py::test_workflow_preserves_confirmed_receipts_even_if_publish_fails -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/receipt-red-4' --tb=short
# RED: 1 failed; success-only cache.

NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_release_delivery_continuity.py tests/test_report_delivery.py tests/test_release_delivery_audit.py tests/test_intel_workflow.py -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/receipt-green-4'
# GREEN: 51 passed in 1.73s, exit0.

git diff --check -- src/intel_sources/report_delivery.py tests/test_release_delivery_continuity.py tests/test_intel_workflow.py tests/test_release_delivery_audit.py .github/workflows/news-tracker-daily.yml
# exit0; only a Git LF/CRLF advisory, no whitespace error.
```

## Still not claimed

- Dedupe is **exact-byte** only. A regenerated artifact whose render timestamp changes has a different SHA256 and is announced. No-material-change semantic dedupe is not closed; changing its policy must not falsely claim newly rendered bytes were sent when only an older file was delivered.
- A successful HTTP request whose response is lost is ambiguous, not confirmed. Exactly-once delivery under network loss is not established, and a rerun can duplicate such an ambiguous send.
- Telegram text and document form one channel operation; a confirmed text followed by failed document can repeat the brief on rerun. Only full attachment confirmation suppresses that channel.
- Fixed temporary-file name and no concurrent-process lock remain limitations for simultaneous local publishers. Workflow concurrency serializes hosted runs, not arbitrary CLI invocations. Unique tempfiles/fsync/locking and write-failure injection still need acceptance evidence.
- No new actual Telegram/Discord messages, hosting writes, paid inference, credentials changes, previous blocked download retry, commit or push in this follow-up.
- Full shared-suite and clean-state CI are deferred until four source/usefulness workers finish; their files may currently be in a RED→GREEN cycle.

## Files changed by parent

- `src/intel_sources/report_delivery.py`
- `.github/workflows/news-tracker-daily.yml`
- `tests/test_release_delivery_continuity.py` (new)
- `tests/test_intel_workflow.py`
- `tests/test_release_delivery_audit.py`
- `docs/RELEASE_ACCEPTANCE.md`, this document, and Obsidian handoff.
