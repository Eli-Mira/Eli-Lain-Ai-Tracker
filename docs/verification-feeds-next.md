# Individual-feed reliability verification

Observation date: **2026-10-01 UTC**. This is a collection check, not a publication, recommendation, provider-inference, or notification check.

## Scope and actual configuration

Changed only `src/news_tracker/adapters.py`, `src/news_tracker/health.py`, `tests/test_feed_reliability.py`, and this document. No main entry point, template, workflow, schema, recommendation/publication module, router database, or deployment was edited by this work.

The inspected `main.py` uses `get_all_adapters()` without an adapter config and already has a 45-second outer adapter timeout. The actual defaults are seven adapters: GitHub, Reddit, Hacker News, arXiv, RSS, Hugging Face, and YouTube. RSS has 17 feeds; Reddit six subreddits; HN eight keywords; arXiv five categories; YouTube three channels; HF two pages. GitHub searches once, enumerates nine organizations, and considers at most ten repositories per organization. PapersWithCode is a class but is **not** in the configured adapter factory.

Reddit authentication and YouTube API fallback require explicit config; this main path therefore uses anonymous Reddit RSS and YouTube RSS. GitHub can read its existing token from the environment; the live verification below explicitly removed that header and used public endpoints only. No credentials or private configured destinations were recorded.

## Fixes

- Each subfeed has its own timeout and failure boundary, with bounded concurrency. Successful sibling results survive blocked/failed feeds and the internal collection deadline.
- Defaults: **5 seconds per subfeed**, **35 seconds total per adapter**, **four concurrent operations**. GitHub's enumeration and release phases share the same total budget. A zero/exhausted budget launches no work. Queued feeds at the collection deadline are `not_attempted`, not invented HTTP failures.
- A local HTTPFetcher subclass retains the existing fetcher interface while returning HTTP failures immediately instead of sleeping inside HTTPFetcher on a 429. Requests retain host throttling, serialize throttle reservations, follow at most five redirects, and cap the final decoded response body at **1,048,576 bytes**.
- Health separates unobserved, successful, failed, and disabled records. Failure classification, last success/failure, consecutive failure count, and cooldown deadline are retained. Ordinary cooldown begins after three consecutive failures and lasts **300 seconds**. A 429 starts an immediate cooldown from numeric or HTTP-date Retry-After; absent/unusable values use 300 seconds; supported delays are clamped to **1–86,400 seconds**. Expired cooldown permits a new attempt but does not invent recovery; only a successful fetch resets failure history.
- RSS/Atom parsing checks an actual feed version and rejects malformed feeds and HTTP-200 HTML challenges. A valid empty feed is a successful zero-item fetch, not proof of an error.
- Feed identity in diagnostics/state is `adapter:SHA256-prefix`, not a private destination. Exception messages and item validation values are not logged. YouTube API credentials use the documented `X-Goog-Api-Key` header instead of URL query strings.
- PRAW listings run with separate per-worker clients, bounded request timeout, and no configured PRAW rate-limit sleep. The collector deadline includes listing conversion. Worker clients close on completion; no shared requests.Session is used by the configured worker path.
- Optional JSON persistence is atomic and round-trips cooldowns and observations. `get_all_adapters` shares a single tracker when a state path is supplied, preventing independent adapters from overwriting each other's rows.

## Official endpoint evidence and replacements

All URLs in this section are public publisher endpoints. No unofficial RSS proxy was substituted.

