# Customer release delivery audit

## Current status — supersedes the historical snapshot below

**Release NOT approved.** The text-only implementation described below is historical, pinned to run `36810623236` / commit `0ce25843`. Subsequent verified hosted runs `36856918737` and `36860505208` attached exact `index.html` bytes to Telegram and Discord; Discord independently read back its attachment. See `release-hosted-artifact-verification.md` and the dated evidence in `RELEASE_ACCEPTANCE.md`.

On October 1, independent complete-snapshot review `deleg_8571a6cf` passed; reviewed runtime `a8c2478` was pushed and manual CI **36904275396** succeeded. Actual Pages bytes are identical to the downloaded public artifact: **3,068,597 bytes**, SHA256 `d2172e330e7f2cf2af345856adf05221812dd01bbca84fe9451566d578050104`, **2,099 rows**. Both new HTML attachments are confirmed (Telegram receipt; Discord independent readback), and **46 real Chromium checks / zero failures** passed on the actual served bytes. Full local suite: **792 passed**; clean-runner suite: **790 passed / 2 setup-dependent skips**. Daily Pages was enabled only after these checks and read back `true`; Netlify is retained as the mirror. The earlier truncated-input review was replaced, never treated as approval. Fresh evidence: `release-six-bugs-hosted-verification.md`. Broad release/delivery guarantees remain OPEN.

Every implementation/remote-state statement below describes the historical audited commit, not the current implementation or newest hosted run.

## Historical audit verdict

**NOT customer-release accepted.** The most recent completed remote workflow successfully published a sanitized standalone HTML object and posted **text + a link** to both channels. It did **not** attach the HTML file to Telegram or Discord. Green CI here proves the implemented plumbing, not the requested file delivery, content usefulness, or end-user consumption.

Scope: read-only GitHub/Netlify inspection, captured CI artifact, local offline protocol/security tests. No send, deploy, workflow trigger, push, commit, login change, or production/workflow edit was performed by this audit. Only this document and `tests/test_release_delivery_audit.py` are owned by the audit. Other workers are changing the worktree; remote acceptance evidence below is pinned to the exact remote SHA, not their uncommitted edits.

## Current remote evidence

Last remote check: **2026-10-01T04:58:39.216774+00:00**.

| Field | Observed value |
|---|---|
| Latest run | `36810623236`, attempt `1` |
| Workflow | `EliLain — Daily Intel Audit` |
| Event | `workflow_dispatch` |
| Commit | `0ce25843c96eadc3eb58fad8936c7f63ae245439` |
| Created / updated | `2026-10-01T03:27:55Z` / `2026-10-01T03:30:21Z` |
| Run / job | `completed` / `success` |
| Regression step | CI log: `431 passed, 2 skipped` |
| Publish step | success, `03:30:12Z`–`03:30:17Z` |
| Publish output | `delivered: true`; Telegram `receipt-confirmed`; Discord `independently-read-back` |
| Public artifact | `elain-public-36810623236`, artifact ID `11139712152`, not expired |
| Internal reports artifact | `elain-report-36810623236`, artifact ID `11139448458`, not expired |
| Gate | repository variable `PUBLISH_ENABLED` is `true` |

Run URL: `https://github.com/Eli-Mira/Eli-Lain-Ai-Tracker/actions/runs/36810623236`.

The GitHub artifact digest refers to its ZIP container, **not** the HTML bytes. Downloaded artifact `index.html` has:

- Size: **532,948 bytes**.
- SHA-256: `1ade55b416cbcd1341a0b9fe2da242f564e6853d79661f5121a62dea765f204d`.
- SHA-1: `1c24444c9c85a9fcfb3bfa8f93abb73b0b371cea`.
- Render time from its footer: `2026-10-01T03:30:10.249517+00:00` (regeneration of saved observations, not a new probe).
- Discovery DOM rows, counted programmatically: GitHub Trending `49`; OpenRouter models `100`; OpenRouter providers `100`; Skills.sh `100`; UnoRouter models `100` (449 total).
- No automatic remote/active dependency elements from the audited selector set; no match for the credential/local-host/path canary patterns scanned. These bounded checks are not a complete secret scanner.
- Exact downloaded standalone file retained at `C:/Users/emadg/AppData/Local/hermes/cache/scratch/release-delivery-audit/public/index.html`.

