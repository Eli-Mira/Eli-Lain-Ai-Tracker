# Skills.sh + GitHub Trending customer-release audit

**Audit date:** 2026-10-01 UTC. **Worktree:** `C:/tmp/eli-lain-tracker` (private repository). **Scope owned:** `src/intel_sources/tools.py`, new `tests/test_release_tools.py`, and this evidence document. Other workers are changing the evaluator, public projection, storage and templates concurrently; their changes are not attributed to this adapter task.

## Outcome and release boundary

The public sources are reachable and genuinely used. The final fresh adapter observation retained **461 unique Skills.sh skills + 49 unique GitHub repositories = 510 discoveries**. A bounded **40-request skill detail pass produced 35 useful metadata observations, five empty responses, no errors, and 421 unscanned candidates**. GitHub descriptions were available for **47 of 49 repositories**. These are observed/self-reported metadata, not integration tests, safety reviews, repository creation dates, license validation, free entitlement, or evidence that any discovered code works in Hearth/gesture-control.

Confirmed adapter defects were reproduced with RED tests before fixing: false useful-enrichment accounting; cross-skill redirect attribution; explicit bearer forwarding across origins; query/fragment identity normalization; missing detail provenance; redirected-view misattribution; and ambiguity between initial server HTML and hydrated DOM counts. Scoped adapter/store verification is **63 passed**. Latest shared full-suite observation is **516 passed, three failed**, all three in the concurrently added `tests/test_release_public_template.py`, outside this task's write scope. This is **not** a claim that the complete customer release is green.

No discovered repositories/skills were installed or executed. No authenticated live API request, credential inspection, notifications, commit, push or deployment was performed. The real `data/intel_state.json` was read but never used as a smoke-test write target. Its SHA-256 remained:

```text
4f931776e456a0dee6b3eb4674336e2fe705b749e7d7e4c4f4b69833eceac4b0
```

## Exact environment and commands

Run from `C:/tmp/eli-lain-tracker`, using the repository's `.venv/Scripts/python.exe`, not system Python/pip. Probe scripts and generated artifacts are under `C:/Users/emadg/AppData/Local/hermes/cache/scratch/`; they import the actual adapter and actual store/report modules, not a synthetic implementation.

```bash
# Root-cause source/history discovery; no modifications.
git status --short
git log -3 --oneline
date -u '+%Y-%m-%dT%H:%M:%SZ'

# Initial real HTTP views + documented API probes + actual pre-fix collector.
.venv/Scripts/python.exe 'C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_tools_probe.py'

# Each regression was executed RED before the associated production patch.
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py -q
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py::test_detail_redirect_cannot_attach_another_skill_capability -q
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py::test_api_bearer_is_not_forwarded_to_redirected_origin -q
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py::test_skill_identity_does_not_silently_normalize_query_or_fragment -q
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py::test_public_detail_provenance_survives_store_without_forging_github_metadata -q
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py::test_redirected_view_is_not_mislabeled_as_requested_coverage -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-pytest'
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py::test_empty_detail_is_not_useful_enrichment -q

# Latest scoped GREEN (11 new adapter cases + existing tools/store cases).
.venv/Scripts/python.exe -m pytest tests/test_release_tools.py tests/test_intel_tools.py tests/test_intel_store.py -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-pytest'
# Actual latest output: 63 passed in 0.47s

# Fresh real data -> isolated IntelStore -> evaluator -> real Lain template.
.venv/Scripts/python.exe 'C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_tools_trace.py'

# Chromium public views, raw-response versus hydrated-DOM counts,
# offline report filtering and JavaScript-disabled full inventory.
.venv/Scripts/python.exe 'C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_tools_browser.py'

# Full suite, including other workers' in-progress changes; pipe status preserved.
set -o pipefail
NOTIFICATION_CHANNEL=none PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' .venv/Scripts/python.exe -m pytest tests -q --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-full-pytest' 2>&1 | tee 'C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-audit/full-suite-latest.txt'
# Actual latest output: 3 failed, 516 passed in 12.02s; exit 1.

git diff -- src/intel_sources/tools.py
```

