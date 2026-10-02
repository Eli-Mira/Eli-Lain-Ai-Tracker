# Customer release acceptance — EliLain Intel

Status: **NOT RELEASE-APPROVED**. Opened 2026-10-01 after Eli rejected plumbing-only completion.

This checklist supersedes the old IMPLEMENTATION_TODO.md checked boxes and historical handoff completion language. PASS requires the actual output consumer and useful outcome, not merely a file existing or tests returning green.

## Current gate — October 2, 2026 (Cairo): Cloudflare-only hosting + BUG9

**BUG9 news-feed health consumer: VERIFIED SHIPPED. BUG10: CLOSED (superseded below). Hosting: Cloudflare Pages only. Customer release remains OPEN.**

- BUG9 shipped as runtime `7925ed5b` on reviewed diff `0b2b8d0b...a5b4c7` (independent reviewer passed, no security or logic findings). CI `37055762463`: **845 passed + 2 skipped**; Pages byte-verified 3,975,646 bytes SHA `8816f3ff...d20fd`; **171 offline Chromium checks / 0 failures** on the 3 actual downloaded CI HTML files; **138 real health rows** per internal report including **138/138 UNKNOWN** on the report-only restart; public export carries zero health sections.
- Hosting decision: Netlify's account ran out of deploy credits (HTTP 403 `Account credit usage exceeded`, `auto_topup_enabled=false`). This was **not** a credential-scope problem. Runtime `580612d2` makes **Cloudflare Pages the only host**; Netlify is removed from the workflow and reduced to an explicit opt-in best-effort mirror (`NETLIFY_MIRROR_ENABLED=true`) that can never block a publish. Independent review found 2 blocking logic errors and a receipt-binding flaw; all reproduced RED and were fixed.
- Proof: CI **`37062735469` SUCCESS** on `580612d2` — **861 passed + 2 skipped**, Pages byte-verified **4,090,516 bytes SHA `9b90ff92...f1355`** (CI and anonymously served copies identical), `delivered: true`, Telegram **receipt-confirmed**, Discord **independently-read-back**, exact `index.html` attached, and **zero Netlify references in the run log**.
- Durable proof: `EliLain-Intel-Audits/hosted-37062735469/`.

**Still OPEN and owned by Eli:** the customer-release verdict itself, recommendation depth/enrichment policy, Cloudflare token rotation, open-sourcing timing/licence, and the deferred Scrapling evaluation. FreeLLMAPI is **not** an acceptable open-source dependency by Eli's decision; anything built on it must be optional. No live provider inference, no paid AI summary, no router change. No CI database artifact exists, so there is **no independent DB-value audit**. Delivery receipts are never an exactly-once promise or proof a human opened the file.

## Superseded: news date consumer gate — October 2, 2026 (Cairo)

**BUG8 rendered publication/saved-observation metadata: VERIFIED SHIPPED; customer release remains OPEN.** Exact six-file/nine-hunk V2 review SHA `92f8a5b515f7fddb9cbc98e59a0bfb2416d286ddfb80bf7a0026bc98faf0c027` approved by `deleg_c03fecf5`; tested runtime `d252865af1e2f7316d54e6fa73f6d479511298b2`. Local831passed, clean CI **36942612716** **829passed/2setup-dependent skips**. Both actual INTERNAL CI reports show **483 story/date rows / 885 time elements / 81 unknown publications**, with **56 offline browser checks / zero failures**, saved dates unchanged across483 shared `(url,title)` identities. Actual Pages equals downloaded sanitized **3,478,348-byte** file SHA `2bcef3eb8eb447952f882861b85237e486577746c0baa4ffa841115395f7c09f`; **102 served-file checks / zero failures**. **2,430 inventory rows**, all1,335Skills.sh literal owner IDs preserved; originalstyle/header preserved and publicnews excluded. Telegram exact attachment receipt-confirmed, Discord independently read back, cache save successful. Actual review coverage remains12/1395candidates. Full proof: `release-internal-news-dates-hosted-verification.md` and durable `EliLain-Intel-Audits/hosted-36942612716/`.

