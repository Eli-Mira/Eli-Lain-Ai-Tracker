# Public Lain dashboard

## Product surface (R01–R07, R09)

The public report is an **Explore** surface, with source coverage as secondary
monitoring. It retains the existing teal/dark header and subdued scanlines, not
a marketing hero or fabricated metric tiles. Runtime typography uses a deliberately
selected local humanist/system stack (Segoe UI, Candara, Trebuchet MS, system sans),
17px body/description text and 14px provenance; mono is reserved for terminal accents.
The historical first CSS block remains reference evidence; additive runtime rules
implement the user-authorized layout/readability changes in both template copies.

Dark and soft-grey light mode share layout and teal accents. The system preference
applies until an explicit choice, persisted under `lain-dashboard-theme` when
storage is available. Blocked storage leaves an in-memory toggle functional;
without JavaScript, CSS still honors system theme and disabled controls are honest.
Native inventory/evidence disclosures work by pointer and keyboard without JS.

## Truthful browsing and sorting

- Search is a literal case-insensitive substring filter over public rendered fields,
  including owner-qualified IDs and vetted metadata. Topic and source filters
  intersect it. Every validated row remains in the DOM; no pagination silently
  truncates the public inventory. Explicit caller caps remain supported and disclose
  exported-of-total counts and omitted rows per source.
- **Popular** groups by source, then descending GitHub total stars or Skills.sh
  all-time installs. It never compares stars with installs as a universal score.
  Other catalogs have no popularity metric. Unknown metrics sort last within the
  source; ties use literal owner-qualified identity. Zero is a valid known value,
  not a replacement for missing data. Popularity does not establish suitability.
- **Latest (Newest)** uses validated saved `first_seen`, labelled **First observed**,
  newest first across sources. It is not publication, latest refetch, or regeneration
  time. Future, offsetless, missing or malformed times remain unknown and sort last;
  ties use source and literal identity. Last observation remains separately labelled
  in provenance evidence. No date is manufactured from generation time.
- **Relevant is intentionally omitted (R06).** Literal substring search is not a
  defensible suitability/relevance ranking. No inert dropdown option or personal
  project-fit score is exposed. A future relevance mode needs an explainable public
  query/topic model and its own acceptance tests.

## Public/private boundary and artwork

`build_public_payload` does not import/call the personalized project evaluator and
exports no recommendation groups or coverage. Public rendering also ignores
explicitly supplied personal groups. Private legacy reviews require explicit
`recommendation_groups` supplied to the internal reporter; they are not a public
product. No inventory row or Skills.sh owner identity is discarded to achieve this.
Provider/news observations, operational changes/actions, raw cached prose/errors,
private coverage, credential-scoped catalogs and local paths remain excluded.

The chosen **Serial Experiments Lain** third-party JPEG is embedded, byte-unchanged,
in `tracker_core/branding.py` (74,801 bytes, SHA-256
`4f928317acb16f4ab30488a83d34410ce78c884797fef2c00dfcada3163f6135`).
It was supplied/selected by the user, not fetched from GitHub or another service.
Original artist/rights-holder licence is not established; ownership and
redistribution rights are **not** asserted. This artwork is **not covered by the
repository's MIT code licence**. The page footer carries the provenance note;
public release still needs appropriate artwork-rights review.

The exporter accepts at most this one digest-bound JPEG with exact safe attributes;
it does not accept arbitrary data URIs, SVG, remote images, `srcset`, event handlers
or other automatic dependencies. The CSP permits data images, hashes the inline
controller, blocks connections/fonts/objects/media/forms and uses no-referrer.
Only three fixed existing dashboard section anchors bypass public HTTP validation.
The dedicated public directory contains **only `index.html`**. Saved inputs are
read-only; dirty directories and symlink/junction paths are still rejected.

## Reproduce local verification (no fetch, deploy or send)

From the repository root, use the project venv with inherited PYTHONPATH removed:

```bash
export NOTIFICATION_CHANNEL=none
export PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe'
env -u PYTHONPATH .venv/Scripts/python.exe scripts/build_project_ui_artifacts.py "$TMPDIR/lain-dashboard-latest"
env -u PYTHONPATH .venv/Scripts/python.exe scripts/verify_project_ui_browser.py "$TMPDIR/lain-dashboard-latest/public/index.html"
env -u PYTHONPATH .venv/Scripts/python.exe -m pytest tests/test_public_dashboard.py -q --basetemp="$TMPDIR/dashboard-tests-unique"
```

The builder replaces the latest public file only, exports the full validated saved
inventory with no default cap, verifies input hashes unchanged and prints exact
artifact hash/counts. It also accepts `--state` and `--news-db` for synthetic tests.
The verifier asserts 360/390/1440px, JS on/off, both system themes (12 combinations),
200% zoom/no overflow, native keyboard disclosure, loaded avatar, working filter
and deterministic Popular/Latest DOM order, theme toggle/reload persistence,
no personal groups/paths, and zero HTTP requests/console/page errors.
Browser launch and assertion failures fail the command rather than becoming skips.

These are **local saved-state and synthetic-test results**, not a fresh source fetch,
hosted deployment/readback, legal clearance or release approval. No repository
visibility, credentials, notifications, delivery configuration or durable task
ledger is changed by this dashboard work.

## Superseded acceptance semantics

R09 replaces the earlier public `project-shortlists`-first contract. Public tests
now assert Explore first/no personal groups while preserving private explicit-review
tests, complete inventory counts/identities, disclosure/live-region behavior,
public sanitization, script CSP, no-JS, input immutability and remote-dependency
rejection. Historical hardcoded 640px runtime-width checks become 1120px responsive
layout checks; the original CSS reference hash remains unchanged. Security tests
allow only the trusted avatar and fixed internal navigation, not arbitrary images
or previously rejected links. Dark-mode fixtures explicitly select dark system
preference because system-default light is now supported.