The CI export JSON and publish JSON both report the same SHA-256 as the downloaded file. `report_delivery._Session.host()` compares the actual anonymous canonical HTTP response bytes to that SHA-256 **before** notifying. This is evidence that the exact response matched **during that run**; the reported channel success is not merely a skipped opt-in step.

### Netlify independent metadata read

Existing CLI credential permitted GET `/sites` and GET deploy file listing. The actual target is site ID **`979350fc-66cc-4965-9654-153969fd2be6`**, not the test fixture site's ID.

- Canonical site: `https://eli-lain-intel.netlify.app`.
- `sso_login: false`, `account_sso_login: false`.
- Published deploy: **`6abdd3c5187088abb602fa78`**, `ready`.
- Created: `2026-10-01T03:30:13.869Z`; published: `2026-10-01T03:30:15.480Z`.
- GET `/deploys/6abdd3c5187088abb602fa78/files`: exactly one object, `/index.html`, MIME `text/html`, size `532948`, SHA-1 exactly equal to the downloaded HTML.

**Current anonymous external exact-byte readback could not be independently repeated from this host.** Direct httpx and environment-aware httpx timed out; urllib failed with `URLError`; curl returned timeout exit `28`, including attempts pinned separately to both DNS answers (`63.176.8.218`, `35.157.26.135`). Browser verification also timed out. The configured extract backend cannot extract URLs. These are local reachability/tool blockers, not evidence that Netlify is serving an incorrect file. Do not relabel the metadata check or CI's historical readback as a successful current browser readback.

An initial Netlify site GET used the test fixture site ID and returned `404`; listing sites resolved the real target above. No site setting was changed.

## Exact bytes and template chain

At the audited remote commit, `.github/workflows/news-tracker-daily.yml` runs:

1. `python main.py today --theme lain`: fetch/process/store news; can emit breaking text through the **legacy** notifier; creates internal report HTML.
2. `python main.py audit --theme lain`: restores provider state, skips local probes in CI, refreshes discovery, creates internal provider/news/tools HTML. No provider-change replay when probes were skipped.
3. `python main.py export-public --public-dir ./public`: `public_report.export_public_report()` reads saved state and read-only news input, projects only authorized public discovery families, explicitly excludes provider statuses/actions/changes/news, renders with `LainReporter`, adds CSP/referrer protections, atomically writes **`public/index.html`**.
4. Artifact upload stores `reports/*.html` separately from `public/index.html`; neither upload delivers a file to chat consumers.
5. `python main.py publish --public-dir ./public --no-export`: `load_artifact()` snapshots the existing `index.html` bytes, derives SHA-1/SHA-256, deploys only `/index.html`, polls matching deploy/site IDs, anonymously GETs canonical `ssl_url` with no redirect following and a `no-cache` header, hashes response bytes, then builds a brief and calls both channels.

The consumed template is **`src/templates/report_template_lain.html`**, through `tracker_core.reporter_html.HTMLReporter.TEMPLATE_DIR`; it is **not** the original attachment and not the duplicate `src/tracker-core/templates/` copy. Runtime template filename was verified locally and pinned remote reporter/template content was fetched separately.

- Remote consumed template raw SHA-256: `5f6ba48625b94eb9596e86d98b0e3daf57880aa31fa5aec18d08cce54d216f47`.
- Original attachment: `C:/Users/emadg/AppData/Local/hermes/attachments/report_template_lain.html`.
- Original attachment SHA-256: `c6d506229ba422a1f28e5d505ab89b9e00b7fc53dfd47d8b3e7ed7373a820440`.
- Original locked `<style>` block was found intact in the locally consumed extended template. This is **style preservation**, not byte-for-byte preservation of the whole original template.
- The remote workflow equals the original local workflow after newline normalization. Current local renderer/template/storage may differ because of parallel release work; do not substitute those files for the captured CI artifact.

## Notification consumer and attachment verdict

`src/intel_sources/report_delivery.py`:

- Telegram: POST `sendMessage`, JSON `chat_id`, `text`, disabled link previews. Checks `ok`, positive message ID, exact chat and exact returned text. There is **no `sendDocument`, multipart upload, file ID, filename, file bytes, or attachment receipt**. Its result is an official send receipt, not independent readback or proof a person viewed/downloaded the report.
- Discord: POST channel `/messages`, JSON `content` and empty allowed-mentions policy. GETs that exact returned message ID and checks channel/text. There is **no multipart file upload or attachment verification**. Readback confirms message content exists, not a user's consumption of the URL.
- The brief includes render/observation times, source counts, caveats, and the hosted link. It does not embed the full report.
- Legacy `TelegramNotifier` and `DiscordNotifier` also only send truncated text; `FileNotifier` saves Markdown, not HTML.

