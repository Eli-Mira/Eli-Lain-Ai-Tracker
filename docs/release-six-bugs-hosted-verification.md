# Hosted six-bug and Pages verification — run 36904275396

> **SUPERSEDED 2026-10-02:** the sentence below describing Netlify as a retained second copy is
> historical. Netlify was removed as a host (account out of deploy credits); Cloudflare
> Pages is now the only host. See `docs/RELEASE_ACCEPTANCE.md` for the current gate.

## Verdict

**Six repair implementations shipped; Pages end-to-end publication gate PASS. Customer release acceptance remains OPEN.** This is fresh hosted evidence, not the earlier local-only 792-test repair or historical `e756bfd` artifact.

- Reviewed runtime commit: `a8c24789ba065433c7dd7d9d5cba831edd61c90e`.
- Independent review `deleg_8571a6cf`: all **21 files / 36 hunks** approved with no introduced security or logic findings. Parent matched returned coverage/digest to the unchanged staged snapshot, SHA256 `d034d4cc7de09e15c2ba230356a4d0038907a009d83965b5a392167326cc0656`.
- The first review correctly failed closed because its input was truncated. It was replaced, not treated as approval.
- Manual workflow run **36904275396**, attempt 1, `workflow_dispatch` with `publish_pages=true`; created `2026-10-01T18:05:51Z`, completed successfully at `2026-10-01T18:09:51Z`.
- Checkout, dependency installation, Chromium installation, regressions, fresh news/discovery refresh, sanitized export, preflight, Pages deployment/readback, channel publication and state-cache save all reported success.
- Fresh clean-runner suite: **790 passed, 2 skipped in 44.98s**. Local parent suite: **792 passed in 41.65s**, zero skipped/failed. The two clean-runner setup-dependent tests reference the local original attachment and a pre-existing public export; those inputs are absent before the workflow export step. This is not a Chromium-launch failure. The actual new export was independently exercised after generation.

## Exact publication and consumer evidence

Downloaded public artifact `elain-public-36904275396` contains only `index.html`:

- **3,068,597 bytes**.
- SHA256 **`d2172e330e7f2cf2af345856adf05221812dd01bbca84fe9451566d578050104`**.
- Actual anonymous fixed-origin Pages readback matched the downloaded CI file **byte for byte**, not only provider deployment status.
- The production credential-free verifier independently returned `verified=true` for those bytes.
- Real Chromium against the **actual served bytes**: **46 checks, zero failures**, 390px and 1440px, JavaScript on/off, offline. Counts, visible search/source filtering, inert no-JS controls, error absence, self-request-only loading, CSP and overflow were checked. Browser execution did not change the file.

Reconciled discovery DOM:

| Source | Exported rows |
|---|---:|
| GitHub Trending | 60 |
| OpenRouter models | 642 |
| OpenRouter providers | 112 |
| Skills.sh | 1,011 |
| UnoRouter models | 274 |
| **Total** | **2,099** |

Actual visible public metadata now contains **1,011 detail-status fields**, **54 detail observation fields** and **54 detail body digests**. This is direct consumer evidence that vetted details survive projection; generic listing counts alone were not used to close the projection repair.

Safe CI publication receipt matched the same SHA256:

```json
{
  "attachment": "index.html",
  "delivered": true,
  "discord": "independently-read-back",
  "telegram": "receipt-confirmed",
  "url": "https://eli-lain-intel.pages.dev/",
  "sha256": "d2172e330e7f2cf2af345856adf05221812dd01bbca84fe9451566d578050104"
}
```

Telegram is a send-response attachment confirmation, not independent download/readback. Discord independently read back attachment metadata through the actual message consumer. Neither proves a person opened the file. Netlify remains the second copy; the publisher still executes its verified mirror path before using Pages in both briefs.

## Recurrence enabled only after verification

After the successful run, actual served-file comparison, browser QA and both attachment receipts, `CLOUDFLARE_PUBLISH_ENABLED` was changed to `true` and **read back from the exact GitHub variable**. Server `updated_at`: `2026-10-01T18:22:46Z`. Existing `PUBLISH_ENABLED` stays `true`.

The workflow schedule remains fixed **06:00 UTC**. This verifies the enabled configuration and manual consumer path; it is not a claim that a future scheduled invocation has already happened. Cloudflare credential values remain encrypted GitHub secrets and were consumed by the real action successfully. No token values were copied into this document or source.

## Safety and acceptance limits

- No real provider probe, paid inference, real summarizer request or router write was authorized/performed. Qualified route and optional summary CLI fixes are proved by simulated production-path tests in the shipped code; broader live provider/summary acceptance remains gated on Eli's explicit go.
- Summary default remains zero requests. Existing `OPENAI_API_KEY` alone does not activate it; explicit `--enable-ai-summary` plus all three settings is required.
- Same-name Skills.sh owner rows were not destructively deduplicated and no owner winners were selected.
- Pages access is verified from CI and Mira. Eli's phone access is not guaranteed by these checks; precise Netlify reachability cause remains unproven.
- Delivery semantic dedupe/ambiguous response behavior, receipt locking/fsync, advisory/history/lockfile evidence, broader source/usefulness and project-fit work remain separate open gates. **Release NOT approved; improvements remain deferred.**
- The token previously supplied in chat is exposed to that transcript; rotate it and replace the encrypted secret after this successful consumer verification. Rotation itself was not performed.

## Evidence retained

Scratch source artifacts/records: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/ci-36904275396/`:

- `public/index.html`, `served/index.html`: exact CI/actual served payloads.
- `verified-evidence.json`, `export-receipt.json`: safe log receipts and reconciled source counts.
- `served-readback.json`, `hosted-browser-qa.json`, `pages-gate-readback.json`.
- Internal reports retained privately: `eli-lain_20261001_180734.html`, `eli-lain_20261001_180850.html`; not included in public deployment.

Durable verified evidence copy: `C:/Projects/CODING/CODINGWITHMIRA/EliLain-Intel-Audits/hosted-36904275396/`.

Subsequent documentation-only commits record this result without changing the runtime tree tested at `a8c2478`; compare their changed paths rather than treating a documentation commit as untested new application code. No redundant manual publication is needed merely to record its own receipt.
