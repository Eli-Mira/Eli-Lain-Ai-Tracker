# Catalog discovery verification

## Scope and integration contract

Only `src/intel_sources/catalogs.py`, `tests/test_intel_catalogs.py`, and this document belong to the catalog implementation. No `__init__.py`, shared models, templates, router database, `main.py`, credentials, commits, or pushes were changed by this work.

```python
async def fetch_catalogs(
    client: httpx.AsyncClient,
    freellmapi_url="http://localhost:3001",
    api_key=None,
    unorouter_api_key=None,
    include_local=True,
) -> dict:
    ...
```

The return value has exactly `items: list[dict]` and `sources: list[dict]`.

Every item has exactly these keys:

- `id`: stable namespace plus the upstream identifier, not a timestamp or generated UUID.
- `headline`, `summary`, `url`: catalog data, never executable instructions.
- `source`: exact corresponding source row `name`, suitable for persistence and freshness lookup.
- `project_types: list[str]`: sorted observable capabilities; unknown capabilities remain unclassified, not excluded.
- `evidence: dict`: allowlisted catalog fields, endpoint provenance, and both `inference_verified=False` and `free_entitlement_verified=False`.
- `fingerprint_data: dict`: meaningful catalog properties; excludes timestamps and selected operational noise, and normalizes ordering of capability sets.

Each source has `name`, `status` (`ok`, `partial`, `error`, or `skipped`), `checked_at` (ISO UTC), `item_count`, `error` (sanitized string or null), and `url`.

| Source ID | Item ID prefix | Selection |
|---|---|---|
| `openrouter-models` | `openrouter:model:` | Every model output modality, including paid and free |
| `openrouter-providers` | `openrouter:provider:` | Separate official hosting-provider stream |
| `unorouter-models` | `unorouter:model:` | Broad public catalog, not restricted by an API key |
| `freellmapi-models` | `freellmapi:model:` | Authenticated local `/v1/models`, or explicit skipped/error source |
| `unorouter-accessible-models` | `unorouter:accessible-model:` | Optional additional key-scoped stream only when `unorouter_api_key` is supplied |

Default calls return four source rows. An explicit UnoRouter key adds a fifth source row without narrowing the public UnoRouter catalog. The same underlying model can appear in separate public/local/key-scoped streams; these are not automatically independent corroborating sources.

## Official endpoint discovery

The specified UnoRouter Platform page contains the actual Platform API link; that linked page was fetched and read rather than substituting OneRouter.[1][2]

UnoRouter documents the unauthenticated `GET https://api.unorouter.com/api/pricing/catalog` for the broad model catalog, with input/output prices expressed in USD per million tokens.[2]

UnoRouter also documents authenticated `GET https://api.unorouter.com/v1/models` as the subset the supplied API key may use; it can include explicit `context_length` and `max_output_tokens`.[2]

Its pricing guide distinguishes free versus paid variants and explains that catalog availability can change with provider availability; none of that is used as proof that this user successfully invoked a model or has a working free entitlement.[3]

OpenRouter documents `GET https://openrouter.ai/api/v1/models` and `output_modalities=all`; the default output filter is text, so the implementation explicitly requests `all` without price, provider, or supported-parameter filters.[4]

OpenRouter documents `GET https://openrouter.ai/api/v1/providers`, allowing provider discovery without inferring hosting providers from a model-author namespace.[5]

The provider documentation shows bearer authentication, but the actual live request returned HTTP 200 without a key. The implementation makes this public attempt and reports truthful auth failure if that availability changes.

Retrieval issue: this subagent's configured web extraction tool rejected extraction because its OpenAI-native backend is search-only. Native client-side search also failed and was rescued by configured search fallbacks. Primary pages were successfully fetched with the repository Python 3.11 `httpx` + BeautifulSoup. No account, key management, key reveal, or inference endpoints described in those pages were called. A tool literally named `web.run` was not exposed to this subagent; the requested exact lookup tool requirement remains a parent-level verification limitation.

## Safety, provenance, and interpretation