The very first provenance test used pytest's default disposable temp location; subsequent store tests explicitly used the Hermes scratch `--basetemp`. No test wrote real discovery state. The first shared full run, before other workers added their new release tests, passed 484 tests; that earlier result does not supersede the later full-suite failures.

## Live source evidence and timestamps

### Initial HTTP observation, before fixes

The public probe saved actual response HTML, hashes and observation times in `release-tools-audit/pages.json` and `page-0.html` through `page-6.html`.

| Requested public view | UTC request start | HTTP result | Initial HTML row count |
| --- | --- | --- | ---: |
| Skills.sh all-time `/` | 2026-10-01T04:40:18.140576Z | 200 after `www.skills.sh` redirect | 188 |
| Skills.sh `/trending` | 2026-10-01T04:40:18.864473Z | 200 after `www.skills.sh` redirect | 166 |
| Skills.sh `/hot` | 2026-10-01T04:40:19.429497Z | 200 after `www.skills.sh` redirect | 182 |
| GitHub `?since=daily` | 2026-10-01T04:40:20.007329Z | 200 | 17 |
| GitHub `?since=weekly` | 2026-10-01T04:40:21.656011Z | 200 | 18 |
| GitHub `?since=monthly` | 2026-10-01T04:40:23.248662Z | 200 | 23 |

The initial collector deduplicated these views into 470 skills and 49 repositories. It claimed 40 enrichments, but only 35 skill summaries were nonempty; the five remaining details contained neither useful descriptions nor topics. `before.json` preserves the actual pre-fix result. Hot rankings changed during the audit: the later observation is a separate snapshot, not a conflicting assertion about a fixed catalog size.

### Final real adapter observation

Final network run: **2026-10-01T04:52:34.021410Z–04:52:47.005429Z**. The source-level timestamps are collection-start observations, not timestamps for every individual HTTP response: Skills.sh **04:52:34.104851Z** and GitHub **04:52:42.136395Z**. Enriched details now additionally retain their individual `metadata.checked_at`.

| Source | View counts | Deduplicated count | Source status | Capability metadata available |
| --- | --- | ---: | --- | --- |
| Skills.sh | all-time 188; trending 166; hot 176 | 461 | partial; error null | 35 descriptions; five topic-bearing rows (overlap with descriptions); five empty details; 421 unscanned |
| GitHub Trending | daily 17; weekly 18; monthly 23 | 49 | ok; error null | 47 repository descriptions; two missing |

All six per-view/page statuses were `ok`. Skills.sh source status remains `partial` because public initial HTML is bounded coverage, not the entire skills catalog. `rendered_rows` remains the legacy per-view field name; the added `coverage.representation=server-rendered-initial-html` and revised scope define exactly what it counts. Detail coverage reconciles as `40 attempted = 35 enriched + 5 empty + 0 errors`; `461 candidates = 40 attempted + 421 not_scanned`.

### Actual Chromium, after bounded hydration settle

Chromium anonymous public-page observations at **04:54:12.958203Z–04:54:29.860569Z** returned 200 for all six views. For each response the script parsed the actual HTTP body and separately counted the final browser DOM after a bounded 1.5-second settle:

| Public view | Initial response rows | Hydrated DOM rows |
| --- | ---: | ---: |
| Skills all-time | 188 | 31 |
| Skills trending | 166 | 26 |
| Skills hot | 176 | 31 |
| GitHub daily | 17 | 17 |
| GitHub weekly | 18 | 18 |
| GitHub monthly | 23 | 23 |

**Important:** the Skills.sh server response and hydrated client DOM are not the same representation. The audit did not scroll/crawl client-side pagination, and does not claim the hydration mechanism's exact implementation. Do not describe the adapter's initial-HTML row count as the current visible browser row count. The scope label was corrected rather than replacing the broader initial-HTML observation with a viewport-sized sample.

Screenshots of Skills trending and GitHub daily are `public-view-1.png` and `public-view-3.png`. Browser observations and filter assertions are in `browser.json`.

## Official Skills.sh API: checked, not assumed