**At this historical gate BUG10 and BUG9 were both OPEN** (SQLite ingestion assumed non-null tzinfo meant a known offset). Both have since been repaired and verified — see the current gate above. No inference/summary/router/owner changes occurred; no customer-release approval.

## Earlier decision-first gate — October 2, 2026 (Cairo)

**BUG7 decision-first first-view/order/disclosure defect: VERIFIED SHIPPED; customer release remains OPEN.** Reviewed production runtime `e62b0faf3938ca7d6fe9e35dcbaa8420640513b3`; independently approved test-only native-toggle follow-up `8ee2bd8730fb89759feac441efb5834809557c36`. Fresh manual CI **36933189703** succeeded (**798 passed / 2 skipped**, local **800 passed**, 40 repeated width-case executions). Actual Pages bytes equal the downloaded CI file byte for byte: **3,294,609 bytes**, SHA256 `e5d5f04b432bfd6cbaca89a4e69091f8451b9b04848e1dd5cd392395a6a93e44`. **102 offline browser checks / zero failures**, 390px/1440px, JS on/off; public shortlist first, full **2,281-row** archive closed initially, all **1,187 Skills.sh owner IDs** retained. Telegram exact HTML attachment receipt-confirmed; Discord independently read back; Pages verified before sends and cache save succeeded. Current recommendation coverage remains **12/1,247 candidates**, 10 low-confidence cards; relevance/live/dependency/security/delivery limits stay open. Full proof: `release-decision-first-hosted-verification.md` and durable `EliLain-Intel-Audits/hosted-36933189703/`.

The preceding failed CI **36932048178** published nothing; its three identical native-toggle test races were corrected without weakening expected strings or changing production code. Its old pending status is superseded by the fresh success above, not rewritten as a success. No real provider probe, paid inference, router edit, summary request or destructive owner dedupe occurred in this repair.

## Earlier repair gate — October 1, 2026

**Fresh publication gate PASS; customer release remains OPEN.** Independent reviewer `deleg_8571a6cf` approved all 21 files / 36 hunks and the parent matched exact coverage/digest before committing/pushing runtime `a8c24789ba065433c7dd7d9d5cba831edd61c90e`. Manual CI `36904275396` succeeded: clean-runner **790 passed / 2 setup-dependent skips**; local full suite **792 passed**. Downloaded CI export and actual served Pages bytes match byte for byte: **3,068,597 bytes**, SHA256 `d2172e330e7f2cf2af345856adf05221812dd01bbca84fe9451566d578050104`, **2,099 rows**, **46 Chromium checks / zero failures** on the actual served file. Telegram attachment is receipt-confirmed; Discord attachment independently read back. Pages recurrence was enabled only afterward and the exact GitHub variable read back `true`. Netlify remains the mirror. Full evidence and limits: `release-six-bugs-hosted-verification.md`.

The first review failed closed on truncated input; its pending status is obsolete and it was never approval. Six reproduced implementation defects are closed by reviewed shipped code, production-path regressions and fresh consumer evidence. Qualified provider and optional summary wiring were simulated, not live-inference accepted. Broad source/usefulness/security/delivery acceptance rows remain open rather than being silently closed by CI green. No real probe, paid inference, summary request, router edit or destructive owner dedupe occurred.

## Requirements locked by Eli
- Fruit-slicer was **deleted by Eli on 2026-10-02**. It is not an active recommendation target. Historical archived state and rules are preserved; the game project is no longer active.
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
- [x] Telegram: exact HTML attachment protocol, truthful receipt/readback limits, real target verification.
- [x] Discord: exact HTML attachment protocol and independent target readback.
- [x] Netlify: publish only the sanitized standalone file; exact hosted byte hash verified; no private state tree.
- [ ] Workflow: eight state files restored; failed-job receipt preservation now locally tested, fresh hosted CI verification still owed. Exact-byte dedupe is not no-material-change dedupe.
- [ ] Security/dependencies/failure paths: prior 561-test/hosted CI gate passed; latest fixes, dependency evidence and clean-state release verification still owed.
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