| Configuration | Observed old endpoint | Replacement and primary evidence |
|---|---|---|
| OpenAI Blog | `https://openai.com/blog/rss.xml` redirected to the new endpoint, HTTP 200, 1,240 entries at 00:14:50.703905–00:14:51.591239 UTC | Use the publisher's final canonical `https://openai.com/news/rss.xml`; direct check at 00:14:54.334378–00:14:54.848230 UTC also returned 200 and 1,240 entries. This was canonicalization, not a falsely claimed outage. |
| Google AI Blog | `https://blog.research.google/feeds/default/full/`: 404 at 00:14:50.729454–00:14:51.286097 UTC | Official `https://research.google/blog/` advertises `https://research.google/blog/rss/` in its own HTML; observed 00:30:57.003692–00:30:57.717963 UTC. The advertised feed returned 200, RSS 2.0, 100 entries, no parser error in a direct check starting 00:31:16.897165 UTC. |
| Mistral Blog | `https://mistral.ai/feed/`: 404 at 00:14:51.286097–00:14:51.794881 UTC | Official `https://mistral.ai/news/` advertises `/news/rss`; observed 00:30:57.717963–00:30:58.450505 UTC. `https://mistral.ai/news/rss` returned 200, 88 entries, no parser error at 00:14:54.339402–00:14:54.471248 UTC. The news HTML was truncated at 1 MiB; the feed link was present in the observed portion. |
| AI Explained | Old configured channel ID returned RSS 404 at 00:14:53.952592–00:14:54.334378 UTC | Official channel `https://www.youtube.com/@aiexplained-official` exposed canonical ID `UCNJ1Ymd5yFuUPtn21xtRbbw`. Its RSS returned 200, Atom, 15 entries at 00:30:58.450505–00:30:58.755295 UTC. |
| Two Minute Papers | Old configured channel ID returned RSS 404 at 00:14:53.954600–00:14:54.339402 UTC | Official channel `https://www.youtube.com/@TwoMinutePapers` exposed canonical ID `UCbfYPyITQ-7l4upoX8nvctg`. Its RSS returned 200, Atom, 15 entries at 00:30:58.755295–00:30:58.998329 UTC. |
| Yannic Kilcher | Old configured channel ID returned RSS 404 at 00:14:54.099789–00:14:54.446629 UTC | Official channel `https://www.youtube.com/@YannicKilcher` exposed canonical ID `UCZHmQk67mSJgfCCTn7xBfew`. Its RSS returned 200, Atom, 15 entries at 00:30:58.998329–00:30:59.095200 UTC. |

The initial public probes used four concurrent requests, a six-second socket timeout, an eight-second per-request outer limit, at most five redirects, and a 1-MiB observation body cap. Channel metadata came from official pages; the Two Minute Papers and Yannic page observations were truncated at that cap, with complete canonical IDs present in the observed portion. An initial probe formatting bug accessed a missing feedparser `version` attribute for non-feed Reddit responses; those five AttributeErrors are **not** claimed as endpoint failures. The actual adapter check below supplies the usable Reddit evidence.

Primary protocol references checked: `https://python-httpx.org/async` for streaming; `https://praw.readthedocs.io/en/stable/getting_started/multiple_instances.html` for PRAW's non-thread-safe instances; `https://prawcore.readthedocs.io/en/stable/code_overview/requestor.html` for request timeouts. The Google system-parameter table at `https://cloud.google.com/apis/docs/system-parameters` returned 200 in a check starting 00:45:09.775389 UTC and explicitly maps API keys to `X-Goog-Api-Key`.

## Strict RED → GREEN evidence

Each implementation slice was preceded by its failing regression command, with direct **exit 1**, and followed by a passing command, with direct **exit 0**. No output pipeline was used to infer test success.

Observed RED signals included:

- Health called a failed source `healthy` instead of `failed`.
- Blocked RSS, Reddit RSS, PRAW, HN, arXiv, HF, YouTube and GitHub feeds hit the outer deterministic TimeoutError instead of preserving the good sibling.
- 403/429 RSS responses returned items; HTTP-200 HTML/malformed feeds had zero failures instead of a parsing failure.
- A real HTTPX MockTransport 429 became `timeout` because the old fetcher slept on Retry-After, rather than retaining `http_429` and a cooldown.
- YouTube HTTP/API failures became timeout or healthy empty success instead of their observed HTTP failure.
- Six official RSS/channel endpoint assertions failed against the old constants.
- Optional state was never saved (FileNotFoundError); factory-created trackers were separate objects.
- PRAW's two workers shared one client identity instead of two separate bounded clients.
- An oversized response still supplied a news item; concurrent throttle calls peaked at four instead of one.
- API credentials were present in request URLs; item parse logs contained the private-value fixture.
- A zero collection budget started work, returned a news item and recorded a spurious failure.

**Final evidence:** JUnit XML was parsed programmatically: **30 feed reliability cases**, **399 full-suite cases**, **0 failures**, **0 errors**, **0 skipped**. Pytest reported `399 passed in 7.57s`, direct exit **0**, with no warnings. The suite includes other concurrent worktree changes; 399 is the observed worktree gate, not a claim that this task authored all of those tests.

Final command:

```bash
NOTIFICATION_CHANNEL=none \
PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' \
.venv/Scripts/python.exe -m pytest tests -q \
  --basetemp=C:/Users/emadg/AppData/Local/hermes/cache/scratch/pytest-feed-full-final \
  --junitxml=C:/Users/emadg/AppData/Local/hermes/cache/scratch/feed-full-final.xml
```

`git diff --check` for both production files returned exit 0. No commit or push was made.

## Bounded actual adapter fetch

Exact observation window: **2026-10-01T00:42:34.122609+00:00 to 2026-10-01T00:43:08.541144+00:00**. This exercised the actual `fetch_all()` methods and NewsItem parsing, not fabricated fixture output.

