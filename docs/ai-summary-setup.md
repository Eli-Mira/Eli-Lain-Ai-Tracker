# Optional private AI summaries

The tracker works without an inference service or API subscription. AI summarization is **off by default**: omit `--enable-ai-summary` to make zero summarizer requests, even if all summary environment variables (or `OPENAI_API_KEY`) are populated. News collection itself can still make its ordinary source requests. No AI keys belong in the shared dashboard, browser JavaScript, public repository, HTML, deployment artifact, or public logs.

This is a private backend feature, not a shared multi-user inference server. The public export currently excludes news summaries; enabling the backend does not authorize exporting internal news/provider state or credentials. Review any future public news projection separately.

## Configuration contract

Set environment variables in the backend process, then explicitly run `python main.py run --enable-ai-summary`. There is no automatic dotenv loader in this CLI; a private env file is useful only if your own launcher safely loads it. Never source an untrusted env file. Do not put a key on the command line or print it.

| Variable | Supported value / behavior |
| --- | --- |
| `SUMMARIZER_PROVIDER` | Exactly `openai-compatible`, `openai`, or `anthropic`. Unset means `openai-compatible` for existing setups. Case changes, surrounding whitespace, and aliases such as `claude` are rejected. |
| `SUMMARIZER_MODEL` | Required for CLI opt-in. The provider's exact API model identifier, 1–256 printable ASCII characters without whitespace. No automatic model lookup or substitution. |
| `SUMMARIZER_API_URL` | Required for CLI opt-in. A **complete request endpoint**, not just a base origin. HTTPS outside loopback; HTTP is allowed only on `localhost`, `127.0.0.1`, or `[::1]`. |
| `SUMMARIZER_API_KEY` | A private API credential, not a consumer subscription/session token. Required for `openai` and `anthropic`, including on loopback, and for remote `openai-compatible`. Unset or empty is allowed only for loopback `openai-compatible`. Nonempty keys must be printable ASCII without whitespace, at most 4096 characters. |

Settings are validated before the CLI creates tracker state. No value is silently trimmed, repaired, or printed. URLs must have a lowercase scheme/authority, a conventional literal hostname/address, and a complete slash-prefixed ASCII path. Credentials in URLs, queries/fragments (even empty `?`/`#`), percent escapes, backslashes, whitespace/control characters, dot path segments, empty/noncanonical/out-of-range ports, unspecified addresses (`0.0.0.0`, `[::]`), and ambiguous numeric addresses are rejected. This intentionally narrow contract does not support signed query-string endpoints.

Only the three named loopback hosts qualify for keyless inference; a DNS hostname that happens to resolve locally does not. Configure only an endpoint you control or trust. HTTPS validation is not a provider-identity allowlist, a DNS pin, or a general-purpose SSRF defense: do not expose these backend settings to untrusted visitors. A caller-selected compatible router can still forward to paid remote services, even when its listening address is loopback.

### Request protocols

- `openai-compatible`: POST to the exact endpoint with `model`, one user `messages` entry, and `max_tokens`. A configured key is sent only as `Authorization: Bearer …`; no auth header is sent for keyless loopback. Ordinary models get temperature `0.3`; models matching the existing reasoning-name hints omit temperature and use a larger token ceiling. This supports an appropriately configured local Ollama or compatible self-hosted service; compatibility is not proof of remote-routing policy or free entitlement.
- `openai`: OpenAI Chat Completions, normally `https://api.openai.com/v1/chat/completions`. Uses private Bearer auth and `max_completion_tokens` rather than deprecated `max_tokens`; omits temperature for model compatibility. This adapter is not the Responses API, Azure-specific auth, a ChatGPT login/session, or a guarantee that every API model accepts Chat Completions.
- `anthropic`: Native Messages, normally `https://api.anthropic.com/v1/messages`. Uses private `x-api-key`, `anthropic-version: 2023-06-01`, JSON content type, `model`, `messages`, and `max_tokens`. No OpenAI Bearer header. Only nonempty text blocks with `stop_reason: end_turn` are accepted; tool/thinking/refusal/truncated output is not treated as a summary. No extended-thinking/tool parameters are enabled.

Choose a model your account/runtime actually exposes and that supports the selected protocol. This feature does not probe catalogs or upstream accounts to choose one.

