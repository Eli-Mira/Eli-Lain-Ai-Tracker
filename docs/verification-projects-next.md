# Project discovery shortlists — verification and integration

Verified locally on **2026-10-01 (UTC)**. This is an advisory suitability review of observed public metadata, **not** installation, integration testing, a security audit or a benchmark of any selected third-party project.

## Delivered files

- `src/intel_sources/recommendations.py`: pure, read-only evaluator.
- `tests/test_project_recommendations.py`: strict RED → GREEN tracer-bullet tests, including frozen-artifact replay.
- `data/project_evaluations.json`: actual saved-state snapshot, official observations, source coverage, shortlist results and provenance.
- This document.

No changes were made by this work to the store/decisions modules, discovery collectors, main/report rendering, providers/news, workflow, router database or parent checklist. No third-party repository was cloned, installed or executed. Nothing was committed, pushed, deployed or notified.

## Actual source state and observations

The input was the existing `data/intel_state.json`, SHA-256:

```text
4f931776e456a0dee6b3eb4674336e2fe705b749e7d7e4c4f4b69833eceac4b0
```

- Broad saved inventory: **1,772 rows**, unchanged byte-for-byte after generation.
- Discovery subset: **503 unique rows**, comprising **454 Skills.sh** rows and **49 GitHub Trending** repositories. All 503 are preserved in the artifact, not replaced by the shortlist.
- Saved discovery checks: Skills.sh `2026-09-30T14:04:05.492681+00:00`; GitHub Trending `2026-09-30T14:04:13.813647+00:00`.
- Official metadata review: **12 observed candidate identities**, **9 upstream repositories**, **8 exact capability documents**. Repository API observations were obtained on `2026-10-01` at `00:16:40–00:16:41 UTC`. Final capability enrichment completed at `2026-10-01T00:28:16.140316+00:00`.
- Artifact generated at `2026-10-01T00:37:08.455132+00:00`. Its frozen freshness describes that instant, not the reader's current date.
- **491 discovery rows remain unreviewed** by this bounded project-specific pass. No absence or incompatibility claim is made about those rows. Leaderboards are not complete catalogs.

Metadata sources are recorded per observation and selection in `source_urls`: official GitHub repository API URLs and exact upstream `raw.githubusercontent.com` capability-document URLs. Only descriptive frontmatter was retained from skill documents; instructions were not executed. Repository/license descriptions are self-reported metadata, not independent verification. API response/document SHA-256 values and observation timestamps are retained. Longer descriptions are bounded excerpts with truncation flags.

Two guessed Matt Pocock document locations returned HTTP 404. An official repository-tree lookup located the real `skills/engineering/<name>/SKILL.md` paths; both final capability requests returned HTTP 200. Prior path failures are disclosed in the saved official observations.

## Actual shortlist

| Project | Selected observed identities | Project-specific application and limits |
| --- | --- | --- |
| Hearth POS | `mattpocock/skills/domain-modeling`; `obra/superpowers/systematic-debugging`; `obra/superpowers/test-driven-development` | Order/bill/refund boundaries, SQLAlchemy sessions, Qt signal lifecycle, Decimal totals and split-bill rollback. Guidance only; no payment-terminal, fiscal-compliance or receipt-device validation. |
| Gesture control | `mattpocock/skills/codebase-design`; the two `obra/superpowers` skills above | Detector ownership, immutable frame snapshots, fresh accepted input, loss/reacquisition and neutral-release replay with fake camera/OS drivers. No new detector selected; no real-camera or latency experiment performed. |
| Fruit-slicer | `mattpocock/skills/domain-modeling`; the two `obra/superpowers` skills above | Fruit lifecycle, double-hit suppression, swept collision, combo expiry and fixed-clock spawn tests. Engine/render stack is unconfirmed; no engine migration or frame-rate claim. |
| Data/AI | `supabase/agent-skills/supabase-postgres-best-practices`; `obra/superpowers/test-driven-development`; `pytorch/pytorch`; `VectifyAI/PageIndex` | Conditional PostgreSQL schema/query/tenant-isolation review, ETL/model adapter regressions, tensor/model-development experiments and document retrieval evaluation. Windows/Python/GPU compatibility, retrieval accuracy, privacy and operating cost still need separate tests. |

