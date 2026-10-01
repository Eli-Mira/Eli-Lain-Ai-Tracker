# Orphaned worker recovery and independent public-inventory verification — 2026-10-01

## Status

Four follow-up workers in `deleg_ccc1157f` all terminated with "no reply: the turn stopped while a tool result was still pending" after doing real filesystem work. **No worker summary was returned for any of them.** Their code and tests were therefore treated as unverified third-party edits: the whole suite was re-measured by the parent, every regression they added was executed, and the parent independently reproduced the actual public artifact.

**Release verdict: still NOT release-approved.** These changes are local and uncommitted at the time of writing.

## What the orphaned edits actually changed (parent-verified by reading the diff)

| File | Change | Parent verdict |
|---|---|---|
| `src/news_tracker/adapters.py` | Per-row parse validation before persistence; partial-vs-healthy feed status; `_checked_fetch` allow-status; GitHub 404 release; repo `updated_at` no longer claimed as publication; Reddit config errors no longer silently downgrade to anonymous; HN switched to `search_by_date` | Useful and consistent with the reporting invariants. Kept. |
| `src/news_tracker/summarizer.py` | Whole-batch validation before mutating any item; object/nonstring/partial/raw-line responses now raise instead of becoming unlabelled summaries; refusal/`finish_reason`/empty-content checks; no upstream message in logs | Directly fixes a real truth defect. Kept. |
| `src/freellmapi_tracker/tracker.py` + `prober.py` | `PRAGMA query_only=ON`; `load_probe_catalog(qualified=True)` builds exact `platform:model` (and endpoint-pinned `custom:`) member IDs; bound routes are authoritative and never widen to HTTP aliases; empty completion is not LIVE; `X-Routed-Via` must equal `platform/model`; LIVE action text no longer claims free entitlement | Correct direction for the 21/28 `unknown` problem. Kept. **Not live-verified here** — no router probe was run by the parent. |
| `src/intel_sources/tools.py` | 40-slot detail budget split into workflow-hint lanes plus view round-robin, with per-row `metadata_selection` provenance and honest `not_scanned` accounting | Addresses the first-40 bias. Kept. **Live Skills.sh coverage not re-measured by the parent.** |
| `src/intel_sources/public_report.py` | Complete-inventory default export with explicit caller caps still honoured; OpenRouter `~alias` first-segment validation; many typed lifecycle/price/capability/detail-provenance fields; UTF-8 byte ceilings; retained/exported/omitted disclosure | Mostly good. **Contained one real over-blocking bug — fixed by the parent below.** |

## Defect found and fixed by the parent: the secret heuristic deleted real catalog rows

The public URL guard rejected any URL *containing* `sk-`, `password`, `secret`, `token` or similar as a substring. On the real saved state that silently removed three legitimate Skills.sh rows:

```
skills:open.feishu.cn/... (15 rows, 2-segment site identities — still rejected by policy, unchanged)
skills:mattpocock/skills/ask-matt                                    ← dropped
skills:emilkowalski/skills/ask-sonner                                ← dropped
skills:better-auth/skills/email-and-password-best-practices           ← dropped
```

Root cause: substring matching on identifiers. `ask-matt` contains `sk-`; `email-and-password-best-practices` contains `password`. A substring test cannot distinguish a name from a credential.

Fix (`tests/test_release_public_url_policy.py`, RED first): match credential *shapes* — a vendor prefix plus an opaque body (`sk-` + ≥6 body chars not preceded by a word character, `gh[pousr]_` + 16, `github_pat_` + 20, `Bearer ` + 12) and named secrets in `name=value` / `name: value` form — plus an explicit ASCII URL character allowlist that rejects redaction markers (`«…»`) and homoglyphs. Six legitimate URLs and thirteen rejection shapes are asserted in both directions.

One boundary correction during the fix: `https://example.org/sk-abc123` is only 6 body characters, so the first `{8,}` threshold let it through. The threshold is now `{6,}` with a negative lookbehind, verified against the real `ask-matt` slug.