The actual CI publish entry point prints only confirmation labels, URL and hash; **message IDs and partial channel receipts are lost** in `main.py` output. `scripts/publish_report.py --json` has richer receipts, but the workflow does not call it. The existing Telegram/Discord encrypted secrets cannot be read through the GitHub secrets API. No local channel credential was available, so an independent current Discord GET or Telegram consumer inspection was not authorized by an available credential. No live channel request was attempted.

## Auth inventory (names/availability only)

- `gh auth status`: **not authenticated**.
- Existing Git HTTPS helper: credential fields `host`, `protocol`, `username`, `password` available; successful private GitHub API reads. Password was captured only in process memory and passed as **child-process `GH_TOKEN` environment**, never argv, printed output, or a plaintext credential file. No login was changed and no interactive prompt was requested.
- At initial inventory, none of `GH_TOKEN`, `GITHUB_TOKEN`, `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` were populated in the audit process environment.
- Existing Netlify CLI `auth.token`: available; read-only API access verified.
- Repository encrypted secret names: `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`, `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`, `NOTIFICATION_CHANNEL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Existence is not proof of validity; values cannot be decrypted through the metadata API.
- Repository variable names: `ELILAIN_AI_TRACKING_AUTOMATION`, `PUBLISH_ENABLED`. The former currently contains only the nonempty field name `NOTIFICATION_CHANNEL`; audited credential-shape patterns did **not** match its value. Historical plaintext credential exposure is not asserted to remain present now.
- Local Hermes dotenv credential/config names observed: `FREELLMAPI_API_KEY`, `GLM_API_KEY`, `HERMES_CUSTOM_1_API_KEY`, `HF_TOKEN`, `NOTION_API_KEY`, `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`. None supplies Telegram/Discord delivery credentials; values were not printed or loaded for this audit.

## Required fixes for the parent (no production changes here)

| ID | Severity | Root cause / required fix |
|---|---|---|
| DEL-01 | Release blocker | Implement real standalone **HTML file attachment on both selected channels**, using the already verified `ReportArtifact.data`, stable safe filename, bounded multipart upload, and explicit attachment receipts/readback. Require text **and file** success; a link is not the file deliverable. |
| DEL-02 | High | `deliver_report()` has no durable per-artifact/per-channel send ledger. A rerun after one channel fails duplicates the channel that succeeded. Persist pending/confirmed/uncertain receipts keyed by report content identity and channel; do not blindly retry an uncertain POST. Rendering a new timestamp changes bytes, so define a saved-observation/content identity as well as byte hash. |
| DEL-03 | High | `--no-export` trusts a footer marker and source attributes; it accepts appended active dependencies/private payloads. Revalidate standalone restrictions, source-bound identities, CSP, excluded sections/free text, and directory ancestors at publication. Reuse/strengthen a single fail-closed boundary rather than treating an HTML footer as an attestation. |
| DEL-04 | Medium | `load_artifact()` reads unbounded input before parsing/uploading. Bound regular-file size/read to `MAX_HTML_BYTES` and reject malformed UTF-8/HTML with safe codes before any side effects. The existing response limit is too late to bound upload input. |
| DEL-05 | High security | Legacy notifier logs exception messages and response bodies; httpx exceptions can embed the Telegram token URL. Replace all raw messages/body logging in notifier and calling exception paths with class/status/channel safe codes; suppress secret-bearing HTTP wire logs on that path too. |
| DEL-06 | High truth | Legacy `MultiNotifier` returns success if **any** channel succeeds; Telegram trusts HTTP 200 without checking `ok`, destination/text/message ID; Discord trusts status without message readback and permits mentions. Use explicit per-channel receipts, all-required success, safe text, disabled mentions, bounded sends and validated API results. |
| DEL-07 | High duplicates/truth | News DB dedup is not delivery dedup: `run()` splits and sends all processed high-score items even when `save_items()` inserts zero. Persist per-item/per-channel breaking delivery receipts; retry only appropriate unconfirmed work. `run()` ignores the boolean breaking-send result and does not fail/record delivery failure. It claims all breaking rows pushed while formatting only five. Fix reporting counts and propagate incomplete required delivery. |
| DEL-08 | Medium state | Cache includes five state paths but omits `data/feed_health.json`; per-feed cooldowns reset on runners. Include that state and the delivery ledger. Make cache persistence independent of an unrelated later notification failure. Keep serialized workflow concurrency. |
| DEL-09 | High security under DEBUG | `_quiet_http_logs()` disables parent `httpcore`, but Python descendant loggers can still propagate wire records past a disabled parent. Explicitly suppress/filter the secret-bearing logger hierarchy during requests, restore prior settings, and test an actual `httpcore.http11` record. Avoid changing process-global logging without concurrency protection. |

Additional required hardening/acceptance details:

- The pinned transport orders all validated addresses but only tries `ordered[0]`; its docstring's IPv6 "fallbacks" are **not implemented**. On connect failure, try other validated addresses only when safe to determine no request was sent; never replay ambiguous side-effecting POSTs. Existing deterministic tests only prove ordering.
- Canonical `ssl_url` is restricted to the `.netlify.app` suffix, but not explicitly bound to the site GET's canonical origin/published deployment. Validate exact origin, reject userinfo/query/fragment/unsafe paths, and confirm `published_deploy.id` when claiming this exact deploy is canonical. Exact HTML hashing is strong content proof but not itself deploy-origin binding.
- `main.py publish` should persist/print safe message IDs, per-channel receipts and attachment hashes on both success and partial failure. Current receipt information is insufficient to safely resume or independently recheck the exact consumer message.
- `today`'s legacy breaking sends occur **before** export/hosting/readback; enabling public publish does not suppress them. This means multiple notification categories per successful run, and repeated news on reruns, not two calls to `run()` inside `today` + `audit`. Choose one explicit release notification policy and distinguish genuine breaking updates from the report brief; validate all required sends consistently.
- At the pinned remote commit `SQLiteStore.save_items()` uses `conn.total_changes` for the insert counter. It can inflate "new" counts for duplicate rows. The parallel storage worker has already changed the local code to `cursor.rowcount`; that is not deployed remote evidence yet.
- Cache evidence is real: latest run restored `intel-state-Linux-36807623963-1` and saved `intel-state-Linux-36810623236-1`. Files restored: `intel_state.json`, `provider_changes.json`, `provider_state.json`, `news.db`, `health.json`. SQLite uses WAL; current successful CLI process exit normally closes/checkpoints before cache post-processing. **No WAL data loss was established in this audit**. Still explicitly checkpoint/close before snapshot and test cancellation/failure recovery; copying only an open live WAL database is unsafe.
- Public HTML intentionally excludes news/provider conclusions and uses generic metadata caveats. Do not call successful attachment delivery evidence that the customer's useful-provider/news/project acceptance criteria were met; those require separate content evaluation.

## Tests and reproduction

All new tests are offline. They reuse the realistic existing MockTransport protocol, invoke the real delivery/notifier/news methods, isolate SQLite in temporary directories, and never send/deploy. Strict xfails record unfixed customer/security acceptance gaps; **xfail is not acceptance**. Remove each marker after fixing the underlying behavior.

Initial existing gate: `NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest tests/test_report_delivery.py -q` -> **22 passed**.

Combined gate:

```bash
NOTIFICATION_CHANNEL=none .venv/Scripts/python.exe -m pytest \
  tests/test_report_delivery.py tests/test_release_delivery_audit.py -q -rx \
  --basetemp C:/Users/emadg/AppData/Local/hermes/cache/scratch/pytest-release-delivery-audit
```

Final combined result: **31 passed, 9 xfailed in 1.64s**, exit `0`. The nine strict expected failures are unresolved acceptance defects, not successful acceptance. `git diff --check` for the owned paths also passed. The new tests add current text-only consumer characterization, host HTTP-failure guards (401/403/429/500/503), partial Telegram failure with surviving Discord confirmation, logging-flag restoration after an exception, exact runtime template resolution, and strict expected failures for DEL-01 through DEL-09.

An early new-test failure was a **test stub defect**: the reused protocol learned the shared brief only from a successful Telegram response. The failure override now records the attempted text before returning 429, allowing the real Discord path to be tested. Production was not modified to accommodate the stub.
