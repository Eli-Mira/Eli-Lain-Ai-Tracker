# Eli Lain — AI/Tech News Tracker

> Public AI/tool dashboard: [Open Eli Lain Intel](https://eli-lain-intel.pages.dev/). Ordinary public Telegram/Discord notifications share this hosted page, not a required HTML download.
>
> Hosted release acceptance is separate from local implementation; publishing remains opt-in.

AI/Tech News Tracker — pulls latest developments from GitHub, Reddit, Hacker News, arXiv, and tech news sites.

## How It Runs

- **GitHub Actions** triggers the workflow daily at 11 AM Cairo time
- Fetches from GitHub releases, Reddit RSS, and tech news sources
- Scores, summarizes, deduplicates
- Generates an HTML report with the "lain" theme
- Pushes notifications to configured channels

## Notification Channels

| Channel | Setup |
|---------|-------|
| Discord | Bot token + channel ID |
| Telegram | Bot token + chat ID |
| Email | SMTP host/port/user/password |
| WhatsApp | Via Hermes Gateway (optional) |

## Local Dev

```bash
cd tracker-core
pip install -e ".[dev]"

cd ../news-tracker
pip install -e "."
```

## Usage

```bash
# Run full tracking cycle
python main.py run

# Generate report
python main.py report

# List recent news
python main.py list --days 7

# Quick run + report for today
python main.py today

# Use lain theme
python main.py report --theme lain
```

## Sources

- **GitHub**: Releases from tracked orgs (OpenAI, Anthropic, Google DeepMind, Meta AI, etc.)
- **Reddit**: r/MachineLearning, r/LocalLLaMA, r/artificial, r/OpenAI, r/ChatGPT, r/GenerativeAI
- **Hacker News**: AI/LLM related stories via Algolia API
- **arXiv**: New papers in cs.AI, cs.CL, cs.LG, cs.CV, cs.NE
- **RSS Feeds**: TechCrunch AI, The Verge AI, VentureBeat AI, company blogs

## Output

- Routine internal HTML replaces `reports/latest.html`; sanitized public HTML replaces `public/index.html`.
- Current deduplicated discovery state and bounded first-seen/fingerprint metadata live in `data/intel_state.json`; the working news SQLite database and cooldowns are preserved.
- Public notifications are hosted-link-first by default. An HTML attachment is secondary and explicit (`PUBLIC_REPORT_ATTACHMENT=true` or `scripts/publish_report.py --attach-html`).
- Restart/partial-failure receipts are mode-bound and capped; no exactly-once guarantee or automatic send retry.
- Existing archives are not deleted. `python scripts/cleanup_local_outputs.py --dry-run --json` lists exact candidates/exclusions for separate approval.

See [link-first delivery](docs/link-first-delivery.md) and [local retention](docs/local-retention.md) for settings, bounds, safety limits and integration contracts.

## Secrets

Credentials are stored in `.env` (local) and GitHub Secrets (Actions). See `.env.example` for required variables.

---

*Built by Eli + Lain — 2026*
