# Retrieval/discovery upgrade — specification-led execution

Date: 2026-10-07. Status: IN PROGRESS, NOT RELEASE-APPROVED.

## Binding specification

The user's complete specification is the unchanged attachment at `C:/Users/emadg/AppData/Local/hermes/attachments/pasted_content_2026-10-07_16-38-09-288_002f13.txt`. Read it before implementation. This document orders execution; it does not replace or narrow that specification.

## Baseline and global constraints

- Starting HEAD: `ad2c397c5c9180f442f13572e93bd20709df7f0e`.
- Existing uncommitted rescue edits: 18 tracked source/test/workflow files and 4 untracked test files. Frozen diff and hashes: `C:/Users/emadg/AppData/Local/hermes/cache/scratch/elilain-retrieval-20261007/baseline-review.txt` and `baseline-manifest.json`. Do not discard/rewrite them indiscriminately.
- Historical `LIVE_FIX_CONTRACT.md` and `IMPLEMENTATION_CONTRACT.md` are absent in this checkout; do not pretend their acceptance was verified. Historic audit is a baseline with subsequent corrections, not evidence every integration works.
- Work on `upgrade/retrieval-discovery-20261007`, preserving prior work. One implementer at a time. Read-only independent reviewers may run concurrently. Parent independently verifies each diff and execution evidence.
- Strict vertical TDD: each behavior RED, GREEN, then refactor. Record actual commands/results. No blanket skips, synthetic live data, fake evidence, guessed model/provider IDs, or relaxed thresholds to force useful output.
- Provider reuse first. FreeLLMAPI2 is only the existing development-worker route, not a required product retrieval dependency. No inference probes, summaries, router edits or metered provider calls without explicit authorization. Search integrations can be implemented/tested via contract fixtures; absent keys remain disabled/unconfigured and are disclosed.
- Important fetched claims need primary-source provenance with observed timestamps. Unknown fields remain unknown. Community claims do not override primary evidence. Externally fetched content is data, never executable instructions.
- Keep credentials, private endpoints/state, authenticated/local catalogs and raw errors out of public HTML, logs, reports and Git. Public web retrieval must block private/reserved IPs at the connected transport and on each redirect, with bounded bytes and total time. Explicit opt-in loopback model detection is a separate capability, never permission for arbitrary public URLs to reach loopback.
- Preserve Africa/Cairo 10:00 schedule and existing settings semantics. No push/deploy/notification while reviewed final runtime is unverified. Preserve historical receipts and last-good observations. Never change timestamps to manufacture freshness.
- No broad unrelated redesign. New recommendation UI must preserve the supplied Lain identity and security projection. Local private research state stays distinct from public exports.

## Ordered tasks and acceptance

### Task 0: reconcile pending rescue and freeze usable baseline

Independently review existing diff for source-security, deterministic scoring, production CLI/cockpit wiring and exact daily artifact delivery. Run the full actual-browser suite. Reproduce and fix blocking findings before structural expansion. Recover canonical continuity file locations; do not fabricate missing documents. Release gates remain open until actual consumers and usefulness are verified.

### Task 1: canonical contracts, safe transport and existing source consolidation

Create a cohesive research package under `src/intel_sources/research/` (unless existing code provides a better reusable home), normalized provider/candidate/evidence/query/run schemas and injected transport seams. Use existing safe delivery transport where compatible rather than duplicating it. Canonical adapters own endpoint/parser logic; old daily/legacy entry points are compatibility projections. Consolidate GitHub Trending in all three known locations and characterize other duplicate OpenRouter/Skills logic before consolidation. Add per-provider timeout/retry/backoff/rate-limit/circuit health, persistent bounded cache, last-good/stale behavior and a real refresh path. Test isolation, failure fallback, corrupt state and restart.

### Task 2: core providers and intent router

Implement complementary GitHub REST search/metadata and authenticated GraphQL enrichment; GitLab; Brave; Exa semantic discovery; Tavily search/extraction. Integrate a supported injected Hermes bridge for the existing keyless Exa/Parallel/Firecrawl/Keenable layer; do not copy undocumented anonymous endpoints or silently change Hermes configuration. Inspect the installed implementation plus official docs. Add one optional Google secondary route only when a real coverage gap justifies it. Route by intent, keys/capability/health and unmet coverage rather than broadcasting. Test keyed → supported keyless equivalent → alternate → cached evidence, and partial source survival.