- Only read-only GETs to the fixed official catalog URLs and the explicitly configured local `/v1/models` endpoint are made.
- Keys are only the two explicit function parameters. The module does not search secrets or automatically read environment variables.
- An absent local key yields `skipped` with `Explicit FreeLLMAPI API key required`. Disabled local fetching yields `skipped` with `Local catalog disabled`. Neither state claims an authenticated local request succeeded.
- Shared-client authentication, cookies, extra headers, and inherited query filters are stripped; local and UnoRouter keys go only to their intended endpoints. Redirects are not followed. HTTP timeout components are explicitly set to 20 seconds.
- Credential-bearing or non-HTTP local base URLs are rejected before a local request; the source records `[invalid]` rather than echoing a credential-bearing URL.
- HTTP 401/403/429/503 and other failure status codes, timeouts, offline errors, HTML/non-JSON bodies, malformed envelopes, empty lists, invalid identifiers, invalid numeric prices, invalid limits, and malformed capabilities are not healthy results.
- One bad row does not discard valid rows: valid items remain and the source is `partial`. All-invalid lists are `error`. Incomplete totals/next-page indicators are `partial`; untrusted pagination URLs are not followed.
- Server response bodies, exception messages, and Retry-After values are not echoed into error text. Known explicit key values are redacted from data, nested credential fields are dropped, and identifiers reflecting a supplied key are rejected rather than rewritten.
- FreeLLMAPI evidence retains upstream identifiers/ownership when actually present and records `provenance.kind=local_aggregated_catalog`, `independent_of_upstream=False`, and the actual declared upstream source or null. Local listing is not separate corroboration of a working upstream model.
- Optional UnoRouter key-scoped evidence likewise records its dependent scope. It is not a completion probe.
- Text, vision, image generation, tools, reasoning, multimodal, audio, video, embeddings, speech, transcription, and reranking classification is based on actual declared modalities/parameters or explicit UnoRouter type/capability tags. Marketing descriptions and model-name guesses do not classify a model. Context windows are not guessed from UnoRouter `1M` tags.
- Catalog descriptions are retained as DATA. Consumers must escape them when rendering HTML; this module neither executes descriptions nor follows their links.

## Strict vertical TDD and acceptance tests

Each behavior slice was written as a failing test, executed RED, minimally implemented, then executed GREEN before proceeding. HTTP MockTransport exercises the real async function and actual HTTPX request/response handling; no API keys or public network are needed for unit tests.

Observed green progression: 1, 2, 3, 4, 11, 18, 19, 21, 22, 32, 33, 37, 38, 43, 44, and finally **48 passing cases**. Counts include parametrized validation and transport cases. A later provider-summary assertion and inherited-query assertion each independently failed before their fixes.

Acceptance coverage:

| Behavior | Test |
|---|---|
| Paid/free retention, exact item shape, actual pricing/context | `test_openrouter_keeps_paid_and_free_models_with_actual_properties` |
| Every output modality, no price/provider filter | `test_openrouter_requests_every_output_modality_without_price_filter` |
| Independent hosting-provider stream | `test_provider_catalog_is_an_independent_discovery_stream` |
| Actual UnoRouter public endpoint and observable tags/types | `test_unorouter_uses_documented_public_catalog_not_onerouter_or_key_subset` |
| Empty/error/malformed envelopes never healthy; other streams continue | `test_invalid_or_empty_catalog_never_reports_healthy_and_other_sources_continue` |
| 401/403/429/503, timeouts, offline, HTML and sanitized errors | `test_transport_failures_are_actionable_without_echoing_response_or_exception` |
| Local authenticated GET, explicit provenance, no key leakage | `test_local_catalog_is_authenticated_read_only_and_retains_upstream_provenance` |
| Explicit skipped state; no environment key lookup | `test_skipped_local_source_is_explicit_and_never_probes_or_reads_environment` |
| Optional key-accessible catalog does not replace public catalog | `test_unorouter_explicit_key_adds_separate_accessible_catalog_without_narrowing_public` |
| Partial results retain good rows and reject malformed rows | `test_malformed_rows_are_ignored_but_valid_rows_retained_with_partial_status` |
| Credential/query isolation, bounded timeout, no redirects | `test_requests_strip_client_credentials_bound_timeouts_and_never_follow_redirects` |
| Meaningful limits change fingerprint; timestamps/order do not | `test_fingerprints_detect_real_limits_but_ignore_timestamps_and_set_order` |
| Speech, transcription, reranking remain explorable | `test_non_text_output_types_remain_classifiable` |
| Reflected and nested secrets cannot become evidence/items | `test_server_echoed_keys_and_nested_credentials_never_escape_as_catalog_evidence` |
| Invalid/credential-bearing local URLs rejected without probing | `test_credential_bearing_or_non_http_local_urls_are_rejected_without_probing` |
| Incomplete catalogs truthfully partial; no untrusted pagination | `test_incomplete_catalog_is_partial_and_untrusted_pagination_is_not_followed` |
| Invalid prices/provider limits cannot be healthy | `test_invalid_pricing_or_provider_limits_cannot_be_healthy` |

