# Customer release storage/news/provider audit

## Scope and release verdict

**Partial news coverage, not all sources live.** This audit changed only `src/intel_sources/store.py`, `src/news_tracker/health.py`, `src/news_tracker/store_sqlite.py`, `tests/test_release_storage.py`, and this document. No router mutation, inference request, commit, push, deployment, or notification. Local provider access was SQLite `mode=ro` + `PRAGMA query_only=ON` and one authenticated `GET /v1/models`; no credential bytes were printed or saved.

The actual default factory configures seven news adapters and 51 fixed subfeeds. PapersWithCode exists as an unused class, is absent from `get_all_adapters`, and is not supported by `get_adapter`; it was not represented as configured or tested live. GitHub adds up to ten release feeds per successful organization listing, not every repository/release. Its configured `topics` list is not used by the actual fixed `ai+llm` search query.

## Fixed root causes and RED → GREEN evidence

All fixes had deterministic failing regression tests before production edits. Test state and probes are under Hermes scratch, not actual `data/`.

| Defect | Observed RED | Minimal repair |
|---|---|---|
| SQLite new-item count used connection-wide `total_changes` | Two identical rows returned inserted=2 for one stored row | Count the individual INSERT cursor's `rowcount`; repeated and restarted duplicates return zero |
| Malformed health row invalidated valid sibling cooldowns; untyped counters/flags were accepted | All eight invalid-row cases failed, either losing valid cooldown or accepting corrupt values | Parse/validate one record at a time; skip invalid record with generic warning, retain valid siblings |
| SQL serialization diagnostics leaked item titles/upstream messages | Private item canary appeared in captured log | Class-name-only warning; valid serializable siblings persist |
| Syntactically valid partial intel snapshots were silently overwritten | Four malformed structure/flag cases updated successfully | Validate list containers, core identity fields and boolean flags; fail closed and preserve corrupt bytes |
| Invalid incoming intel identity poisoned the previous good file | Three cases raised only after atomic replace and changed bytes | Apply the same validator before writing/replacing the candidate snapshot |
| SQLite replaced observation time with insertion time | Thirty-day-old item was reported with today's stored fetch time | Persist `NewsItem.fetched_date`; normalize aware timestamps to UTC. Legacy `NewsItem.utcnow()` naive values are explicitly treated as UTC |
| SQL failure was swallowed and a partial batch was committed as success | Trigger-induced IntegrityError did not propagate | Roll back pending batch and propagate SQLite errors; malformed individual serialization remains isolated |
| Health failure sanitized only on save, not in logs/display/restored JSON | Four private/nonstring error cases leaked or retained invalid values | One error-class sanitizer at record/load/save boundaries |
| Future news observation appeared in recent queries and weekly counts | Tomorrow's observation was included as recent | Use SQLite Julian-date lower/upper bounds; future/invalid observation times do not qualify as recent. `days=0` remains an unrestricted history view |

`tests/test_release_storage.py`: **40 passed** after final store fixes. Includes real SQLite restart/dedup/rollback/corrupt DB; bad-row and bad-document health recovery; failed atomic replace cleanup; stale/future intel restart; unconfigured-summary zero-inference and publisher-excerpt round trip; all seven actual adapters' fixed feed enumeration plus a deterministic release child per GitHub organization.

Final targeted storage/news/provider regression gate: **126 passed in 1.31s**. Final full concurrent-worktree recheck with real Chromium: **549 passed, 9 xfailed in 14.30s**. `git diff --check` passed for owned files. Expected failures remain disclosures of known gaps, not proof of those behaviors. Earlier transient missing-intel-file and Lain section-order failures disappeared after the responsible workers repaired their files. These suite results are point-in-time, not comprehensive live certification or certification of later edits.

## Bounded live anonymous public-news smoke

Run: `2026-10-01T04:48:29.749021+00:00` through `2026-10-01T04:49:04.929683+00:00` (UTC). Adapter constraints: 5 seconds per subfeed, 35 seconds per adapter, concurrency 4, 1 second host throttling, 45-second outer cap; adapters were exercised concurrently in an isolated harness, unlike main's sequential adapter loop. GitHub Authorization was explicitly removed; Reddit RSS and YouTube RSS only. Every fixed feed and every discovered dynamic feed was reconciled against actual `feed_results` keys, including children never started.

