"""Main entry point for AI/Tech News Tracker.

Wires together: health tracking, scoring/categorization, SQLite persistence,
breaking news push, and multi-channel notifications.
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
from tracker_core.scheduler import TrackerScheduler
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


def _apply_importance_score(item: NewsItem) -> NewsItem:
    """Apply importance scoring to an item."""
    importance = score_importance(item)
    # Blend importance with relevance (70% relevance, 30% importance)
    item.relevance_score = (item.relevance_score * 0.7) + (importance * 0.3)
    return item


logger = logging.getLogger(__name__)


class NewsTracker:
    """Main tracker for AI/tech news."""

    def __init__(
        self,
        data_dir: Path | str = "./data",
        cache_dir: Path | str = "./.cache",
        reports_dir: Path | str = "./reports",
        theme: str = "default",
        summarizer_config: dict[str, Any] | None = None,
        failure_threshold: int = 3,
    ):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.reports_dir = Path(reports_dir)
        self.theme = theme
        self.summarizer_config = summarizer_config or {}

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

        # Notifier for alerts — load all credentials, MultiNotifier picks what it needs
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

        # Breaking news threshold (score above this triggers immediate push)
        self.breaking_threshold = 0.7

        self.last_run_date: datetime | None = None

    async def fetch_all(self) -> list[NewsItem]:
        """Fetch news from all sources with circuit breaker."""
        logger.info("Fetching news from all sources...")

        adapters = get_all_adapters()
        all_items: list[NewsItem] = []

        for adapter in adapters:
            # Skip circuit-broken sources
            if not self.health.is_source_enabled(adapter.name):
                logger.info(f"Skipping {adapter.name} (circuit broken)")
                continue

            try:
                logger.info(f"Fetching from {adapter.name}...")
                items = await adapter.fetch_all()

                if items:
                    all_items.extend(items)
                    self.health.record_success(adapter.name, len(items))
                else:
                    # Empty result counts as failure for circuit breaker
                    self.health.record_failure(adapter.name, "Empty result")

            except Exception as e:
                logger.error(f"Failed to fetch from {adapter.name}: {e}")
                self.health.record_failure(adapter.name, str(e))

        logger.info(f"Total fetched: {len(all_items)} items")

        # Persist health state
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
        """Process items: deduplicate, summarize, score, categorize, importance."""
        context: dict[str, Any] = {}

        # Deduplicate
        logger.info("Deduplicating...")
        unique_items, dedup_stats = deduplicate_and_filter(items)
        context["dedup"] = dedup_stats
        logger.info(f"  After dedup: {len(unique_items)} items")

        # Summarize
        logger.info("Summarizing...")
        summarized_items = await summarize_news(unique_items, self.summarizer_config)

        # Score and categorize (#2 + #3)
        logger.info("Scoring and categorizing...")
        scored_items = score_and_categorize(summarized_items)

        # Apply importance scoring (#8 Phase 1)
        logger.info("Applying importance scoring...")
        scored_items = [_apply_importance_score(item) for item in scored_items]

        # Filter by relevance
        relevant_items = [item for item in scored_items if item.is_relevant]
        context["relevant_count"] = len(relevant_items)

        return relevant_items, context

    def _split_breaking_news(self, items: list[NewsItem]) -> tuple[list[NewsItem], list[NewsItem]]:
        """Split items into breaking news and regular digest."""
        breaking = []
        regular = []
        for item in items:
            if item.relevance_score >= self.breaking_threshold:
                breaking.append(item)
            else:
                regular.append(item)
        return breaking, regular

    async def push_breaking_news(self, items: list[NewsItem]) -> bool:
        """Push breaking news items immediately via notification."""
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

        # Fetch
        items = await self.fetch_all()

        # Process
        processed_items, context = await self.process(items)

        # Save to SQLite
        inserted = self.sqlite.save_items(processed_items)
        context["inserted"] = inserted

        # Split breaking news from digest
        breaking_items, regular_items = self._split_breaking_news(processed_items)
        context["breaking_count"] = len(breaking_items)
        context["regular_count"] = len(regular_items)

        # Push breaking news immediately
        if breaking_items and push_breaking:
            await self.push_breaking_news(breaking_items)

        logger.info(
            f"Completed: {inserted} new items, "
            f"{len(breaking_items)} breaking, {len(regular_items)} regular"
        )

        return {
            "date": run_date.isoformat(),
            "total_fetched": len(items),
            "breaking": len(breaking_items),
            "regular": len(regular_items),
            "health_table": self.health.get_health_table(),
            **context,
        }

    def generate_report(
        self,
        date: datetime | None = None,
        output_path: Path | str | None = None,
        group_by_cat: bool = True,
    ) -> str:
        """Generate HTML report for a specific date."""
        run_date = date or self.last_run_date or datetime.now(timezone.utc)

        # Load items from SQLite
        items_raw = self.sqlite.get_items(days=1)

        # Group by category
        if group_by_cat and items_raw:
            items_by_category = {}
            for item in items_raw:
                cat = item.get("category", "unknown")
                items_by_category.setdefault(cat, []).append(item)
        else:
            items_by_category = {"all": items_raw}

        api_items = []
        news_items = []

        for item in items_raw:
            news_items.append({
                "headline": item.get("title", ""),
                "source": item.get("source", "unknown"),
                "summary": item.get("summary") or "",
                "url": item.get("url", "#"),
            })

        output_path = output_path or self.reports_dir / f"news_{run_date.strftime('%Y%m%d')}.html"

        html = self.reporter.render(
            api_items=api_items,
            news_items=news_items,
            report_date=run_date.strftime("%Y-%m-%d"),
            generated_at=datetime.now(timezone.utc).strftime("%H:%M UTC"),
            persona_image_url=None,
        )

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(html, encoding="utf-8")
            logger.info(f"Report saved to {output_path}")

        return html

    def list_recent(self, days: int = 7) -> list[dict]:
        """List recent news items."""
        return self.sqlite.get_items(days=days, limit=50)

    def get_weekly_summary(self, weeks: int = 1) -> dict[str, Any]:
        """Get weekly summary."""
        return self.sqlite.get_weekly_summary(weeks=weeks)

    def get_health_table(self) -> list[dict[str, Any]]:
        """Get source health table."""
        return self.health.get_health_table()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="AI/Tech News Tracker")
    parser.add_argument(
        "action",
        choices=["run", "report", "list", "today", "health", "summary"],
        help="Action to perform",
    )
    parser.add_argument("--theme", choices=["default", "lain"], default="default", help="Report theme")
    parser.add_argument("--days", type=int, default=7, help="Days to look back for list action")
    parser.add_argument("--date", help="Specific date for report (YYYY-MM-DD)")
    parser.add_argument("--data-dir", default="./data", help="Data directory")
    parser.add_argument("--reports-dir", default="./reports", help="Reports directory")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create tracker
    tracker = NewsTracker(
        data_dir=args.data_dir,
        reports_dir=args.reports_dir,
        theme=args.theme,
    )

    # Execute action
    if args.action == "run":
        result = asyncio.run(tracker.run())
        print(f"Run complete:")
        print(f"  Total fetched: {result['total_fetched']}")
        print(f"  Relevant: {result['relevant_count']}")
        print(f"  Breaking: {result['breaking']}")

    elif args.action == "report":
        date = None
        if args.date:
            date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        html = tracker.generate_report(date=date)
        print(f"Report generated ({len(html)} bytes)")

    elif args.action == "list":
        items = tracker.list_recent(days=args.days)
        print(f"\nRecent news ({len(items)} items):")
        print("-" * 80)
        for item in items:
            cat = item.get("category", "unknown")
            score = item.get("relevance_score", 0)
            print(f"[{item['source']}] ({cat}, {score:.2f})")
            print(f"  {item['title']}")
            if item.get("summary"):
                print(f"  {item['summary'][:100]}")
            print()

    elif args.action == "today":
        try:
            result = asyncio.run(tracker.run())
            tracker.generate_report()
            print(f"Today's tracker complete: {result['relevant_count']} relevant items")
            
            # Send a test notification to verify channels work
            test_msg = (
                f"🔔 Eli Lain AI Tracker — test notification\n"
                f"Run complete: {result['relevant_count']} items fetched, "
                f"{result.get('breaking', 0)} breaking, {result.get('regular', 0)} regular"
            )
            test_result = asyncio.run(tracker.notifier.send(test_msg))
            print(f"Test notification sent: {test_result}")
        except Exception as e:
            print(f"ERROR: {e}")
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
        print(f"\nWeekly Summary ({summary['total_items']} items)")
        print("\nTop Categories:")
        for cat in summary["top_categories"]:
            print(f"  {cat['category']}: {cat['count']}")
        print("\nTop Sources:")
        for src in summary["top_sources"]:
            print(f"  {src['source']}: {src['count']}")


if __name__ == "__main__":
    main()