Primary reference: `https://skills.sh/docs/api`, retrieved 200 at **2026-10-01T04:40:17.294034Z** (redirected to `https://www.skills.sh/docs/api`). The documented API requires a verified Vercel OIDC bearer token. It documents listing, search, curated, detail and audit endpoints. Listing supports `all-time`, `trending` and `hot`, zero-based pages and up to 500 rows/page; search supports bounded keyword/semantic queries. Hot compares the current hour to the same hour yesterday. The public trending page describes this week; do not conflate its installs with GitHub's daily stars or a repository launch date.

Unauthenticated requests to the exact documented listing (`/api/v1/skills?view=all-time&per_page=1`, **04:40:24.913009Z**) and search (`/api/v1/skills/search?q=sql&limit=1`, **04:40:25.428149Z**) returned **401 Unauthorized**. No endpoint invention or authentication bypass was attempted. Authenticated live catalog/search/detail quality is therefore **blocked/unverified in this audit**. The existing optional API branch is deterministic-test verified, not live authenticated verified. Its explicit limit is three pages/view × 500 rows/page across three views; overlap reduces unique rows, and `has_more=true` correctly remains partial. No claim of full-catalog coverage is justified by this implementation.

## Confirmed findings, root causes and fixes

### High severity: incorrect provenance/security boundaries — fixed

1. **Bearer forwarded across origins.** `_get` manually re-used explicit headers on every allowlisted redirect. `skills.sh -> www.skills.sh` is a different origin even though both hosts are approved for public pages. The failing test observed nine redirected requests carrying the synthetic bearer. The fix refuses authenticated cross-origin redirects *before contacting the next origin*. Credential-free canonical public redirects still work. External/non-HTTPS/credentialed/bad-port/traversal links continue to be rejected by existing tests. Caller contract remains the dedicated credential-free HTTP client used by `main.discover_tools`.
2. **Different skill's capability attached to original identity.** `_skill_metadata` validated only that returned markup had `main/h1`; a redirect to a different allowed skill supplied an unrelated Android-game summary for `owner/repo/sql-tool`. RED returned `Android game engine` for the wrong identity. The fix validates final HTTPS host/path identity against `evidence.skill_id` before extracting description/topics, retains the leaderboard row and marks its detail error.
3. **Redirected leaderboard falsely attributed to requested view.** GitHub daily redirected to weekly and was persisted as daily; Skills all-time/trending redirected to hot and were persisted under all three views. RED reproduced both. The fix validates final page path/period/query/fragment against the requested scope. Failed views now report errors instead of fabricated coverage; usable sibling views survive.
4. **Query/fragment identity was silently normalized.** Both untrusted query-bearing and fragment-bearing skill links became apparently clean identities after path-only parsing. RED produced a row where rejection was expected. `_path_identity` now rejects both before any canonical row is accepted, rather than stripping an invalid literal token and calling it validated. Normal GitHub period queries remain valid because they are discovery-page parameters, not repository identity links.

### Medium severity: useful metadata/coverage accounting — fixed

5. **Fetched detail was counted as useful enrichment.** Every 200 detail incremented `enriched`, even after generic installation boilerplate was intentionally discarded. RED reported one enrichment for an empty detail. Useful now means nonempty capability-description metadata or topics: empty pages receive `metadata.status=empty`; independent `descriptions`, `topics_available` and `empty` counters prevent 200/fetched from implying useful.
6. **Missing verifiable detail provenance.** A successful detail only stored the requested URL and field name, losing the actual final response URL, response fingerprint and per-detail observation time. RED failed on missing `final_url`. Validated details now persist final URL, HTTP status, UTC timestamp and SHA-256 of the actual response bytes. These remain ordinary source evidence; they are deliberately **not** forged into GitHub `official_metadata`, whose evaluator contract requires GitHub API/repository-bound provenance. The hash is not a security verdict and does not enter the change fingerprint.
7. **Server versus browser coverage wording.** Side-by-side browser/body evidence showed materially different row counts. Coverage now explicitly declares its initial-server-HTML representation and warns that hydrated browser rows can differ. It still exposes all observed rows, does not install anything or silently reduce discovery scope to a viewport sample.

