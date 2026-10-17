# Release catalog shipping audit — October 1, 2026

## Outcome and scope

The actual public HTTP catalogs were fetched without credentials three times. The final adapter accepted **638 OpenRouter models, 112 OpenRouter hosting providers, and 256 UnoRouter models** (1,006 unique public rows). All three GETs returned HTTP 200. UnoRouter is a changing public pricing catalog, not a key-accessible/free-inference entitlement check. OpenRouter is a public model/provider early-warning inventory, not a free-provider probe.

Changes owned by this audit: `src/intel_sources/catalogs.py`, `tests/test_release_catalogs.py`, and this evidence file. No edits to main/store/public projection/templates/recommendations/workflow; other workers were changing those files concurrently. No inference requests, credential reads/mutations, deploys, messages, commits or pushes were performed. All smoke persistence and HTML generation were isolated under Hermes scratch. Real `data/intel_state.json` was read only.

## Fresh read-only HTTP evidence

Final collection window: `2026-10-01T04:55:24.207669+00:00` through `2026-10-01T04:55:24.984704+00:00`. The earlier windows were `04:40:28.779637`–`04:40:29.621325` and `04:53:05.944998`–`04:53:06.710163`, all UTC on October 1, 2026. These are local observation timestamps, not vendor release dates.

| Source | Final checked_at (UTC) | HTTP | Raw / unique / accepted | Declared total | Cache evidence |
|---|---|---|---|---|---|
| OpenRouter models | `2026-10-01T04:55:24.553283+00:00` | 200 | 638 / 638 / 638 | 638 | Age 143s; max-age 120s; exceeds-max-age |
| OpenRouter providers | `2026-10-01T04:55:24.590266+00:00` | 200 | 112 / 112 / 112 | Not supplied | Age 156s; max-age 300s; within-max-age |
| UnoRouter public models | `2026-10-01T04:55:24.866465+00:00` | 200 | 256 / 256 / 256 | 256 | Age/Cache-Control not supplied; unknown |
| Local FreeLLMAPI | `2026-10-01T04:55:24.867973+00:00` | Not requested | 0 | — | Explicitly skipped: Local catalog disabled |

Actual URLs, with no provider/price/capability filter:

```text
https://openrouter.ai/api/v1/models?output_modalities=all
https://openrouter.ai/api/v1/providers
https://api.unorouter.com/api/pricing/catalog
```

No Authorization header was sent. Redirects were not followed. HTTPX timeout components were 20 seconds; this is not a total wall-clock deadline or an origin-refresh guarantee. The shared-client isolation regression suite also verifies that inherited auth, cookies, query credentials and unrelated filters do not travel. Optional key-accessible UnoRouter `/v1/models` and authenticated local inventory were intentionally not called.

Final body bytes and SHA-256:

| Source | Bytes | SHA-256 |
|---|---:|---|
| OpenRouter models | 947,077 | `4b1ff5bd832268fa2133f08aa98cfcbad05bb8634152855da23d12dc122756f8` |
| OpenRouter providers | 26,029 | `302e7b55773582f0192c3a689b171332e9fc6c5a1dae1d182b2fa66233938b6d` |
| UnoRouter models | 117,361 | `ad1dac054fdf6e08eb3973c57f24d4277dd1c358a5ed9293edd1fd07211a1491` |

The initial UnoRouter response had 258 models (133 catalog-free, 125 paid, 44 vendors); the final response had 256 (131 catalog-free, 125 paid, 44 vendors). The initial count is not substituted for the final count. Both OpenRouter response bodies were byte-identical across the captures. OpenRouter also explicitly permits stale-while-revalidate/stale-if-error for 3,600 seconds. A fresh GET can therefore return cached data beyond max-age. Source `status=ok` means successful collection; item `freshness=fresh` means recently collected inventory, not fresh inference or necessarily fresh origin data. Bounded numeric cache diagnostics are now separately persisted in source coverage. Response Date headers were about 20 seconds ahead of this machine's observation clock; exact supplied values were retained in scratch, not used to rewrite observation times.

## Actual current schema and retained decision inputs

Full recursive path/type/count probes are saved as `*-schema.json` next to the captured payloads. They are measured from real responses, not documentation examples.

### OpenRouter models

Envelope: `data` list, `total_count=638`, `links.next=null`. Every row had `id`, `canonical_slug`, `hugging_face_id`, `name`, `created`, `description`, `context_length`, `architecture`, `pricing`, `top_provider`, `per_request_limits`, `supported_parameters`, `default_parameters`, `supported_voices`, `knowledge_cutoff`, `expiration_date`, and `links`. Nullable fields remain nullable. Reasoning was present in 332 rows; benchmarks in 268; alias targets in 19. The initial capture had 27 non-null expiration dates and 180 non-null knowledge cutoffs. Creation time is a vendor claim, not this tracker's first observation.

