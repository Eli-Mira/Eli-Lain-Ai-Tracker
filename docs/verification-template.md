# Original-template extension verification

## Provenance and design lock

The design source is the user's untouched attachment:
`C:/Users/emadg/AppData/Local/hermes/attachments/report_template_lain.html`.
The `-2`, `-3`, `-4`, and `-5` variants were inspected by hashing; all five
are identical (6,129 bytes; SHA-256
`c6d506229ba422a1f28e5d505ab89b9e00b7fc53dfd47d8b3e7ed7373a820440`).
No attachment was modified.

The pre-extension repository Lain template was already a divergent v2:
720px width rather than the attachment's 640px, a shortened settle animation,
and a changed page title. The attachment's **entire original style block**
was restored, not redesigned. Its normalized UTF-8 style-block SHA-256 is
`347adbd0fc894df1675f565ca9d93d591a320ac2b63934b0d7615fa3554e76b8`.
The existing default theme style block remains unchanged; SHA-256
`658269321258ed6bd5230d489a3c75d0e5f76c19a1d1913b8df28548a4ad51e1`.
These hashes refer to text with LF line endings, including style tags.

Preserved Lain invariants:

- Background `#05070a`, cyan `#6fffe9`, original panel/text/border tokens.
- Original monospace stack and scanline pseudo-element, pointer-events disabled.
- 640px wrapper, mobile padding, 64px portrait/placeholder and header hierarchy.
- Original title, present-day prompt, h1 and full 900ms glitch-settle keyframes.
- Tracker section/list/item structure and original provider/news commands.
- Original footer's “close the world, open the next tab” text.

Additive rules live exclusively in a second `style#intel-extensions` block:
filters, evidence disclosure, safe line wrapping and hidden filtered rows.
The permitted extension adds changes/actions/source health ahead of inventory;
providers, tool/model discoveries, and news remain vertical tracker sections.
Explicit empty states do not collapse missing inventory into apparent success.
The constant Mira runner assertion was removed; this is a truthfulness change,
not a new brand/layout. The default header also uses the supplied runtime label.

The original attachment comment contains literal Jinja tag examples. Those
comments are preserved inside a `raw` block: HTML comments alone do not stop
Jinja parsing. The actual page does not silently fall back on syntax errors.

## Runtime paths and contracts

`HTMLReporter.TEMPLATE_DIR` resolves to **src/templates**, not the packaged
`src/tracker-core/templates` folder. Both named templates are byte-identical
between these locations. Tests enforce copy equality plus locked style hashes
without needing access to the personal attachment path in CI. A separate local
provenance test compares the attachment itself when it is available.

Existing positional render/save arguments remain compatible. New fields are
keyword-only and optional:

- `change_items`: headline, source, summary, url, change_type.
- `action_items`: title, priority, reason, action, url.
- `source_items`: name, status, checked_at, item_count, error, url, coverage.
- `baseline=False`: true displays first-run/no-comparison messaging; false with
  an empty change list displays no-material-change messaging.
- `runtime_source=None`: an explicit local/CI label; absent means
  “runtime not supplied”, never an invented machine name.

Tool rows retain headline/source/summary/url and optionally show id,
project_types (list of strings), evidence (list of dictionaries), freshness,
and change_type. Provider rows retain name/status/description and optionally
show actual_status, freshness, checked_at, probe_source and evidence.

Freshness is explicitly supplied `fresh`, `stale`, or `unverified`; absent or
unsupported values render unverified. Report generation time never replaces
checked_at and is labelled “report generation, not a probe timestamp”. Source
health describes collection coverage, not provider availability. The renderer
neither probes nor decides freshness; callers own the observation contract.

Evidence uses native, initially closed details/summary elements with
Jinja autoescaping. Discovery filtering is plain embedded JS: case-insensitive
text search and intersecting project-type/source filters, labels, live result
counts, visible zero-match state, and a no-JS static-content fallback. JS uses
textContent and option elements, not HTML insertion or external libraries.