## Parent verification of worker claims (2026-10-01, after the batch returned)
- Full suite re-run independently: **553 passed, 9 xfailed** at that moment. Worker counts were not trusted; every claim below was re-measured.
- **Corrected my own false template alarm.** The template worker stated the original locked style block was "byte-identical (`347adbd0…`)". My first check appeared to confirm a mismatch, but the fault was my own regex: `<style>` appears as literal text inside the template's leading HTML comment, so `re.search(r'<style>')` matched the comment, not the real style element. With the genuine element extracted, the original CSS is **112 canonical rules, identical, and an exact prefix** of the active style block (both canonicalize to `a12ee659dbb9fc5e`). The attachment itself is unchanged at `c6d506229ba422a1`. Claim upheld after correction.
- Actual public export regenerated from saved state: **659,604 bytes**, SHA-256 `d19287da1fa264b9864e40a3df277446b223113d1faac13168e8fb6efac8f203`, directory contains only `index.html`, project groups are exactly `data-ai, gesture-control, hearth-pos`, and `fruit-slicer` is absent.
- `load_artifact()` accepts that real export: rendered-at `2026-10-01T05:40:28Z`, 5 saved observation timestamps, source counts github-trending 49, openrouter-models 100, openrouter-providers 100, skills-sh 100, unorouter-models 100.

## Delivery defects: all nine reproduced, then fixed (parent-owned)
Each was a strict `xfail` reproduction first; every one now passes with **zero xfails**.
1. **HTML file was never sent** — both channels received text plus a hosted link only. Now the exact `index.html` bytes are attached to Telegram (`sendDocument`) and Discord (`files[0]` multipart); receipts verify filename and size, and Discord's independent readback must confirm the attachment.
2. Oversized artifact was uploaded before any refusal → `artifact_too_large` preflight before deployment.
3. `--no-export` trusted a footer string, so a remote `<script src>` passed → real standalone check across script/link/iframe/object/embed/img/source.
4. **Real secret leak**: `notifier.py:78` logged the full Telegram URL including the bot token. Now logs the exception class only. Discord's error body had the same problem.
5. `MultiNotifier` reported success when only some channels worked → partial delivery is now a failure.
6. `Logger.disabled` does not propagate to child loggers, so `httpcore.http11` could still print the token → the whole httpx/httpcore/h11 tree is suppressed. My first attempt also detached handlers and broke 26 tests; simplified to prefix-matching disable plus level.
7. Restored cache replayed yesterday's headline as breaking news → only genuinely new URLs may raise an alert.
8. Workflow cache omitted `feed_health.json` and `project_evaluations.json`, silently resetting cooldowns and derived state every run → both added, plus `delivery_receipts.json`.
9. No durable dedup → identical artifacts are no longer announced twice; changed ones still are.

Historical post-fix full suite: **561 passed in 15.49s, no xfails**. Commit `dae3eba` pushed; manual CI run `36820991710` completed successfully with exact hosted SHA256 `271ccfc9cb5ee73eb6caeae3ccaefee7f67cc52c177c26723954f446762c2d06`, Telegram document receipt and Discord attachment readback. Later continuity tests revealed additional gaps; this historical green run does not close them.

## Follow-up verification — 2026-10-01
- Four disjoint workers in `deleg_ccc1157f`: useful bounded Skills.sh detail selection; public source coverage/lifecycle/price projection; exact local provider/router bindings; news freshness and strict summary response validation. Work remains pending parent verification; these are not completed claims.
- Parent RED→GREEN: partial fan-out preserves confirmed sibling across restart; changed destination cannot borrow an old confirmation; four corrupt receipt states fail before any external write; CI uses explicit restore/save so failed publish does not discard confirmed receipts.
- Parent scoped command: `NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_release_delivery_continuity.py tests/test_report_delivery.py tests/test_release_delivery_audit.py tests/test_intel_workflow.py -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/receipt-green-4'` → **51 passed in 1.73s**, exit0. `git diff --check` on parent-owned code/workflow/tests exit0.
- Full release evidence and unresolved exactly-once/material-change/concurrent-publisher limits: `docs/release-delivery-continuity-followup.md`. Latest changes are local/uncommitted, not live-deployed. No previous blocked artifact download was retried.

