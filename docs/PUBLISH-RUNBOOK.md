# Publish runbook — EliLain Intel

Everything is committed at `c4e574f` on `main` in the **private** repo. Nothing is
deployed, nothing is public yet, and no notification has been sent.

The local suite is green (**1007 passed**) and the artifact is browser-verified.
The only remaining step is a real hosted deploy + readback, which needs your go.

## What is waiting, and why it matters

`https://eli-lain-intel.pages.dev/` is **live right now and serves the OLD page**.
Measured from this machine, anonymously:

| Check | Live page today | New artifact |
|---|---|---|
| Hearth POS section | present | absent |
| Gesture control section | present | absent |
| `#project-shortlists` | present | absent |
| Lain avatar | absent | present |
| Light-mode toggle | absent | present |
| Discovery rows | 2960 | 1673 validated |

So the personal-project leak is **live on the public URL right now**, not just in
code. Publishing is a privacy fix, not only a polish step.

The live page exposes no credentials, no local paths, no `emadg` string and no
loopback addresses — that part is clean. The problem is scope only.

## Pre-publish decisions (yours, all of them)

1. **Artwork rights.** The Lain JPEG is third-party and excluded from the MIT code
   licence. Publishing embeds it publicly. Replace it with your own art, or accept
   the risk knowingly.
2. **Repository visibility.** The repo is `private` today. A public dashboard does
   not require a public repo, and I recommend keeping it private. Open-sourcing is
   a separate decision.
3. **The 13 old local archives** (26,110,024 bytes). Deletion is dry-run only.
   Unrelated to publishing; do it whenever.
4. **Whether to notify.** The daily cron at 06:00 UTC will deploy and post to
   Telegram + Discord on its own, because `PUBLISH_ENABLED` and
   `CLOUDFLARE_PUBLISH_ENABLED` are both already `true`.

## The publish step (only after the decisions above)

Pushing does **not** trigger a run — the workflow is `schedule` +
`workflow_dispatch` only, so a push is safe on its own.

```bash
cd C:/tmp/eli-lain-tracker
git push origin main

# exactly one manual run, then assert only one entry exists for this SHA
gh run list --limit 1 --json headSha,status,conclusion
gh workflow run news-tracker-daily.yml -f publish_pages=true
gh run watch
```

Then read back the **actual served bytes** — the deploy log's hash is not proof:

```bash
gh run download <run-id> -D "$TMPDIR/qa"     # sanitized artifact only
curl -sS -A "Mozilla/5.0" https://eli-lain-intel.pages.dev/ -o "$TMPDIR/live.html"
sha256sum "$TMPDIR/qa/index.html" "$TMPDIR/live.html"
```

Both hashes must match. Then re-run the private-section audit against the served
page, and confirm the browser render at 360/390/1440px with JS on and off.

## If the deploy fails

Do not re-run blindly. A rerun re-publishes and can resend a duplicate
notification to both channels. Read the failing step first.

If a notification lands, identify which bot posted it by matching the account,
not by the timestamp — a busy channel can look like a third party.

## After a verified deploy

- Record the run id, both hashes, and the readback result in the pre-release
  checklist and `SESSION_LOG`.
- Only then does R08 become fully verified and `customer-release-verdict` become
  answerable.
