# Verified report hosting and delivery (next)

Scope of this pass: `src/intel_sources/report_delivery.py`, `scripts/publish_report.py`,
`tests/test_report_delivery.py`. Nothing else in the repo was modified. No commit, push,
deployment, live notification or site/repo creation was performed.

## What the pipeline does, in order

1. `DeliveryConfig.from_env` requires the four channel credentials
   (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DISCORD_BOT_TOKEN`,
   `DISCORD_CHANNEL_ID`). **Netlify is no longer required**: `NETLIFY_AUTH_TOKEN`
   and `NETLIFY_SITE_ID` are read only when `NETLIFY_MIRROR_ENABLED=true`, and a
   mirror enabled without them degrades to `mirror-unavailable/missing_config`
   instead of failing the run. Any missing required value raises `missing_config`
   **before** the first HTTP request.
2. `load_artifact` refuses any export directory that does not contain exactly one regular,
   non-symlink, non-reparse `index.html` (`unexpected_files`). It then requires the footer
   sentence that identifies the file as the sanitized saved-observation export, requires
   exactly one timestamp in that footer (the render time), and requires every
   `#discoveries .discovery-item` `data-source` to be a member of `public_report.PUBLIC_SOURCES`
   (`invalid_artifact`). So a hand-edited, stale-typed or private-tree directory cannot be published.
3. Netlify digest deploy of that one file only: `GET /api/v1/sites/{site_id}` (id must match),
   `POST /api/v1/sites/{site_id}/deploys` with `{"files": {"/index.html": "<sha1>"}, "draft": false}`
   and no `functions`/`edge_functions`, then `PUT /api/v1/deploys/{deploy_id}/files/index.html` with the
   raw bytes as `application/octet-stream` only when the response lists the digest in `required`,
   then `GET /api/v1/deploys/{deploy_id}` polled until `state == "ready"`. A foreign `id`/`site_id`
   in the status response is `deploy_mismatch`; exhausting the poll budget is `deploy_not_ready`.
4. Hosted readback: the `deploy_ssl_url` from the ready status must be an `https` host under the
   `netlify.app` suffix (`unsafe_url` otherwise). The pipeline GETs that exact URL with no
   credentials, no cookies and no redirect following, streams at most 4 MiB, and requires
   `sha256(bytes) == sha256(local index.html)`. A mismatch is `html_mismatch` and **no message is sent**.
5. `build_brief` produces one plain-text brief: render timestamp, first-to-last saved observation
   timestamp, exported discovery count with per-source exported counts, the "saved data, not a fresh
   fetch / metadata only / unverified / excluded" limits, and the verified hosted URL. No markdown
   characters, no item titles, no source URLs, no provider data. Measured 532 characters for the
   current 449-row export; the ceiling is 1500.
6. Telegram `POST /bot<token>/sendMessage` with `link_preview_options.is_disabled` and **no**
   `parse_mode`. A `sendMessage` result is validated for `ok is True`, a positive integer
   `message_id`, `result.chat.id` equal to the configured chat, and `result.text` equal to the brief.
   The receipt is reported as `receipt-confirmed`. The official Bot API has no arbitrary
   get-message method, so this is explicitly *not* labelled as an independent readback.
7. Discord `POST /api/v10/channels/{channel}/messages` with
   `allowed_mentions: {"parse": [], "replied_user": false}`, then
   `GET /api/v10/channels/{channel}/messages/{id}` requiring matching `id`, `channel_id` and
   `content`. Only that GET is reported as `independently-read-back`.
8. `deliver_report` raises `channel_failure` unless **both** receipts confirm. The exception carries
   the per-channel `DeliveryResult`, so a half-delivered run reports exactly which channel is
   unconfirmed and its safe `error_code`. No send is retried: a duplicate post is worse than a
   recorded partial failure. `MultiNotifier`'s any-success contract is untouched and unused here.

## Network safety

- `_PinnedTransport` allows only `https` on default port to `api.netlify.com`, `api.telegram.org`,
  `discord.com`, plus the single `*.netlify.app` host learned from the ready deploy. It resolves each
  host through the injected `resolver`, refuses any answer that is not global (`unsafe_dns`), and
  connects to the resolved IP while keeping `Host` and setting `sni_hostname` so TLS still validates
  the hostname. Pools are per-hostname, so an IP-pinned connection is never reused across
  differently-authenticated names.
- Redirects are never followed, so a 302 cannot bounce the token to another origin (`http_status`).
- Response bodies are capped (4 MiB hosted HTML, 128 KiB API JSON) while streaming.
- `httpx`/`httpcore` loggers are disabled for the duration of the operation, because httpx INFO
  logging would otherwise record the Telegram token embedded in the request path.
- Errors carry a fixed safe code only. Server bodies, response headers and request URLs are never
  placed in an exception, a result, a log record or CLI output. Tokens are read from the environment
  into memory and are not written to any artifact, and the token appears nowhere in the CLI argument
  list, so no process command line carries a secret.

## Official API references

- Netlify, "Get started with the Netlify API" — digest deploy, `POST /api/v1/sites/{site_id}/deploys`
  with a path→SHA1 map, `PUT /api/v1/deploys/{deploy_id}/files/index.html`, `GET /api/v1/deploys/{deploy_id}`
  state polling, `draft`, and the `Authorization: Bearer` header:
  https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/
- Netlify OpenAPI, Deploy API — `files` is "A hash mapping file paths to SHA1 digests", response carries
  `required`, `required_functions`, `state`, `ssl_url`, `deploy_ssl_url`; state enum includes
  `preparing`, `prepared`, `uploading`, `uploaded`, `ready`:
  https://github.com/api-evangelist/netlify/blob/main/openapi/netlify-deploy-api-openapi.yml
  (and `netlify-file-api-openapi.yml` for `PUT /deploys/{deploy_id}/files/{path}`)
- Telegram Bot API, `sendMessage` (`chat_id`, `text`, `link_preview_options`, no `parse_mode`):
  https://core.telegram.org/bots/api#sendmessage
  The Bot API exposes no arbitrary message-read method, which is why Telegram is receipt-confirmed only.
- Discord, Create Message (`allowed_mentions` with `parse` and `replied_user`) and Get Channel Message:
  https://docs.discord.com/developers/resources/message#create-message
  https://docs.discord.com/developers/resources/message#get-channel-messages

## Test evidence

`17 passed` for `tests/test_report_delivery.py` under `.venv/Scripts/python.exe -m pytest`.
Cases cover: single-file digest deploy plus hosted byte readback and both receipts in one ordered
call sequence; missing config with zero requests; an extra file in the export directory; hosted HTML
mismatch with zero notifications; an unfollowed redirect; a foreign/private hosted host; a non-global
DNS answer; deploy polling that never reaches `ready`; a foreign deploy id; partial channel failure
with exactly one Discord attempt and no second Telegram post; Discord readback mismatch; Telegram
labelled receipt-confirmed and never read back; brief size/content/markdown/URL limits; no secret or
server body in exception text, receipts or captured logs; oversized hosted response; the real
`public/index.html` export end to end; and the CLI failure path.

These are deterministic `httpx.MockTransport` protocol tests. The mock asserts the exact methods,
paths, hosts, headers, digests and payloads, but **mock output is not a live deployment** and no
test in this file contacted Netlify, Telegram or Discord.

## Honest current blocker

No live run happened and none is possible from this environment yet:

- The only local values are `NETLIFY_AUTH_TOKEN` and `NETLIFY_SITE_ID`; the Telegram and Discord
  secrets exist only as encrypted GitHub secret *names* on the private repo, and GitHub's API cannot
  return secret values. There is no local host/auth environment for either bot.
- The hosted URL is taken from `deploy_ssl_url` and must end in `netlify.app`; the current private
  repository plan rejects GitHub Pages deploys (422), and the task scope forbids making the repo
  public, creating a new repository or site, or signing up or paying for anything.
- A first live run therefore needs the six environment values supplied from a trusted host, and
  authorization for the real deploy plus both live posts. Until then the only verified claims are the
  protocol shapes, the fail-closed ordering and the brief content.

The daily workflow integration is deliberately not done here; `main.py`, the workflow template and
`public_report.py` are untouched. The integration call is
`scripts/publish_report.py --export-dir public --json` after a successful
`scripts/export_public_report.py`, and its exit status must be preserved rather than inferred from a
later command.
