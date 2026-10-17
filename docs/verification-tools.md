# Broad tools discovery verification

## Integration contract

Owned files only: `src/intel_sources/tools.py`, `tests/test_intel_tools.py`, and this document. No commits or pushes.

```python
from intel_sources.tools import fetch_tools

result = await fetch_tools(
    client,                      # caller-owned httpx.AsyncClient; also works with MockTransport
    skills_token=skills_token,    # caller passes VERCEL_OIDC_TOKEN, or None
    github_periods=('daily', 'weekly', 'monthly'),
)
```

Returns `{'items': [...], 'sources': [...]}`. Every item has `id`, `headline`, `source`, `summary`, `url`, `project_types`, `evidence`, and `fingerprint_data`. Source names **exactly match** item sources: `skills-sh` and `github-trending`. Sources contain UTC `checked_at`, `status`, `item_count`, `error`, `url`, and structured `coverage`.

IDs are stable across leaderboard periods: `skills:{official-source}/{slug}` and `github:{owner/repository}` (GitHub identity is case-insensitive). Public `/site/domain/slug` routes map to official `domain/slug` identities. One row merges all observed skill views or GitHub periods. Duplicate entries in the same view preserve the first/best rank; counts distinguish scanned rows from unique items. No top-15, star-threshold, language, or user-stack filtering.

Dependencies: `httpx` and `beautifulsoup4`, present in the working virtualenv. The parent owns dependency declarations and package installation; rerun editable installation after adding the new package or run with `PYTHONPATH=src`. No `__init__.py` was added by this task.

## Verified upstream interfaces and scope

Primary documentation checked on September 30, 2026:

- https://skills.sh/docs/api — `GET /api/v1/skills`, views `all-time`, `trending`, `hot`, zero-indexed `page`, and `per_page` up to 500; Bearer authentication uses the project's Vercel OIDC token. Responses use `data` and `pagination.hasMore`. Hot entries additionally expose `installsYesterday` and `change`.
- Public rendered leaderboard fallback: https://skills.sh/, https://skills.sh/trending, https://skills.sh/hot.
- Actual GitHub Trending HTML: https://github.com/trending?since=daily, https://github.com/trending?since=weekly, https://github.com/trending?since=monthly. No invented Trending REST API or search approximation.

Implementation limits:

- With an explicitly supplied token, API monitoring scans at most **3 pages of 500 requested rows per view**, stopping earlier when `hasMore` is false. Coverage records exact pages, observed unique counts, upstream-reported totals, and remaining-pagination flags. Capped scans are `partial`, never presented as the complete catalog.
- Without a token, it fetches all rows actually rendered in each of the three public pages. This is always `partial`: no undocumented API, guessed page query, or unrendered infinite-scroll rows are fetched. If authenticated discovery fails, real public HTML provides fallback while API errors remain visible.
- GitHub fetches every repository row in each requested unfiltered period page. Source status is aggregate `ok`, `partial` when a period fails but other rows are retained, or `error` when no usable rows exist. An empty period tuple is explicitly `skipped`.
- Metadata enrichment is limited to **40** missing-description skill entries, with at most six requests in flight. It reads only public HTML meta descriptions and topic labels. Queued requests stop after a 429; coverage reports actual attempts, successes, errors, and unscanned entries. It never fetches API file trees, runs commands, installs skills, follows installation links, or executes page scripts/prompts.

Ranks and stars gained remain period-specific, including original displayed star text. Total stars, forks, and language are separate evidence. Public skill install displays can be rounded (`K`/`M`); their original text is retained. Hot change text is preserved without treating it as an all-time count.

Tags cover web, mobile, data, automation, agents, game, devops, design, security, and documentation. Each inferred tag records the matched observable term and its field (headline, description, or topic). These are **keyword inferences, not verified capabilities**; unmatched entries keep an empty tag list rather than being filtered out.

Fingerprints include identity-adjacent content, descriptions, inferred tags, language, origin/type, topics, and duplicate flags. They deliberately exclude ranks, view/period membership, stars, installs, counters, fetch timestamps, and transient metadata status. Metrics-only changes do not make every item repeatedly new. Discovery explicitly records advisory-only observation and unknown creation date: first-seen means local observation, **not actual creation**.