**121 reconciled feeds = 51 fixed + 70 dynamic release feeds: 57 healthy, 22 failed, 42 not_attempted.** There were 75 completed HTTP responses (41 HTTP 200, 21 HTTP 404, 6 HTTP 429, 7 HTTP 403); cancelled/deadline requests have no completed response. A successful GitHub release 404 means no latest release and is recorded healthy with zero items, not inferred release coverage.

The 121 per-feed health records survived a new tracker instance exactly. Actual parsed observations were stored in isolated SQLite: **246 new rows, repeat save=0, read count=246, reopened count=246**. The difference from raw parsed count includes overlapping exact `(url,title)` duplicates; no synthetic stories were stored. The harness retained observed publisher excerpts or used labelled title excerpts with the unconfigured summarizer. It bypassed scoring/relevance filtering and did not render/publish a customer artifact; production stores only processed relevant news.

Evidence (scratch, not committed):
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-news-live-complete/results.json`
- same directory `feed_health.json` and `news.db`
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-provider-storage.json`

| Source | Reconciled feeds | Healthy | Failed | Not attempted | Parsed items |
|---|---:|---:|---:|---:|---:|
| arxiv | 5 | 5 | 0 | 0 | 50 |
| github | 80 | 27 | 11 | 42 | 17 |
| hackernews | 8 | 8 | 0 | 0 | 80 |
| huggingface | 2 | 2 | 0 | 0 | 31 |
| reddit | 6 | 1 | 5 | 0 | 10 |
| rss | 17 | 14 | 3 | 0 | 70 |
| youtube | 3 | 0 | 3 | 0 | 0 |

### Every fixed source/subfeed (actual one-run outcome)

Healthy means the bounded fetch/parser operation completed, **not current publication, inference availability, full source coverage, or a guarantee on the next run**. Items below are raw subfeed item counts before adapter/global dedup and parsing; thus their sum need not equal stored rows.