Commands run from `C:/tmp/eli-lain-tracker`:

```bash
.venv/Scripts/python.exe -m pytest tests/test_intel_catalogs.py -q
# 48 passed in 0.14s

.venv/Scripts/python.exe -m pytest tests/ -q --tb=short -k 'not test_browser'
# 208 passed, 6 deselected, 3 warnings in 8.46s

git diff --check
# exit 0
```

An earlier full-suite run reached 192 passing tests but six unrelated reporter browser fixtures errored because the installed Playwright Chromium headless-shell executable was absent. No browser installation or out-of-scope reporter changes were made. The latest non-browser run passes; three existing tracker-core Pydantic deprecation warnings remain.

## Live smoke: real public responses, September 30, 2026

A real `httpx.AsyncClient` called the final function with default `include_local=True`, no keys, and a request hook recording URLs. The smoke asserted every declared source count equals the count of returned rows assigned to that source, every item source has a matching source record, and reported total/unique identifiers programmatically.

Exact request URLs:

```text
https://openrouter.ai/api/v1/models?output_modalities=all
https://openrouter.ai/api/v1/providers
https://api.unorouter.com/api/pricing/catalog
```

Exact final output summary:

```json
{
  "sources": [
    {"name": "openrouter-models", "status": "ok", "checked_at": "2026-09-30T13:23:53.855255+00:00", "item_count": 635, "error": null, "url": "https://openrouter.ai/api/v1/models"},
    {"name": "openrouter-providers", "status": "ok", "checked_at": "2026-09-30T13:23:53.938082+00:00", "item_count": 112, "error": null, "url": "https://openrouter.ai/api/v1/providers"},
    {"name": "unorouter-models", "status": "ok", "checked_at": "2026-09-30T13:23:54.268092+00:00", "item_count": 238, "error": null, "url": "https://api.unorouter.com/api/pricing/catalog"},
    {"name": "freellmapi-models", "status": "skipped", "checked_at": "2026-09-30T13:23:54.268092+00:00", "item_count": 0, "error": "Explicit FreeLLMAPI API key required", "url": "http://localhost:3001/v1/models"}
  ],
  "total_items": 985,
  "unique_ids": 985
}
```

The public UnoRouter count changed from 239 in an earlier smoke to 238 in the final run; the summaries above use the exact final response rather than assuming a static count.

Full real return data is saved outside the repository at `C:/Users/emadg/AppData/Local/hermes/cache/scratch/catalog-smoke.json`; the live harness is `catalog-smoke.py` in the same scratch directory. Neither artifact contains supplied API keys. Authenticated local and UnoRouter-key smoke testing was intentionally left to the parent, which owns explicit credential injection. No successful/free inference is claimed.

## Sources

[1] https://unorouter.com/en/docs/platform
[2] https://unorouter.com/en/docs/platform/platform-api
[3] https://unorouter.com/en/docs/platform/models-and-pricing
[4] https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties
[5] https://openrouter.ai/docs/api/api-reference/providers/list-all-providers