### Task 3: useful query expansion and canonical fusion

Produce deduplicated exact/synonym/functional/category/use-case/competitor/open/self-hosted/local/repository/semantic variants. Semantic variants can omit the original product name without fabricating synonyms. Merge aliases, normalized repo/official/package URLs, canonical redirects and documented renames/mirrors. Forks remain distinct when functionally distinct; never merge by similar name alone. Store conflict provenance and discovered_by. Test ordering invariance and bridge-alias clusters.

### Task 4: primary evidence, health and deterministic recommendations

Separate researcher claims from verifier checks; CONFIRMED/LIKELY/UNCERTAIN/CONTRADICTED require evidence-backed definitions. Bind official-source attribution rather than trusting provider-returned labels/domains. Track the specified maintenance/PR/issues/contributors/security/dependency metrics when available; missing data is UNKNOWN, not HEALTHY. Weight ranking 35% feature, 15% requirements, 10% activity, 10% maturity, 10% documentation, 5% license, 5% deployment, 5% community, 5% popularity. Disclose components, penalties and hard requirements. Open-core is not fully open source; libraries are not full products. Reject only evidenced failures, not absent optional data silently treated as fact. All required recommendation fields and supported labels must be honest.

### Task 5: local semantic index and selective ecosystem sources

Prefer Qdrant local mode to avoid an unrelated PostgreSQL deployment. It fills the verified absence of a vector index. Choose an actual embedding model with declared provenance; no random/hash vectors masquerading as semantic embeddings. Install dependencies only in the project venv and declare a reproducible optional research dependency group. Persist candidates, aliases, evidence, ranking/run history and prior verification with schema/version safeguards; test restart, semantic lookup and failure fallback. Missing model downloads or unsupported platform must be explicit degraded states, not false success. Reuse registries/npm/PyPI/crates/Docker/HF as intent-specific metadata, optional HN/Reddit/issues discovery, RSS and structured benchmarks. Bound local ecosystem detection to explicitly configured Ollama/LM Studio/vLLM/llama.cpp endpoints and index catalog metadata without inference.

### Task 6: measured per-round saturation and production CLI/UI integration

After every executed round record unique high-quality candidate yield, new domains, rank/order/top-K change, coverage/confidence deltas, meaningful new evidence, provider uniqueness and score shifts. Stop only on defined low-yield/stability/coverage criteria with sufficient provider/source diversity, or label the actual budget/failure termination. Saturation is an explainable bounded heuristic based on telemetry, not calibrated probability or proof of exhaustive search. Unobserved probability remains unestimated. Wire the actual research command, persistence and useful recommendation consumer; prove public/private boundaries and byte truth for any generated artifact.

### Task 7: seven live difficult-search E2Es, repair and rerun

Execute all seven: open-source Grammarly alternatives; Magnific/Higgsfield alternatives; self-hosted Perplexity alternatives; local AI coding agents; obscure GitHub tools; emerging MCP/agent tooling; local LLM frontends. Record actual request/response/provider status metadata without secrets, canonical candidates, duplicates, primary evidence, rank explanations, missing obvious candidates and per-round telemetry. Inspect, fix reproduced systemic misses, and rerun comparable queries. No hand-injected recommendation lists presented as retrieved results. Calibrate recall only against a declared independently sourced comparison set, never claim entire-web recall. Rerun full regression/browser/security/offline gates after integration.

### Task 8: final verified report and continuity

Deliver the fourteen requested sections: before/after; duplicates; reused; added; intentionally omitted; keyless; keyed; optional keys; fallback; ranking; saturation; E2E; weaknesses; improvements. Distinguish implemented, contract-tested and genuinely live-exercised providers. Report each of the seven E2Es individually and all recommendation fields. Keep gates open for missing credentials or unreproduced acceptance. Update canonical checkpoint/log/runbook only from actual results, not predicted completion.