| Source | Configured subfeed | Endpoint | Outcome | Raw items | Failure classification |
|---|---|---|---|---:|---|
| arxiv | cs.AI | `http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending` | healthy | 10 | — |
| arxiv | cs.CL | `http://export.arxiv.org/api/query?search_query=cat:cs.CL&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending` | healthy | 10 | — |
| arxiv | cs.CV | `http://export.arxiv.org/api/query?search_query=cat:cs.CV&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending` | healthy | 10 | — |
| arxiv | cs.LG | `http://export.arxiv.org/api/query?search_query=cat:cs.LG&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending` | healthy | 10 | — |
| arxiv | cs.NE | `http://export.arxiv.org/api/query?search_query=cat:cs.NE&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending` | healthy | 10 | — |
| github | org:anthropic-ai | `https://api.github.com/orgs/anthropic-ai/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:cerebras | `https://api.github.com/orgs/cerebras/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:google-deepmind | `https://api.github.com/orgs/google-deepmind/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:groq | `https://api.github.com/orgs/groq/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:meta-llama | `https://api.github.com/orgs/meta-llama/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:microsoft | `https://api.github.com/orgs/microsoft/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:mistralai | `https://api.github.com/orgs/mistralai/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:openai | `https://api.github.com/orgs/openai/repos?per_page=100&type=public` | healthy | 0 | — |
| github | org:togethercomputer | `https://api.github.com/orgs/togethercomputer/repos?per_page=100&type=public` | failed | 0 | timeout |
| github | search:ai llm | `https://api.github.com/search/repositories?q=ai+llm&sort=updated&per_page=15` | healthy | 15 | — |
| hackernews | ai | `https://hn.algolia.com/api/v1/search?query=ai&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | anthropic | `https://hn.algolia.com/api/v1/search?query=anthropic&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | claude | `https://hn.algolia.com/api/v1/search?query=claude&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | deep learning | `https://hn.algolia.com/api/v1/search?query=deep%20learning&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | gpt | `https://hn.algolia.com/api/v1/search?query=gpt&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | llm | `https://hn.algolia.com/api/v1/search?query=llm&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | machine learning | `https://hn.algolia.com/api/v1/search?query=machine%20learning&tags=story&hitsPerPage=10` | healthy | 10 | — |
| hackernews | openai | `https://hn.algolia.com/api/v1/search?query=openai&tags=story&hitsPerPage=10` | healthy | 10 | — |
| huggingface | models | `https://huggingface.co/models?sort=trending` | healthy | 27 | — |
| huggingface | papers | `https://huggingface.co/papers` | healthy | 4 | — |
| reddit | ChatGPT | `https://www.reddit.com/r/ChatGPT/.rss` | failed | 0 | http_429 |
| reddit | GenerativeAI | `https://www.reddit.com/r/GenerativeAI/.rss` | failed | 0 | http_429 |
| reddit | LocalLLaMA | `https://www.reddit.com/r/LocalLLaMA/.rss` | failed | 0 | http_429 |
| reddit | MachineLearning | `https://www.reddit.com/r/MachineLearning/.rss` | healthy | 10 | — |
| reddit | OpenAI | `https://www.reddit.com/r/OpenAI/.rss` | failed | 0 | http_429 |
| reddit | artificial | `https://www.reddit.com/r/artificial/.rss` | failed | 0 | http_429 |
| rss | Anthropic Blog | `https://www.anthropic.com/blog/rss.xml` | failed | 0 | http_404 |
| rss | Ars Technica | `https://feeds.arstechnica.com/arstechnica/technology-lab` | healthy | 5 | — |
| rss | DeepMind Blog | `https://deepmind.google/blog/rss.xml` | healthy | 5 | — |
| rss | Google AI Blog | `https://research.google/blog/rss/` | healthy | 5 | — |
| rss | Google News - AI | `https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en` | healthy | 5 | — |
| rss | Google News - AI Agents | `https://news.google.com/rss/search?q=ai+agents&hl=en-US&gl=US&ceid=US:en` | healthy | 5 | — |
| rss | Google News - Claude | `https://news.google.com/rss/search?q=claude+anthropic&hl=en-US&gl=US&ceid=US:en` | healthy | 5 | — |
| rss | Google News - GPT | `https://news.google.com/rss/search?q=gpt+openai&hl=en-US&gl=US&ceid=US:en` | healthy | 5 | — |
| rss | Google News - Gemini | `https://news.google.com/rss/search?q=gemini+google&hl=en-US&gl=US&ceid=US:en` | healthy | 5 | — |
| rss | Google News - LLM | `https://news.google.com/rss/search?q=large+language+model&hl=en-US&gl=US&ceid=US:en` | healthy | 5 | — |
| rss | Meta AI Blog | `https://ai.meta.com/blog/tag/research/rss/` | failed | 0 | http_404 |
| rss | Mistral Blog | `https://mistral.ai/news/rss` | healthy | 5 | — |
| rss | OpenAI Blog | `https://openai.com/news/rss.xml` | healthy | 5 | — |
| rss | TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` | healthy | 5 | — |
| rss | The Verge AI | `https://www.theverge.com/rss/index.xml` | healthy | 5 | — |
| rss | VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | failed | 0 | http_429 |
| rss | Wired AI | `https://www.wired.com/feed/tag/ai/latest/rss` | healthy | 5 | — |
| youtube | AI Explained | `https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw` | failed | 0 | http_404 |
| youtube | Two Minute Papers | `https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg` | failed | 0 | http_404 |
| youtube | Yannic Kilcher | `https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew` | failed | 0 | http_404 |

### Every discovered GitHub release subfeed

Only the first ten repositories returned per successful org listing were scheduled. Org listing success is not equivalent to useful recent releases. The togethercomputer org listing timed out, so no child identity for it was discovered; all its possible children remain unverified. Forty-two scheduled children never started before the shared budget expired. `collection_deadline` means started but unfinished; `not_attempted` is not a failure. HTTP 404 with healthy/0 is an observed absence of latest release, not a release story.

