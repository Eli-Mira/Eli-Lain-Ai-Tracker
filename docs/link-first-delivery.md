# Hosted-link-first public delivery

The share target is `https://eli-lain-intel.pages.dev/`. Routine public notifications start with “Open the public dashboard” and its hosted URL. HTML remains an internal generated/deployable artifact; the recipient is not required to download it.

`deliver_report()` validates the sanitized single-file artifact and receipt state, independently byte-verifies the fixed Pages origin, then sends a text-only Telegram message and a text-only Discord message. Telegram validates the official send receipt; Discord independently reads its message back. Both configured channels must be confirmed. No side-effecting send/deploy is automatically retried. An optional Netlify mirror remains opt-in, best-effort and independent of channel identities.

## Explicit optional export

Ordinary delivery uses `PUBLIC_REPORT_ATTACHMENT=false` (also the default when absent). Only literal `true`/`false` are accepted; invalid settings fail before requests.

For a secondary standalone HTML attachment, explicitly set `PUBLIC_REPORT_ATTACHMENT=true` or use:

```bash
python scripts/publish_report.py --export-dir ./public --attach-html --json
```

`--link-only` overrides an attachment-enabled environment. Optional export still verifies uploaded filename/size and Discord attachment readback. Telegram's document ID must accompany its brief ID. Attachment failure fails that optional-mode delivery rather than claiming a file was delivered. The hosted URL remains the first line in either mode.

This command verifies an **already deployed** Pages artifact; it does not create a deployment or change site visibility. Both channel credentials remain private environment/CI secrets, never public HTML. Running the command with real credentials sends real messages and needs the operator's authorization.

## Restart, modes and bounded receipts

Both the standalone publishing CLI and `main.py publish` use `data/delivery_receipts.json`; the standalone CLI accepts `--state-path` to select an isolated alternate file. Missing state is a first-run baseline. Corrupt/unreadable/oversized state fails safely before requests, without overwriting it.

Confirmation is bound to artifact SHA256, hashed bot/destination/public-URL identity, and **delivery mode**. Link mode stores separate `telegram_link`/`discord_link` confirmations with a mode marker in their hashed binding. Attachment mode preserves the pre-existing `telegram`/`discord` schema and binding, so authentic legacy attachment confirmations remain usable only for that mode. Switching modes requires its own confirmation; switching back reuses the corresponding retained confirmation, including independently confirmed siblings from a partial failure. Raw tokens and destination IDs are never stored.

Telegram's confirmed brief ID survives an optional document failure. An explicit restart skips that confirmed brief and attempts only the missing document. A fully confirmed sibling is skipped. No attachment confirmation is treated as proof of a newly sent link-only notification, nor is link-only confirmation proof of file delivery.

The receipt writer serializes read/merge/atomic writes and fsyncs its temporary file. It retains at most 64 artifact records, with only fixed essential fields and bounded values. Recent completed history is evicted first; incomplete fan-outs and latest confirmed sibling per mode/channel are pinned. If pinned evidence exhausts the bound, `receipt_capacity` stops a new delivery before requests. Existing files above the replay window are compacted on a successful routine receipt write; a corrupt state is never silently discarded. This is not a second HTML/message archive.

**Limits:** Byte-identical replay suppression is finite. Evicted older hashes can be announced again; regeneration changes hashes even when the underlying observations do not change. A lost response may mean a message landed without a provable ID: there is no automatic retry, and an explicit operator rerun can duplicate it. Concurrent senders are not serialized by the receipt-write lock, so this does **not** promise exactly-once delivery. Do not auto-rerun failed/ambiguous publish steps.

## Workflow and acceptance

The scheduled workflow explicitly chooses `PUBLIC_REPORT_ATTACHMENT=false` and preserves receipt state even when a sibling channel fails. Hosting/notification flags remain opt-in; this implementation does not enable them. Tests use MockTransport and synthetic artifacts, never real deployment/notifications. Actual anonymous hosted rendering/readback and operator-approved end-to-end delivery remain release gates.