### Open customer-usefulness limitations — not silently changed

- **Detail selection is popularity/order-biased.** The first 40 description-missing rows consume the metadata budget in merged all-time-first order. Of 461 skills, 421 remain unscanned. This is a major usefulness bottleneck, not evidence that those 421 skills lack capabilities. For example `skills:obra/superpowers/test-driven-development` was genuinely present at all-time rank **255**, trending rank **348**, but had empty summary/tags and `metadata.status=not-scanned`. Raising budget, rotating coverage, adding project-aware selection or documented authenticated search is a scope/product decision; this task did not silently hardcode project identities or enlarge the network budget.
- **Tags are explainable keyword inferences, not capabilities or native-stack fit.** The final observed tag memberships were agents 62, automation 15, design 34, web 29, documentation 5, data 13, mobile 12, devops 2, security 7. Memberships overlap. No PySide6, camera-latency, transaction-correctness, payment-device, licensing or support proof follows from these tags. Broad adapter discovery is intentionally retained rather than filtered to guessed projects.
- **API live quality remains blocked on documented authentication.** Public views work; API/search returned 401 without a token. A token's existence or success was not assumed or fabricated. API fallback preserves successful API rows, public rows, nested API failure coverage and source partial status; bearer values are redacted from final rows/errors and never sent on public fallback/detail requests.
- **Requests are bounded by count, not a single adapter wall-clock deadline.** Metadata limit 40/concurrency six, redirect cap four responses, 30-second per-request HTTP timeout; API cap three pages/view. There is no overall wall-clock guard for this tools collector. Count-bounded must not be advertised as a strict runtime SLA. Persistent slow redirects could still take materially longer than a normal run; parent owns any broader orchestration decision.
- **Malformed row handling remains per-view, not per-row.** A malformed row can stop parsing later rows in that view; already collected rows and sibling pages survive with error/partial coverage. Existing unsafe-link tests verify fail-closed behavior. Per-row quarantine would need an explicit acceptance policy, not a silent change to source-error semantics.

## Real data trace to persisted state and report fields

1. **Network -> adapter.** Skills anchors provide literal IDs, origin, name, view rank, installs and hot change text. GitHub `article.Box-row` provides repository identity, description, language, total stars/forks and per-period rank/growth. `_row` marks these as advisory leaderboard observations; creation date stays null. `_classify` keeps keyword matches and includes meaningful capability fields in `fingerprint_data`, but popularity counts/rank, per-detail timestamp and hash do not generate fake capability updates.
2. **Adapter -> isolated `IntelStore`.** The actual 510-row payload was persisted at `release-tools-audit/final/isolated-intel-state.json`, re-read and compared. Baseline true; changes zero; stored row counts agree with source counts. First-seen is the local baseline observation **04:52:47.023950Z**, not creation. Item `checked_at` is its source observation timestamp. New regression coverage proves a subsequent failed adapter fetch preserves prior evidence and first-seen/checked-at while making retained rows stale, without reporting empty fetches as fresh success. Existing store tests cover metrics-vs-meaningful changes, corruption refusal and atomic-replace failure.
3. **Concrete enriched skill.** `skills:vercel-labs/skills/find-skills` maps name to `headline`, public meta description to `summary`/`evidence.description`, topic `Agent workflows` to `evidence.topics`, and inferred agents/automation to `project_types` with exact matching evidence. Final detail URL is `https://www.skills.sh/vercel-labs/skills/find-skills`; detail observation **04:52:37.380252Z**, HTTP 200, SHA-256 `427a7ed5de75dd160fa08b3639bbb06e2fc279e0266e12f9ea9726ddc8ec2a42`. All-time rank 1 / installs 3.6M; trending rank 10 / installs 16.9K. These are source claims and leaderboard metrics, not adoption recommendations.
4. **Store -> internal report.** The real Lain renderer was fed persisted rows with evidence dictionaries converted to its expected list shape (as `main.generate_report` does), source records and evaluator groups. BeautifulSoup and actual Chromium both found **510 `.discovery-item` nodes**, split skills 461 / GitHub 49. `headline`, `summary`, `url`, `id`, `project_types`, freshness and full evidence reach the inventory; source coverage reaches the source panel. The scratch artifact is `isolated-tools-internal.html`, not a deployed customer report.
5. **Filtering -> real browser.** With external requests blocked, GitHub source filtering showed exactly **49** rows; Skills + data intersection showed **7**; a nonexistent query showed **zero** with the visible empty-state and `0 of 510 discoveries shown` counter. JavaScript disabled showed all **510** rows. This proves filter behavior over real adapter output, not merely a small synthetic fixture. Untagged skills must remain visible under all-project filters.
6. **Evaluation -> public projection (read-only trace).** The actual evaluator reviewed **12 identities**, leaving **498 unreviewed** among 510 candidates. Active groups were Hearth POS, gesture-control and data/AI; fruit-slicer was absent after the parent's active-project fix. This task did not edit or claim ownership of that fix. The default public per-source cap exported **100 skills + 49 repositories = 149 rows**. TDD was absent from that alphabetically capped inventory despite existing in the source/evaluation. As of the **04:56:53Z** readback, the other worker's new `public_metadata` included typed leaderboard rank/install fields, but public summaries remained fixed advisory text and the detail SHA/timestamp/capability description was not exported. The safe projection must not be weakened by dumping raw internal evidence. Any useful public capability projection is owned by the public/template worker and needs its own allowlist/provenance tests.

