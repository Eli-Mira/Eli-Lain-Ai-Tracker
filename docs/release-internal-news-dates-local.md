# Internal news dates — local repair candidate (October 2, 2026)

Status: **V2 LOCAL GREEN (831 tests); renewed independent review and fresh CI verification pending. NOT release-approved.** V1 was review-blocked and is not approved. Its timezone-ambiguity correction is now independently read back and regression-tested by the parent; health rendering remains separate and open. Public news remains excluded.

## Confirmed boundary failure

The read-only audit `deleg_3acd0c7a` traced separate persisted `published_date` / `fetched_date` fields to their loss in `main.NewsTracker.generate_report` (previous `main.py:434-442`). The parent independently read the projection, renderer contract and both Lain template copies and parsed both supplied internal HTML artifacts from CI `36933189703`: each contained **444 news rows**, **zero news time elements**, and **zero dedicated news-date elements**. Existing source-health rendering receives discovery/catalog sources, not the already available news-feed health. This finding is about the supplied CI files, not a new remote latest-run lookup.

## RED → GREEN

`tests/test_release_news_dates.py::test_internal_news_retains_publication_and_saved_observation` exercised synthetic `NewsItem` rows through real SQLite persistence and the actual production report method. Before production edits it failed on the precise missing `.news-dates` element, not setup or a mocked renderer. Evidence: `news-dates-red.xml`, one failure / zero errors. The same regression passed after the repair (`news-dates-green.xml`).

The projection now retains both saved fields. The reporter registers a bounded timestamp filter, and both byte-identical Lain templates show separate **Publication (UTC)** and **Saved observation (UTC)** values using semantic `time` elements. Offset-aware publication time is displayed in UTC; absent, malformed or timezone-ambiguous publication time remains **unknown**. Only the SQLite fetched-date storage contract permits attaching UTC to an offsetless observation value. Invalid types, date-only strings, oversize values and UTC overflow are not echoed or guessed.

No schema/storage mutation or historical backfill was introduced. Generation is separately labelled; restarting and regenerating a report does not refresh the saved observation. Legacy caller rows lacking dates remain renderable with explicit unknown values. Reporter positional arguments are unchanged.

## V1 local verification (before the new timezone-ambiguity regressions)

- Focused news/public suite: **164 passed / exit 0** before the final four browser cases were added.
- Final full suite: **829 passed / zero failures, errors, skips or xfails**, **47.74 seconds / exit 0**. JUnit: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/news-dates-final.xml`.
- New tests cover real SQLite/report projection, unknown publication, type/format/offset/precision bounds, both template copies, public date canaries, restart/regeneration, and offline Chromium at **390px/1440px × JS on/off**. Those browser inputs are explicitly **synthetic fixtures**, not live observations; dates are visible, no horizontal overflow, one local file request and no page errors.
- Exact source comparison: every template byte outside the internal news section is unchanged against the pre-repair HEAD; the original header and locked style are untouched. Original style SHA256: `347adbd0fc894df1675f565ca9d93d591a320ac2b63934b0d7615fa3554e76b8`.
- Using the actual saved public input, a fixed render time and the production explicit `public_export=True` mode, old/new standalone public bytes are identical: **2,533,631 bytes**, SHA256 `7d36956149588484131f153659cc9a4c21fff07f4f02518d290306063332c39b`. This is a local controlled comparison, **not** the deployed 3,294,609-byte CI artifact. Receipt: `news-dates-public-comparison.json`.
- `git diff --check` passed; Git emitted existing LF→CRLF worktree warnings for the template paths. Frozen review bytes must be captured directly from Git, not normalized tool text.

## Saved-state QA limits and stopped probes

The local news database snapshot contains **120 retained rows**, all with saved fetched time `2026-09-30 14:15:40`; the actual one-day production report window currently yields **zero eligible rows**. A private saved-news-only QA attempt therefore stopped rather than changing timestamps/window semantics or claiming nonempty current-news verification. The old CI internal HTML omits dates and cannot reconstruct its underlying saved date values.

The first normal SQLite `mode=ro` backup attempt stopped when the source DB/WAL file-set hash guard changed. Empty WAL and SHM sidecars were subsequently observed; no initial source-byte equivalence is claimed. A second attempt used `mode=ro&immutable=1` only after checking the WAL was empty. Its source DB/WAL/SHM hashes remained unchanged; the copy passed integrity check, then stopped on the zero-row reporting-window guard. Both partial snapshots remain **private scratch**, not public proof or deliverables. Do not use immutable mode to ignore committed WAL data.

An initial old/new comparison accidentally omitted `public_export=True` and compared internal-mode output. The production export caller at `src/intel_sources/public_report.py:594` supplies that flag explicitly. The corrected public-mode comparison passes; no production export change was needed. The project's own `.venv/Scripts/python.exe` was used after the generic tool interpreter lacked APScheduler; no dependency was installed.

## Independent review blocker and parent reproduction

Reviewer `deleg_fb1e16f5` verified the complete six-file/nine-hunk V1 package and exact SHA256 `69f1e2b19e702c788e1d7f8b95b158b98a56a5929c283d701d7fc4c0f731d348`, but returned **passed=false**. A non-null `tzinfo` can still return `None` from `utcoffset()`; the old guard let `astimezone()` infer local time. Parent added and ran both publication/observation regressions: **2 failed / zero setup errors / exit 1**, evidence `news-dates-offset-red.xml`. Publication falsely produced `2024-01-02T08:15:00+00:00` instead of unknown, and observation falsely produced that value instead of saved-wall-time UTC `2024-01-02T10:15:00+00:00`. Third-context fixer `deleg_4d244e79` changed only the guard to `if parsed.tzinfo is None or parsed.utcoffset() is None:`. Parent read back the actual formatter, verified the exact one-line delta against the still-frozen V1 index and confirmed all unrelated files unchanged. Child JUnit receipts independently read back: two regressions **2 passed**, complete date file **31 passed**, zero errors/failures/skips. Parent reran the entire suite: **831 passed / zero failures, errors, skips or xfails / 47.24 seconds / exit 0** (`news-dates-v2-full.xml`). Two new RED cases now pass; the original publication and observation contracts are preserved. V2 still needs a new complete frozen manifest and independent approval. Never treat the blocked V1 verdict as approval.

The parent repeated the fixed-time, actual-saved-input public comparison after the correction: old/new standalone bytes remain identical at **2,533,631 bytes**, SHA256 `7d36956149588484131f153659cc9a4c21fff07f4f02518d290306063332c39b` (`news-dates-public-comparison-v2.json`). Both template copies remain identical, original style/header and all bytes outside internal news remain unchanged. This remains local controlled evidence, not a fresh hosted artifact.

## Remaining gates and boundaries

1. Independent exact frozen-diff review before any commit/push.
2. Fresh CI artifacts must demonstrate persisted publication/observation fields in the actual internal consumer; do not reuse old hosted proof for this repair.
3. News-feed health still needs its own RED production-boundary regression and separate fix, including history/current-run separation and unavailable per-run outcomes.
4. Real provider inference, paid calls, summarizer requests, router changes, feed removal, owner deletion and token rotation remain unauthorized/unperformed. No collection, deployment or notification was initiated by this local repair.
5. Customer release, relevance-depth and broader source/security/delivery acceptance remain open.