All observed price keys are retained: prompt/completion (638 each), input_cache_read (303), web_search (182), input_cache_write (94), overrides (80), image_output (55), image (41), image_token (38), audio (37), input_cache_write_1h (33), internal_reasoning (31), input_audio_cache (28), audio_output (2). Official primary pricing documentation distinguishes USD per input/output/cache/audio/reasoning token, per input/output image, per request and per web search. Do not apply a universal per-million-token unit to every price. Conditional override entries can depend on context/time and later matching entries win per key; override order is deliberately preserved in fingerprints.

Actual modality-derived counts: text 614, vision 372, image-generation 57, audio 80, video 118, embeddings 37, speech 21, transcription 24, rerank 9; multimodal 483. Supported-parameter-derived counts: tools 395, reasoning 333. Counts overlap and are not totals. No capabilities or context limits were guessed from names/descriptions. Structured reasoning metadata is retained even where supported_parameters does not advertise reasoning. Benchmarks remain outside this adapter's retained projection; they have not been independently evaluated and are not inference evidence.

### OpenRouter providers

Envelope: `data` list; no declared total/pagination. All 112 rows had name, slug, privacy_policy_url, terms_of_service_url, status_page_url, headquarters and datacenters, with nullable fields. All these fields are retained independently of the model stream. This is a hosting-provider listing, not a model-to-endpoint/provider routing matrix and not operational status. Model `links.details` values reference relative endpoint-detail routes; this audit retained those links but did not fetch those routes or provider status pages.

### UnoRouter public catalog

Envelope: `counts`, `first_free_model`, `models`, `vendors`. Final `counts` was `{models: 256, free: 131, paid: 125, vendors: 44}`. Model rows contain model_name/vendor/vendor_id/type/tags/release_ts/is_free/online/input_price/output_price/fixed_price/is_fixed_price/chat/supported_endpoint_types/uptime_24h. Optional original_input_price/original_output_price occurred in 182 final rows; original_fixed_price in five. Optional icon/success_rate/avg_latency_ms occurred in 226 rows. Tags were **lists**, whereas the official API example uses a comma-separated string; both formats remain supported.

Final raw types: text 177, image 53, **embedding (singular) 19**, audio 7. Fixing the singular type/tag mapping makes all 19 embeddings classifiable for data/retrieval discovery. Endpoint formats, chat flag, raw tags and catalog online/free flags are retained. Audio does not by itself identify speech versus transcription, and size tags such as 8.2K/1M are not explicit context limits. Raw release_ts is retained as catalog metadata but excluded from change fingerprints. Icons and vendor performance telemetry are intentionally not retained as decision/probe evidence.

Primary UnoRouter documentation says the public input/output prices are already USD per million tokens and distinguishes the authenticated `/v1/models` subset. Fixed-price mode/values are retained; the existing fixed-price-per-request label is not enough to establish task/variant-specific billing conditions. No real completion, free quota, uptime, success rate or latency was verified by these GETs.

## Confirmed adapter defects fixed with RED → GREEN tests

1. UnoRouter singular `embedding` disappeared from embeddings classification: now maps to the existing `embeddings` project type (19 real rows).
2. OpenRouter `knowledge_cutoff`, `expiration_date`, `alias_target` and `links` were dropped before persistence: now retained; expiration/alias changes produce updated fingerprints and store changes.
3. UnoRouter original_fixed_price/chat/release_ts disappeared at the projection boundary: now retained; meaningful price/chat changes fingerprint, release-time churn does not.
4. Percent-encoding legal path colons made public `:free`/`:batch` model links fail the unchanged public identity boundary: colons now remain literal; unsafe other characters are still encoded. Same-capture eligible OpenRouter models increased **518 → 619**, UnoRouter **125 → 258**. Free-suffix eligibility increased **0 → 24 OpenRouter / 133 UnoRouter**. This is a consumer survival check before export caps, not an entitlement check.
5. Duplicate identifiers were counted as accepted rows and then silently collapsed by the store: adapter now retains the first valid occurrence, marks duplicates partial and reports unique accepted/invalid/duplicate counts. Contradictory/invalid declared totals are partial, not complete/healthy coverage.
6. Newly observed numeric price dimensions/overrides and original_fixed_price bypassed validation; malformed UnoRouter flags/tags could appear healthy. They are now validated; valid siblings survive as partial, all-invalid sources are errors. Decimal finite checks do not convert stored prices, and legitimate numeric sentinels are not blindly rejected as negative prices.
7. Reordering supported reasoning efforts generated false updates: membership order is normalized in fingerprints without rewriting evidence. Capability membership changes still update; pricing override order remains significant.
8. HTTP cache age/policy were discarded: safe bounded numeric diagnostics now distinguish within-max-age/exceeds-max-age/unknown from successful collection. Arbitrary response header text is not persisted.