## Independent verification of the real artifact (parent-run, not worker-reported)

`main.py export-public` was re-run from real saved state and the produced bytes were read back with `load_artifact()`:

```
bytes                     1,894,744          (previous capped export: 659,604)
sha256                    45364502370e271ae9d40a71bf4613a0afc25ac8ef41bc7c9a6b7d73aa3672f4
load_artifact()           OK
rendered_at               2026-10-01T11:38:40.347771+00:00
observations              5 saved timestamps
source_counts             github-trending 49, openrouter-models 533,
                          openrouter-providers 112, skills-sh 439, unorouter-models 125
DOM rows match counts     yes (49/533/112/439/125)
tilde alias rows          19  (were previously dropped)
restored by the URL fix   ask-matt, ask-sonner, email-and-password-best-practices
fruit-slicer              absent
typed public metadata     1,259 blocks; 38 explicitly "not supplied"
field survival            Listed input price 624 · Reasoning mandatory 254 ·
                          Detail metadata status 439 · Catalog free flag 125 ·
                          all-time rank 175 · Context 469
CSP meta tag              present
remote script/link        none
artifact ceiling          1.89 MB < 4 MB delivery limit
```

`sk-` occurrences in the artifact are exactly the four restored legitimate slug URLs; no secret-shaped token exists in the output.

**Honest coverage limit:** `Catalog expiration date` renders 0 times because the *saved* `data/intel_state.json` was fetched before the adapter began retaining `expiration_date`/`knowledge_cutoff`/alias fields — the projection code is tested and correct, but this state file has no such data. A fresh discovery run is required before that field can appear. This is a data-age fact, not a projection bug.

## Commands and results

```bash
# Full suite after integrating orphaned edits (parent, real Chromium, -p no:randomly)
NOTIFICATION_CHANNEL=none PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' \
  .venv/Scripts/python.exe -m pytest tests -q -p no:randomly --basetemp='.../orphan-full-1'
# 1 failed, 677 passed in 28.19s
# Failure: tests/test_next_phase_integration.py::test_optional_feed_state_write_failure_cannot_discard_success
# Root cause: the fixture row {'title': 'Observed item'} has no URL, so the new per-row
# validation correctly rejects it before persistence. The TEST fixture was wrong, not
# the production code. Fixture corrected to a complete observed row. -> 678 passed.

# RED for the URL-policy defect
.venv/Scripts/python.exe -m pytest tests/test_release_public_url_policy.py -q --tb=line
# 6 failed, 15 passed  (ask-matt/ask-sonner/password slugs wrongly rejected)

# GREEN
# 20 passed

# Final full suite, diag probes removed
# 698 passed in 35.37s, exit 0, no xfails
```

## Limits of this recovery pass

- Four orphaned worker transcripts exist at
  `C:/Users/emadg/AppData/Local/hermes/cache/delegation/live/deleg_ccc1157f/task-{0..3}.log`.
  They are the only record of what those agents actually observed live. Their findings are
  **unverified**; the parent re-derived the artifact numbers above from scratch.
- No live Skills.sh, OpenRouter, UnoRouter, GitHub, news-feed or router probe was run by
  the parent in this pass. All source-truth numbers remain the previous audit's, now older.
- A stale `.pyc` for one worker test file briefly produced five phantom failures with an
  impossible regex result; the specific cache file was removed and the tests re-run clean.
  No repository file was deleted.
- Provider binding fixes, news/summary fixes and detail-selection fixes are **regression-tested
  but not live-verified**. They must not be reported as working intelligence until a real
  run proves them.
- The 15 two-segment `open.feishu.cn` skill identities remain excluded by the 3-segment
  identity policy. That is a deliberate fail-closed choice, not a bug, and it is disclosed
  in the report's saved-vs-exported counts.
- Exact-byte delivery dedupe, ambiguous-response duplication and concurrent-publisher
  locking remain open per `docs/release-delivery-continuity-followup.md`.
