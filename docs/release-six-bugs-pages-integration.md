# Six-bug repair and Pages integration — October 1, 2026

## Status and scope

**LOCAL REGRESSION PASS; independent pre-commit review and fresh hosted acceptance OPEN.** These changes are staged but not committed, pushed or deployed. The read-only GitHub check at `2026-10-01T17:41:04.379705+00:00` still found remote `main` at `f59b8c3cc2dc05cbc5afefbf5c92b75d8521e330`, `CLOUDFLARE_PUBLISH_ENABLED=false`, and the existing `PUBLISH_ENABLED=true`.

No live provider probe, real summarizer request, paid inference, router mutation, owner-winner selection or destructive Skills.sh dedupe was performed. All production-path request tests use simulated HTTP transports and synthetic credentials. The independent reviewer is `deleg_1d830f47`; a frozen 17-file diff is under Hermes scratch. Its verdict is pending, not assumed.

## Repairs independently exercised by the parent

| Defect | Current local behavior | Evidence |
|---|---|---|
| BUG1 detail projection | `www.skills.sh` is allowed only for matching detail identity; listing-host policy stays unchanged. | 39 detail/URL regression cases, included in the parent full suite. |
| BUG2 dedup crash | Both indexes contain only retained rows; URL and fuzzy-title replacements release removed identities. | Worker RED reproduction plus parent production `main.run()` reproduction against original source: `ValueError: list.remove(x): x not in list`. Current run persists three winners from four fixture inputs. |
| BUG3 publication boundary | Reuses standalone export checks, scans private-content/credential shapes, checks CSP/referrer, bounds reads and rejects symlinks/reparse targets. | Unsafe-file RED cases and successful preflight on the newly regenerated real saved-state artifact. CRLF is normalized only in the validation copy, not the shipped bytes. |
| BUG4 standalone CLI cap | Omitted cap exports the complete validated inventory. Explicit caps still work and disclose omissions. | Actual subprocess CLI tests: 137 rows by default; caller caps 17 and 100. |
| BUG5 CLI provider pins | `NewsTracker.probe_providers()` passes `bound_model_routes=load_probe_catalog(qualified=True)`. | Production-path test posts exact `groq:vendor/member-original`, not the generic HTTP catalog group slug, verifies matching routed identity and unchanged fixture DB bytes. Focused provider suite: 54 passed. |
| BUG6 optional summary wiring | CLI passes configured model/key/endpoint only with `--enable-ai-summary`; default ignores populated summary environment and makes zero requests. | Simulated API production run plus missing-setting/unsafe-URL tests. Focused summary suite: 18 passed. |

The parent integration harness initially treated SQLite result dictionaries as objects. That harness error was corrected to the actual dictionary interface; production storage was not changed to satisfy the test.

## Optional configuration — NOT enabled by this repair

Default scheduled/local runs remain unconfigured and make zero summarizer requests. `OPENAI_API_KEY` alone does not enable summaries. Only after Eli explicitly approves a real call, set all of:

```dotenv
SUMMARIZER_API_KEY=<keep in environment, never commit a real value>
SUMMARIZER_MODEL=<explicit model identifier>
SUMMARIZER_API_URL=<full chat-completions endpoint>
```

Then the explicit local opt-in is `python main.py run --enable-ai-summary`. This command was **not** executed with real credentials. HTTPS is required except HTTP on localhost/127.0.0.1/::1. Credential-bearing, query/fragment, invalid-port and whitespace URLs are rejected without echoing their values. Incomplete opt-in fails before creating tracker state or sending requests. Model and API URL have no implicit vendor/free-tier defaults; no billing entitlement is inferred.

## Caller-selected public cap

```bash
# Complete validated saved inventory, not a fresh source fetch:
python scripts/export_public_report.py

# Explicitly bounded by the caller; omissions are disclosed in coverage:
python scripts/export_public_report.py --max-items-per-source 100
```

Public validation may exclude unsafe rows or duplicate full identities; the complete-inventory default does not authorize publishing private records or merging different owners with the same name.

## Combined parent execution

```bash
NOTIFICATION_CHANNEL=none PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' .venv/Scripts/python.exe -m pytest tests -q --basetemp=C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-six-bugs-confirmed --junitxml=C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-six-bugs-confirmed.xml
```

Actual result: **792 passed in 41.65s**, exit 0. Staged `git diff --check` passed; added-line static scan found no matches for hardcoded credentials, shell injection, dynamic execution, unsafe deserialization or interpolated SQL. This bounded scan is not a dependency advisory/history audit or an independent review verdict.

## Real local artifact, NOT new hosted evidence

The parent ran the standalone CLI against actual saved `data/intel_state.json` / read-only news inputs into a dedicated scratch directory, then exercised the strengthened preflight:

- Artifact: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-six-bugs-public/index.html`.
- Bytes: **2,532,143**.
- SHA256: `02fea909be2bb748d0b60864b885349a2ba364a0426630258a4fe99868b883dc`.
- DOM counts match the CLI receipt: GitHub Trending 60; OpenRouter models 638; providers 112; Skills.sh 617; UnoRouter models 246; **1,673 total**.
- Real Chromium on these exact bytes: **46 checks, zero failures**, 390px/1440px, JavaScript on/off, offline. Counts/search/source filter, no-JS inert controls, no overflow, no errors, only the self-request and CSP were checked. File bytes remained unchanged.
- QA: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-six-bugs-browser-qa.json`; receipt: `elilain-six-bugs-export-receipt.json`; reusable QA harness: `elilain_artifact_browser_qa.py`.

This is saved-state regeneration, not fresh observations, not a deployment, and not a channel send. Its source counts differ from the historical CI snapshot because the saved inputs differ; no owner rows were deleted.

## Gates still open

1. Resolve independent reviewer findings before committing or pushing.
2. Exercise the manual Pages input on the reviewed commit; verify CI's actual artifact SHA, fixed-origin hosted readback and both attachment receipts.
3. Enable daily Pages recurrence only after that end-to-end evidence passes.
4. Keep provider live-probe and real summarizer validation explicitly blocked on Eli's authorization. A hosted run deliberately skips local probes and does not opt into summaries.
5. Security/dependencies, broader source/usefulness, delivery ambiguity/locking and semantic dedupe remain separate acceptance work. **Release NOT approved.** Improvements remain deferred.

Historical attachment and hosted proof remains in `release-hosted-artifact-verification.md` and `RELEASE_ACCEPTANCE.md`; do not substitute this local regeneration for it.