## Local setup: direct Ollama, without router forwarding

After you have separately installed/started your runtime and chosen an already-installed model, run from the repository root in bash:

```bash
SUMMARIZER_PROVIDER=openai-compatible \
SUMMARIZER_API_URL=http://127.0.0.1:11434/v1/chat/completions \
SUMMARIZER_MODEL='YOUR_INSTALLED_MODEL_IDENTIFIER' \
SUMMARIZER_API_KEY='' NOTIFICATION_CHANNEL=none \
python main.py run --enable-ai-summary
```

Replace the model placeholder explicitly. This command runs ordinary news collection and updates the configured local tracker data, but does not run provider probes or discovery. Use isolated `--data-dir`/`--reports-dir` paths for acceptance exercises. For a **single retained-title check without collection or persistence**, call the production API on an in-memory copy of a selected real `NewsItem`:

```python
from news_tracker.summarizer import summarize_news

result = await summarize_news([selected_news_item.model_copy(deep=True)], {
    "provider": "openai-compatible",
    "api_key": None,
    "model": "YOUR_INSTALLED_MODEL_IDENTIFIER",
    "base_url": "http://127.0.0.1:11434/v1/chat/completions",
    "max_tokens": 4096,
})
assert result[0].summary
assert not result[0].summary.startswith("Title excerpt (not AI summary):")
```

Imports require the repository's `src` and `src/tracker-core` on `sys.path` (importing `main` establishes both). `selected_news_item` must come from your actual retained observations, not an invented announcement. This check mutates only the copy and makes one opt-in inference request; it does not call feeds, send notifications, or write the original news database. It proves title/excerpt consumer behavior, **not** full-article factual quality. The private `NewsTracker.process(items)` path calls this same API after deduplication and before scoring.

The legacy programmatic default endpoint remains `http://localhost:3001/v1/chat/completions`; an empty/absent configuration still makes no request. A nonempty programmatic configuration explicitly enables inference, so always supply an intentional model and endpoint. The legacy default model string `free-tier` is merely an old router alias, not a portable model or free-access promise. If using FreeLLMAPI instead of direct Ollama, select a known local-only route yourself and verify its routing policy before enabling it. Do not infer local execution or zero fees from the router's listening address.

## Remote BYOK / self-hosted backend

Keep provider, endpoint, and model in private backend configuration. Inject `SUMMARIZER_API_KEY` with your hosting platform's secret mechanism or a protected process environment. For OpenAI, select `SUMMARIZER_PROVIDER=openai` and its full Chat Completions endpoint; for Claude, select `anthropic` and its full Messages endpoint. Keys are not read from `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` as an implicit opt-in. Configure a dedicated least-privilege credential where supported, account budgets/alerts, and rotate it if disclosed.

For a remote compatible service, select `openai-compatible` with its documented full HTTPS endpoint and private key. Unsupported models/protocol variants fail to an honest fallback, not a different provider. Never expose a keyless local inference listener publicly. Put remote self-hosted services behind access control and HTTPS. Containers and hosted CI have their **own** loopback, not your workstation's; a workstation Ollama URL is not reachable there just because it works locally. Proxies from environment variables and automatic redirects are disabled for summary requests to avoid accidental credential/prompt forwarding. A service requiring a proxy or nonstandard certificate setup needs a separately reviewed integration, not disabling TLS verification.

## Protected CI setup (optional, not enabled by this change)

Configure the nonsecret provider/model/endpoint as appropriate workflow variables, and the private key as an encrypted CI secret. On a trusted job only, explicitly map:

```yaml
env:
  SUMMARIZER_PROVIDER: ${{ vars.SUMMARIZER_PROVIDER }}
  SUMMARIZER_MODEL: ${{ vars.SUMMARIZER_MODEL }}
  SUMMARIZER_API_URL: ${{ vars.SUMMARIZER_API_URL }}
  SUMMARIZER_API_KEY: ${{ secrets.SUMMARIZER_API_KEY }}
  NOTIFICATION_CHANNEL: none
```

Then explicitly use `python main.py run --enable-ai-summary` in that trusted job. Gate optional paid inference using a nonsecret opt-in variable/approved environment; keep it disabled on untrusted pull requests/forks. Never echo environment values, enable shell tracing (`set -x`), cache env files, or upload the internal database/logs as public artifacts. Do not paste secrets into ordinary GitHub variables or static hosting build output. Disabling AI means omitting the CLI flag; deleting a key alone is not the recommended disable mechanism.

