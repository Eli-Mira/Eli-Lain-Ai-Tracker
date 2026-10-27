# INTEL V3 checklist — source expansion to internal RC

States: TODO / IN_PROGRESS / PASS / FAIL / BLOCKED / DEFERRED. PASS needs verified bytes, command+exit code, test counts, provenance, no unauthorized side effects, local commit where available.

| ID | Task | Deps | State |
|---|---|---|---|
| M3.1 | Per-candidate exclusion codes in private evidence; frozen-now determinism | - | IN_PROGRESS |
| M3.2 | UnoRouter GET-vs-HEAD reuse (fetch-time GET evidence, no duplicate call) | - | IN_PROGRESS (fallback landed a41e3fb) |
| M3.3 | License evidence states (none-declared vs lookup-failure vs verified); policy untouched | - | IN_PROGRESS |
| M4 | Source registry module + schema tests + registry doc, disabled-by-default | M3 | TODO |
| M5 | Offline fixture adapters: vendor RSS, GitHub releases, Replace.so reference, research/HF | M4 | TODO |
| M6 | Evidence module: canonical URL/entity, corroboration grouping, novelty vs baseline | M4 | TODO |
| M7 | Report sections + honest quiet states verified on current bytes | M6 | TODO |
| M8 | Security negative fixtures for new code paths | M5 | TODO |
| M9 | Focused suites + full regression on final bytes | M8 | TODO |
| M10 | Internal RC pack: registry, demo, status, owner decision sheet | M9 | TODO |

Prior landed (V2 session, 2026-10-26): a41e3fb GET-fallback verification, ab44585 320px daily layout repair, b5aae30 path-redaction completeness. Full suite at b5aae30: 1493P/6S/0F, exit 0 (Windows).
