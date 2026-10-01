# Release template / public-consumer audit

## Outcome

Reproduced the complaint against the supplied attachment, actual `public/index.html`, and the latest existing private report in real Chromium. The colors/header were present; saying “the CSS matches” was not sufficient. The public inventory began 6,644.80px down the desktop page and 9,335.14px down the mobile page, and **all 449 discovery rows had lost structured source details**. The public projection also rendered an unsupported “No material changes detected” claim.

Fixed the confirmed projection/template/export paths, with RED regressions first. That offset measurement was taken under the catalog-first layout and is superseded: the evaluated shortlist now begins the page, and the catalog sits below it inside a collapsed archive, so its position is intentionally deep. The evaluated project shortlist (`#project-shortlists`) now leads the page, with the original provider/news sections immediately after it and the complete collected catalog retained underneath as a native `<details id="discovery-inventory">` archive that is collapsed by default in the public export and open in internal reports. Private observations are explicitly excluded, not represented as zero tracked providers/news or successful change assessment. No row and no Skills.sh owner identity was dropped in that reorder; the catalog remains reachable and searchable, and filtering auto-opens the archive so a match is never left hidden. The original dark/cyan, monospace, scanline, portrait, spacing and 640px design remain. Readable counters use additive extension CSS; the locked original style block is untouched.

No deployment, notification, push or commit was performed.

## Root-cause trace and falsified hypotheses

1. **Wrong file/theme selected:** falsified for the inspected runtime. `main.py` defaults to `lain`, calls `get_html_reporter`, and resolves `LainReporter`. The actual Jinja loader selects `src/templates/report_template_lain.html`, not the tracker-core copy. Both copies were identical. The supplied original stylesheet was present. A separate confirmed hazard existed: the named Lain reporter silently fell back to an unrelated default template if its file was missing; the production named reporter now fails closed. Legacy generic `HTMLReporter` fallback behavior remains compatible.
2. **Structural drift despite matching styles:** confirmed by screenshots/DOM. Empty changes/actions, lengthy source health and project reviews came before the original sections and public discoveries. The public template now leads with the bounded evaluated shortlist, retains the original two-section lead-in immediately after it, keeps the full inventory as a collapsed-but-complete archive with its filters, and never renders an empty synthetic change assessment. Internal reports retain change-first behavior when actual changes/baseline are supplied.
3. **Loss at the public projection seam:** confirmed. Public catalog adapters/store held context, prices, modalities, provider geography, repository statistics and leaderboard observations. `build_public_payload` discarded all of these, emitted a fixed disclaimer plus two timestamps, and the renderer could not recover them. The repair reconstructs a separate `public_metadata` list from a small typed allowlist; it does not restore raw dictionaries or cached descriptions.
4. **Offline/no-JS and counter usability:** confirmed. The three filters looked enabled without JavaScript but did nothing. Controls now start disabled and become enabled only after the inline controller initializes. Native disclosure controls remain usable without JavaScript. Original dim counter contrast measured 4.3712:1; counter text now uses the existing light text token through additive CSS.

## Public metadata contract

All labels are static. All values are closed-vocabulary enums, exact booleans or bounded finite numbers. Unknown fields, objects, freeform descriptions, URLs inside raw evidence, operational errors, credentials and arbitrary cached `public_metadata` are not copied.

| Public family | Details reaching the consumer |
|---|---|
| OpenRouter models | Context and maximum-output token limits; input/output modalities; allowlisted supported parameters; base input/output/cache/request prices with explicit units; a fixed warning when conditional price tiers exist |
| OpenRouter providers | Allowlisted headquarters/datacenter country codes; explicit missing-structured-metadata notice when neither is supplied |
| UnoRouter public catalog | Model type, allowlisted capability tags and endpoint formats; token or fixed-request pricing; explicitly labelled catalog free/online flags (not entitlement/inference proof) |
| GitHub Trending | Allowlisted language, stars/forks, daily/weekly/monthly ranks and stars gained |
| Skills.sh public HTML | All-time/trending/hot ranks and installation observations |

Prices use source-specific units: OpenRouter token prices are converted to million-token prices using Decimal; UnoRouter input/output catalog prices already use million-token units. Only explicitly fixed-price UnoRouter rows show request pricing. Missing, negative, nonfinite, malformed and extreme values are omitted rather than guessed. OpenRouter conditional overrides are not dumped; the base-rate scope warning sends the consumer back to the public source.

Source health also retains safe per-window status enums and bounded row counts. Stored raw errors/coverage strings are never copied. Exported row counts and full valid saved public inventory are labelled separately.

Key-scoped origins are excluded even when a cached row uses a public source name: explicit key-accessible/local provenance is rejected, and Skills.sh API-mode observations/source coverage are not public-authorized. News, provider probes, provider operational statuses/actions, local router inventory and account/key-accessible catalogs remain excluded. No project count is hardcoded; this artifact contains the three active groups supplied by the project evaluator.

## RED → GREEN evidence

Evidence and screenshots are outside the public tree:
`C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-template-audit/`.