There are **13 project selections across 7 unique identities**. `mksglu/context-mode` is reviewed but **deferred** from Data/AI by the four-item limit. Hearth, gesture and fruit each expose **8 explicit exclusions**; Data/AI exposes **4**. An identity not assigned to a project is not silently claimed to be compatible with it.

Browser automation, React/Next.js and web-only UI auditing are withheld from native PySide6 and camera/input work. Browser/React adoption is also withheld from fruit-slicer until its actual stack is confirmed. PostgreSQL tuning is not recommended for Hearth without confirming the backend. PyTorch is not recommended as a gesture detector replacement without a stated training need and replay/latency evidence.

Every selection exposes reason, three fit axes, constraints, source URLs, both discovery/official freshness, explicit unknowns, confidence rationale, evaluation status and a proposed next validation. All installed-integration flags are **false**. Confidence never exceeds **medium**, and it refers only to metadata-supported suitability. Cost and support are **unknown** for all candidates. API null/`NOASSERTION` license values remain **unknown** (including PyTorch and context-mode); an MIT/Apache metadata label is not a free hosting/inference entitlement or a complete dependency/model-license review.

## Callable and data contract

```python
from intel_sources.recommendations import evaluate_projects

result = evaluate_projects(items, now=None)
```

`items` is the **list of row dictionaries** in `IntelStore.read()['items']`, not the enclosing store payload. Passing the full inventory is supported: non-discovery catalogs are ignored for selection but included in `inventory_count`. The artifact passes only its actual 503-row discovery subset and records the original 1,772-row count separately in provenance.

Relevant saved fields are `id`, `headline`, `source`, `summary`, `url`, `checked_at`, `first_seen`, `freshness`, `not_observed_in_latest_fetch` and `evidence`. Literal IDs must be `github:<owner>/<repo>` or `skills:<owner>/<repo>/<skill>` (two-component site skills are recognized for coverage); source and URL must match. Invalid tokens are reported, never repaired.

Optional enrichment belongs at **`row['evidence']['official_metadata']`**:

- `status`, `checked_at`, `repository`, `url` (official GitHub repository API), `source_urls` (API plus capability URL, if any).
- `description`, `license` (API SPDX value or null), `archived`, `disabled`, `pushed_at`, `language`, `default_branch`, `http_status`, `sha256`.
- For skills: `capability_description`, `capability_url`, optional `capability_checked_at`, `capability_http_status`, `capability_sha256` and `capability_error`.

Metadata is accepted only when bound to the literal repository and exact reviewed skill path; another skill in the same repository cannot supply capability evidence. Untrusted URLs/extra fields are not promoted. A repository API license alone does not corroborate a skill capability. Missing enrichment stays provisional/low-confidence. Archived, disabled or unavailable-capability observations withhold adoption.

`now` is an aware `datetime`, normalized to UTC; a naive time raises `ValueError`. Default: UTC now. Freshness is recomputed with a **24-hour** ceiling. Future/ambiguous timestamps, failed metadata and retained stale discovery cannot gain medium confidence. Use `IntelStore.read(now=now)` so source failure flags are preserved.

Return shape:

```text
{
  evaluated_at: ISO UTC string,
  inventory_count: input row count,
  coverage: {
    inventory_replaced: false,
    shortlist_limit_per_project: 4,
    discovery_count: deduplicated valid discovery count,
    invalid_rows: [{id, reason}],
    unreviewed_ids: sorted list
  },
  groups: {
    hearth-pos | gesture-control | fruit-slicer | data-ai: {
      project: project description,
      shortlist: [selection], deferred: [selection], excluded: [exclusion]
    }
  }
}
```