| Repository | Endpoint | Outcome | Raw items | Failure classification |
|---|---|---|---:|---|
| Cerebras/archivemount | `https://api.github.com/repos/Cerebras/archivemount/releases/latest` | not_attempted | 0 | — |
| Cerebras/aws-parallelcluster-node | `https://api.github.com/repos/Cerebras/aws-parallelcluster-node/releases/latest` | not_attempted | 0 | — |
| Cerebras/g3log | `https://api.github.com/repos/Cerebras/g3log/releases/latest` | not_attempted | 0 | — |
| Cerebras/libtins | `https://api.github.com/repos/Cerebras/libtins/releases/latest` | not_attempted | 0 | — |
| Cerebras/modelzoo | `https://api.github.com/repos/Cerebras/modelzoo/releases/latest` | not_attempted | 0 | — |
| Cerebras/modelzoo-staging | `https://api.github.com/repos/Cerebras/modelzoo-staging/releases/latest` | not_attempted | 0 | — |
| Cerebras/online-normalization | `https://api.github.com/repos/Cerebras/online-normalization/releases/latest` | not_attempted | 0 | — |
| Cerebras/open-register-design-tool | `https://api.github.com/repos/Cerebras/open-register-design-tool/releases/latest` | not_attempted | 0 | — |
| Cerebras/sdk-examples | `https://api.github.com/repos/Cerebras/sdk-examples/releases/latest` | not_attempted | 0 | — |
| Cerebras/tensorflow | `https://api.github.com/repos/Cerebras/tensorflow/releases/latest` | not_attempted | 0 | — |
| google-deepmind/lua-pprint | `https://api.github.com/repos/google-deepmind/lua-pprint/releases/latest` | healthy | 0 | — |
| google-deepmind/plplot-ffi | `https://api.github.com/repos/google-deepmind/plplot-ffi/releases/latest` | healthy | 0 | — |
| google-deepmind/strict | `https://api.github.com/repos/google-deepmind/strict/releases/latest` | failed | 0 | http_403 |
| google-deepmind/torch-cephes | `https://api.github.com/repos/google-deepmind/torch-cephes/releases/latest` | healthy | 0 | — |
| google-deepmind/torch-distributions | `https://api.github.com/repos/google-deepmind/torch-distributions/releases/latest` | healthy | 0 | — |
| google-deepmind/torch-dokx | `https://api.github.com/repos/google-deepmind/torch-dokx/releases/latest` | healthy | 0 | — |
| google-deepmind/torch-hdf5 | `https://api.github.com/repos/google-deepmind/torch-hdf5/releases/latest` | healthy | 0 | — |
| google-deepmind/torch-oocairo | `https://api.github.com/repos/google-deepmind/torch-oocairo/releases/latest` | healthy | 0 | — |
| google-deepmind/torch-randomkit | `https://api.github.com/repos/google-deepmind/torch-randomkit/releases/latest` | healthy | 0 | — |
| google-deepmind/torch-totem | `https://api.github.com/repos/google-deepmind/torch-totem/releases/latest` | failed | 0 | http_403 |
| groq/deployment | `https://api.github.com/repos/groq/deployment/releases/latest` | not_attempted | 0 | — |
| groq/groq-aisdk-chatbot | `https://api.github.com/repos/groq/groq-aisdk-chatbot/releases/latest` | not_attempted | 0 | — |
| groq/groq-api-cookbook | `https://api.github.com/repos/groq/groq-api-cookbook/releases/latest` | not_attempted | 0 | — |
| groq/groq-python | `https://api.github.com/repos/groq/groq-python/releases/latest` | not_attempted | 0 | — |
| groq/groq-typescript | `https://api.github.com/repos/groq/groq-typescript/releases/latest` | not_attempted | 0 | — |
| groq/groqflow | `https://api.github.com/repos/groq/groqflow/releases/latest` | not_attempted | 0 | — |
| groq/marge-bot | `https://api.github.com/repos/groq/marge-bot/releases/latest` | not_attempted | 0 | — |
| groq/mlagility | `https://api.github.com/repos/groq/mlagility/releases/latest` | not_attempted | 0 | — |
| groq/nix | `https://api.github.com/repos/groq/nix/releases/latest` | not_attempted | 0 | — |
| groq/speech-to-speech-demo | `https://api.github.com/repos/groq/speech-to-speech-demo/releases/latest` | not_attempted | 0 | — |
| meta-llama/PurpleLlama | `https://api.github.com/repos/meta-llama/PurpleLlama/releases/latest` | not_attempted | 0 | — |
| meta-llama/codellama | `https://api.github.com/repos/meta-llama/codellama/releases/latest` | not_attempted | 0 | — |
| meta-llama/llama | `https://api.github.com/repos/meta-llama/llama/releases/latest` | not_attempted | 0 | — |
| meta-llama/llama-api-python | `https://api.github.com/repos/meta-llama/llama-api-python/releases/latest` | not_attempted | 0 | — |
| meta-llama/llama-cookbook | `https://api.github.com/repos/meta-llama/llama-cookbook/releases/latest` | not_attempted | 0 | — |
| meta-llama/llama-models | `https://api.github.com/repos/meta-llama/llama-models/releases/latest` | not_attempted | 0 | — |
| meta-llama/llama-stack-ops | `https://api.github.com/repos/meta-llama/llama-stack-ops/releases/latest` | not_attempted | 0 | — |
| meta-llama/llama3 | `https://api.github.com/repos/meta-llama/llama3/releases/latest` | not_attempted | 0 | — |
| meta-llama/prompt-ops | `https://api.github.com/repos/meta-llama/prompt-ops/releases/latest` | not_attempted | 0 | — |
| meta-llama/synthetic-data-kit | `https://api.github.com/repos/meta-llama/synthetic-data-kit/releases/latest` | not_attempted | 0 | — |
| microsoft/BeanSpy | `https://api.github.com/repos/microsoft/BeanSpy/releases/latest` | not_attempted | 0 | — |
| microsoft/HealthVault-Mobile-iOS-Library | `https://api.github.com/repos/microsoft/HealthVault-Mobile-iOS-Library/releases/latest` | not_attempted | 0 | — |
| microsoft/LIS3.5 | `https://api.github.com/repos/microsoft/LIS3.5/releases/latest` | not_attempted | 0 | — |
| microsoft/WindowsAzureToolkitForEclipseWithJava | `https://api.github.com/repos/microsoft/WindowsAzureToolkitForEclipseWithJava/releases/latest` | not_attempted | 0 | — |
| microsoft/filter-effects | `https://api.github.com/repos/microsoft/filter-effects/releases/latest` | not_attempted | 0 | — |
| microsoft/filter-explorer | `https://api.github.com/repos/microsoft/filter-explorer/releases/latest` | not_attempted | 0 | — |
| microsoft/healthvault-ios-sdk | `https://api.github.com/repos/microsoft/healthvault-ios-sdk/releases/latest` | not_attempted | 0 | — |
| microsoft/php-sdk-binary-tools | `https://api.github.com/repos/microsoft/php-sdk-binary-tools/releases/latest` | not_attempted | 0 | — |
| microsoft/plcrashreporter | `https://api.github.com/repos/microsoft/plcrashreporter/releases/latest` | not_attempted | 0 | — |
| microsoft/real-time-filter-demo | `https://api.github.com/repos/microsoft/real-time-filter-demo/releases/latest` | not_attempted | 0 | — |
| mistralai/FastChat-release | `https://api.github.com/repos/mistralai/FastChat-release/releases/latest` | failed | 0 | http_403 |
| mistralai/TensorRT-LLM | `https://api.github.com/repos/mistralai/TensorRT-LLM/releases/latest` | not_attempted | 0 | — |
| mistralai/client-js | `https://api.github.com/repos/mistralai/client-js/releases/latest` | failed | 0 | collection_deadline |
| mistralai/client-python | `https://api.github.com/repos/mistralai/client-python/releases/latest` | failed | 0 | collection_deadline |
| mistralai/cookbook | `https://api.github.com/repos/mistralai/cookbook/releases/latest` | not_attempted | 0 | — |
| mistralai/megablocks-public | `https://api.github.com/repos/mistralai/megablocks-public/releases/latest` | failed | 0 | collection_deadline |
| mistralai/mistral-inference | `https://api.github.com/repos/mistralai/mistral-inference/releases/latest` | failed | 0 | http_403 |
| mistralai/platform-docs-public | `https://api.github.com/repos/mistralai/platform-docs-public/releases/latest` | failed | 0 | collection_deadline |
| mistralai/transformers-release | `https://api.github.com/repos/mistralai/transformers-release/releases/latest` | failed | 0 | http_403 |
| mistralai/vllm-release | `https://api.github.com/repos/mistralai/vllm-release/releases/latest` | failed | 0 | http_403 |
| openai/InfoGAN | `https://api.github.com/repos/openai/InfoGAN/releases/latest` | healthy | 0 | — |
| openai/atari-py | `https://api.github.com/repos/openai/atari-py/releases/latest` | healthy | 0 | — |
| openai/doom-py | `https://api.github.com/repos/openai/doom-py/releases/latest` | healthy | 0 | — |
| openai/gym | `https://api.github.com/repos/openai/gym/releases/latest` | healthy | 1 | — |
| openai/gym-http-api | `https://api.github.com/repos/openai/gym-http-api/releases/latest` | healthy | 0 | — |
| openai/kubernetes-ec2-autoscaler | `https://api.github.com/repos/openai/kubernetes-ec2-autoscaler/releases/latest` | healthy | 0 | — |
| openai/mujoco-py | `https://api.github.com/repos/openai/mujoco-py/releases/latest` | healthy | 1 | — |
| openai/pachi-py | `https://api.github.com/repos/openai/pachi-py/releases/latest` | healthy | 0 | — |
| openai/requests-for-research | `https://api.github.com/repos/openai/requests-for-research/releases/latest` | healthy | 0 | — |
| openai/vime | `https://api.github.com/repos/openai/vime/releases/latest` | healthy | 0 | — |

