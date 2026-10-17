# EliLain-Intel — integration and live verification

Verification date: September 30, 2026. Workspace: `C:/tmp/eli-lain-tracker`.

## Final handoff verification — October 1, 2026 (local date)

The last test-setup loose end is fixed: a local browser may be skipped only if its default executable is genuinely absent, no explicit browser path was supplied, and the run is not GitHub Actions. CI launch errors, invalid explicit paths, and installed-browser startup errors propagate rather than silently making a green run. Three parameterized regressions reproduced the hidden failures before this fix.

Latest actual execution, with real Chromium: **230 passed, 3 existing warnings in 11.61s**. Fresh declared-dependency environment, also with real Chromium: **230 passed, 3 warnings in 11.33s**. The clean local environment without a browser reports **224 passed, 6 explicitly skipped, 3 warnings in 8.63s**. This is not a remotely executed CI run.

Readback verified the existing report hash and DOM counts: 1,772 discovery rows, 28 provider rows, and 100 news rows. Original template hash and synchronized active/package copies verified again. No fresh discovery or provider probes were sent in this final handoff; the live observations below remain the September 30 snapshot.

## Early Pydantic compatibility fix — October 1, 2026

Eli approved moving the deprecated configuration fix ahead of structural refactoring. `Provider`, `NewsItem` and `NewsBatch` now use `model_config = ConfigDict(json_schema_extra=...)` with their original schema examples intact. The new subprocess regression first failed on schema import with Pydantic deprecations promoted to errors, then passed with schema example validation and JSON round trips preserved.

Full command used the installed real Chromium and `-W error::pydantic.warnings.PydanticDeprecatedSince20`: **231 passed in 11.07s, no warnings**. `git diff --check` passed. This remains a local result, not an updated remote CI run.

A live Git read and authenticated GitHub API metadata read confirmed the correct existing private `Eli-Mira/Eli-Lain-Ai-Tracker` origin, default/main branch, push permission, and local/remote main at `2b8b4a6606aeb8f28c599dffc83b7347aebc6a65`. The new work is uncommitted/unpushed; the two recent successful GitHub runs were on that older SHA. No report website is claimed deployed; the repository Pages API returned 404.

## Earlier regression results (September 30)

Project environment:

```bash
NOTIFICATION_CHANNEL=none \
PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' \
.venv/Scripts/python.exe -m pytest tests -q
```

Actual execution: **227 passed, 3 warnings in 9.69s**. `git diff --check` passed. The three warnings are existing Pydantic class-Config deprecations, not newly failing behavior.

Reinstalled only declared editable project + tracker-core dependencies into a fresh Python 3.11 environment at `C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-clean-venv`, then exercised the same suite. Without a browser path the same run reports **221 passed, 6 skipped, 3 warnings in 8.00s**: the 6 browser-only cases now skip with an explicit Chromium-unavailable message instead of erroring. With the real installed Chromium, that run reports **227 passed, 3 warnings in 10.35s**. This verifies local clean dependency installation, not a remote GitHub Actions run.

## Integration regressions reproduced RED before fixes

- Persisted discoveries absent from the CLI report.
- Main discovery flow not calling both source families or persisting their coverage.
- Old LIVE state and obsolete advice displayed as current despite stale timestamps.
- Probe observation timestamps/evidence lost by manual status assignment.
- Provider changes missing after reopening the tracker; identical probe replay creating noise.
- Full audit excluded news/discoveries and returned HTML under a path variable.
- Evidence dicts rendered only their keys instead of diagnostic values.
- Missing parser/browser dependencies and absent CI Chromium setup.
- Real local models labeled `owned_by=freellmapi` were not mapped to enabled upstream/key bindings.
- Gateway available flags suppressed actual provider checks.
- Unknown/unverified prior status was falsely labeled a recovery.
- Stale providers CLI showed LIVE and old remedial advice.
- Stalled news adapter prevented later adapters from running.
- Unconfigured summarizer made unauthenticated requests; failed configured calls retried every batch and saved error text as successful AI content.

The old summary unit contract expecting invented error JSON was deliberately replaced with a failure-propagation assertion; public fallback behavior is separately tested with actual MockTransport HTTP requests and distinct observed news rows.

## Actual live execution

Executed the real local audit, discovery refreshes and provider checks with notifications disabled. Router configuration/database/keys were not changed. Existing provider/model bindings were read through SQLite `mode=ro`; tiny inference requests can consume provider quota.