Limits: sequential adapters; public/credential-free; socket timeout 2 seconds; subfeed timeout 3 seconds; adapter internal budget 10 seconds; outer limit 12 seconds; concurrency four within each adapter; host delay one second; final response cap 1 MiB; five redirects. Notifications, providers, state persistence and discovered third-party execution were not invoked. The shorter smoke limits are intentionally stricter than production defaults.

| Adapter | Start UTC | Finish UTC | Parsed items | Feed outcomes |
|---|---|---|---:|---|
| GitHub | 00:42:34.122609 | 00:42:44.127209 | 16 | 6 successful, 10 failed, 14 not attempted |
| Reddit | 00:42:44.128216 | 00:42:48.643687 | 10 | 1 successful, 5 failed |
| Hacker News | 00:42:48.643687 | 00:42:54.663685 | 40 | 4 successful, 4 failed |
| arXiv | 00:42:54.663685 | 00:42:58.253709 | 30 | 3 successful, 2 failed |
| RSS | 00:42:58.253709 | 00:43:04.664405 | 55 | 11 successful, 6 failed |
| Hugging Face | 00:43:04.664405 | 00:43:06.092171 | 27 | 1 successful, 1 response too large |
| YouTube | 00:43:06.092171 | 00:43:08.541144 | 15 | all 3 successful |

Programmatically reconciled totals: **193 parsed items**, **71 enumerated feed operations**, **57 attempted** = **29 successful + 28 failed**, and **14 not attempted**. Items are collection results, not cross-source deduplicated or publication-approved news. Successful GitHub repository enumeration can produce zero news items while scheduling release checks.

The corrected OpenAI, Google Research and Mistral RSS feeds each supplied five items in the actual adapter run. All corrected YouTube channels supplied five items each. Anthropic and Meta were still 404; VentureBeat was 429. Three Google News subfeeds hit the deliberately short deadline. Reddit had three 429s and two timeouts while its successful subreddit supplied ten items. HF's surviving page supplied 27 model items; its papers page exceeded the 1-MiB limit. HN and arXiv returned partial results despite sibling timeouts. GitHub retained results despite its collection deadline and did not claim the queued release checks had been fetched.

Raw sanitized observation evidence is in the local scratch file `C:/Users/emadg/AppData/Local/hermes/cache/scratch/feed_adapter_live.json`; it contains hashed feed keys, counts, failure classifications and UTC health observations, not configured private destinations or credentials.

## Parent integration and exact remaining limits

1. **Do not claim cross-process cooldown persistence is active in the current main path.** Without config, feed health is shared in memory across adapter instances in one process. To enable the tested persistence path, the parent can replace its factory call with `get_all_adapters({"feed_health_state_path": str(self.data_dir / "feed_health.json")})`. Factory adapters then share the persisted tracker. No SQLite/schema migration is required.
2. **Do not call an aggregate adapter success full coverage.** The parent must surface `adapter.feed_results` and/or the shared `adapter.feed_health.get_health_table()` separately from its existing aggregate `self.health` table. Main/report integration was outside this task's edit ownership and remains the parent's action. `healthy` means an observed successful collection, not verified editorial usefulness; per-feed item counts precede final NewsItem validation.
3. No confirmed official RSS replacement was established for Anthropic or Meta. Their existing endpoints remain configured and will report failures/cooldowns instead of being silently replaced with guessed URLs or unofficial proxies. Rate limits/timeouts are observations, not proof that an endpoint is obsolete.
4. A synchronous PRAW worker cannot be forcibly killed by coroutine cancellation. Its collector stops awaiting it; the separately configured request timeout limits socket operations, but PRAW/internal retries can outlive that collector deadline. Authenticated PRAW and real YouTube API fallback were tested deterministically, not with live credentials.
5. The default final-response cap rejects the observed larger HF papers page. The API remains available for an explicitly assessed alternate strategy; none was invented here. Parsing is synchronous and cancellation is cooperative, so the 35-second budget is not a hard real-time CPU interruption guarantee.
6. GitHub pagination remains intentionally limited: one repository search page, one organization page (100 repositories), first ten repositories per organization, one latest-release endpoint per repository. The smoke's ten-second budget did not finish every enumerated release check. PWC was not configured or live-checked.
7. Optional state writes still propagate filesystem errors; the atomic file is not a multi-process merge/locking protocol. Keep one collection writer per state file. Legacy aggregate SQLite `is_disabled` records without a cooldown deadline are not migrated by this patch; the parent should handle any existing permanently-disabled aggregate records before claiming those are automatically retried.
