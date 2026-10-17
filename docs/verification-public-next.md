# Public standalone export verification — 2026-10-01

## Outcome and scope

Implemented an explicit sanitized-public boundary without changing `main.py`, the reporter, either template, workflow, provider/store/decision/catalog/news modules, or the parent checklist. Nothing was committed, pushed, deployed, posted or notified. The private repository and internal JSON/SQLite were not published. Discovery items were not installed or executed.

Final artifact: `C:/tmp/eli-lain-tracker/public/index.html`

- SHA-256: `15e86f196f8977f03a8bd6db365ce38a2886731b714fd3afc9372bcc460724f3`
- Bytes: `467430`
- Export directory contents verified: **`index.html` only**.
- Rendered at: `2026-10-01T00:31:46.191851+00:00`.
- Actual Chromium verification completed at `2026-10-01T00:31:50.826425+00:00`.
- 449 public discovery rows: GitHub Trending 49; OpenRouter models 100; OpenRouter providers 100; Skills.sh 100; UnoRouter public models 100. Five public source-coverage rows.

Saved-state input JSON contained 1772 rows. The public source families are exactly `openrouter-models`, `openrouter-providers`, `unorouter-models`, `github-trending`, `skills-sh`. Authenticated/local catalogs, provider statuses, private actions/changes, account/key IDs, raw probe evidence, errors, private runtime paths and private coverage are excluded. The known private tracker repository is explicitly rejected even if a forged cache labels it public trending.

**News is intentionally not public in this boundary:** the existing `news.db` has 120 saved stories from arXiv, GitHub, Hacker News and Hugging Face; none are in the authorized five-family public allowlist. A bounded read of 100 existing rows was exercised through SQLite URI `mode=ro` plus `query_only=ON`; they remain internal and `news_items=[]`. Missing news databases are not created. Publishing news later requires an explicit additional public source policy and corresponding regressions, not automatically widening this exporter.

## Exact Python API

Module: `intel_sources.public_report`

```python
public_http_url(value: Any) -> str
build_public_payload(state: dict[str, Any], *,
                     now: datetime | None = None,
                     max_items_per_source: int = 100) -> dict[str, Any]
read_saved_inputs(state_path: str | Path, news_db_path: str | Path, *,
                  news_limit: int = 100) -> tuple[dict[str, Any], list[dict[str, Any]]]
export_public_report(state_path: str | Path, news_db_path: str | Path,
                     export_dir: str | Path, *, now: datetime | None = None,
                     max_items_per_source: int = 100) -> Path
```

`read_saved_inputs` returns **internal, non-publishable** dictionaries. Only `build_public_payload` performs the public projection. `export_public_report` handles projection itself and must be preferred over rendering internal input directly.

State must have `items` and `sources` lists. The reader rejects JSON larger than 16 MiB before parsing. Item/news limits are integers 1–200, with default 100. `now` must be timezone-aware; render time is UTC. Rows are sorted by `(source, id)`, deduplicated by source/identity, filtered, then capped per family. Inputs are not mutated.

### Exact public renderer payload

No original input dictionary is passed through. The top-level keys are:

- `api_items`, `news_items`, `change_items`, `action_items`: always empty lists.
- `tool_items`: public projected discovery rows.
- `source_items`: public collection-health/coverage rows only, never provider availability.
- `report_date`: UTC render date (`YYYY-MM-DD`).
- `generated_at`: UTC render ISO timestamp.
- `runtime_source`: fixed public disclosure explaining saved observations, no fresh fetch, and excluded sections.
- `persona_image_url`: always `None`.
- `baseline`: always `False`; this export does not calculate changes or capture a new baseline.

Every `tool_items` row has exactly:

```text
id: str                 # source namespace bound to validated public detail-page URL
headline: str           # bounded selected public title or safe identifier fallback
source: str             # one of the five public families
url: str                # validated HTTPS URL on that family's exact hostname
summary: str            # fixed advisory/listing disclaimer, never saved free-text summary
project_types: list[str]# finite known type allowlist
freshness: str          # fresh / stale / unverified, recomputed at render time
evidence: [{observed_at: str, first_observed_at: str}]
```

This generated evidence contains dates only, not any stored evidence/probe dictionary. Valid aware ISO observation strings are preserved verbatim; invalid, ambiguous or future dates become `not supplied`. `fresh` means the saved observation is within 24 hours, its public source had `ok`/`partial` status, and the row was not missing from its latest fetch. It is never a fresh-fetch, inference or entitlement claim.

The project-type allowlist is `agents`, `audio`, `automation`, `data`, `design`, `devops`, `documentation`, `embeddings`, `image-generation`, `mobile`, `multimodal`, `reasoning`, `rerank`, `security`, `speech`, `text`, `tools`, `transcription`, `video`, `vision`, `web`.

Every `source_items` row has exactly `name`, `status`, `checked_at`, `item_count`, `url`, `coverage`. Status is a bounded collection-status enum (`ok`, `partial`, `error`, `skipped`, or `unverified`). URLs and coverage disclaimers come from fixed public constants, not saved source URLs/coverage/errors. `checked_at` is the preserved valid source observation string or `None`. Counts describe **exported rows**, never hidden/private totals.

Saved public source observation times preserved in this artifact:

| Source | Observation time |
| --- | --- |
| OpenRouter models | `2026-09-30T14:04:04.769235+00:00` |
| OpenRouter providers | `2026-09-30T14:04:04.818373+00:00` |
| UnoRouter public models | `2026-09-30T14:04:05.134525+00:00` |
| Skills.sh | `2026-09-30T14:04:05.492681+00:00` |
| GitHub Trending | `2026-09-30T14:04:13.813647+00:00` |

