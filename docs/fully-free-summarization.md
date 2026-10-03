# Fully-free summarization: R13 research decision

Reviewed **October 3, 2026**. Scope: research and reproducible operator setup, not model installation, production acceptance, or release approval.

## Decision

**Adopt direct, operator-owned Ollama as the independent opt-in local pilot; defer default AI summaries and any universal free-hosted-inference promise.** Keep no-AI excerpts usable and optional BYOK separate. FreeLLMAPI and Hermes may remain personal conveniences, but neither is a public dependency. Reject unaudited proxy routers or access based on somebody else's keys.

Here, “free” means a permissively licensed local runtime/model without a mandatory inference subscription—not free electricity, hardware, maintenance, hosting, or unlimited capacity. Public customers must supply their own local runtime or private backend; a shared static dashboard must not contain credentials or expose our machine. There is **no evidence of universally free, sustainable public hosted inference** in this review.

## Evidence and its boundaries

- **Parent-reported live evidence, not repeated here:** installed Ollama tags included `minicpm5-2b-q8:latest`, `miraguard:latest`, `gemma4-e4b-unsloth:latest`, and `spark-x2.5-4b-external:latest`; no model was initially running. A direct loopback OpenAI-compatible completion using a saved arXiv paper **title** returned JSON with `finish_reason: stop` in **4.72 seconds**, with the database hash preserved. Its summary was only “A paper about DeepSeek-R1, an LLM model.” This supports route availability, not article-summary quality, a benchmark, or sustained throughput. The parent did not identify that completion's model in this evidence message.
- **Inspected local implementation:** `src/news_tracker/summarizer.py` calls a full chat-completions URL, validates a JSON array containing nonempty `summary` and `dedup_key`, and uses observed excerpts on failure. Its prompt uses titles and at most 200 characters of existing context—not full articles. The inspected request timeout is 30 seconds. `main.py` gates AI behind `--enable-ai-summary` and reads `SUMMARIZER_*` environment variables. These are code observations, not fresh consumer acceptance; other release work is changing these files concurrently.
- **Primary-source research:** official runtime documentation, publisher model cards/licenses, and provider documentation were fetched live. No model download or inference was performed by this document's author. API reachability, JSON validity, factual faithfulness, and long-running operational availability are different acceptance gates.

## Licensing and model selection

| Component | Reviewed evidence | Decision/limit |
|---|---|---|
| Ollama runtime | MIT license permits use/modification/distribution subject to preserving its notice; software is supplied without warranty.[22] | Suitable independent runtime. Its license does not license every model it loads. |
| Existing `minicpm5-2b-q8:latest` | OpenBMB's **MiniCPM5-2B** publisher card expressly licenses repository and weights under Apache-2.0 and links its license.[24][25] | First local candidate **if provenance matches**. The local alias alone does not establish its source, quantizer, modifications, or license. Record those before redistributing or declaring the installed artifact licensed. |
| Optional future candidate | **Qwen3-4B-Instruct-2507** is explicitly non-thinking; its publisher license is Apache-2.0.[3][23] | Research-only alternative if an already available, provenance-checked copy exists. Not installed according to the parent inventory; no download is proposed or authorized here. No measured quality advantage. |

Apache-2.0 redistribution has license, modification-notice, attribution, and applicable NOTICE obligations; it is not a warranty of output correctness.[25] MiniCPM's card separately warns of inaccurate/manipulable outputs and calls for safeguards and lawful use; review that disclaimer rather than treating a license label as a safety guarantee.[24] Do **not** select the MiraGuard security specialist as a generic summarizer. The other custom local tags were not license/provenance-reviewed here.

## Protocol, privacy, and runtime limits

- Direct tracker endpoint: `http://127.0.0.1:11434/v1/chat/completions`. An OpenAI **SDK** instead takes the base URL `http://127.0.0.1:11434/v1/`; the two configurations are not interchangeable. Ollama documents an ignored dummy SDK key, and its raw local HTTP example needs no real credential.[1]
- Supported chat fields include `model`, `messages`, `max_tokens`, `temperature`, `stream`, and `response_format`; thinking controls are model/version-dependent. Prefer nonstreaming responses for this consumer. Structured-output or thinking controls would need separate adapter verification; current inspected tracker code does not send them.[1] Native `/api/chat` has a different response contract and is not a drop-in endpoint for this adapter.[2]
- Ollama says local prompts/data are not seen by Ollama; **cloud models are a different route**. For strict local-only operation, disable cloud features with `OLLAMA_NO_CLOUD=1` in the serving process and restart deliberately. Keep the server bound to loopback; its documented default is `127.0.0.1:11434`.[2] Do not use a cloud tag, tunnel, broad CORS permission, or public bind as a shortcut. Local logs, caches, backups, and published summaries still need privacy controls.
- CPU execution/system RAM and GPU execution/VRAM are distinct resource paths; `ollama ps` reports placement.[2] Larger context consumes more memory; a model-card maximum is not proof of affordable context on this machine.[16] Bound input size, completion budget, batches, concurrency, and retries. Cold loads, reasoning output, competing workloads, and memory pressure can exhaust the tracker's timeout. No RAM/VRAM minimum, speed target, or energy estimate was measured here.

## Reproducible setup (instructions only; not executed here)

Use the existing Ollama installation and tracker environment. Commands below use **Bash/Git Bash**. Do not install, pull, or automatically substitute models.