Latest discovery observations: September 30, 2026 around 14:04 UTC.

| Source | Observed unique rows | Collection status |
|---|---:|---|
| OpenRouter models (all modalities, paid/free) | 635 | ok |
| OpenRouter providers | 112 | ok |
| UnoRouter documented public catalog | 237 | ok |
| Authenticated local FreeLLMAPI model catalog | 280 | ok |
| Skills.sh public all-time/trending/hot views | 454 | partial, explicitly scoped |
| GitHub Trending daily/weekly/monthly | 49 | ok, scoped to rendered periods |

Programmatic aggregation: **1,767 latest observed rows**, **1,772 total retained rows**, including 5 historical rows. Every unique ID and source item_count was validated against actual collected items in the live harness. Catalog presence and metadata do not establish entitlement or successful inference.

Skills.sh: public view row counts 183 / 175 / 178, deduplicated across views. Forty safe public detail pages enriched; 414 details not scanned in that budget. Official API access was not fabricated or bypassed.

Provider results: 28 configured platforms assessed; 8 made completion attempts. Six verified matching routes (`cohere`, `groq`, `mistral`, `zhipu`, `agnes`, `google`), one server-error verdict (Llm7), one success-at-other-route mismatch and 20 no-matching-model results. Resulting statuses: **6 LIVE / 1 DEGRADED / 21 UNKNOWN**. No matching model/route is an investigation item, not a false broken-key claim.

News `today` originally timed out on legacy retry behavior; after the source timeout regression fix, the real run completed: **176 fetched, 120 relevant unique records persisted**. GitHub anonymous release enumeration was rate-limited; Reddit and RSS collections hit their per-source budgets; several legacy RSS URLs and YouTube feeds were unavailable. Hacker News, arXiv, Hugging Face and the GitHub search portion continued. External availability and legacy subfeed follow-ups remain explicit in the checklist.

The original summarizer saved 24 literal error-summary placeholders during the diagnostic run. After fixing fallback behavior, the project's news DB was backed up and those exact placeholders were replaced with clearly labeled excerpts of their already observed titles. Readback verified 120 rows before/after and zero error placeholders. No news was deleted. Backup: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-news-before-summary-repair.db`.

## Final artifact and real browser checks

Final report, regenerated from persisted observations without re-probing:

`C:/tmp/eli-lain-tracker/reports/eli-lain_20260930_143122.html`

Generated artifact SHA256:

`91782ddca85ba5fefe1528a7c8a7d4f86e93379b65398fdf3449691cfa59f2d0`

Actual size: 4,368,403 bytes. Final report contains all 1,772 retained discoveries, all 28 provider rows, and the existing latest-100 news view. The 120 stored news total is not falsely presented as 120 rendered rows.

Real Chromium assertions on that HTML at **1440×1000** and **390×844** passed:
- Whole retained discovery inventory is rendered.
- Search returning no matches shows the correct empty state.
- Source filtering returns the actual Skills.sh row count.
- Combined source/project filtering matches programmatically computed tagged rows.
- Provider evidence details expand.
- No page JavaScript errors.
- No horizontal overflow.
- Desktop/mobile screenshots inspected.

Separate reporter tests cover JS-disabled fallback, malicious data, URL schemes, optional fields and template syntax errors. Known runtime credentials were checked for absence from HTML and saved provider state without printing them.

Machine-readable counts/timestamps/coverage/screenshots: `docs/verification-live.json`.

## Template provenance / repository scope

All five supplied original Lain HTML attachments remain unchanged with SHA256:

`c6d506229ba422a1f28e5d505ab89b9e00b7fc53dfd47d8b3e7ed7373a820440`

Active and tracker-core template copies are byte-identical. They extend the supplied design rather than silently replacing it.

HEAD remains `2b8b4a6606aeb8f28c599dffc83b7347aebc6a65`. **No commit, push, deployment, container restart, router DB edit, credential rotation or remote CI run.** Optional services, private API access, full ecosystem coverage and S-tier evaluation are not claimed completed.

## Next-phase boundaries

Refactor only after this verified functional baseline: split orchestration/storage/presentation, migrate old Pydantic Config classes, evaluate recommendations against actual projects, resolve legacy news subfeed setup and consider inventory pagination/packaging polish. Keep the read-only router boundary, credential-isolated discovery and freshness semantics intact.
