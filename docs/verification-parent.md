# Parent persistence/decision/workflow verification

Baseline (isolated Python 3.11 editable install): `27 passed, 3 warnings in 6.32s`. The warnings are existing deprecated Pydantic class Config; structural migration remains out of scope.

Strict vertical RED→GREEN commands run using `.venv/Scripts/python.exe -m pytest` with PYTHONPATH pointing to `src` and `src/tracker-core` while new editable packages are being introduced.

- Baseline inventory test: RED ModuleNotFoundError for nonexistent IntelStore; GREEN 1 passed after creating module. Observation timestamp is distinct from model launch time.
- Repeat/update test: RED baseline True on repeat; GREEN after persisted baseline and fingerprint comparison. Star counter changes do not manufacture new items.
- Failure preservation test: RED erased inventory (0 vs 1); GREEN after retaining cached rows and marking source failures stale.
- Period evidence merge test: RED duplicate rows (2 vs 1); GREEN merged evidence/project tags.
- Unobserved/corruption test: RED cached absent row falsely fresh; GREEN absent cache marked stale. Corrupt JSON raises and is not overwritten.
- Atomic replace test: RED no OSError (in-place overwrite); GREEN uses fsynced temporary file + os.replace, old snapshot survives a failed replacement.
- Stale key advice test: RED missing decision module; GREEN re-probe advice before credential replacement.
- Priority/alternative test: RED no fresh auth action; GREEN auth first, fresh alternatives only, registry reset schedules explicitly unverified.
- Provider change test: RED missing provider_changes; GREEN recovered/quota_exhausted changes only with current verified probes; first observation and stale verdicts cannot produce recovery claims.
- Workflow test: RED scheduled workflow never ran audit; GREEN actual audit invocation, cached intel/news history, explicit read-only permission.

Discovery accepts source coverage/failure evidence. Render-only operations read persisted checks without changing them. Parser/source tests and full CLI/browser/live verification are separate workstreams; not yet claimed complete here.