## History, persistence and transport truth

- Intel JSON and health JSON use sibling temporary file, flush/fsync, and atomic replace. Regression failure injection preserved the old file and removed temporary files. Atomic replacement protects against torn single writes, **not concurrent writers/lost updates or multi-file transactional consistency**.
- Intel baseline/change detection survives restart, tracks first_seen, retains absent/failed-source inventory as stale, and does not refresh old checked_at on render. Naive/invalid check time is unverified; future or over-age checks are stale. JSON nested evidence/content is not a complete typed schema; concurrent writes, quota errors, full-disk/power-cut recovery were not exhaustively exercised.
- News DB uses WAL, parameterized queries, UNIQUE `(url,title)`, no silent overwrite on corruption, and explicit rollback/propagation for per-insert database errors. Exact duplicates do not refresh timestamp or update an older summary. A renamed headline at the same URL is a distinct historical row. URL normalization, fuzzy cross-run dedup, dedup_key persistence and summary refresh are not implemented by this store.
- Individual unserializable raw_data is skipped with class-only warning; this partial-item policy is deliberate. SQL storage failure aborts the batch. OS-level failed commit/disk-full/power loss was not physically exercised; caller must treat propagated database error as failed delivery, not generate a success claim.
- Recent/weekly filters use **observed/fetched time**, not publication time. The live HN `search` endpoint returned 2016–2026 stories and GitHub releases included 2021 material; these were newly observed, not new launches. Main's current news HTML projection omits published/fetched dates, so freshness is not visible per news card. No repair outside the owned store files was attempted.
- `FileCache` is constructed in NewsTracker but has no get/set calls in the actual news loop. Therefore no raw-feed cache replay or offline HTTP fallback is established. Its non-atomic writer and placeholder cached_at path are unused by this pipeline and were not repaired.
- Source-level cooldown and per-feed cooldown JSON persist locally. Source-level DB is legacy metadata with no deadline: main intentionally does not restore its is_disabled forever; JSON carries current deadlines. Full malformed health JSON cannot reconstruct omitted cooldowns and loads no new state; valid siblings survive individual malformed rows. A loaded last_success is collection history, not a TTL-based assertion of current source availability. Getter helpers get_disabled_sources/get_healthy_sources do not independently expire cooldowns; callers that need current state must use is_source_enabled/get_health_table.
- A fresh NewsTracker reload restores health records but not the latest-run `feed_results` summaries; feed JSON has hashed identity/counters, not human-readable destinations or complete prior feed outcome lists. Healthy zero-item success resets failure counter; rate-limit deadline is persisted; deadline-not-started is not counted as a failure.
- Workflow caches `intel_state.json`, `provider_changes.json`, `provider_state.json`, `news.db`, `health.json`. It **does not cache `feed_health.json` or `project_evaluations.json`**. Local feed restart correctness does not establish cross-run hosted CI continuity. Workflow/artifact state/history edits are outside this task's allowed files.
- Cache transports only `news.db`, not WAL/SHM. That is safe only after last writer closes/checkpoints, or with an explicit SQLite backup snapshot. This audit exercised reopen on closed isolated DB, not interruption while CI saves cache. Require an explicit close/checkpoint/backup contract before claiming crash-resilient history transport.
- Actual saved `data/news.db` was opened read-only: quick_check=ok, 120 rows, source counts arxiv=28/github=13/hackernews=73/huggingface=6. Every stored fetched_date was `2026-09-30 14:15:40`; this audit did not refresh or rewrite those rows. Both actual health.json and feed_health.json were absent at the read-only snapshot. Each existing inspected data file's hash was unchanged after reading.