- `red-metadata.txt`: exact end-to-end failure for missing `Context: 128,000 tokens` (1 failed, 1 passed); then `green-metadata.txt`.
- `red-layout-security.txt`: original-section order, silent named-template fallback and key-scoped public projection failures (3 failed, 15 passed).
- `red-controls.txt`: all four desktop/mobile × JS/no-JS browser cases failed the measured contrast threshold.
- `red-nojs.txt`: after the contrast repair, both no-JS cases failed because controls were enabled.
- `red-missing-template.txt`: missing-template error exposed the Jinja search path instead of a generic public export failure; now translated to a generic ValueError and no artifact is written.
- `red-coverage.txt`: missing-metadata notice and per-window coverage failures (2 failed).
- Final dedicated regression: **26 passed**. Full real-browser suite: **553 passed, 9 xfailed**, 13.72 seconds (`full-suite.txt`). No existing tests were edited by this work. Xfails are recorded by the shared suite, not treated as successful acceptance.
- `git diff --check` passed for owned implementation/template/test paths.

Browser tests include typed values reaching actual HTML, forged metadata, private canaries, malformed/nested values, booleans masquerading as integers, negative/nonfinite/extreme prices, exact original style, runtime loader, source filters, combined search filters, empty/reset states, keyboard focus, native disclosures, link safety, provenance dates, horizontal overflow, request/error/CSP monitoring and no-JS static visibility.

## Actual artifact and browser readback

Regenerated public artifact from saved inputs at **2026-10-01T05:11:43.581653+00:00**. This is regeneration, not collection. Public observation timestamps remain September 30, 2026.

| Property | Verified value |
|---|---|
| Public artifact | `C:/tmp/eli-lain-tracker/public/index.html` |
| Bytes | 659,604 |
| SHA-256 | `d5f1f08f100d1c82de5b7a17aa7c85a7bbb2bc7456493809031535fa4a4c5c52` |
| Export directory | Exactly `index.html` |
| Exported source counts | GitHub 49; OpenRouter models 100; OpenRouter providers 100; Skills.sh 100; UnoRouter 100 |
| Structured metadata | 416 rows, plus 33 explicit unknown provider-metadata notices; no disclaimer-only public rows |
| Template copy hash, both | `5bc6174ca05b3685e460e91f5da2fbceb16c8f96aa4aeae7b4a093e9cbca5bf5` |
| Locked original style hash | `347adbd0fc894df1675f565ca9d93d591a320ac2b63934b0d7615fa3554e76b8` |
| Original attachment hash, unchanged | `c6d506229ba422a1f28e5d505ab89b9e00b7fc53dfd47d8b3e7ed7373a820440` |

`final-artifact.json` records exact input hashes: attachment, state JSON and news DB are unchanged before/after regeneration. The public artifact hash was unchanged throughout browser verification.

`before-evidence.json` / `after-evidence.json` contain actual Chromium DOM results and screenshot paths. After verification covers **1440px and 390px**, offline, with JS both enabled and disabled; browser version is 145.0.7632.6. Every source/project option was exercised and compared against DOM-derived expected counts (28 combinations in each public JS viewport). Search empty/reset paths were exercised. All 486 public native disclosures were opened/closed via their native summary click behavior, with a separate actual pointer click for a sample provenance disclosure. Source links were validated without navigating away: opening external detail pages intentionally needs network access.

Each context issued only the local HTML request; no automatic remote requests, page errors or console/CSP errors were observed. The public artifact has hash-authorized inline-script CSP, no-referrer policy, no external assets, and no unsafe event handlers. Screenshots were visually inspected against the unchanged original.

## Remaining boundaries / blockers

- The 33 public provider listings do not contain vetted geography in the saved observation. They now say so explicitly; no private descriptions or invented provider availability were substituted.
- Saved catalog identities are still filtered by the pre-existing strict public-URL rule, which rejects query strings. That excludes legitimate OpenRouter `:free` suffixed model pages (23 saved rows; 0 accepted) and 117 UnoRouter rows plus 18 Skills.sh rows with non-canonical paths at the default cap. Total valid saved public inventory is 686 rows versus 1,097 before filtering. Fixing that changes identity binding rules and the existing public boundary tests, so it is reported here rather than silently changed.
- Existing historical files under `reports/` remain historical, not silently rewritten. The inspected latest historical private report hash is `91782ddca85ba5fefe1528a7c8a7d4f86e93379b65398fdf3449691cfa59f2d0`. A fresh private saved-inventory render and browser verification are retained in scratch as `regenerated-internal.html`; the parent should regenerate the final private report through its main-entrypoint acceptance path after all sibling changes settle.
- Full descriptions, complete pricing tier tables, licensing, installability and integration performance are not inferred from a leaderboard. Public structured metadata improves usefulness but is not an integration evaluation.
- No hosted/delivered URL was supplied or changed in this subtask. The verified local artifact is ready for the parent’s separate acceptance/delivery decision; no public publication occurred here.
