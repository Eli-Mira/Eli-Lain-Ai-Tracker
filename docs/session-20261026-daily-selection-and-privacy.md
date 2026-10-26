# Session 2026-10-26 — daily selection repair, layout repair landing, path-redaction completeness

Scoped record of this session's local changes on `fix/daily-selection-320px`
(based on `release/verified-e2e-20261015-0115` @ a857c5b). Local commits only;
nothing pushed, published, dispatched or delivered. All runs offline with saved
fixtures or mocked HTTP unless stated.

## 1. UnoRouter link verification GET fallback (M1)

Recorded evidence (`sanitized-release-20261015/live-postpublic-01`): all five
fresh free-tier UnoRouter candidates were excluded "link not verified" — HEAD
against `https://api.unorouter.com/api/pricing/catalog` answers 404 while the
same URL served the adapter's successful GET moments earlier in the same run.

Change: `verify_candidates` now falls back to one bounded GET (same guarded
transport, same SSRF/WAF/byte-cap/deadline checks) when HEAD answers 404/405.
WAF-flagged and 401/403 responses are never re-probed. A 200 GET verifies.

Tests: `tests/test_daily_verify_get_fallback.py` (8 cases) — fallback verifies,
405 covered, HEAD 200 does not GET, WAF never re-probed, dead link stays
unverified, GET failure stays unverified, plus a 5-qualified-selection
acceptance fixture with traceable exclusions (too old / dead link / duplicate /
below-threshold). min_score stays 60; `default_settings()` semantics unchanged.

## 2. Daily digest 320px/200% repair landed on the branch (M2)

The verified Linux layout repair (`linux-layout-repair-20261015-current01/repair.patch`
— mobile `.card{grid-column:auto}`, `main,footer{overflow-wrap:anywhere}`,
stale `#daily-digest`→`#main` skip-target expectation, 320px viewport cases,
element-level meta-bar/footer/grid assertion) existed only in audit copies and
was never committed. Applied byte-exact via `git apply` in this session.

Verified with real Chromium 1248 at 1440/390/320px × 100%/200% × JS on/off:
9/9 zoom + selector tests pass. The lain report route was measured at
320px/200% (representative + adversarial fixtures incl. escaped anchor markup
and long unbroken tokens): no document-level overflow on current bytes; no
template change made. The 320px limitation recorded in RELEASE_ACCEPTANCE.json
traces to the daily route pre-repair.

## 3. Path redaction completeness (M2 privacy)

Planting real content exposed a two-layer leak: `daily_digest._PATH_RE`
redacted only the drive prefix (`C:/Users/emadg/notes.md` →
`[PATH REDACTED]Users/emadg/notes.md`), and `daily_public._PATH_RE` was
`^`-anchored, so the remnant passed validation into the exported HTML.

Change: the sanitizer now redacts the whole path token (URLs intact, `s:/`
inside URLs still untouched); the export validator detects local paths anywhere
in a field (fail-closed, lookbehind keeps `https://` safe). Export re-check
with planted username/path/token: no leaks in exported HTML.

Tests: `tests/test_path_redaction_completeness.py` (12 cases).

## Owner-gated (unchanged, not decided here)

- GitHub/Skills calibration: fresh fully-verified records without verified
  license metadata score 51/49 < 60. Raising them is a scoring-product policy
  decision; left unchanged pending owner authorization.
- Live scans (`DAILY_RUN_ENABLED`), AI summarization, notifications,
  publication/dispatch: not exercised. All evidence is fixture/replay-based.
- Token scope/rotation, Git-history privacy remediation, Phase 0 acceptance:
  owner decisions, untouched.

## Environment note (no dependency changes)

The project venv's Playwright driver was missing `node.exe` (incomplete wheel
extraction); a Node ≥18 binary was copied from the system Playwright install to
repair it. No package versions changed; lockfile untouched. Browser tests use
`PLAYWRIGHT_EXECUTABLE_PATH` pointing at an existing local Chromium because the
managed `chromium-1243` download is absent on this machine.