## Summaries and title fallback

Unconfigured summarizer never requests inference. It preserves non-empty publisher excerpts and labels missing text `Title excerpt (not AI summary): ...`; both survive SQLite restart. Existing regression confirms configured 401 stops after one request, preserves all news, and uses fallback. This audit used only offline HTTP mocks for configured summarization.

Configured-summary success, batch-schema correctness, prompt safety and model routing were **not live-verified** (inference forbidden). Static review: valid JSON objects/strings instead of the expected array, partial arrays, nonstring summary fields and raw non-JSON lines are not strictly validated; raw lines can become unlabelled summaries. Pipeline CLI does not pass summarizer credentials/model config into NewsTracker, and adapters receive feed_health config only, so workflow REDDIT_CLIENT_ID/SECRET and YOUTUBE_API_KEY are not wired into their optional authenticated paths. PRAW and Data API branches have mock regressions but no authorized live proof here. These are parent/summarizer/adapter integration gaps, not fixed by this storage audit.

## Read-only provider binding truth

Observed `2026-10-01T04:50:22.215947+00:00`. **28 enabled key rows, 347 enabled model rows, 35 union platforms**. All key gateway statuses were healthy; freshly constructed tracker statuses remained unknown. Gateway metadata is not successful inference or free-tier entitlement. Credentials, encrypted blobs, raw diagnostic messages, user/session data and key labels were never selected for output.

