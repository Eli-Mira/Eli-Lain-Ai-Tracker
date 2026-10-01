# EliLain-Intel — implementation checklist

## Scope
Approved by Eli: trustworthy verification, change-first reporting, sanitized evidence, prioritized actions, broad tool/skill/model discovery, regression fixes and tests. Preserve the original Lain site template; defer structural refactoring. Discovery is advisory: never auto-install discovered skills/tools. OpenRouter is an early-warning catalog source, not a request for free inference tokens.

## Verified starting point
- Repository: `C:/tmp/eli-lain-tracker`; clean starting HEAD `2b8b4a6`.
- Original template: `C:/Users/emadg/AppData/Local/hermes/attachments/report_template_lain.html`; copies -2 through -5 have identical SHA256.
- Active reporter template directory: `src/templates/` (not only the tracker-core copy).
- Isolated runtime: `.venv/Scripts/python.exe`, Python 3.11; dependencies installed editable with uv.
- Baseline: `27 passed, 3 warnings` (Pydantic deprecated class Config).
- Git HTTPS saved credential helper works; `gh` is not authenticated.

## Acceptance checklist
- [x] Recover actual repository/template and reproduce baseline tests.
- [x] Add checked_at/probe_source and explicit fresh/stale/unverified states; never refresh a check timestamp just by rendering.
- [x] Persist sanitized per-attempt evidence and fix model fallback/error-classification/state-merge failures.
- [x] Show new/recovered/broken/exhausted and meaningful discovery changes before full inventory; first run is a baseline, not invented launches.
- [x] Add prioritized action queue: verification before stale remedial advice; evidence-backed alternatives; reset schedules marked unverified if only registry knowledge.
- [x] OpenRouter: full model + provider catalog, paid and free, actual API metadata; listing != working entitlement.
- [x] UnoRouter: real documented public catalog/API, visible auth/network failures; never substitute OneRouter.
- [x] FreeLLMAPI: real authenticated local catalog/probes and explicit offline/CI handling; router DB is read-only, no restarts/key changes.
- [x] Skills.sh: monitored all-time/trending/hot, project-type/usefulness tags, first-seen vs actual-new distinction, explicit coverage limits; no auto-install.
- [x] GitHub Trending: daily/weekly/monthly, broad project-type tags, merged evidence and repeat suppression; no fabricated trending REST endpoint.
- [x] Preserve user template design, synchronize actual template copies, render freshness/evidence/changes/actions/source health, test filters and unsafe content handling.
- [x] Persist last successful discovery snapshot; failed/partial source fetch cannot erase prior data or imply healthy current checks.
- [x] Fix confirmed broken CLI/report/workflow behavior without structural refactoring.
- [x] Run provider/classification/model-fallback/missing-DB/stale-state tests, entire regression suite, real source smoke tests and browser/site verification.
- [x] Check CI command/packaging/data persistence; no duplicate scheduled workflows.
- [x] Deliver real HTML artifact, exact test results, source coverage and any unresolved blockers; inspect diff before publishing.

## Baseline bugs — now fixed
- generate_report never passes tool_items; audit discards discovered rows, disables tools/news, and returns HTML under a path variable.
- Scheduled workflow invokes today/report but no discover/audit, so it does not run promised discovery/probing.
- DB healthy gets treated as LIVE without a real completion; saved state only fills missing providers instead of merging checks into DB-loaded records.

## Verification records
- `docs/verification-provider.md` — provider workstream
- `docs/verification-catalogs.md` — public/local model sources
- `docs/verification-tools.md` — skills and repository trends
- `docs/verification-template.md` — template provenance/rendering
- `docs/verification-integration.md` — final regression, clean-install, live provider/news/discovery and real browser evidence.
- `docs/verification-live.json` — machine-readable actual counts, timestamps, coverage and screenshots.

## Constraints / honest coverage
Public leaderboard coverage is not the entire ecosystem. Expose observed page/view coverage and failures. Catalog agreement is corroboration, not independent proof of successful inference; FreeLLMAPI can derive metadata from upstream catalogs. Do not claim a discovered tool is S-tier without evaluation evidence.

## Final verification — September 30, 2026
- [x] Full project suite: **227 passed, 3 existing Pydantic deprecation warnings in 9.69s**.
- [x] Fresh Python 3.11 environment with declared dependencies only: **221 passed, 6 skipped, 3 warnings** without a browser path (browser-only cases now skip explicitly instead of erroring) and **227 passed, 3 warnings** with real Chromium.
- [x] Actual desktop/mobile HTML assertions at 1440×1000 and 390×844: search, source/project filters, empty states, evidence expansion, no JS errors, no horizontal overflow.
- [x] Original five supplied templates unchanged (SHA256 `c6d506229ba422a1f28e5d505ab89b9e00b7fc53dfd47d8b3e7ed7373a820440`); active and tracker-core template copies byte-identical.
- [x] Real latest source observations: 635 OpenRouter models, 112 OpenRouter providers, 237 UnoRouter models, 280 local models, 454 public Skills.sh skills, 49 unique GitHub Trending repositories.
- [x] Counts programmatically reconciled: **1,767 latest observations; 1,772 retained rows**, including 5 historical rows. Full discovery inventory rendered.
- [x] Real provider snapshot: 28 configured platforms assessed; 8 made completion attempts; **6 LIVE, 1 DEGRADED, 21 UNKNOWN**. Six matching routes; one server error; one mismatched fallback route; twenty without matching exposed enabled models.
- [x] News run completed despite blocked sources: 176 fetched, 120 relevant unique rows retained; report uses the existing latest-100 news view.
- [x] News collection now has per-source timeout isolation; unconfigured AI summarization makes no requests; failed configured summaries stop repeated unauthorized requests and use clearly labeled observed-title excerpts.
- [x] Backed up project news DB and repaired 24 literal error-summary placeholders, retaining all 120 records. Router DB untouched.
- [x] No known runtime credential present in HTML/provider-state output; `git diff --check` passes.
- [x] Final HTML delivered: `reports/eli-lain_20260930_143122.html`; SHA256 `91782ddca85ba5fefe1528a7c8a7d4f86e93379b65398fdf3449691cfa59f2d0`.
- [x] HEAD unchanged at `2b8b4a6606aeb8f28c599dffc83b7347aebc6a65`; no commit/push/deployment, router restart/key changes or remote CI run. Notifications disabled for verification.