1. Verify the running server and installed artifact, without inference. Tags expose model names/digests; model details expose license, parameters, and capabilities.[12][17][18]

   ```bash
   curl --fail --silent --show-error http://127.0.0.1:11434/api/version
   curl --fail --silent --show-error http://127.0.0.1:11434/api/tags
   curl --fail --silent --show-error http://127.0.0.1:11434/api/show \
     -H 'Content-Type: application/json' \
     -d '{"model":"minicpm5-2b-q8:latest"}'
   ```

   Record the Ollama version, exact tag/digest, quantization, source checkpoint revision, and licensing provenance. Metadata is helpful but not proof of ancestry. Stop if the model is absent or provenance cannot be resolved.

2. Check the existing server's cloud-disable and binding settings. Changes require the operator's approval and affect the **server process**, not merely a client's shell. Use the platform-specific FAQ instructions; do not start a second server on an occupied port.[2]

3. Configure the tracker process explicitly; these are session-only settings:

   ```bash
   export SUMMARIZER_PROVIDER='openai-compatible'
   export SUMMARIZER_API_URL='http://127.0.0.1:11434/v1/chat/completions'
   export SUMMARIZER_MODEL='minicpm5-2b-q8:latest'
   export SUMMARIZER_API_KEY='ollama'
   ```

   `ollama` is an **ignored local placeholder, not a secret**.[1] It satisfies the inspected CLI's nonempty-key validation; the local summarizer itself supports keyless loopback calls. Never reuse this placeholder for a remote service. No router, Hermes session, or private third-party key is required.

4. In a **separately authorized isolated consumer run**, use `python main.py run --enable-ai-summary` with the existing project environment. This command fetches sources, persists state, and may notify configured channels; it is **not** a harmless setup probe. The parent should control those side effects. Check real saved items through the consumer, not just curl: complete JSON batch, no truncation/refusal, facts supported by the provided text, preserved source URLs/dates, and clearly labelled fallback. Measure cold/warm latency, memory, and repeated-batch success without extrapolating one request. Omit `--enable-ai-summary` to retain no-AI operation; verify zero inference requests separately.

## Optional remote free-tier choices—not the sustainability plan

| Route | Compatibility and quota evidence | Privacy/cost limits |
|---|---|---|
| GroqCloud, user's own account/key | OpenAI-compatible base `https://api.groq.com/openai/v1`; full tracker endpoint `https://api.groq.com/openai/v1/chat/completions`.[9] Free-plan request/token limits are organization-scoped; check the authenticated Limits page and response headers, not a permanent hardcoded allowance.[7] | Remote processing. Groq documents default nonretention of inference content, exceptions for reliability/abuse and persistence features, retained usage metadata, and configurable zero-data-retention controls.[14] Review account controls; do not equate nonretention with local processing. |
| Gemini Developer API, user's own account/key | OpenAI-compatible full endpoint `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`.[10] Some models offer free input/output; others do not.[8] Limits vary by model/tier and apply per project, not per key; view active limits in AI Studio.[11] | Unpaid-service terms generally allow product improvement and human review; do not send confidential/personal data. EEA/Switzerland/UK and paid-service classifications have different data terms.[13] |

These are optional BYOK candidates, **not tested here**. Recheck model availability, account/region eligibility, terms, quota, and pricing before enabling either. Use a private backend and an explicitly free-eligible model; do not enable paid upgrades or paid-tool features automatically. Authentication, quota exhaustion, model retirement, and policy changes must fall back honestly to no-AI excerpts. Do not evade quotas with extra accounts/keys or silently route private input remotely.

## Review outcome and remaining gates

**Research decision: adopt the independent local architecture; defer quality acceptance and public free hosting.** Publisher licenses and documented local-only operation support continuity without a remote quota or private router dependency, provided the installed model's provenance is verified.[2][24][25] The parent's single completion supplies present-tense availability evidence—not longitudinal reliability.

Remaining: match the installed MiniCPM artifact to its upstream license; independently verify the parent consumer evidence; evaluate representative real title/excerpt batches for faithfulness, usefulness, malformed output, timeout and fallback; measure workload/resource bounds; verify no-AI zero-request behavior and sanitized public exports. Full-article summarization needs an explicitly reviewed input pipeline, not a stronger claim about the current title/excerpt prompt. This research does not close R11/R12 acceptance or approve release.

## Sources

[1] https://docs.ollama.com/api/openai-compatibility
[2] https://docs.ollama.com/faq
[3] https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
[7] https://console.groq.com/docs/rate-limits
[8] https://ai.google.dev/gemini-api/docs/pricing
[9] https://console.groq.com/docs/openai
[10] https://ai.google.dev/gemini-api/docs/openai
[11] https://ai.google.dev/gemini-api/docs/rate-limits
[12] https://docs.ollama.com/api/tags
[13] https://ai.google.dev/gemini-api/terms
[14] https://console.groq.com/docs/your-data
[16] https://docs.ollama.com/context-length
[17] https://docs.ollama.com/api-reference/show-model-details
[18] https://docs.ollama.com/api-reference/get-version
[22] https://raw.githubusercontent.com/ollama/ollama/main/LICENSE
[23] https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/main/LICENSE
[24] https://huggingface.co/openbmb/MiniCPM5-2B/raw/main/README.md
[25] https://raw.githubusercontent.com/OpenBMB/MiniCPM/main/LICENSE