## CLI and integration

```bash
.venv/Scripts/python.exe scripts/export_public_report.py --max-items-per-source 100
```

Optional flags: `--state`, `--news-db`, `--output-dir`, `--max-items-per-source`. Defaults are anchored to the repository, not the shell's current directory. The CLI prints JSON containing exactly `artifact`, `bytes`, `sha256`, `source_counts`, computed by reading the final file. Input/destination failures print a fixed generic error without internal tracebacks or source text.

The exporter accepts an empty output directory or one containing only a regular `index.html`; it refuses other entries, index directories, symlinks and Windows reparse/junction ancestors. HTML is written by atomic replacement; temporary sanitized HTML is cleaned up. No DB, JSON, stylesheet, image, source file or asset is copied. Before/after input SHA checks on the real saved export confirmed unchanged JSON/SQLite.

Parent integration still needed:

1. Decide whether generated `public/` is gitignored; this subagent did not alter `.gitignore`.
2. If adding a CLI/report hook, call `export_public_report` or this standalone script; never feed internal reporter dictionaries to the public route.
3. Preserve private repo visibility and deploy/copy **only the final HTML**, not the repository, data directory or broader build tree. Deployment remains unauthorized in this turn.
4. Excluded-provider/change/action/news template empty states are retained to preserve the supplied design. The footer explicitly says those sections are excluded, not evaluated. Do not interpret the template's empty change message as a measured public change result. A more prominent exclusion banner can be a separate parent-owned template decision.

## Safety and standalone dependencies

The original Lain reporter/template is used unchanged. The original locked style string is retained exactly. Additions are only meta CSP/referrer controls in the generated HTML. The template's current portrait is a CSS-only placeholder; no remote decorative resource is needed. Existing inline CSS, system monospace fonts and the original inline discovery filter are self-contained.

- Reject credentials/userinfo, local/private/loopback/link-local IPs and ambiguous numeric IP encodings. All IP literals are conservatively rejected, including public IPs.
- Reject single-label/local domains, non-default ports, whitespace/control characters, backslashes, percent escapes, query strings and fragments. Rejecting **all** query/fragment/percent forms avoids relying on an incomplete list of secret field names.
- Further bind exported item IDs, HTTPS hostnames, detail paths and source namespaces. GitHub identifier/path casing can differ; other source identities must match exactly. No DNS lookup or network fetch is performed by the export.
- Never render arbitrary saved descriptions, errors, raw evidence, fingerprints or runtime labels. Selected titles are bounded and checked for credentials, local paths/hosts/IPs, account/key metadata and active markup; unsafe titles fall back to the validated public slug.
- Jinja autoescaping remains active. Public anchors retain `noopener noreferrer`; a `no-referrer` meta further prevents referrer disclosure.
- CSP blocks all default/connect/image/font/media/object requests and permits only the hash of the current inline filter plus inline CSS. Filters work under that CSP.
- Future remote/active template dependencies cause export failure, not silent network fallback. Test external scripts intentionally lack SRI because they are malicious regression fixtures that the exporter must reject, not deployed dependencies.

This is a field/provenance allowlist, not a universal secret classifier: deliberately forged public-looking title/identifier strings cannot be proven publicly sourced without a fresh fetch, which is outside this saved-state export. Public-like raw title text is selected only from the five allowed families after detail URL/identity validation. Do not broaden that free-text allowance to saved summaries or evidence. Outbound links are user-initiated navigation to public catalogs/repositories; third-party destination behavior is outside the standalone artifact.

## TDD and verification evidence

Observed RED → GREEN slices covered the missing projection; missing strict URL validator; identity/source spoofing; unsafe-title fallback; deterministic dedupe/caps; malformed shapes/limits; saved input reader and real HTML output; dirty-directory/CSP/remote dependency failures; standalone CLI; strict provenance/byte bound; forged private repository; and private hosts/paths/tokens hidden in selected titles. Tests were run before implementing each corresponding missing behavior/regression. Chromium acceptance additionally exercised already-implemented behavior.

Final targeted gate:

```bash
PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' \
.venv/Scripts/python.exe -m pytest tests/test_public_report.py -q --tb=short \
  --basetemp='C:/Users/emadg/AppData/Local/hermes/cache/scratch/public-report-tests'
```

**105 passed**, no skips. Fixtures cover private operational dictionaries, query/fragment credentials, malformed/local URLs, namespace spoofing, raw errors, XSS, unsafe titles, dirty output trees, missing DB, SQLite/JSON immutability, generic CLI failure, future/naive observation times, invalid shapes and offline dependency rejection.

Final full working-tree gate (includes parent/other-subagent concurrent changes): **374 passed in 10.33 seconds**, no skips. The preceding full run had one time-sensitive sibling-source test (`test_feed_reliability.py::test_other_adapters_preserve_sibling_on_timeout[github]`) fail at its 0.2-second outer timeout; isolated rerun passed, and the final complete run passed. No out-of-scope code was edited to address it.

Real Chromium tested both malicious fixtures and the **exact generated 449-row saved-state artifact** at 360, 390, 768 and 1440 px: no horizontal overflow, no injected script execution, no script/CSP console errors, zero automatic network requests, correct source/search intersections and reset, expandable evidence, and all 449 rows visible with JavaScript disabled. Desktop/mobile screenshots were inspected; original dark/cyan Lain styling and usable filter controls were intact. Only bounded public source details were visible.

Local screenshots and verification probe are scratch-only, not in `public/` and not publication artifacts:

- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/public-report-mobile.png`
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/public-report-desktop.png`
- `C:/Users/emadg/AppData/Local/hermes/cache/scratch/verify_public_report.py`