## Open issues already evidenced
- Complete validated public inventory, useful typed metadata and source coverage are under follow-up. Preserve the raw-text/private-evidence exclusion; do not use generic disclaimers as a substitute for safe typed intelligence.
- Skills.sh public API authentication remains a separate boundary from useful public HTML; no full-catalog coverage claim.
- Provider free-cost/routing proof, old news observations versus publication time, and strict summarizer contracts require factual evidence.
- Original scope/evaluation-persistence defects were fixed in `dae3eba`; do not repeat historical false pending/active-fruit claims.

No claim of zero bugs or release readiness until all blocking gates are closed with evidence.

## Recovery pass after four orphaned workers — 2026-10-01
- All four `deleg_ccc1157f` workers ended with "no reply"; none returned a summary. Their filesystem edits were treated as unverified and re-measured by the parent. Full detail: `docs/release-orphan-worker-recovery.md`.
- Parent caught one real over-blocking defect in the new public URL guard (it deleted three legitimate Skills.sh rows because their names contain `sk-`/`password`) and fixed it with a shape-based credential test.
- Real artifact re-read by the parent: **1,894,744 bytes**, sha256 `45364502370e271ae9d40a71bf4613a0afc25ac8ef41bc7c9a6b7d73aa3672f4`, `load_artifact()` OK, 49/533/112/439/125 rows per source matching DOM counts, 19 tilde aliases restored, 1,259 typed metadata blocks, 38 explicit "not supplied", no fruit-slicer, no remote dependencies, under the 4 MB delivery ceiling.
- Full suite **698 passed, no xfails**, exit 0. Commit `7869a97` pushed; CI run `36856918737` started on it.
- **Still not live-verified:** provider binding pins, news/summary validation, Skills.sh detail selection. Regression-tested only. `Catalog expiration date` renders 0 times because the saved state predates the adapter retaining those fields; a fresh discovery run is required.

## Hosted run 36860505208 — news truncation fix verified in production
- Commit `e756bfd`, success. 701 passed / 2 skipped. Publish: `{"artifact": "public/index.html", "bytes": 2887807, "sha256": "d068303c6e06b00b20d0d0feafb8c3add6260c0af246fdbfd1ddfac0dc046cfc", "delivered": true, "discord": "independently-read-back", "telegram": "receipt-confirmed"}`.
- **The news fix is confirmed live.** Both internal reports from that run render **`308 stories` with 308 rows** — previously `100 stories` against a 160-row database, silently truncated. Public export correctly still excludes news.
- A second truth defect surfaced from that same log and was fixed in `d76d458`: `save_items` logged `({len(items)} total)` — the *batch* size labelled as a running total. It read `(160 total)` while 308 stories were retained. Now reports the real retained row count. Full suite **705 passed**.
- Real Chromium QA against the previous hosted artifact: **86 assertions, 0 failures** at 390px/1440px × JS on/off, offline. 1,723 rows, per-source counts exact, 1,685 typed blocks + 38 honest not-supplied markers = every row covered, 1,790 links all on vetted hosts, 1,760 details toggling, 1 network request, zero errors, locked design confirmed. Evidence: `docs/release-hosted-artifact-verification.md`.

## Hosted CI verification — run 36856918737 (success)
Commit `7869a97`, started 2026-10-01T11:41:11Z, completed successfully.
- Clean-runner regression gate: **696 passed, 2 skipped in 44.11s**. The 2 skips are the Chromium-absent guard, expected on an unconfigured local run; the hosted run installs Chromium.
- Publish step: `{"attachment": "index.html", "delivered": true, "discord": "independently-read-back", "sha256": "ccaea0380b98cf01398aa5f2961ca8aee8451afcc7b359279991ea4b9a2c5ff6", "telegram": "receipt-confirmed", "url": "https://eli-lain-intel.netlify.app/"}`
- The published sha256 differs from the local `4536450237…` because the hosted run performed a **fresh discovery and news fetch** before export. That is the first run where the new adapters, receipt state, cache/save split and full public projection all executed together in production conditions.
- Delivery now: exact `index.html` bytes attached to both channels, Discord attachment independently read back, and `data/delivery_receipts.json` saved even on failure.
