# Decision-first consumer — fresh hosted verification (2026-10-02 Cairo)

## Verdict and boundary

**BUG7 first-view/order/disclosure defect: VERIFIED SHIPPED. Customer release: NOT APPROVED.**
This is a newer bounded publication proof, not a replacement for open source, recommendation-depth, dependency/security, live-provider, real-summary or delivery-continuity acceptance.

## Reviewed code and real CI

- Approved production runtime: `e62b0faf3938ca7d6fe9e35dcbaa8420640513b3`. Full v7 review `deleg_85b10c21` passed; incremental v8 reviewer `deleg_e9561445` approved exact complete diff SHA256 `b2ef427d25b78f0608d94ded44ba068ad3bfc666c8496d2bb5beffbd7dde4513` with no findings.
- First manual CI `36932048178` failed its test gate: 3 failed / 795 passed / 2 skips. It did not refresh, deploy or notify. All three failures were the native toggle's queued status update in `tests/test_public_report.py` at 390/768/1440px.
- Test-only follow-up: local import of Playwright `expect`; wait for the identical exact status using `to_have_text`. No production change, skipped assertion, expected-value weakening or sleep. Reviewer `deleg_cf0fa6a2` approved 1 file / 2 hunks / 1,638 LF bytes, exact SHA256 `c59cc1969c25285bd18c27d3484c6a22d78b5aac3d36068a97e114e212030649` with no findings.
- Tested commit `8ee2bd8730fb89759feac441efb5834809557c36` differs from the approved production runtime in `tests/test_public_report.py` only. Local full suite **800 passed**, direct exit0; ten repeated public four-width cases **40 executions passed**.
- Fresh trusted manual CI **36933189703**, created **2026-10-01T22:08:17Z** (October 2 in Cairo), completed success **2026-10-01T22:12:50Z**. Real clean-runner checkout, dependency install, Chromium, tests, refresh, export, preflight, upload, Pages deploy/readback, publish/notify and state-cache save succeeded. Regression output: **798 passed / 2 skipped in 71.48s**. These skips are not accepted failures; unchanged local setup-dependent artifact/attachment checks pass in the local full suite.

## Actual bytes, not local regeneration

| Evidence | Measured result |
|---|---|
| Canonical public origin | `https://eli-lain-intel.pages.dev/` |
| File | `index.html` |
| Bytes | 3,294,609 |
| SHA256 | `e5d5f04b432bfd6cbaca89a4e69091f8451b9b04848e1dd5cd392395a6a93e44` |
| CI export versus anonymous Pages GET | byte-for-byte equal |
| Production Pages verification CLI | `verified: true` |
| Browser provenance | `actual-served-ci-36933189703` |
| Offline actual-file Chromium checks | **102 / zero failures**, 390px and 1440px, JS on and off |
| Initial disclosures | **zero `details[open]`** in public file |
| Recommendation groups | Hearth POS; gesture control; data/AI |
| Shortlist cards | **10**, all low-confidence / metadata-only / not integration-tested |
| Review coverage | **12 reviewed / 1,247 discovery candidates** |
| Collected/exported inventory | **2,281 rows**, still entirely reachable |
| Skills.sh literal identity check | all **1,187** rendered IDs match their full public owner/repository/name links; no name-based deletion |
| Locked original style SHA256 | `347adbd0fc894df1675f565ca9d93d591a320ac2b63934b0d7615fa3554e76b8` unchanged |

Actual source row counts: GitHub Trending **60**; OpenRouter models **645**; OpenRouter providers **112**; Skills.sh **1,187**; UnoRouter models **277**. Counts reconcile programmatically to 2,281 and match the export receipt and actual DOM.

The **public** export begins with `#project-shortlists`. **Internal** reports retain the provider/news lead-in but place the shortlist before inventory. Do not describe both modes as literal first-section placement. Public inventory is a native closed archive; internal inventory stays open. Active search/filter results pin the public archive open with a resolved cyan cue; reset clears the cue. Native pointer/keyboard/no-JS disclosures, combined filters, counts, empty/reset states, layout before any click at scrollY zero, focus, safe links, standalone requests/errors and CSP were exercised against the served file. First-screen captures remain outside the single-file public tree; finite entrance animation was disabled for the settled screenshot, not by altering the report.

## Attachment and host receipts

- Pages verification completed **before** either attachment was sent.
- Telegram: exact `index.html` attachment **receipt-confirmed**. This is not an independent fetch-back or proof that Eli opened it.
- Discord: exact `index.html` attachment **independently-read-back**.
- CI's delivery receipt binds this same SHA256 and filename. Netlify mirror path and partial-channel receipt/state-cache persistence remain retained; no host was removed.
- No-material-change dedupe, lost-response ambiguity, concurrent locking/fsync, Telegram two-step delivery and failed-fanout hosted replay remain separately open. No exactly-once promise.

## Durable private proof and continuity

`C:/Projects/CODING/CODINGWITHMIRA/EliLain-Intel-Audits/hosted-36933189703/`
contains both sanitized CI/served copies, safe status/export/delivery summaries, actual browser/consumer JSON, settled first-screen screenshots, QA tool and a per-file hash manifest. Copied bytes were verified. **Only `public/index.html` is the deliverable; do not publish the audit directory.** No credentials, internal report/state/DB, raw authenticated logs or signed download URL is archived in this proof folder.

Failed-CI/local/review evidence remains separately named under `decision-first-local-e62b0fa-ci36932048178/`; it was never represented as hosted proof. This documentation follow-up does not refresh sources or resend attachments. The tested runtime SHA above remains distinct from later documentation commits.

## Still parked / not silently completed

- Recommendation evidence/relevance depth: only 12/1,247 reviewed, all 10 public cards low confidence. Official metadata/enrichment policy and installed-integration acceptance are not established by this layout repair.
- No new real EliLain provider inference probe, paid inference, router edit or real news summarizer call was authorized or performed. Earlier Hermes compressor diagnostics are separate history, not tracker acceptance.
- Feed reductions, owner-collision winners, exposed Cloudflare-token rotation and least-privilege scope require Eli's decision. No destructive merge/deletion or token rotation performed.
- News consumer published/fetched dates and per-feed health still need a source-to-consumer check; don't invent them from regeneration time.
- Dependency lock/advisory/full-history evidence and remaining broad acceptance gates remain open in `RELEASE_ACCEPTANCE.md`.
