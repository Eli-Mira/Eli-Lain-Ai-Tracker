# Eli Lain — AI/Tech News Tracker

> Automated digest of AI/tech news, pushed to Discord, Telegram, WhatsApp, and email via GitHub Actions.

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

- Daily JSON batches in `data/news_YYYYMMDD.json`
- HTML reports in `reports/news_YYYYMMDD.html`
- Deduplicated, filtered, and summarized items

## Secrets

Credentials are stored in `.env` (local) and GitHub Secrets (Actions). See `.env.example` for required variables.

---

*Built by Eli + Lain — 2026*