## Failure-path coverage and latest blockers

The new release file has **11 parametrized test cases**. In addition to the RED/GREEN bugs above, it checks topic-only usefulness, budget accounting, scripts never copied/executed, failed-fetch stale retention, actual store persistence, mixed API-success/public-fallback preservation and bearer isolation. Existing adapter tests exercise 401/429/timeout/invalid JSON/missing pagination, malformed/login/blocked/parser-changed pages, unsupported periods, safe-host redirects, absent typed values, deduplication, page caps, rate-limit queue stopping, secret echoes/redaction and popularity-insensitive fingerprints. These injected HTTP responses test the actual adapters; they do not establish current external failure incidence.

Latest out-of-scope shared-suite failures (log `full-suite-latest.txt`):

- `test_public_layout_retains_original_sections_first_and_does_not_claim_unchecked_changes`: original public section ordering assertion fails.
- `test_named_lain_reporter_never_silently_renders_an_unrelated_fallback`: renderer still permits unrelated fallback instead of raising.
- `test_public_excludes_key_scoped_discoveries_even_under_a_public_source_name`: key-scoped/authenticated discoveries are still included in the forged-source regression fixture.

These are release blockers for their owners, not failures in `test_release_tools.py`. Earlier out-of-scope storage/public typed-metadata RED tests subsequently passed; do not report those historical failures as still open. The repository is being edited in parallel, so the parent must re-run the full suite after all workers finish before asserting release acceptance.

## Evidence files and retention

Repository deliverables:

- Modified `C:/tmp/eli-lain-tracker/src/intel_sources/tools.py`.
- Created `C:/tmp/eli-lain-tracker/tests/test_release_tools.py`.
- Created `C:/tmp/eli-lain-tracker/docs/release-tools-audit.md` (this document).

Actual raw public observations / isolated artifacts:

- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_tools_probe.py`, `release_tools_trace.py`, `release_tools_browser.py` (reproducible probes).
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-audit/pages.json`, `page-0.html` … `page-6.html`, `before.json` (initial evidence).
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-audit/final/after.json`, `trace.json`, `isolated-intel-state.json`, `isolated-tools-internal.html` (final live/persist/report evidence).
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-tools-audit/browser.json`, `public-view-1.png`, `public-view-3.png`, `scoped-final.txt`, `full-suite-latest.txt`.

Scratch is ephemeral and may be pruned after inactivity; the factual observations, commands, hashes and acceptance limitations are preserved in this repository document. JSON/HTML raw snapshots are not public exports and were not committed or published. Git status includes other workers' concurrent files; this task did not edit them.
