# Internal news date consumer — fresh CI verification (2026-10-02 Cairo)

> **SUPERSEDED 2026-10-02:** "Netlify remains the mirror" below is historical. Netlify was later
> removed as a host; Cloudflare Pages is now the only host.

## Verdict and exact scope

**BUG8 missing/ambiguous rendered date metadata: VERIFIED SHIPPED. Customer release: NOT APPROVED.**
The source projection now retains publication and saved observation, and both Lain templates expose them as escaped semantic UTC `time` elements. Offsetless/invalid publication stays unknown; only the SQLite fetched-date contract permits interpreting an offsetless saved observation as UTC. Regeneration does not refresh either clock. Public news remains excluded.

This is consumer verification, not proof that every possible ingestion input or every configured feed is correct. A separate, newly reproduced ingestion boundary defect (BUG10, below) remains open, as does per-feed health rendering (BUG9).

## Reviewed runtime and actual CI

- V1 reviewer `deleg_fb1e16f5` blocked the original snapshot: non-null `tzinfo` with `utcoffset() == None` allowed machine-local conversion. Parent reproduced both publication and observation cases RED; V1 was never approved.
- Third-context correction `deleg_4d244e79` changed only the reporter guard. Parent read the exact line and verified the complete renewed snapshot.
- Independent reviewer `deleg_c03fecf5` approved **6 files / 9 hunks / 25,145 UTF-8/LF bytes**, SHA256 `92f8a5b515f7fddb9cbc98e59a0bfb2416d286ddfb80bf7a0026bc98faf0c027`: no security concerns or logic errors. Optional non-UTC CI regression strengthening remains a suggestion, not a failed gate.
- Tested runtime **`d252865af1e2f7316d54e6fa73f6d479511298b2`** exactly matches that reviewed diff; remote main was read back after push.
- Parent local full suite: **831 passed / zero failures, errors, skips or xfails**, 47.24 seconds. The date file contains **31 cases**, including both new nil-offset regressions.
- Fresh manual CI **36942612716**: created **2026-10-01T23:46:58Z**, final success read back **2026-10-01T23:51:34Z** (October 2 in Cairo, UTC+3). Clean checkout/install/Chromium regression output: **829 passed / 2 setup-dependent skips / 74.85 seconds**. The corresponding complete local suite has no skips.
- Refresh, export, standalone preflight, both artifact uploads, Pages deploy/readback, publish/notify and eight-file state-cache save all independently read back successful. CI provider skip was observed; commands used no explicit AI-summary enable flag. No real tracker provider probe, paid inference, router edit or real summarizer request was introduced.

## Actual INTERNAL consumers, not regenerated fixtures

Both private files downloaded from this exact run contain **483 news rows**, **483 date metadata rows**, **885 UTC time elements**, **81 explicitly unknown publications**, and **zero unknown saved observations** each:

| Actual CI file | Bytes | SHA256 |
|---|---:|---|
| `eli-lain_20261001_234901.html` | 5,967,135 | `9183723fc0f9f2e1ef1138035c7a5856035f995d01466dcd06775c028448923d` |
| `eli-lain_20261001_235020.html` | 6,194,550 | `5807b307afbab8c57cd197313a948c59a658355c2ca3f098156a022fe987b14b` |

**56 actual-file Chromium checks / zero failures**, each file at 390px/1440px and JavaScript on/off, offline: all date labels/values preserved, first/last metadata reachable, honest unknown-publication counts, no horizontal overflow, no page/console errors and only the local file requested. All **483 shared stored story identities** keep identical publication/observation values between the two CLI outputs. QA keys literal `(url, title)`, matching the existing SQLite uniqueness contract; URL alone incorrectly rejects legitimate retained title revisions. That checker mistake was corrected without changing or deleting stored stories.

Storage-to-value mapping and regeneration/restart preservation were tested independently through actual isolated SQLite fixtures. **No CI database artifact was supplied**, so this is not an independent CI DB-value audit. Private HTML remains in private scratch and was neither publicly hosted nor copied into the sanitized durable publication proof.

## Actual public bytes and preserved identity