## Costs, privacy, limits, and fallback

- Open-source/no-AI core usage needs no inference subscription. Optional remote API inference may incur usage charges and account/model-specific rate limits. A ChatGPT Plus/Pro or Claude Pro/Max subscription is **not** a promise of API access, API credits, or free entitlement; API billing/access is separate. Verify current model availability, pricing, account limits, and service terms yourself before enabling it. No fixed prices or ongoing free-tier guarantees are claimed here.
- A local model avoids a remote provider's per-token inference charge only when it really executes locally. Hardware, electricity, installation, runtime capacity, and the model's license/privacy obligations still matter. A compatible/free service can change quotas or route remotely.
- The prompt uses up to 1000 title characters, up to 200 existing-excerpt characters, and a category per item. It does **not** fetch/read full articles. AI text may be wrong; it is not independent source verification. News titles/excerpts are untrusted input; never send private material to an endpoint you do not trust.
- Default batches contain at most five items. Calls are sequential, without automatic retries or provider switching. Default output ceiling is 1000 tokens; existing reasoning-name hints use 4096. Programmatic `max_tokens` accepts only integers 1–4096. These are output limits, not account spending caps; input/reasoning token charges and aggregate run costs still depend on the provider and number of retained items. Name hints are heuristics, not a full model registry.
- Requests use a 30-second HTTPX per-operation timeout. Responses are streamed with a 64 KiB decoded-byte ceiling before JSON parsing; content is limited to 32768 characters, each summary to 2000, and each dedup key to 128. Duplicate JSON fields, wrong/missing types, wrong array length, deeply malformed JSON, nontext content, refusal, and truncation are rejected. HTTP 401/429/5xx, timeouts, redirects, and invalid output do not trigger retries or another provider.
- Every batch is validated completely before replacing observations in that batch. On failure, already validated earlier batches remain; processing stops before requesting subsequent batches. Existing publisher excerpts are preserved. Items without excerpts receive `Title excerpt (not AI summary): …`, never a fabricated successful AI summary. Failure logs contain fixed messages and exception **class**, not upstream bodies, keys, private endpoint settings, or exception messages. HTTPX/HTTPCore verbose request traces are suppressed; do not re-enable wire logging around private inference.
- Literal configured credentials/endpoints reflected in returned fields (including JSON escapes) are rejected before persistence. This does not make arbitrary model-generated text safe to publish wholesale: the separately sanitized public export remains the authorization/privacy boundary.

## Offline verification and live acceptance

`tests/test_ai_summary_providers.py` exercises real CLI → tracker → summarizer → SQLite behavior using HTTPX MockTransport, including native Anthropic headers/payload/text blocks, OpenAI completion-token fields, keyless direct loopback, populated-env/no-AI zero requests, URL/key/model validation before state creation, bounded streamed reads, safe failure logs, and escaped credential reflection. Legacy summary tests also run through MockTransport rather than an invented HTTP client shape. These tests do not invoke paid APIs or prove live model access/entitlement.

A controlled direct-loopback live consumer check is a separate acceptance step owned by the operator. Use one real retained observation on a copy, inspect the actual model result, and keep the original database unchanged. Full-article quality, public news publication, hosted delivery, and release approval are separate gates.

## Primary protocol and billing references

Official documentation checked October 3, 2026; no inference was called as part of documentation verification:

- OpenAI API authentication: <https://developers.openai.com/api/reference/overview>
- OpenAI Chat Completions (`max_completion_tokens`, `messages`, response choices): <https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create>
- Anthropic API headers (private key authentication and `anthropic-version`): <https://platform.claude.com/docs/en/api/overview>
- Anthropic Messages (`max_tokens`, user messages, text content, `end_turn`): <https://platform.claude.com/docs/en/api/messages>
- Claude subscription versus API billing: <https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console>
- OpenAI ChatGPT Plus help (API usage separately billed): <https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus>

The OpenAI help page rejected direct automated retrieval (HTTP 403); its billing distinction was checked via the official search result rather than treating the fetch as successful. Consult the current provider pages rather than relying on a subscription label or this document for prices/quotas.
