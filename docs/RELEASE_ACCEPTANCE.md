# Customer release acceptance — EliLain Intel

Status: **NOT RELEASE-APPROVED**. Opened 2026-10-01 after Eli rejected plumbing-only completion.

This checklist supersedes the old IMPLEMENTATION_TODO.md checked boxes and historical handoff completion language. PASS requires the actual output consumer and useful outcome, not merely a file existing or tests returning green.

## Requirements locked by Eli
- Fruit-slicer is paused/canceled. It is not an active recommendation target. Preserve historical state; do not delete the game project.
- Active project recommendation groups: Hearth POS, gesture control, data/AI. Keep broad agent/tool/model discovery alongside them.
- Skills.sh, OpenRouter, UnoRouter, GitHub Trending, local FreeLLMAPI and every configured news source must be accounted for.
- SQLite/JSON hold real internal state; report generation uses it and updates derived evaluations. Fetch/check time must never be replaced by render time.
- The exact supplied original Lain HTML is the design reference. Do not overwrite the attachment or quietly replace the design.
- Delivery must verify the requested standalone HTML FILE and actual hosted bytes, not conflate link messages with attachment delivery.
- Verify usefulness/stability first, structural refactoring next, new features afterward. Private Obsidian architecture map remains a separate requested artifact.
- Do not publish secrets/private state, auto-install discovered tools, mutate router keys/models, or claim listing metadata proves inference/free entitlement.

## Definition of PASS for every source
1. Exact source and endpoint documented, actual bounded live fetch recorded with observation timestamp.
2. Actual current schema parsed; identities, units and capabilities validated.
3. Real source counts reconciled programmatically, including partial/failed/not-attempted coverage.
4. SQLite/JSON persistence round-trips across restart. Failed refresh retains prior rows and marks them stale honestly.
5. Useful fields reach the actual internal/public report consumer, where authorized; no generic listing-only replacement of all intelligence.
6. Recommendations/changes have factual provenance, actionable reasons, limitations and honest confidence.
7. Tests reproduce confirmed defects RED before fixing; malformed/empty/stale/rate-limited/auth-failure/timeouts covered.
8. No secret/error/private evidence leaks, unsafe links or source cross-auth contamination.

## Tracked acceptance gates
- [x] Establish baseline: **433 passed in 11.83s** with real Chromium; this is not release acceptance.
- [x] Reproduce paused-project mismatch in a failing customer-scope test.
- [x] Remove fruit-slicer from active groups while preserving archived rules/history; internal/public scope test GREEN.
- [x] Reproduce report discarding derived project evaluation instead of writing its JSON.
- [x] Persist exact report evaluation/snapshot/provenance atomically; test GREEN, empty-first-run test GREEN.
- [x] Regenerate local saved-state internal report and derived evaluation for the three active groups; no new fetch/probe claimed. Previous one-off evaluation backed up under Hermes scratch.
- [ ] Skills.sh: live leaderboards/documented API, useful detail metadata, coverage, persistence and visible consumer.
- [ ] GitHub Trending: daily/weekly/monthly, merged identities, metadata evidence and fit.
- [ ] OpenRouter models: current schema, exact pricing units/modalities/context, model changes, visible useful output.
- [ ] OpenRouter providers: current listing/provenance, provider observations distinct from local inference verdicts.
- [ ] UnoRouter: exact public catalog, schema, prices/capabilities, failure states and visible consumer.
- [ ] Local FreeLLMAPI: configured bindings/read-only state, observed catalog and routing proof; CI cannot claim a fresh local probe.
- [ ] Enumerate each remaining configured source/subfeed and attach per-source PASS/FAIL/BLOCKED evidence.
- [ ] News: all source/subfeed timeouts/health/cooldown/restart, summary/fallback truth, dedup/scoring and actual output consumer.
- [ ] JSON/SQLite: corruption, atomic write failure, retained history, cache transport, derived-data replay and no false freshness.
- [ ] Original attachment vs selected template vs rendered internal/public/hosted HTML: structural and visual fidelity.
- [ ] Chromium: desktop/mobile, offline, no JavaScript, all controls/search/filters/links, counts, empty states, errors and overflow.
- [ ] Telegram: exact HTML attachment protocol, truthful receipt/readback limits, real target verification.
- [ ] Discord: exact HTML attachment protocol and independent target readback.
- [ ] Netlify: publish only the sanitized standalone file; exact hosted byte hash verified; no private state tree.
- [ ] Workflow: restores all required state, fails on missing report or delivery failure; no duplicate/replayed notices.
- [ ] Security/dependencies/failure paths: actionable vulnerability evidence, full suite, clean-state suite and actual CI.
- [ ] Consolidated release verdict with blocking findings, commands, timestamped evidence and delivery artifacts.

## Evidence files (five independent workstreams)
- `docs/release-tools-audit.md` — Skills.sh / GitHub Trending.
- `docs/release-catalogs-audit.md` — OpenRouter / UnoRouter.
- `docs/release-template-audit.md` — exact template / safe public information / browser QA.
- `docs/release-storage-news-audit.md` — JSON/SQLite / news / provider truth.
- `docs/release-delivery-audit.md` — workflow / hosting / actual channel consumer.

Entries are pending until the parent verifies worker findings and resulting integrated behavior. Worker self-reports are not final release sign-off.

## Parent verification performed so far
- `tests/test_release_project_scope.py`: paused project test failed before correction, then passed.
- Derived-evaluation persistence test failed because `project_evaluations.json` was absent, then passed after atomic integration.
- Empty-first-report case caught a missing-input-state crash and passed after explicitly handling an empty baseline.
- Targeted parent regression: **16 passed** (scope + next-phase + intel integration), **36 passed** (recommendations + real Chromium project UI).
- Actual local saved-state internal report: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/eli-lain-release/active-project-saved-state.html`, 1,772 saved inventory entries, three active groups. This is regeneration, not a fresh source observation.
- GitHub CLI currently unauthenticated; delivery audit is checking the existing git helper as an authorized read-only alternative without exposing credentials.

## Open issues already evidenced
- The public exporter currently strips fetched descriptions into fixed generic listing disclaimers; usefulness of typed public metadata is under audit. Do not solve this by exposing raw private evidence.
- Derived project evaluation was a one-off saved artifact, not regenerated by the actual report command. Fixed locally, not published yet.
- Existing historical tests/documents treated fruit-slicer as active and overstated completion. Correct current scope instead of relying on those old check marks.

No claim of zero bugs or release readiness until all blocking gates are closed with evidence.