A selection includes `id`, `headline`, `reason`, `axes`, `score`, `constraints`, `next_validation`, `source_urls`, `evaluation_status='metadata-only'`, `integration_tested=False`, `confidence`, `confidence_reason`, `license`, `cost`, `support`, `freshness={discovery, official_metadata}` and `evidence={discovery, official_metadata}`. Exclusions include the same disclosure/evidence fields but no fit axes/score. Discovery evidence carries original observed fields and an explicit non-capability/non-integration semantics label.

Axes are bounded reviewer judgments: `problem_fit`, `stack_fit`, `adoption_safety`, each 0–3. Their sum is an advisory priority score, **not a probability, benchmark or quality tier**. Stack fit describes conceptual/language fit, not tested binary compatibility; adoption safety describes proposed review-only scope, not a security audit. Ranking is descending sum, then medium-before-low when tied, then literal ID. At most four candidates are returned per project; overflow remains in `deferred`. Duplicate IDs use the latest observation timestamp, with canonical JSON as deterministic tie-breaker. Stars, installs, trend position and tags have **no effect** on eligibility or score.

## Parent integration (not wired into main/rendering here)

Keep the broad inventory and add this as a separate advisory report field. Enrichment must be attached to copies, not written back into the discovery store:

```python
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from intel_sources.store import IntelStore
from intel_sources.recommendations import evaluate_projects

now = datetime.now(timezone.utc)
state = IntelStore('data/intel_state.json').read(now=now)
rows = deepcopy(state['items'])
artifact_path = Path('data/project_evaluations.json')
observations = (json.loads(artifact_path.read_text(encoding='utf-8'))
                ['official_observations'] if artifact_path.exists() else {})
for row in rows:
    if row['id'] in observations:
        row.setdefault('evidence', {})['official_metadata'] = deepcopy(observations[row['id']])
project_recommendations = evaluate_projects(rows, now=now)
# Pass project_recommendations separately; continue publishing state['items'].
```

This recomputes freshness; it does **not** represent a new public-source check. Fresh metadata would require a separate bounded fetch. Render `reason`, constraints, unknowns, freshness, confidence rationale and status alongside names; do not reduce results to badges/top lists. Never use these views to auto-install or auto-execute anything.

## Test evidence

Each behavior slice was written and observed RED before implementation: missing evaluator; per-project reasoning; official metadata; curated routing; bounded ranking; freshness downgrade; framework exclusions; provenance binding; archived/disabled/unavailable blockers; aware-time validation; malformed discovery; evidence preservation; missing artifact/replay; and same-repository wrong-skill rejection. Intermediate GREEN runs were made after the corresponding implementation. Test fixtures are synthetic only in unit tests; the shipped artifact is generated from actual saved rows and successful public observations.

Final focused run:

```text
.venv/Scripts/python.exe -m pytest tests/test_project_recommendations.py -q
33 passed in 0.11s
```

Coverage with branch measurement: **93% combined**, 123 statements, 6 missed, 60 branches, 7 partial branches. Compilation of the module and test file passed.

Final full-suite run with the real declared Chromium executable and notifications disabled:

```text
NOTIFICATION_CHANNEL=none PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' .venv/Scripts/python.exe -m pytest tests -q
394 passed in 12.68s
```

One intervening full-suite run reported `test_praw_workers_use_separate_bounded_clients` failing (`1 failed, 391 passed`, reused client ID assertion). That unrelated news/feed test then passed in isolation, and the full-suite rerun above passed. No out-of-scope feed file was edited. Counts changed while other delegated work added tests; the final numbers above are actual execution results, not inferred totals.

Artifact replay is asserted by `test_real_saved_shortlist_artifact_replays_exactly_from_metadata_only_snapshot`: it reevaluates the preserved rows at the artifact's actual generation time and requires exact equality with the saved result. The generator also checked that the discovery state was byte-for-byte unchanged and that every official candidate already existed in the observed inventory.

The JSON is a dated review artifact, not a live status service. It is under `data/`; the parent should explicitly decide whether to include this potentially ignored metadata-only artifact in its final commit. No credentials or provider/router records are included in the discovery snapshot.