**Twenty enabled model rows have a non-key text binding `no quota headers exposed` in key_id.** Tracker excludes them rather than guessing/repairing router state. Nine configured keyed platforms have zero eligible catalog candidates: anyapi, bai, blaze, electronhub, github, navy, reka, routeway, waterfall. Seven model-only platforms are absent from provider tracking because there is no api_keys row. The generic custom platform has eight endpoint-scoped candidates but no dedicated registry entry; route identity and endpoint-specific provider fidelity require verification, not a guessed binding.

Authenticated catalog GET returned **200 with 280 model IDs, all owned_by=freellmapi**. Only 29 of 268 DB candidate IDs were exact matches; generic owned_by cannot identify an upstream. Namespace differences or multi-platform metadata can account for some mismatches; the audit did not interpret every non-match as a dead provider. No provider completion, quota/reset claim, free-tier claim or recovery was verified.

| Platform | Key rows / enabled | Enabled models | Selected key ID | Eligible candidates | Other/non-key bindings | Null key bindings | Registry entry |
|---|---:|---:|---:|---:|---:|---:|---|
| agnes | 1 / 1 | 2 | 9 | 2 | 0 | 2 | yes |
| aihorde | 0 / 0 | 16 | — | 0 | 0 | 16 | no |
| aion | 1 / 1 | 5 | 10 | 4 | 1 | 4 | yes |
| anyapi | 1 / 1 | 1 | 20 | 0 | 1 | 0 | yes |
| bai | 1 / 1 | 1 | 16 | 0 | 1 | 0 | yes |
| bazaarlink | 1 / 1 | 3 | 17 | 3 | 0 | 3 | yes |
| blaze | 1 / 1 | 0 | 34 | 0 | 0 | 0 | yes |
| cerebras | 0 / 0 | 1 | — | 0 | 1 | 0 | yes |
| cloudflare | 1 / 1 | 27 | 4 | 26 | 1 | 26 | yes |
| cohere | 1 / 1 | 15 | 1 | 15 | 0 | 15 | yes |
| custom | 1 / 1 | 8 | 36 | 8 | 0 | 0 | no |
| electronhub | 1 / 1 | 1 | 15 | 0 | 1 | 0 | yes |
| github | 1 / 1 | 1 | 5 | 0 | 1 | 0 | yes |
| google | 1 / 1 | 12 | 26 | 11 | 1 | 11 | yes |
| groq | 1 / 1 | 7 | 2 | 7 | 0 | 7 | yes |
| huggingface | 1 / 1 | 118 | 23 | 117 | 1 | 117 | yes |
| kilo | 0 / 0 | 12 | — | 0 | 0 | 12 | no |
| llm7 | 1 / 1 | 5 | 29 | 4 | 1 | 4 | yes |
| mistral | 1 / 1 | 12 | 3 | 12 | 0 | 12 | yes |
| modelscope | 0 / 0 | 11 | — | 0 | 0 | 11 | no |
| nara | 1 / 1 | 3 | 27 | 2 | 1 | 2 | yes |
| navy | 1 / 1 | 1 | 14 | 0 | 1 | 0 | yes |
| nvidia | 1 / 1 | 18 | 24 | 17 | 1 | 17 | yes |
| ollama | 0 / 0 | 6 | — | 0 | 0 | 6 | no |
| opencode | 0 / 0 | 1 | — | 0 | 1 | 0 | yes |
| openrouter | 1 / 1 | 12 | 7 | 12 | 0 | 12 | yes |
| ovh | 0 / 0 | 13 | — | 0 | 0 | 13 | no |
| reka | 1 / 1 | 1 | 19 | 0 | 0 | 1 | yes |
| requesty | 1 / 1 | 9 | 18 | 8 | 1 | 8 | yes |
| routeway | 1 / 1 | 1 | 12 | 0 | 1 | 0 | yes |
| sealion | 1 / 1 | 6 | 11 | 5 | 1 | 5 | yes |
| unorouter | 1 / 1 | 5 | 32 | 4 | 1 | 2 | yes |
| waterfall | 1 / 1 | 0 | 33 | 0 | 0 | 0 | yes |
| xkiro | 1 / 1 | 9 | 31 | 8 | 1 | 8 | yes |
| zhipu | 1 / 1 | 4 | 8 | 3 | 1 | 3 | yes |

