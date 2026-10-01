# Real artifact verification — hosted CI run 36856918737 and the news truncation defect

Parent-run, from the actual published bytes. Nothing in this file is a worker claim.

## 1. Hosted artifact read back from CI, not regenerated

```bash
gh run download 36856918737 -D <scratch>/ci-36856918737
```

| Artifact | Bytes | sha256 |
|---|---|---|
| `elain-public-36856918737/index.html` | 2,583,106 | `ccaea0380b98cf01398aa5f2961ca8aee8451afcc7b359279991ea4b9a2c5ff6` |
| `elain-report-36856918737/eli-lain_20261001_114251.html` | 4,086,077 | `affb70b913e9d8597900eb9c6e3b15fedc18f51fbfc5b3c2b65a2f9dffbc8ec7` |
| `elain-report-36856918737/eli-lain_20261001_114406.html` | 4,596,850 | `414179affa1b960ddefac6273f6fef04c56b74a9d6124ddd5748a6780c062c0c` |

The public file's sha256 matches the publish step's logged `sha256` exactly. Under the 4 MB delivery ceiling.

### Row reconciliation (hosted, fresh fetch)

```
github-trending      60
openrouter-models   638
openrouter-providers 112
skills-sh           650
unorouter-models    263
                    ---
                    1,723
```

The hosted run fetched more than the local saved state (1,255 rows), which is why the sha256 differs from the local export.

### Typed fields that only a fresh fetch can populate

| Label | Count | | Label | Count |
|---|---|---|---|---|
| Listed input price | 845 | | Catalog knowledge cutoff | 180 |
| Listed output price | 845 | | Reasoning default enabled | 162 |
| Input modalities | 638 | | Headquarters country | 73 |
| Output modalities | 638 | | Language / Stars / Forks | 60 each |
| Detail metadata status | 609 | | Catalog expiration date | **27** |
| Context | 569 | | Datacenter countries | 26 |
| Max output | 561 | | monthly / weekly rank | 25 / 21 |
| Supported parameters | 507 | | Catalog alias target | **19** |
| hot rank | 354 | | Reasoning supports max tokens | 11 |
| Reasoning mandatory | 332 | | Catalog original input/output price | 188 each |
| Listed cache read price | 303 | | all-time / trending rank | 188 / 184 |
| Catalog free/online/chat flag | 263 each | | | |

`Catalog expiration date` (27) and `Catalog alias target` (19) render in the hosted artifact — the field that showed 0 times locally is populated once the adapter actually retains it. **34 of 40 probed labels populated.** 1,724 metadata blocks with only 38 explicit "not supplied". 2,406 "not supplied" markers overall, i.e. individual fields the source does not publish.

**Leak audit on the real artifact:** the only `freellmapi` string is the public trending repo `github.com/tashfeenahmed/freellmapi`. No `Eli-Mira`, no local path, no credential shape, no traceback. The four `sk-` occurrences are the two legitimate restored slugs.

## 2. Real Chromium QA against the hosted file — 86 assertions, 0 failures

Not a synthetic fixture: the 2.58 MB published file, at 390px and 1440px, JS enabled and disabled, context `offline=True`.

Every viewport/mode pair produced identical, correct results:

```
visible rows      1,723  == expected
per-source counts 60 / 638 / 112 / 650 / 263  (exact match to publisher)
metadata          1,685 typed blocks + 38 not-supplied markers = 1,723 (every row covered)
links             1,790, every href on a vetted public host
details blocks    1,760, all open and close
network requests  1 (the file itself) — nothing remote, offline enforced
page/console      0 errors
locked design     body rgb(5,7,10), h1 rgb(111,255,233), 640px column
overflow          none at 390px
counter           "1723 of 1723 discoveries shown", contrast ratio passing
filters           source filter -> 650 rows, metadata survives filtering, live search finds rows
no-JS             filters disabled, noscript disclosure rendered in the DOM
```

## 3. Real defect found and fixed: the news section silently truncated

The internal report's news section read **`100 stories`** with **no disclosure of any truncation**, while the same CI log recorded `Saved 78 new items to SQLite (160 total)`.

Root cause: `SQLiteStore.get_items` defaults to `limit=100`, and `NewsTracker.generate_report` called `self.sqlite.get_items(days=1)` with no limit. Any day producing more than 100 stories rendered exactly 100 and claimed to be 100 stories — the same string a genuinely quiet day produces. The adjacent discoveries section had this right ("N of N discoveries shown"); news did not.

The public export correctly excludes news entirely (`News excluded from this public export — not assessed.`), so this affected only the internal report and its Telegram/Discord delivery.

Local confirmation on `data/news.db`: 120 rows retained, 100 rendered, the 20 dropped rows scoring at or below the retained cutoff — a pure limit artifact.

Fix:
- `SQLiteStore.count_items(days)` — retained total independent of any list cap.
- `generate_report(..., news_limit=1000)` — an explicit caller ceiling instead of a silent default.
- `news_saved_total` threaded to the reporter as a **keyword-only** parameter (adding it positionally broke `test_legacy_positional_render_arguments_and_missing_optional_fields`, caught by the suite).
- Template prints `N of M stories retained` only when the ceiling actually binds, and the plain count otherwise.

RED first: the 160-row case asserted on `'100 stories'`. GREEN: 5 passed. Full suite: **703 passed**.

## 4. Live source truth from the hosted run

| Source | Result |
|---|---|
| GitHub search | OK, 15 items |
| 13 GitHub orgs | OK, **0 items each** — org-wide release monitoring finds nothing; not an error |
| 20 GitHub latest-release probes | 5× 200 OK (1 item each), 15× **404 treated as healthy no-release** |
| Reddit RSS | `/r/MachineLearning` OK 10 items; **5 subreddits circuit-broken on HTTP 429** (anonymous rate limiting) |
| Hacker News | 4 queries via `search_by_date`, OK 10 items each |
| RSS aggregate | OK, 70 items |
| Hugging Face | models 27 + papers 5 = 32 items |
| YouTube | 3 channels, 5 items each = 15 items |
| **Total fetched** | **259 items → 78 new, 9 breaking, 160 retained** |

The GitHub org/release subfeeds consume most of the 35-second adapter budget for near-zero yield. That is a real cost/coverage observation, not a correctness defect, and it is recorded here rather than changed without Eli's call.

## 5. Skills.sh detail selection — verified live on the current state

The 40-slot metadata budget after the worker fix:

```
lanes: view:all-time 7 · view:trending 7 · view:hot 6
       workflow:development 4 · workflow:data 4 · workflow:testing 4
       workflow:security 4 · workflow:project-stack 4
metadata status: ok 42 · empty 3 · not-scanned 591
```

The workflow lane reached skills that all-time popularity alone would never surface: `systematic-debugging`, `requesting-code-review`, `test-driven-development`, `verification-before-completion`, `supabase-postgres-best-practices`. The first-40 bias is genuinely fixed.

**New observation, not yet fixed:** 33 skill slugs are published by more than one owner — 636 rows represent only **580 distinct capabilities**. Worst clusters: `agent-browser` ×7, `ai-video-generation` ×6, `remotion-render` ×4. Identical slugs from different owners consume separate rows and separate metadata slots. Recorded, not changed.

## 6. Still not live-verified

- Provider binding pins: no router probe was run in this pass (CI logs `freellmapi DB not found`, which is expected — Mira holds the DB).
- UnoRouter: catalog fetched OK (263 rows) but no independent billing/entitlement check was performed.
- Exact-byte dedupe, ambiguous-response duplication and concurrent-publisher locking remain open per `docs/release-delivery-continuity-followup.md`.