Existing failure tests cover HTTP 401/403/429/503, timeouts, network failures, redirects, HTML/invalid JSON, empty/error/malformed envelopes, identifiers, context limits and malformed modalities. Errors never echo server bodies, exception messages or Retry-After. Known explicit secrets are sanitized; catalog metadata is always marked inference_verified=false and free_entitlement_verified=false.

## Persistence and fingerprint contract

The store is the boundary that adds checked_at and first_seen; adapters return stable IDs, selected evidence, project_types and fingerprint_data. Source coverage now records scope, returned/accepted/invalid/duplicate counts, declared total, pagination follow status, all-modality selection and cache diagnostics. Provider totals remain unknown when not supplied; no claim of global catalog completeness is made from an absent total.

An isolated first observation is a baseline, not a model launch. Repeating identical captured items creates **zero** changes. Fingerprints include retained pricing, context/provider limits, capabilities, online/free/chat claims and now lifecycle/alias fields; they exclude created/release timestamps and volatile vendor telemetry. Tests prove failed/empty/error envelopes retain last good rows as stale, preserve their old observation/first-seen times, invent no changes, and allow later identical observations to become fresh again. A 25-hour read becomes stale under the default 24-hour policy. Missing models are retained as not-observed; they are not declared removed/dead or free-access revoked. Updates atomically replace only the isolated state path in this audit.

Real live comparison, using the *same current adapter* for the first/final captures: 251 UnoRouter identities were shared, five were newly observed, seven were not observed in the final capture, and **one shared model had a changed pricing fingerprint**. Raw latency/success/uptime changed on 112/117/19 shared rows and endpoint lists on three; those telemetry/order changes did not create false fingerprint updates. Saved `live-delta-summary.json` gives exact IDs/counts. These are observations, not launches, outages or entitlement decisions.

**Migration warning:** comparing the old versus fixed projection on the very same initial capture changes fingerprints for 638 OpenRouter models and 258 UnoRouter models solely because retained fields were added. An existing initialized store will emit one-time `updated` entries after adapter upgrade; do not market these as vendor changes. The current store saves only latest-cycle changes, not a durable event history or old/new field deltas. A subsequent unchanged refresh replaces changes with an empty list. No store migration/history changes were made here.

Real state integrity: SHA-256 before/after each live probe and the consumer replay remained `4f931776e456a0dee6b3eb4674336e2fe705b749e7d7e4c4f4b69833eceac4b0`. Existing saved public inventory was 635 OpenRouter models, 112 providers, 242 UnoRouter rows (237 fresh, five retained stale); saved source checks were September 30, 2026 at 14:04 UTC. Those saved observations were not replaced by this audit's October 1 HTTP reads.

## Why useful data disappears downstream — unresolved consumer work

The same-capture scratch consumer probe at `2026-10-01T04:52:36.467352+00:00` exercised the real adapter/store/public payload/HTML reporter without touching actual state:

- Internal HTML rendered **1,008** discovery rows with **1,008** evidence details; expiry/alias/fixed-price/chat/release metadata reached the DOM. However, evidence is a generic nested-dictionary presentation, not normalized prices, expiring-model priorities, model/provider implications or a reasoned next-validation decision.
- Public projection (`public_report.py`, build_public_payload) deliberately replaces raw evidence with only observed_at/first_observed_at, substitutes a generic disclaimer, and sets change_items/action_items empty. The public DOM had **300** rows (100 per catalog stream) and no expiry/alias/original-fixed-price metadata. Storage is therefore not proof of useful customer output. Restore only validated typed public fields, not unrestricted raw dictionaries.
- Public export sorts by identity and caps each source at 100 by default (maximum 200); this is a truncated inventory, not a relevance/urgency shortlist. Source counts in that payload are exported counts, not fetched totals. New adapter coverage needs an authorized typed public consumer if original fetched/rejected/cache counts are to be visible.
- **19 real OpenRouter `~vendor/...-latest` alias IDs remain rejected** by the public identity regex. Their safe relative route identity is a public-projection policy issue, not fixed by weakening URL sanitization in the adapter.
- `main.generate_report` passes catalog rows to tool inventory and latest store changes; actions come from operational provider_actions, not catalog change interpretation. Recommendations evaluate github:/skills: identities only, not model/provider catalogs. OpenRouter provider listings do not join the operational FreeLLMAPI status section.
- Source/cache metadata must never become successful inference evidence. A useful consumer can flag listed price/capability/context/alias/expiry changes and propose credential-free validation; it must not promise free entitlement, live routed inference or automatic provider recovery. Active POS/gesture/data-AI context belongs to the parent decision work; no paused fruit-slicer recommendation was added.