## Customer release gates / unverified gaps

1. Resolve or explicitly disclose Anthropic RSS 404, Meta RSS 404, VentureBeat 429, five Reddit 429 feeds, all three YouTube RSS 404s, GitHub denied/timed-out/deadline children. Do not replace these with broad adapter-level success claims.
2. Feed-health continuity must be included in CI history transport; current cache omits it. Evaluation JSON is generated by actual report consumer but omitted from history cache; a JSON file's existence does not establish scheduled persistence.
3. Expose dated news provenance and per-feed partial coverage in the actual delivered customer HTML/JSON projection. At audit read time main passes discovery `source_items` to HTML; per-feed news health is returned by run()/helper, not rendered in the report source-health section. No hosted artifact/browser delivery certification was performed by this worker.
4. Decide whether HN relevance-ranked historic results and old GitHub releases meet “news”; current fetch-date history is not launch-date truth.
5. Verify malformed configured summaries fail transparently with labelled fallback before promising AI summaries. No configured model inference was authorized here.
6. Preserve literal malformed provider key_id bindings as evidence; do not silently rewrite router DB. Resolve upstream identity/candidate mapping with provider worker before any future authorized probe.
7. Final broad recheck passed 549 tests with 9 expected failures; those expected-failure cases remain known unverified/failing behaviors. Rerun after any later concurrent worker edits rather than reusing this point-in-time result.

No claim of comprehensive live service availability, hosted delivery, uninterrupted cache restoration, fault-proof filesystem durability, model entitlement, or every optional authentication branch is supported by this audit.