## Final handoff — October 1, 2026
- [x] Restrict browser skips to missing local installations only; CI and configured/installed-browser launch failures must fail visibly.
- [x] Three regression scenarios reproduced RED before the fix (CI, explicit browser path, installed browser failure).
- [x] Latest full suite with Chromium: **230 passed, 3 existing warnings in 11.61s**.
- [x] Clean declared-dependency environment with Chromium: **230 passed, 3 warnings in 11.33s**; without a local browser: **224 passed, 6 explicitly skipped, 3 warnings in 8.63s**.
- [x] Report hash, DOM counts (1,772 discoveries, 28 providers, 100 news rows), original template provenance and synchronized copies verified again. September 30 source observations were not relabelled as new probes.
- [x] Summary and prioritized additions/polish saved in `docs/HANDOFF_SUMMARY.md`. Implementation/handoff complete; follow-ups remain open deliberately.

## Follow-ups — intentionally not claimed complete
- [ ] Optional credential-assisted Skills.sh full catalog scan. Public all-time/trending/hot rows are scanned, not its entire paginated catalog. Forty detail pages enriched; 414 details not scanned in the latest budget, exposed in coverage.
- [ ] Evaluate actual project recommendations before calling them S-tier; discovery remains advisory and never automatically installs/executes tools.
- [ ] Legacy news subfeed repair/configuration: several RSS URLs returned 404, Reddit/RSS hit rate limits/timeouts, GitHub release enumeration was anonymously rate-limited, and configured YouTube feeds were unavailable without API credentials. Other sources continued; these external/subfeed limitations are not hidden.
- [ ] Optional explicitly configured AI-summary live verification. Current safe fallback is title excerpts, not claimed AI output.
- [ ] Publish/trigger remote CI only after authorization; CI wiring/dependencies/skip behavior are verified locally, not remotely.
- [ ] Structural refactoring remains deferred; consider packaging/pagination and legacy news source-health polish after behavior is stable. Pydantic configuration was migrated early as separately approved.

## Approved next phase — October 1, 2026
- [x] Verify that local origin is the existing `Eli-Mira/Eli-Lain-Ai-Tracker` repository, not a replacement. Live local/remote main both at `2b8b4a6606aeb8f28c599dffc83b7347aebc6a65`; newer work remains uncommitted locally. GitHub API confirms private repository, push permission, and no configured Pages endpoint (404). Do not confuse older successful remote runs with current local tests.
- [x] Migrate all three deprecated model Config classes to ConfigDict while preserving schema examples and JSON validation/serialization; regression reproduced import failure with deprecations-as-errors, then passed.
- [x] Full current suite with real Chromium and Pydantic deprecations treated as errors: **231 passed in 11.07s, no warnings**. Diff whitespace gate passed.
- [x] Feed repair: per-feed isolation, truthful cooldowns and partial-success retention done and wired into the tracker. Live fetch 2026-10-01 00:42 UTC returned 193 items across 71 operations (29 ok, 28 failed, 14 not attempted). Legacy SQLite `is_disabled` no longer disables a source forever. Remaining: Anthropic/Meta 404 endpoints without official replacements; HF papers over the 1 MiB cap.
- [ ] Implement project-specific evaluated shortlists with reasons, evidence, costs/constraints and honest confidence labels.
- [ ] Keep SQLite/JSON and secrets internal; generate one standalone HTML report each run, retaining the original Lain design.
- [x] User chose anyone-with-link sanitized HTML via clarification. Repository and internal databases remain private; only allowlisted public output may be deployed. No raw diagnostics, credentials, key/account IDs or local paths.
- [ ] Automate one hosting destination (GitHub Pages if eligible, or Cloudflare Pages/Netlify with authorized account access); verify the deployed artifact before reporting a link. Local hosting account browser preflight hit a locked, running Brave profile; did not close the user browser or change browser settings.
- [ ] Send a short report brief and verified hosted URL to both configured Telegram and Discord destinations; verify delivery rather than trusting a boolean response. Authenticated GitHub secret-name metadata confirms the existing repo has both channel/token secret pairs; secret values were not read or exposed. Local hosting/notification environment variables are absent.
- [ ] Review/secret-scan and update the existing repository with commit/push; read back the exact remote commit and run its CI. No new repo or force push.
- [ ] Split orchestration/storage/adapters/presentation last, after behavior stabilizes.
