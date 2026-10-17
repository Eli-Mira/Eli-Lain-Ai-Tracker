# Verification — evaluated project shortlists in report UI and public export

Date: 2026-10-01 (local run, saved data only — no fresh fetch, no deploy, no publish).

## Interface added for the parent `main.py`

`src/tracker-core/tracker_core/reporter_html.py` — `HTMLReporter.render()` and `.save()` gained two
optional keyword-only parameters (both default to empty, so every existing call site is unchanged):

```python
recommendation_groups: dict[str, dict[str, Any]] | None = None   # evaluate_projects(...)["groups"]
recommendation_coverage: dict[str, Any] | None = None           # flat public-safe counters
```

- `recommendation_groups` is passed straight through to the template; expected shape is the exact
  `evaluate_projects(items, now=...)["groups"]` output: `{project_key: {"project": label,
  "shortlist": [...], "deferred": [...], "excluded": [...]}}`.
- `recommendation_coverage` is only read for these keys: `reviewed_count`, `discovery_count`,
  `inventory_count`, `shortlist_limit_per_project`. Anything else is ignored, so the evaluator's
  `invalid_rows` / `unreviewed_ids` lists never reach the renderer.
- Per-selection fields consumed by the template: `id`, `headline`, `reason`, `constraints` (list),
  `freshness.discovery`, `freshness.official_metadata`, `confidence`, `confidence_reason`, `cost`,
  `license`, `support`, `next_validation`, `source_urls` (list), `evaluation_status`,
  `integration_tested`. `evidence` is deliberately not rendered.

`src/templates/report_template_lain.html` (+ byte-identical `src/tracker-core/templates/` copy) adds
`section#project-shortlists` before the discovery inventory: one `.project-group[data-project]` per
project, `Shortlist (n)` open plus collapsed `Deferred (n)` / `Excluded (n)` details, each card
`.recommendation-item[data-id][data-decision]` rendering reason, constraint list, both freshness
values, confidence + reason, cost/license/support, next validation, `metadata-only · not
integration-tested`, and provenance links through the existing `safe_url` filter. Coverage line
`p#recommendation-coverage` states reviewed/total and that leaderboards are not full catalogs. The
original `<style>` block, header, and the full discovery inventory are untouched; no new remote
assets and no new inline script (the discovery filter script is unchanged, so the hash-based public
CSP still matches).

## Fail-closed public projection

`build_public_payload()` now validates every public discovery identity first (existing strict
exact-id → host → detail-path rules, private repo excluded), then evaluates the **full** validated
public discovery inventory with `evaluate_projects(...)` — not the alphabetically capped, exported
row subset. Only after evaluation is `tool_items` capped at `max_items_per_source`.

Public payload additions:
- `recommendation_groups`: evaluator output with the `evidence` key deleted from every selection.
  Reasons/constraints/next-validation come from the curated `PROFILES`/`EXCLUSIONS` tables only;
  cached free-text `summary`, `constraints`, `source_urls` and evidence are never copied.
- `recommendation_coverage`: `{reviewed_count, discovery_count, inventory_count,
  shortlist_limit_per_project, max_items_per_source, exported_count, inventory_replaced}`.

Saved state is not mutated, and the existing private-data assertions (`PRIVATE_`, `localhost`, private
repo URL) still hold on the extended payload.

## Tests (strict RED → GREEN)

`tests/test_project_report_ui.py`:
1. `test_lain_render_accepts_evaluated_groups_and_preserves_inventory` — RED: `TypeError:
   HTMLReporter.render() got an unexpected keyword argument 'recommendation_groups'`; GREEN after
   reporter + template change.
2. `test_public_shortlists_review_full_validated_inventory_not_display_cap` — RED:
   `AssertionError: public project shortlists are missing`; GREEN after the public projection change.
3. `test_real_saved_inventory_renders_advisory_shortlists_in_internal_and_public_chromium` — real
   `data/intel_state.json` → internal + public artifacts, verified in real Chromium.

```bash
NOTIFICATION_CHANNEL=none PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' .venv/Scripts/python.exe -m pytest tests -q
```
353 passed in the subset runnable in this worktree (see Limitations); `tests/test_project_report_ui.py
tests/test_public_report.py tests/test_project_recommendations.py` → 141 passed. Six modules
(`tests/test_adapters.py`, `tests/test_feed_reliability.py`, `tests/test_intel_integration.py`,
`tests/test_next_phase_integration.py`, `tests/test_report_delivery.py`, and
`test_optional_feed_state_write_failure_cannot_discard_success`) are owned by other in-flight tasks
in this worktree and currently fail to collect or fail on a missing `intel_sources.report_delivery`
module — unrelated to these files; the parent baseline (399) plus the 3 new tests must be re-confirmed
after those land.

## Real artifacts (readback hashes)

Built by `scripts/build_project_ui_artifacts.py` (saved data only) under Hermes scratch, verified by
`scripts/verify_project_ui_browser.py` with the real Chromium at `chromium-1208`.

| artifact | bytes | sha256 |
|---|---|---|
| `…/scratch/lain-project-ui/internal/elain_project_shortlists.html` | 2330134 | `aa6ff77f4ab453400e45ef068139cbe31baa3aa118f458affe43f5c65f91dccf` |
| `…/scratch/lain-project-ui/public/index.html` | 205912 | `743164b4d39776d16ec91742ac00ab75c10ee73b1817767169fa11f5cc21c897` |

Counts from the built files (not replayed totals):
- Internal: 1772 discovery rows retained, 503 discovery candidates, **12 reviewed**, shortlists
  `data-ai 4 / fruit-slicer 3 / gesture-control 3 / hearth-pos 3`, deferred `data-ai 1`, excluded
  `8/8/8/4`, 42 rendered recommendation cards.
- Public (`max_items_per_source=25`): 1236 validated public inventory rows, **485** discovery
  candidates evaluated, 125 rows exported, **12 reviewed**, 42 cards, CSP meta present.
- Browser (both artifacts × 360 px and 1440 px, plus JavaScript disabled at 1440 px): 4 project
  groups, 42 cards, `first_card_id=skills:mattpocock/skills/domain-modeling`, no horizontal overflow,
  no page errors, exactly one request (the file itself, offline), no `localhost` and no Windows path in
  rendered text.

## Limitations / truth rules preserved

- Metadata-only suitability. No installed integration tests, no auto-install, no execution of
  discovered third-party code; discovery rank never selects a candidate.
- Freshness is shown per axis (`Discovery` / `Official metadata`) and `fresh|stale|unverified` only.
- Cost and support stay `unknown`; `null`/`NOASSERTION` license renders `unknown`.
- Skills.sh/GitHub Trending are observed leaderboards, not full catalogs; shortlist cap is 4/project,
  remainder shown as `deferred`; the broad inventory is never replaced.
- `official_metadata` from `data/project_evaluations.json` is **not** read here: the public projection
  re-evaluates from validated identities only, so official-metadata corroboration stays
  `unverified` in the public artifact (confidence `low`). The internal caller may pass evaluated
  groups built with that evidence.
- No commit, push, deploy, publish, notification, or network asset was performed.