- Downloaded CI `index.html` and anonymous canonical Pages bytes are byte-for-byte identical: **3,478,348 bytes**, SHA256 **`2bcef3eb8eb447952f882861b85237e486577746c0baa4ffa841115395f7c09f`**. The production verification CLI returned `verified: true` again on the actual downloaded export.
- **102 actual-served-file offline Chromium checks / zero failures**, 390px/1440px, JS on/off. Shortlist first, native archive closed initially, filtering/reset/disclosures/focus/layout/standalone safety intact. News dates remain excluded from public HTML.
- **2,430 collected/exported inventory rows**: GitHub Trending 60; OpenRouter models 645; OpenRouter providers 112; Skills.sh 1,335; UnoRouter models 278. These are reconciled exported counts, not proof that every retained row/feed is freshly observed.
- All **1,335 literal Skills.sh identities** still match their full owner/repository/name links. No name-based merges, winner selection or deletion.
- **10 bounded shortlist cards**; current label **12 reviewed / 1,395 discovery candidates**. Official verification and installed integration evidence remain unestablished; no recommendation-depth acceptance inferred.
- Locked original style SHA256 **`347adbd0fc894df1675f565ca9d93d591a320ac2b63934b0d7615fa3554e76b8`** matches both actual internal reports, downloaded public file and served bytes. Both source template copies are identical; header and every source byte outside internal news remain unchanged against explicit baseline `18127ddc05dc5ee980ee212f4e87e5eef7ed1a46`.
- The earlier fixed-time same-saved-input comparison was byte-identical at 2,533,631 bytes. The fresh publication has different inputs/timestamps; do not mistake its different digest for a public date leak.

## Delivery and durable continuity

Pages was verified before notifications. Telegram exact `index.html` is **receipt-confirmed**; Discord attachment **independently-read-back**. These receipts bind this same public SHA256; they do not prove human opening or exactly-once delivery. Netlify remains the mirror; existing delivery/replay/locking/fsync limits remain open.

Durable private proof: **`C:/Projects/CODING/CODINGWITHMIRA/EliLain-Intel-Audits/hosted-36942612716/`**. All **19 payload files** were copied and hash-verified, plus a per-file manifest: sanitized CI/served HTML, safe status/export/reader/delivery/consumer/browser records, screenshots, QA tools and exact review receipt. No raw authenticated logs, signed download URLs, configuration, credentials, SQLite or raw internal HTML were copied. Only the sanitized `public/index.html` is a deliverable; never publish this audit tree. Complete frozen local review/RED/GREEN evidence remains separately under `news-dates-local-v2-92f8a5b5/`.

## Newly reproduced sibling — BUG10, not bundled into BUG8

`src/news_tracker/store_sqlite.py:108` still classifies naive observations by `tzinfo is None` only. An isolated synthetic test confirmed that `NewsItem` accepts a non-null timezone returning no offset: input wall time **2024-01-02 10:15** was silently stored as **2024-01-02 08:15 UTC** on this non-UTC machine, violating the naive-UTC observation contract before the corrected renderer ever sees it. Actual diagnostic exit **1**; temporary synthetic DB only, no production state touched. This is a confirmed rare accepted-input defect, **not evidence that the 483 actual CI stories are wrong**. It remains unfixed and requires its own formal RED, minimal storage correction, portable regression, full suite, exact review and fresh CI proof. Do not claim the whole date pipeline is bulletproof.

## Still open / parked

- BUG9 per-feed health/history/current-run outcomes are not exposed in actual internal HTML; maintain restart unknown-versus-current truth and no raw feed URLs/errors when fixing it.
- BUG10 ingestion ambiguity above gets a separate correction; no state/history rewrite or timestamp backfill.
- Source/feed reductions, owner-collision winners, credential rotation/scope and recommendation enrichment policy remain for Eli. No destructive selection, rotation or routing edits performed.
- Existing Git remote contains embedded authentication. Parent used a credential-free push destination and environment-only API authentication, emitted no credential and did not rewrite that configuration.
- Dependency/reproducibility/advisory/full-history and material-change/lost-response/concurrent-delivery acceptance remain open.
- A later documentation-only commit is not this tested runtime; verify their runtime trees match rather than claiming CI ran on the newer docs SHA.