These observations describe the consumer snapshot exercised at the stated timestamp. Other workers own consumer/store changes; re-run the probe after their changes rather than assume these gaps persist or are solved.

## Verification and precise commands

Run from `C:/tmp/eli-lain-tracker` using its `.venv/Scripts/python.exe`. No `main.py audit/discover` command was invoked because those commands write real state and can invoke other workflows.

```bash
# Final real credential-free HTTP (all output files isolated in scratch):
.venv/Scripts/python.exe C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_catalog_probe.py C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-catalog-audit/final

# Captured-schema replay + isolated store/internal/public DOM audit:
.venv/Scripts/python.exe C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_catalog_consumer_probe.py

# Read-only primary docs fallback:
.venv/Scripts/python.exe C:/Users/emadg/AppData/Local/hermes/cache/scratch/release_catalog_docs_probe.py

# Final targeted contract, including real Chromium public tests:
PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' .venv/Scripts/python.exe -m pytest tests/test_release_catalogs.py tests/test_intel_catalogs.py tests/test_intel_store.py tests/test_public_report.py -q --basetemp=C:/Users/emadg/AppData/Local/hermes/cache/scratch/catalog-tests-final-targeted
# 190 passed in 3.82s. New release-catalog file contains 31 cases.

# Latest full shared-worktree snapshot (concurrent worker changes included):
NOTIFICATION_CHANNEL=none PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' .venv/Scripts/python.exe -m pytest tests -q --basetemp=C:/Users/emadg/AppData/Local/hermes/cache/scratch/catalog-tests-final-full
# 543 passed, 9 xfailed, 1 failed in 11.83s.
# Remaining failure: tests/test_intel_reporter.py::test_changes_render_before_inventory_and_save_propagates[lain]
# The template placed providers before changes; not owned by this audit.
# Earlier full snapshot: 492 passed, 4 failed in 11.92s (typed public projection
# plus three invalid-incoming-storage cases; workers were still changing those files).
# Owned catalog tests passed in both snapshots. Xfailed tests are not acceptance passes.

git diff --check -- src/intel_sources/catalogs.py tests/test_release_catalogs.py docs/release-catalogs-audit.md
```

Initial public-browser verification failed because the default Playwright headless-shell was absent. Re-running with the already installed explicit Chromium path passed all targeted browser tests; nothing was installed or reconfigured. Web extraction was blocked by the configured search-only backend; primary documentation was successfully fetched directly with credential-free HTTPX/BeautifulSoup instead. UnoRouter search fallback also failed; no third-party explanation was substituted.

## Primary documentation and artifact locations

All five official pages returned HTTP 200 on October 1, 2026, between `04:50:42.801258` and `04:50:46.836494` UTC. Documentation examples are not live row counts.

```text
https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties
https://openrouter.ai/docs/api/api-reference/providers/list-all-providers
https://openrouter.ai/docs/client-sdks/python/components/pricing
https://unorouter.com/en/docs/platform/platform-api
https://unorouter.com/en/docs/platform/models-and-pricing
```

Evidence document absolute path: `C:/tmp/eli-lain-tracker/docs/release-catalogs-audit.md`.

Scratch root: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-catalog-audit/`. Initial capture: root `probe-summary.json`, `*-payload.json`, `*-schema.json`, `adapter-result.json`; final capture: same filenames in `final/`; intermediate capture: `after/`. Consumer evidence: `consumer-summary.json`, `replayed-adapter-result.json`, isolated-before/after-state.json, isolated-internal/public.html. Live comparison: `live-delta-summary.json`. Primary-doc evidence: `primary-doc-probes.json`, `primary-doc-0.txt` through `primary-doc-4.txt`. Probe harnesses are adjacent scratch `.py` files named in the commands above. These are local diagnostic artifacts, not published reports, and scratch may be pruned after inactivity.