All anchor and portrait URLs use one `safe_url` filter. Only absolute HTTP(S)
URLs with a host are active; relative URLs, javascript/data schemes, malformed
ports, embedded credentials, whitespace/control characters and backslashes
are rejected without repairing the input. Invalid links become inert label
text; invalid portrait URLs retain the placeholder. To use a portrait, supply
an owned image over HTTP(S), not a relative/data URL. This restriction is
intentional security hardening.

## Recorded vertical TDD execution

Each production slice was preceded by its own observed failure and implemented
before the next slice. Output below is from actual pytest runs, not illustrative
output. All commands used `.venv/Scripts/python.exe -m pytest`.

| Slice | Observed RED | Observed GREEN |
|---|---|---|
| Original locked Lain style/title | 1 failed: attachment style absent | 1 passed |
| Change-first render/save and baseline | 2 failed, 1 passed: unexpected change_items kwarg | 3 passed |
| Actions/source-health/runtime render/save | 2 failed, 3 passed: unexpected action_items kwarg | 5 passed |
| Provider/tool freshness and evidence | 2 failed, 5 passed: missing provider rows/metadata | 7 passed |
| Safe URLs and escaped untrusted fields | 22 failed, 9 passed: unsafe hrefs present | 31 passed |
| Real-browser intersecting filters | 4 failed, 31 passed: search label/control absent | 35 passed |
| Syntax-error transparency | 1 failed: TemplateSyntaxError did not propagate | 36 passed |
| Literal original edit-rule comments | 1 failed, 40 passed: original raw comment missing | 41 passed |

Additional no-drift/style-hash, legacy positional-call, empty-browser and
JavaScript-disabled checks verify existing behavior without additional
production changes. Final owned-test run: **43 passed, 3 warnings**.
The warnings are existing Pydantic class-based Config deprecations in schema.py,
which is outside this task's ownership. `git diff --check` passed.

Browser assertions exercised both themes at 390px and 1024px viewport widths:
filters intersect/reset, exact no-results state, untrusted option labels,
no executed malicious markup, evidence expansion, no JS page errors, and no
horizontal overflow. Computed Lain colors, portrait width, wrapper width,
scanline pointer behavior and animation duration were checked in Chromium.

Playwright's default Chromium download timed out. Tests were actually executed
using the installed Hermes Chromium binary via PLAYWRIGHT_EXECUTABLE_PATH,
not skipped or simulated. The test fixture accepts that environment override;
otherwise it uses Playwright's normal installed Chromium.

```bash
# Standard environment with Playwright and its Chromium already installed:
.venv/Scripts/python.exe -m pytest tests/test_intel_reporter.py -q

# Verified local Windows git-bash command (fresh isolated scratch basetemp):
PLAYWRIGHT_EXECUTABLE_PATH='C:/Users/emadg/AppData/Local/hermes/tools/chromium-1208/chrome-win64/chrome.exe' \
  .venv/Scripts/python.exe -m pytest tests/test_intel_reporter.py -q --tb=short \
  --basetemp C:/Users/emadg/AppData/Local/hermes/cache/scratch/intel-reporter-pytest

# HTML-only checks if a browser is intentionally unavailable:
.venv/Scripts/python.exe -m pytest tests/test_intel_reporter.py -q -k 'not browser'
```

Concurrent full-suite snapshots (other workstreams were still editing):

- Earlier: **162 passed, 1 failed, 3 warnings**, with
  `tests/test_intel_tools.py::test_skill_metadata_description_and_topics_are_read_only_bounded_and_explain_tags`
  failing on an empty summary. That failure was absent in the later run.
- Final snapshot: **184 passed, 1 failed, 3 warnings**, with
  `tests/test_provider_persistence.py::test_database_enabled_and_key_identity_win_in_both_load_orders`
  failing because load_from_db returned 2 rather than 3.

These tests and implementations are owned by other workstreams. No out-of-scope
files were changed to hide or fix them. Owned reporter tests passed in both
full-suite snapshots (41 earlier, 43 final). Final hashing also verified all five
original attachments remained unchanged.