HTTPS and exact official-host allowlists apply before requests and before returning item URLs. Redirects are followed manually and checked before contacting each destination. Userinfo, nonstandard ports, traversal/encoded identifier paths, unsafe schemes, unrelated hosts, and mismatched API identities are rejected. The supplied bearer token is recursively redacted if an upstream response echoes it. The caller/report layer must continue escaping untrusted text when rendering.

## RED → GREEN execution evidence

Each feature slice was tested before its corresponding implementation, using injected `httpx.MockTransport`; no network-dependent tests or fabricated live output.

| Incremental slice | Observed RED | Observed GREEN |
|---|---|---|
| GitHub full-page rows + merged periods | 1 failed: missing `intel_sources` implementation | 1 passed |
| Public skill views + honest coverage | 1 failed, 1 passed: expected 52 observed fixture items, got 0 | 2 passed |
| Documented authenticated pagination | 1 failed, 2 passed: public route requested instead of API | 3 passed |
| API errors with public fallback | 5 failed, 3 passed: fallback items absent | 8 passed |
| Empty/block/login/HTTP handling + explicit skipped period | 1 failed, 14 passed: empty periods incorrectly `ok` | 15 passed |
| URL/redirect validation | 13 failed, 15 passed: unsafe rows accepted/redirect not followed | 28 passed |
| Broad explainable classification | 9 failed, 28 passed: empty tags | 37 passed |
| Bounded metadata description enrichment | 1 failed, 37 passed: missing summary | 38 passed |
| Duplicate rank retention + malformed optional fields | 1 failed, 39 passed: dict headline caused TypeError | 40 passed |
| Visibility/invalid period/stale login markup | 3 failed, 40 passed | 43 passed |
| 429 metadata circuit breaker | 1 failed, 43 passed: 25 requests made despite rate limit | 44 passed |
| Content fingerprints + advisory newness | 1 failed, 44 passed: missing discovery semantics | 45 passed |
| Upstream bearer echo redaction | 1 failed, 45 passed: token leaked in returned description | 46 passed |

Final owned test run:

```text
PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_intel_tools.py -q --tb=short
46 passed in 0.29s
```

`py_compile` succeeded for both Python files. Scoped `git diff --check` returned no errors. The API cap test verifies explicit partial status against a simulated million-item upstream total; it does not claim a million items were monitored.

A broader concurrent-workspace suite run returned `189 passed, 2 failed, 6 errors, 3 warnings`. Failures were outside these owned files: catalog credential echo and provider readonly connection closure; reporter errors were missing Playwright Chromium executable. Other workers own those areas. This is not a claim that the whole repository is green.

## Actual live smoke

Final network smoke completed **2026-09-30T13:14:19.666498+00:00**, using a normal supplied `httpx.AsyncClient()` without auto-redirect assumptions and **no Skills OIDC token**.

| Page | Result | Observed rows |
|---|---|---:|
| Skills all-time public HTML | ok | 183 |
| Skills trending public HTML | ok | 175 |
| Skills hot public HTML | ok | 196 |
| GitHub Trending daily | ok | 17 |
| GitHub Trending weekly | ok | 18 |
| GitHub Trending monthly | ok | 23 |

Programmatic merging produced **484 unique observed skills** (`partial`) and **49 unique observed repositories** (`ok`): **533 unique rows from these scanned pages**, not the whole catalog. Skill metadata budget 40: 29 actual attempts, 27 enriched, 2 errors, 455 not scanned. Public metadata rate limiting was encountered, queued requests stopped, and the source error explicitly reported `2 skill metadata requests failed; leaderboard rows retained`.

Real enriched samples included `vercel-labs/skills/find-skills` (agents/automation), `mattpocock/skills/grill-me` (design), and `vercel-labs/agent-browser/agent-browser` (agents/automation/web), with observed meta descriptions supporting those inferences.

Authenticated API behavior is proven deterministically against the official documented schema, **not live-token verified**; no credential was supplied. Live HTML discovery is verified for all six requested leaderboard/period pages. No external skill was installed or executed.
