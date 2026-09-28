"""Main entry point for Eli-Lain AI Tracker.

Wires together: free LLM provider tracking (freellmapi integration),
GitHub tool discovery, news aggregation, and HTML report generation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src" / "tracker-core"))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tracker_core.schema import NewsItem, SourceType
from tracker_core.reporter_html import get_html_reporter
from tracker_core.cache import FileCache

from news_tracker.adapters import get_all_adapters
from news_tracker.dedup_filter import deduplicate_and_filter
from news_tracker.summarizer import summarize_news
from news_tracker.scoring import score_and_categorize, group_by_category, Scorer
from news_tracker.health import SourceHealthTracker
from news_tracker.store_sqlite import SQLiteStore
from tracker_core.notifier import get_notifier
from news_tracker.importance import score_importance

# New: free LLM provider tracking
from freellmapi_tracker import (
    FreeProvider,
    ProviderStatus,
    ProviderTier,
    FreellmapiIntegrationType,
    FreeProviderTracker,
    ProviderDiscovery,
    AutoProber,
)

logger = logging.getLogger(__name__)


def _apply_importance_score(item: NewsItem) -> NewsItem:
    """Apply importance scoring to an item."""
    from news_tracker.importance import score_importance
    importance = score_importance(item)
    item.relevance_score = (item.relevance_score * 0.7) + (importance * 0.3)
    return item


class NewsTracker:
    """Main tracker for AI/tech news + free LLM providers + GitHub tools."""

    def __init__(
        self,
        data_dir: Path | str = "./data",
        cache_dir: Path | str = "./.cache",
        reports_dir: Path | str = "./reports",
        theme: str = "lain",
        summarizer_config: dict[str, Any] | None = None,
        failure_threshold: int = 3,
        freellmapi_db_path: str | Path = r"C:\Users\emadg\freellmapi-docker\data\freeapi.db",
        freellmapi_url: str = "http://localhost:3001",
    ):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.reports_dir = Path(reports_dir)
        self.theme = theme
        self.summarizer_config = summarizer_config or {}
        self.freellmapi_db_path = freellmapi_db_path
        self.freellmapi_url = freellmapi_url

        # Initialize components
        self.sqlite = SQLiteStore(self.data_dir / "news.db")
        self.cache = FileCache(self.cache_dir)
        self.reporter = get_html_reporter(theme)
        self.health = SourceHealthTracker(
            failure_threshold=failure_threshold,
            state_path=str(self.data_dir / "health.json"),
        )

        # Load persisted health state
        persisted_health = self.sqlite.load_source_health()
        for name, h in persisted_health.items():
            health_record = self.health.get_or_create(name)
            health_record.consecutive_failures = h.get("consecutive_failures", 0)
            health_record.is_disabled = h.get("is_disabled", False)
            health_record.total_items = h.get("total_items", 0)

        # Notifier
        notif_config = {
            "channel": os.getenv("NOTIFICATION_CHANNEL", "none").replace(" ", "").split("\n")[0],
            "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", "").replace(" ", "").split("\n")[0],
            "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", "").strip().split("\n")[0],
            "discord_bot_token": os.getenv("DISCORD_BOT_TOKEN", "").replace(" ", "").split("\n")[0],
            "discord_channel_id": os.getenv("DISCORD_CHANNEL_ID", "").strip().split("\n")[0],
            "email_host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
            "email_port": int(os.getenv("EMAIL_PORT") or "587"),
            "email_user": os.getenv("EMAIL_USER", "").strip(),
            "email_password": os.getenv("EMAIL_PASSWORD", "").replace(" ", ""),
            "email_from": os.getenv("EMAIL_FROM", os.getenv("EMAIL_USER", "")).strip(),
            "email_to": [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()],
        }
        self.notifier = get_notifier(notif_config)

        # Breaking news threshold
        self.breaking_threshold = 0.7
        self.last_run_date: datetime | None = None

        # NEW: Provider tracker
        self.provider_tracker = FreeProviderTracker(
            freellmapi_db_path=self.freellmapi_db_path,
            state_path=self.data_dir / "provider_state.json",
        )

        # NEW: GitHub tool discovery
        self.tool_discovery = ProviderDiscovery()

    # ── Provider tracking methods ──────────────────────────────────────

    def load_providers(self) -> int:
        """Load providers from freellmapi DB."""
        count = self.provider_tracker.load_from_db()
        self.provider_tracker.load_state()
        return count

    async def probe_providers(self) -> int:
        """Run the auto-prober on all enabled providers. Returns count updated."""
        prober = AutoProber(
            base_url=self.freellmapi_url,
            api_key=os.getenv("FREELLMAPI_API_KEY"),
        )
        providers = [p for p in self.provider_tracker.providers.values() if p.probe_enabled]
        results = await prober.probe_all(providers, concurrency=3)

        updated = 0
        for platform, result in results.items():
            provider = self.provider_tracker.providers.get(platform)
            if provider:
                status, reason = result.to_status()
                provider.status = status
                provider.status_reason = reason
                provider.last_verified = datetime.now(timezone.utc)
                provider.last_verified_source = "probe"
                provider.freellmapi_action = self._action_for(provider, result)
                updated += 1

        self.provider_tracker.save_state()
        logger.info(f"Probed {len(results)} providers, {updated} updated")
        return updated

    def _action_for(self, provider: FreeProvider, result: Any) -> str:
        """Generate the next-step action string."""
        status, reason = result.to_status()
        if status == ProviderStatus.LIVE:
            extra = ""
            if result.remaining_quota is not None:
                extra = f" ({result.remaining_quota} remaining)"
            return f"No action needed — free tier active{extra}"
        if status == ProviderStatus.BROKEN_KEY:
            dash = self._dash_url(provider.platform)
            return f"Key returning {result.http_status or 401}. Get a fresh key from {dash} and update freellmapi."
        if status == ProviderStatus.EXHAUSTED:
            if "monthly" in provider.reset_schedule.lower():
                return f"Credit exhausted. Resets monthly ({provider.reset_schedule})."
            if "daily" in provider.reset_schedule.lower():
                return f"Daily quota exhausted. Resets daily ({provider.reset_schedule})."
            return f"Quota exhausted: {reason}. Check {self._dash_url(provider.platform)}."
        if status == ProviderStatus.PAYWALLED:
            return "Provider moved behind paywall. Disable in freellmapi or upgrade."
        if status == ProviderStatus.DEGRADED:
            return f"Degraded: {reason}. May recover — monitor."
        return f"Status unknown ({reason}). Verify manually at {self._dash_url(provider.platform)}."

    @staticmethod
    def _dash_url(platform: str) -> str:
        dashboards = {
            "cloudflare": "dash.cloudflare.com",
            "groq": "console.groq.com/keys",
            "cohere": "dashboard.cohere.com/api-keys",
            "mistral": "console.mistral.ai/api-keys",
            "google": "aistudio.google.com/apikey",
            "zhipu": "open.bigmodel.cn/usercenter/apikeys",
            "huggingface": "huggingface.co/settings/tokens",
            "openrouter": "openrouter.ai/settings/keys",
            "nvidia": "build.nvidia.com/dashboard",
            "cerebras": "cloud.cerebras.ai",
        }
        return dashboards.get(platform, f"{platform}.com")

    def provider_status_rows(self) -> list[dict[str, Any]]:
        """Build api_items-shaped rows from provider tracker."""
        rows = []
        for p in self.provider_tracker.providers.values():
            # Map our statuses to template classes
            status_class = "stable"
            if p.status == ProviderStatus.LIVE:
                status_class = "new" if p.is_new else "stable"
            elif p.status in (ProviderStatus.EXHAUSTED, ProviderStatus.PAYWALLED, ProviderStatus.BROKEN_KEY):
                status_class = "dead"
            elif p.status == ProviderStatus.DEGRADED:
                status_class = "updated"
            elif p.status == ProviderStatus.UNKNOWN:
                status_class = "unknown"

            desc_parts = []
            if p.tier_details:
                desc_parts.append(p.tier_details)
            if p.reset_schedule:
                desc_parts.append(f"resets: {p.reset_schedule}")
            if p.last_verified:
                desc_parts.append(f"verified: {p.last_verified.strftime('%Y-%m-%d %H:%M')} UTC")
            if p.freellmapi_action:
                desc_parts.append(p.freellmapi_action)

            rows.append({
                "name": p.name,
                "status": status_class,
                "description": " · ".join(desc_parts),
            })

        # Sort: dead/exhausted first, then degraded, then live
        priority = {"dead": 0, "updated": 1, "unknown": 2, "new": 3, "stable": 4}
        rows.sort(key=lambda r: (priority.get(r["status"], 99), r["name"].lower()))
        return rows

    # ── GitHub tool discovery methods ──────────────────────────────────

    async def discover_tools(self) -> list[dict[str, Any]]:
        """Discover relevant GitHub tools."""
        tools = await self.tool_discovery.discover_github_tools()
        rows = []
        for t in tools[:15]:  # Limit to top 15
            recency = ""
            if t.last_push:
                days = (datetime.now(timezone.utc) - t.last_push).days
                if days <= 30:
                    recency = f"pushed {days}d ago"
                else:
                    recency = f"last push {t.last_push.strftime('%Y-%m')}"
            rows.append({
                "headline": f"⭐ {t.stars} · {t.repo_name}",
                "source": f"github ({t.category})",
                "summary": f"{t.description} — {t.relevance_reason} {recency}".strip(),
                "url": t.url,
            })
        return rows

    # ── Existing news pipeline (unchanged) ─────────────────────────────

    async def fetch_all(self) -> list[NewsItem]:
        """Fetch news from all sources with circuit breaker."""
        logger.info("Fetching news from all sources...")
        adapters = get_all_adapters()
        all_items: list[NewsItem] = []

        for adapter in adapters:
            if not self.health.is_source_enabled(adapter.name):
                logger.info(f"Skipping {adapter.name} (circuit broken)")
                continue
            try:
                items = await adapter.fetch_all()
                if items:
                    all_items.extend(items)
                    self.health.record_success(adapter.name, len(items))
                else:
                    self.health.record_failure(adapter.name, "Empty result")
            except Exception as e:
                logger.error(f"Failed to fetch from {adapter.name}: {e}")
                self.health.record_failure(adapter.name, str(e))

        logger.info(f"Total fetched: {len(all_items)} items")
        for source_name in self.health._sources:
            source = self.health._sources[source_name]
            self.sqlite.save_source_health(source_name, {
                "consecutive_failures": source.consecutive_failures,
                "last_success": source.last_success.isoformat() if source.last_success else None,
                "last_failure": source.last_failure.isoformat() if source.last_failure else None,
                "is_disabled": source.is_disabled,
                "total_items": source.total_items,
            })
        return all_items

    async def process(self, items: list[NewsItem]) -> tuple[list[NewsItem], dict[str, Any]]:
        context: dict[str, Any] = {}
        unique_items, dedup_stats = deduplicate_and_filter(items)
        context["dedup"] = dedup_stats
        summarized_items = await summarize_news(unique_items, self.summarizer_config)
        scored_items = score_and_categorize(summarized_items)
        scored_items = [_apply_importance_score(item) for item in scored_items]
        relevant_items = [item for item in scored_items if item.is_relevant]
        context["relevant_count"] = len(relevant_items)
        return relevant_items, context

    def _split_breaking_news(self, items: list[NewsItem]) -> tuple[list[NewsItem], list[NewsItem]]:
        breaking, regular = [], []
        for item in items:
            (breaking if item.relevance_score >= self.breaking_threshold else regular).append(item)
        return breaking, regular

    async def push_breaking_news(self, items: list[NewsItem]) -> bool:
        if not items:
            return True
        message = "🚨 **BREAKING NEWS** 🚨\n\n"
        for item in items[:5]:
            message += f"**{item.title}**\n"
            if item.summary:
                message += f"{item.summary[:200]}\n"
            message += f"[Read more]({item.url})\n\n"
        try:
            sent = await self.notifier.send(message)
            if sent:
                logger.info(f"Pushed {len(items)} breaking news items")
            return sent
        except Exception as e:
            logger.error(f"Failed to push breaking news: {e}")
            return False

    async def run(self, date: datetime | None = None, push_breaking: bool = True) -> dict[str, Any]:
        """Run a full news tracking cycle."""
        run_date = date or datetime.now(timezone.utc)
        self.last_run_date = run_date
        logger.info(f"Running news tracker for {run_date.strftime('%Y-%m-%d')}")

        items = await self.fetch_all()
        processed_items, context = await self.process(items)
        inserted = self.sqlite.save_items(processed_items)
        context["inserted"] = inserted

        breaking_items, regular_items = self._split_breaking_news(processed_items)
        context["breaking_count"] = len(breaking_items)
        context["regular_count"] = len(regular_items)

        if breaking_items and push_breaking:
            await self.push_breaking_news(breaking_items)

        logger.info(f"Completed: {inserted} new, {len(breaking_items)} breaking, {len(regular_items)} regular")
        return {
            "date": run_date.isoformat(),
            "total_fetched": len(items),
            "breaking": len(breaking_items),
            "regular": len(regular_items),
            "health_table": self.health.get_health_table(),
            **context,
        }

    # ── Report generation ──────────────────────────────────────────────

    def generate_report(
        self,
        date: datetime | None = None,
        output_path: Path | str | None = None,
        include_providers: bool = True,
        include_news: bool = True,
        include_tools: bool = True,
    ) -> str:
        """Generate HTML report with providers, news, and tools."""
        run_date = date or self.last_run_date or datetime.now(timezone.utc)

        # Provider section
        api_items: list[dict[str, Any]] = []
        if include_providers:
            api_items = self.provider_status_rows()

        # News + tools section
        news_items: list[dict[str, Any]] = []
        if include_news:
            items_raw = self.sqlite.get_items(days=1)
            for item in items_raw:
                news_items.append({
                    "headline": item.get("title", ""),
                    "source": item.get("source", "unknown"),
                    "summary": item.get("summary") or "",
                    "url": item.get("url", "#"),
                })

        output_path = output_path or self.reports_dir / f"eli-lain_{run_date.strftime('%Y%m%d_%H%M%S')}.html"
        html = self.reporter.render(
            api_items=api_items,
            news_items=news_items,
            report_date=run_date.strftime("%Y-%m-%d"),
            generated_at=datetime.now(timezone.utc).strftime("%H:%M UTC"),
            persona_image_url=None,
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(html, encoding="utf-8")
        logger.info(f"Report saved to {output_path}")
        return html

    # ── Convenience methods ────────────────────────────────────────────

    def list_recent(self, days: int = 7) -> list[dict]:
        return self.sqlite.get_items(days=days, limit=50)

    def get_weekly_summary(self, weeks: int = 1) -> dict[str, Any]:
        return self.sqlite.get_weekly_summary(weeks=weeks)

    def get_health_table(self) -> list[dict[str, Any]]:
        return self.health.get_health_table()


async def async_full_audit(tracker: NewsTracker) -> dict[str, Any]:
    """Run the full EliLain audit: load providers → probe → discover tools → report."""
    print("\n=== ELILAIN FULL AUDIT ===")
    print(f"[1/4] Loading providers from freellmapi DB...")
    count = tracker.load_providers()
    print(f"      Loaded {count} providers")

    # Step 2: probe (skip in CI — freellmapi runs locally on Mira, not on GitHub runners)
    prev_statuses = {p.platform: p.status.value for p in tracker.provider_tracker.providers.values()}
    if os.getenv("GITHUB_ACTIONS") == "true":
        print(f"[2/4] Skipping probes (CI environment — freellmapi is local-only). Using persisted state.")
        probed = 0
    else:
        print(f"[2/4] Probing all enabled providers via {tracker.freellmapi_url}...")
        probed = await tracker.probe_providers()
        print(f"      Probed and updated {probed} providers")

    print(f"[3/4] Discovering GitHub tools...")
    tools = await tracker.discover_tools()
    print(f"      Found {len(tools)} candidate tools")

    print(f"[4/4] Generating HTML report...")
    report_path = tracker.generate_report(include_providers=True, include_news=False, include_tools=False)
    print(f"      Report: {report_path}")

    # Compute status changes (compare post-probe against pre-probe snapshot)
    changes = []
    for p in tracker.provider_tracker.providers.values():
        old = prev_statuses.get(p.platform)
        new = p.status.value if p.status else "unknown"
        if old != new:
            changes.append(f"{p.name}: {old} → {new}")

    # Show the provider table inline
    print("\n--- Provider Status ---")
    print(f"{'Name':<14} {'Status':<12} {'Detail'}")
    print("-" * 60)
    for row in tracker.provider_status_rows():
        print(f"{row['name']:<14} [{row['status']:<8}] {row['description'][:50]}")

    if tools:
        print("\n--- Top Tools Discovered ---")
        for t in tools[:10]:
            print(f"{t['headline']}\n     {t['summary'][:80]}")
            print(f"     {t['url']}")

    # Status-change notification (minimalist)
    if changes:
        msg = "\n".join(f"  • {c}" for c in changes[:8])
        try:
            await tracker.notifier.send(f"⚡ EliLain status change:\n{msg}")
        except Exception as e:
            logger.warning(f"Status-change notification failed: {e}")

    return {
        "providers_loaded": count,
        "providers_probed": probed,
        "tools_found": len(tools),
        "report": str(report_path),
        "status_changes": len(changes),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Eli-Lain AI Tracker — v2")
    parser.add_argument(
        "action",
        choices=["run", "report", "list", "today", "health", "summary",
                  "providers", "probe", "discover", "audit"],
        help="Action to perform",
    )
    parser.add_argument("--theme", choices=["default", "lain"], default="lain", help="Report theme")
    parser.add_argument("--days", type=int, default=7, help="Days to look back")
    parser.add_argument("--date", help="Specific date for report (YYYY-MM-DD)")
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--reports-dir", default="./reports")
    parser.add_argument("--freellmapi-db", default=r"C:\Users\emadg\freellmapi-docker\data\freeapi.db")
    parser.add_argument("--freellmapi-url", default="http://localhost:3001")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    tracker = NewsTracker(
        data_dir=args.data_dir,
        reports_dir=args.reports_dir,
        theme=args.theme,
        freellmapi_db_path=args.freellmapi_db,
        freellmapi_url=args.freellmapi_url,
    )

    if args.action == "run":
        result = asyncio.run(tracker.run())
        print(f"Run complete: {result['total_fetched']} fetched, {result['regular']} regular")

    elif args.action == "report":
        date = None
        if args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        tracker.load_providers()
        html = tracker.generate_report(date=date, include_providers=True, include_news=True)
        print(f"Report generated ({len(html)} bytes)")

    elif args.action == "list":
        items = tracker.list_recent(days=args.days)
        print(f"\nRecent news ({len(items)}):")
        for item in items:
            print(f"[{item.get('source','?')}] {item.get('title','')}")
            if item.get("summary"):
                print(f"  {item['summary'][:100]}")
            print()

    elif args.action == "today":
        try:
            result = asyncio.run(tracker.run())
            tracker.load_providers()
            tracker.generate_report()
            print(f"Tracker complete: {result['relevant_count']} relevant items")
        except Exception as e:
            import traceback
            traceback.print_exc()
            exit(1)

    elif args.action == "health":
        table = tracker.get_health_table()
        print(f"\n{'Source':<20} {'Status':<12} {'Fails':<8} {'Items':<8}")
        print("-" * 50)
        for row in table:
            print(f"{row['source']:<20} {row['status']:<12} {row['consecutive_failures']:<8} {row['total_items']:<8}")

    elif args.action == "summary":
        summary = tracker.get_weekly_summary(weeks=1)
        print(f"\nWeekly ({summary['total_items']} items)")
        for cat in summary["top_categories"]:
            print(f"  {cat['category']}: {cat['count']}")

    # ── NEW: Provider tracking actions ─────────────────────────────────

    elif args.action == "providers":
        count = tracker.load_providers()
        print(f"\nLoaded {count} providers from freellmapi DB\n")
        print(f"{'Name':<16} {'Status':<12} {'Tier':<24} {'Action'}")
        print("-" * 80)
        for p in sorted(tracker.provider_tracker.providers.values(), key=lambda x: x.name):
            tier = p.tier_type.value if p.tier_type else "?"
            action = (p.freellmapi_action or "")[:50]
            print(f"{p.name:<16} [{p.status.value:<10}] {tier:<24} {action}")

    elif args.action == "probe":
        tracker.load_providers()
        probed = asyncio.run(tracker.probe_providers())
        print(f"\nProbed {probed} providers\n")
        for p in tracker.provider_tracker.providers.values():
            if p.status != ProviderStatus.UNKNOWN:
                icon = "✓" if p.status == ProviderStatus.LIVE else "✗"
                print(f"  {icon} {p.name:<14} [{p.status.value}] {p.status_reason}")
        tracker.generate_report(include_providers=True, include_news=False)
        print(f"\nHTML report generated.")

    elif args.action == "discover":
        tools = asyncio.run(tracker.discover_tools())
        print(f"\nDiscovered {len(tools)} GitHub tools\n")
        for t in tools:
            print(f"  ⭐ {t['headline']}")
            print(f"     {t['summary'][:90]}")
            print(f"     {t['url']}\n")

    elif args.action == "audit":
        asyncio.run(async_full_audit(tracker))


if __name__ == "__main__":
    main()
