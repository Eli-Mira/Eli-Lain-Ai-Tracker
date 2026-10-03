# Bounded local outputs and discovery state

Routine output is a replacement, not an archive. No historical files, live database, configuration or existing receipts are deleted by this change.

## Runtime contracts

- `intel_sources.retention.latest_report_path(reports_dir)` selects `reports/latest.html`. `write_latest_text(path, text)` and `write_latest_json(path, value)` fsync then atomically replace that path; failed writes preserve the previous file and clean their temporary file. Existing symlinks/Windows junctions/reparse paths are refused. The default per-output budget is 16 MiB (internal reports already exceed the public export's separate 4 MiB budget); oversized writes fail, never silently truncate inventory.
- The public exporter already replaces the single `public/index.html`. Do not copy it to a timestamped local snapshot after publishing.
- `IntelStore.update()` retains all current incoming discovery rows, deduplicated by literal item ID. A nonempty `ok` source snapshot replaces its obsolete full rows. A nonempty incomplete/error snapshot retains up to 1,024 unobserved siblings for that source, preferring the previous state's recently observed rows. `retention.omitted_unobserved` discloses this run's omissions. An empty, wholly failed or absent source retains its entire last-good inventory, even when larger than that historical budget; staleness alone never authorizes wiping useful current results. Size is bounded by current inventories and the historical allowance, not by arbitrarily truncating fresh catalogs.
- Current rows keep their original `first_seen` and full prior change fingerprints. The 64 most recently displaced identities retain only `id`, `source`, `first_seen` and a SHA256 fingerprint. Returning identities within that finite horizon preserve first-seen and update/no-change detection across restarts. Beyond it, `newly_observed` means newly present in retained state, **not** a proven first-ever observation or launch.
- Source/feed cooldowns, provider state/change fingerprints and the working SQLite news database remain untouched. Do not reset those to reduce disk usage. The database is not made bounded by a seven-day display filter; no historical SQL row deletion is authorized here.
- Delivery receipts retain at most 64 artifact hashes with bounded essential message IDs/destination hashes. Incomplete fan-out confirmations and the latest confirmed sibling per mode/channel are pinned. Capacity exhaustion fails before new network requests instead of erasing those confirmations. See `docs/link-first-delivery.md` for the finite replay window and ambiguous responses.

## Minimal integration hooks (owned by main/reporter integrator)

```python
from intel_sources.retention import latest_report_path, write_latest_text

# NewsTracker.generate_report default only; preserve explicit user output_path.
output_path = output_path or latest_report_path(self.reports_dir)
# Replace Path(output_path).write_text(html, encoding="utf-8"):
write_latest_text(output_path, html)
```

`LainReporter.save()` currently requires an explicit output path, so it needs no naming change; optionally use `write_latest_text(output_path, html)` for the same atomic-write safety without changing its positional/keyword contract. No post-run deletion is needed. The CI internal artifact selects `reports/latest.html`, so this hook must land with the workflow change.

## Search/cache/download audit

The active `main.py` constructs `FileCache` but does not call its persistence methods. Current catalog/tool collection keeps HTTP/search responses in memory and writes the deduplicated `intel_state.json`, not raw responses. The legacy tracker-core `FileCache` permits one file per arbitrary key, and legacy JSON batch storage permits date-named news files; they are not the active news/discovery storage path. Do not introduce calls to these archive writers in routine runs. Any new search consumer should retain current structured rows via `IntelStore` (or one fixed latest JSON path), never raw HTTP bodies or timestamped snapshots.

CI's 14-day remote artifact retention is distinct from Mira disk usage. There is no automated `gh run download` helper in this repository. For approved QA, download only the specific sanitized artifact into a single designated **scratch/current** directory. Review the exact scope before replacing a previous scratch directory; never recursively clear a parent audits/projects/vault directory. Keep only latest QA hashes/counts and the bounded receipt afterward; screenshots/raw responses/downloaded HTML must not become an expanding durable audit archive. This procedure does not authorize deleting existing audit evidence elsewhere on Mira.

## Existing archives: discovery only

```bash
python scripts/cleanup_local_outputs.py --root C:/tmp/eli-lain-tracker --dry-run --json
```

The CLI has **no delete/apply option**. It reads only direct children of the exact root's `reports`, `data` and `.cache` directories, matching known date-named report/news/search/snapshot filenames. It returns exact paths, byte sizes, SHA256 hashes and exclusions. Unknown files, nested directories, symlinks/junctions, `public/index.html`, `reports/latest.html`, databases (including WAL/SHM), config, cooldowns/current state and delivery receipts are excluded. Read errors fail the inventory rather than silently treating it as a complete manifest.

Review those exact paths/hashes, plus explicit exclusions, with Eli before any separately authorized deletion. This is deliberately not a whole-disk inventory: external CI downloads/agent audit folders require their own explicitly scoped review. No archive in the actual worktree was removed.

## Synthetic evidence

`tests/test_local_retention.py` runs 90 real temporary-file report/state/MockTransport delivery cycles, then restarts: four routine files, 64 receipts, two current discovery rows, bounded identity metadata, and only the hosted-byte GET on the identical restart (zero message posts). Separate tests cover 100 replacements without adding files, 140 receipt writes with a pinned partial sibling, first-seen/fingerprint recovery, malformed-state refusal, write failures and real Windows junction refusal. These are local deterministic checks, not fresh hosted deployment, live channel delivery, or acceptance of historical cleanup.
