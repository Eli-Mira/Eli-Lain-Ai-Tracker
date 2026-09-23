"""Source adapters for the news tracker."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from dotenv import load_dotenv
load_dotenv()  # Load .env from cwd

import httpx

from tracker_core.schema import NewsItem, SourceType, Category
from tracker_core.pipeline.fetcher import HTTPFetcher, FetchResult


logger = logging.getLogger(__name__)


class BaseNewsAdapter(ABC):
    """Base adapter for news sources."""
    
    name: str = "base"
    source_type: SourceType = SourceType.GITHUB
    
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.fetcher = HTTPFetcher(
            timeout=self.config.get("timeout", 30.0),
            rate_limit_delay=self.config.get("rate_limit_delay", 1.0)
        )
    
    @abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch raw items from source."""
        ...
    
    @abstractmethod
    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse a single raw item into NewsItem."""
        ...
    
    async def fetch_all(self) -> list[NewsItem]:
        """Fetch and parse all items from source."""
        raw_items = await self.fetch()
        items = []
        for raw in raw_items:
            try:
                item = self.parse_item(raw)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse item from {self.name}: {e}")
        return items
    
    def get_fetch_url(self) -> str:
        """Return base URL for caching."""
        return f"https://{self.name}"


class GitHubAdapter(BaseNewsAdapter):
    """Fetch from GitHub releases and trending repos."""
    
    name = "github"
    source_type = SourceType.GITHUB
    
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.topics = (config or {}).get("topics", ["ai", "llm", "gpt", "claude", "openai", "anthropic", "meta-llama"])
        self.orgs = (config or {}).get("orgs", [
            "openai", "anthropic-ai", "google-deepmind", "mistralai",
            "meta-llama", "microsoft", "cerebras", "groq", "togethercomputer"
        ])
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TrackerCore/1.0"
        }
        # Read token from config or environment
        token = (config or {}).get("github_token") or os.getenv("GITHUB_TOKEN")
        if token:
            self._headers["Authorization"] = f"token {token}"
    
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch recent releases from tracked orgs and trending repos."""
        items = []

        # PRIMARY: Trending repos search (catches activity releases miss)
        try:
            url = "https://api.github.com/search/repositories?q=ai+llm&sort=updated&per_page=15"
            result = await self.fetcher.fetch(url, headers=self._headers)

            if result.success and result.status_code == 200:
                data = json.loads(result.content)
                for repo in data.get("items", []):
                    items.append({
                        "source": "github",
                        "title": f"{repo.get('full_name', '')} — {repo.get('description', 'No description')}",
                        "url": repo.get("html_url", ""),
                        "published_date": repo.get("updated_at"),
                        "body": repo.get("description", "")[:300],
                        "raw": repo
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch trending repos: {e}")

        # SECONDARY: Per-repo releases (org-wide releases endpoint doesn't exist)
        for org in self.orgs:
            try:
                # Enumerate repos for this org
                url = f"https://api.github.com/orgs/{org}/repos?per_page=100&type=public"
                result = await self.fetcher.fetch(url, headers=self._headers)

                if not (result.success and result.status_code == 200):
                    logger.warning(f"Failed to enumerate repos for {org}: HTTP {result.status_code}")
                    continue

                try:
                    repos = json.loads(result.content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse repo list for {org}")
                    continue

                for repo in repos[:10]:  # Limit repos per org
                    repo_name = repo.get("full_name", "")
                    if not repo_name:
                        continue

                    try:
                        releases_url = f"https://api.github.com/repos/{repo_name}/releases/latest"
                        releases_result = await self.fetcher.fetch(releases_url, headers=self._headers)

                        # 404 = no releases on this repo (common), skip silently
                        if releases_result.status_code == 404:
                            continue
                        if not (releases_result.success and releases_result.status_code == 200):
                            continue

                        release = json.loads(releases_result.content)
                        items.append({
                            "source": "github",
                            "title": release.get("name") or release.get("tag_name", repo_name),
                            "url": release.get("html_url", ""),
                            "published_date": release.get("published_at"),
                            "body": release.get("body", "")[:500],
                            "raw": release
                        })
                    except Exception:
                        # Per-repo failures are expected (no releases, rate limits)
                        pass

            except Exception as e:
                logger.debug(f"Org {org} enumeration failed: {e}")

        return items
    
    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse raw GitHub item into NewsItem."""
        title = raw.get("title", "Untitled")
        
        # Determine category
        category = self._classify_category(title, raw.get("body", ""))
        
        return NewsItem(
            source=SourceType.GITHUB,
            title=title,
            url=raw.get("url", ""),
            published_date=datetime.fromisoformat(raw["published_date"].replace("Z", "+00:00")) if raw.get("published_date") else None,
            category=category,
            raw_data={"source": "github", "item": raw}
        )
    
    def _classify_category(self, title: str, body: str) -> Category | None:
        """Classify GitHub item into category."""
        text = f"{title} {body}".lower()
        
        if any(kw in text for kw in ["model", "release", "gpt", "claude", "gemini", "llama"]):
            return Category.MODEL_RELEASE
        if any(kw in text for kw in ["tool", "library", "sdk", "framework", "api"]):
            return Category.TOOL_LAUNCH
        if any(kw in text for kw in ["funding", "raise", "series a", "series b", "valuation"]):
            return Category.FUNDING
        return Category.TOOL_LAUNCH  # Default to tool launch


class RedditAdapter(BaseNewsAdapter):
    """Fetch from Reddit subreddits via RSS or PRAW."""

    name = "reddit"
    source_type = SourceType.REDDIT

    SUBREDDITS = [
        "MachineLearning",
        "LocalLLaMA",
        "artificial",
        "OpenAI",
        "ChatGPT",
        "GenerativeAI"
    ]

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._use_praw = False
        self._praw_instance = None

        client_id = (config or {}).get("reddit_client_id")
        client_secret = (config or {}).get("reddit_client_secret")
        user_agent = (config or {}).get("reddit_user_agent", "ai-tech-news-tracker/1.0")

        if client_id and client_secret:
            try:
                import praw
                self._praw_instance = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                    check_for_async=False
                )
                self._use_praw = True
                logger.info("Reddit adapter using PRAW (authenticated)")
            except ImportError:
                logger.warning("praw not installed, falling back to RSS")
                self._use_praw = False
        else:
            logger.info("Reddit adapter using RSS (anonymous, rate-limited)")

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch posts from tracked subreddits."""
        items = []

        if self._use_praw and self._praw_instance:
            items = await self._fetch_praw()
        else:
            items = await self._fetch_rss()

        return items

    async def _fetch_praw(self) -> list[dict[str, Any]]:
        """Fetch using PRAW for higher rate limits."""
        import asyncio
        items = []

        loop = asyncio.get_event_loop()

        for subreddit in self.SUBREDDITS:
            try:
                sub = self._praw_instance.subreddit(subreddit)
                posts = await loop.run_in_executor(
                    None,
                    lambda s=sub: list(s.hot(limit=10))
                )
                for post in posts:
                    items.append({
                        "source": "reddit",
                        "title": post.title,
                        "url": f"https://reddit.com{post.permalink}",
                        "published_date": datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                        "body": post.selftext[:500] if post.selftext else "",
                        "author": post.author.name if post.author else "unknown",
                        "subreddit": subreddit,
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "raw": {"id": post.id, "subreddit": subreddit}
                    })
            except Exception as e:
                logger.warning(f"PRAW fetch failed for r/{subreddit}: {e}")

        return items

    async def _fetch_rss(self) -> list[dict[str, Any]]:
        """Fetch using RSS feeds (anonymous, rate-limited)."""
        import feedparser
        items = []

        for subreddit in self.SUBREDDITS:
            try:
                # Add delay between requests to respect rate limit
                await asyncio.sleep(1)
                url = f"https://www.reddit.com/r/{subreddit}/.rss"
                result = await self.fetcher.fetch(url)

                if result.success and result.status_code == 200:
                    feed = feedparser.parse(result.content)

                    for entry in feed.entries[:10]:
                        items.append({
                            "source": "reddit",
                            "title": entry.get("title", "Untitled"),
                            "url": entry.get("link", ""),
                            "published_date": entry.get("published_parsed"),
                            "body": entry.get("summary", "")[:500],
                            "author": entry.get("author", "unknown"),
                            "subreddit": subreddit,
                            "raw": entry
                        })
            except Exception as e:
                logger.warning(f"RSS fetch failed for r/{subreddit}: {e}")

        return items
    
    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse raw Reddit item into NewsItem."""
        # Convert published date
        pub_date = None
        if raw.get("published_date"):
            try:
                pub_date = datetime(*raw["published_date"][:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        return NewsItem(
            source=SourceType.REDDIT,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            published_date=pub_date,
            category=self._classify_category(raw.get("title", ""), raw.get("body", "")),
            raw_data={"source": "reddit", "subreddit": raw.get("subreddit")}
        )
    
    def _classify_category(self, title: str, body: str) -> Category | None:
        """Classify Reddit post into category."""
        text = f"{title} {body}".lower()
        
        if any(kw in text for kw in ["paper", "arxiv", "research", "study"]):
            return Category.RESEARCH_PAPER
        if any(kw in text for kw in ["model", "gpt", "claude", "llama", "gemini"]):
            return Category.MODEL_RELEASE
        if any(kw in text for kw in ["tool", "lib", "package", "library"]):
            return Category.TOOL_LAUNCH
        if any(kw in text for kw in ["funding", "raise", "money"]):
            return Category.FUNDING
        return Category.DISCUSSION


class HackerNewsAdapter(BaseNewsAdapter):
    """Fetch from Hacker News via Algolia API."""
    
    name = "hackernews"
    source_type = SourceType.HACKERNEWS
    
    KEYWORDS = ["ai", "llm", "gpt", "claude", "openai", "anthropic", "machine learning", "deep learning"]
    
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch recent AI/LLM stories from HN."""
        items = []
        
        # Use Algolia search API
        for keyword in self.KEYWORDS:
            try:
                url = f"https://hn.algolia.com/api/v1/search?query={quote(keyword)}&tags=story&hitsPerPage=10"
                result = await self.fetcher.fetch(url)
                
                if result.success and result.status_code == 200:
                    data = json.loads(result.content)
                    for hit in data.get("hits", []):
                        # Only add if not already in list
                        if not any(i["url"] == hit.get("url", "") for i in items):
                            items.append({
                                "source": "hackernews",
                                "title": hit.get("title", "Untitled"),
                                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                                "published_date": hit.get("created_at_i"),
                                "points": hit.get("points", 0),
                                "comments": hit.get("num_comments", 0),
                                "raw": hit
                            })
            except Exception as e:
                logger.warning(f"Failed to search HN for '{keyword}': {e}")
        
        return items
    
    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse raw HN item into NewsItem."""
        # Convert Unix timestamp
        pub_date = None
        if raw.get("published_date"):
            try:
                pub_date = datetime.fromtimestamp(raw["published_date"], tz=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        return NewsItem(
            source=SourceType.HACKERNEWS,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            published_date=pub_date,
            category=self._classify_category(raw.get("title", "")),
            raw_data={"source": "hackernews", "points": raw.get("points", 0)}
        )
    
    def _classify_category(self, title: str) -> Category | None:
        """Classify HN story into category."""
        text = title.lower()
        
        if any(kw in text for kw in ["paper", "arxiv", "research"]):
            return Category.RESEARCH_PAPER
        if any(kw in text for kw in ["model", "gpt", "claude", "llama"]):
            return Category.MODEL_RELEASE
        if any(kw in text for kw in ["tool", "library", "api", "sdk"]):
            return Category.TOOL_LAUNCH
        return Category.DISCUSSION


class ArXivAdapter(BaseNewsAdapter):
    """Fetch new papers from arXiv."""
    
    name = "arxiv"
    source_type = SourceType.ARXIV
    
    CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.NE"]
    
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch recent papers from arXiv API."""
        items = []
        
        for category in self.CATEGORIES:
            try:
                url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending"
                result = await self.fetcher.fetch(url)
                
                if result.success and result.status_code == 200:
                    import feedparser
                    feed = feedparser.parse(result.content)
                    
                    for entry in feed.entries:
                        items.append({
                            "source": "arxiv",
                            "title": entry.get("title", "Untitled").replace("\\n", " "),
                            "url": entry.get("link", ""),
                            "published_date": entry.get("published_parsed"),
                            "authors": entry.get("authors", []),
                            "summary": entry.get("summary", "")[:500],
                            "raw": entry
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch arXiv category {category}: {e}")
        
        return items
    
    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse raw arXiv item into NewsItem."""
        pub_date = None
        if raw.get("published_date"):
            try:
                pub_date = datetime(*raw["published_date"][:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        return NewsItem(
            source=SourceType.ARXIV,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            published_date=pub_date,
            category=Category.RESEARCH_PAPER,
            summary=raw.get("summary", "")[:300],
            raw_data={"source": "arxiv", "authors": raw.get("authors", [])}
        )


class RSSFeedAdapter(BaseNewsAdapter):
    """Fetch from arbitrary RSS feeds."""
    
    name = "rss"
    source_type = SourceType.NEWS
    
    FEEDS = [
        # AI company blogs
        ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
        ("Anthropic Blog", "https://www.anthropic.com/blog/rss.xml"),
        ("Google AI Blog", "https://blog.research.google/feeds/default/full/"),
        ("Meta AI Blog", "https://ai.meta.com/blog/tag/research/rss/"),
        ("DeepMind Blog", "https://deepmind.google/blog/rss.xml"),
        ("Mistral Blog", "https://mistral.ai/feed/"),
        # Tech news AI sections
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("The Verge AI", "https://www.theverge.com/rss/index.xml"),
        ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
        ("Wired AI", "https://www.wired.com/feed/tag/ai/latest/rss"),
        # Google News RSS (AI & LLM topics)
        ("Google News - AI", "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"),
        ("Google News - LLM", "https://news.google.com/rss/search?q=large+language+model&hl=en-US&gl=US&ceid=US:en"),
        ("Google News - GPT", "https://news.google.com/rss/search?q=gpt+openai&hl=en-US&gl=US&ceid=US:en"),
        ("Google News - Claude", "https://news.google.com/rss/search?q=claude+anthropic&hl=en-US&gl=US&ceid=US:en"),
        ("Google News - Gemini", "https://news.google.com/rss/search?q=gemini+google&hl=en-US&gl=US&ceid=US:en"),
        ("Google News - AI Agents", "https://news.google.com/rss/search?q=ai+agents&hl=en-US&gl=US&ceid=US:en"),
    ]
    
    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.feeds = config.get("feeds", self.FEEDS) if config else self.FEEDS
    
    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch from all RSS feeds."""
        items = []
        
        for name, url in self.feeds:
            try:
                result = await self.fetcher.fetch(url)
                
                if result.success and result.status_code == 200:
                    import feedparser
                    feed = feedparser.parse(result.content)
                    
                    for entry in feed.entries[:5]:  # Limit per feed
                        items.append({
                            "source": "rss",
                            "title": entry.get("title", "Untitled"),
                            "url": entry.get("link", ""),
                            "published_date": entry.get("published_parsed"),
                            "summary": entry.get("summary", "")[:300],
                            "source_name": name,
                            "raw": entry
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch RSS feed '{name}': {e}")
        
        return items
    
    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse raw RSS item into NewsItem."""
        pub_date = None
        if raw.get("published_date"):
            try:
                pub_date = datetime(*raw["published_date"][:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        return NewsItem(
            source=SourceType.NEWS,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            published_date=pub_date,
            category=self._classify_category(raw.get("title", ""), raw.get("summary", "")),
            summary=raw.get("summary", "")[:200],
            raw_data={"source": "rss", "source_name": raw.get("source_name")}
        )
    
    def _classify_category(self, title: str, summary: str) -> Category | None:
        """Classify RSS item into category."""
        text = f"{title} {summary}".lower()
        
        if any(kw in text for kw in ["paper", "research", "study"]):
            return Category.RESEARCH_PAPER
        if any(kw in text for kw in ["model", "release", "launch"]):
            return Category.MODEL_RELEASE
        if any(kw in text for kw in ["tool", "library", "product"]):
            return Category.TOOL_LAUNCH
        if any(kw in text for kw in ["funding", "raise", "acquisition"]):
            return Category.FUNDING
        return Category.DISCUSSION


def get_adapter(source: str, config: dict[str, Any] | None = None) -> BaseNewsAdapter:
    """Factory function to get adapter by source name."""
    adapters = {
        "github": GitHubAdapter,
        "reddit": RedditAdapter,
        "hackernews": HackerNewsAdapter,
        "arxiv": ArXivAdapter,
        "rss": RSSFeedAdapter,
        "huggingface": HuggingFaceAdapter,
    }
    
    adapter_class = adapters.get(source.lower())
    if adapter_class is None:
        raise ValueError(f"Unknown source: {source}")
    
    return adapter_class(config)


class HuggingFaceAdapter(BaseNewsAdapter):
    """Fetch trending models from Hugging Face."""

    name = "huggingface"
    source_type = SourceType.HUGGINGFACE

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch trending models from Hugging Face."""
        items = []

        # Fetch trending models from HF models page
        try:
            url = "https://huggingface.co/models?sort=trending"
            result = await self.fetcher.fetch(url)
            if result.success and result.status_code == 200:
                import re
                # Parse model links - only actual model paths
                model_links = re.findall(r'href="/([A-Za-z][A-Za-z0-9._-]+/[A-Za-z][A-Za-z0-9._-]+)"', result.content)
                seen = set()
                for link in model_links[:30]:
                    # Skip navigation/settings pages
                    skip = ["join", "inference", "settings", "docs", "enterprise", "pricing", "blog", "tasks", "datasets", "spaces"]
                    parts = link.split("/")
                    if parts[0].lower() in skip:
                        continue
                    if link.count("/") == 1 and link not in seen and len(parts[0]) > 1:
                        seen.add(link)
                        items.append({
                            "source": "huggingface",
                            "title": link,
                            "url": f"https://huggingface.co/{link}",
                            "published_date": None,
                            "body": f"Trending model on Hugging Face: {link}",
                            "raw": {"model_id": link}
                        })
        except Exception as e:
            logger.warning(f"HuggingFace models fetch failed: {e}")

        # Fetch papers
        try:
            url = "https://huggingface.co/papers"
            result = await self.fetcher.fetch(url)
            if result.success and result.status_code == 200:
                import re
                paper_links = re.findall(r'href="/papers/([A-Za-z0-9._-]+)"', result.content)
                seen = set()
                for paper_id in paper_links[:10]:
                    if paper_id not in seen:
                        seen.add(paper_id)
                        paper_id_clean = paper_id.replace(".", " ").replace("-", " ").title()
                        items.append({
                            "source": "huggingface_paper",
                            "title": paper_id_clean,
                            "url": f"https://huggingface.co/papers/{paper_id}",
                            "published_date": None,
                            "body": f"Paper on Hugging Face: {paper_id_clean}",
                            "raw": {"paper_id": paper_id}
                        })
        except Exception as e:
            logger.warning(f"HuggingFace papers fetch failed: {e}")

        return items

    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse HF item into NewsItem."""
        source = raw.get("source", "")
        category = Category.RESEARCH_PAPER if "paper" in source else Category.TOOL_LAUNCH

        return NewsItem(
            source=SourceType.HUGGINGFACE,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            category=category,
            raw_data={"source": source}
        )


class PapersWithCodeAdapter(BaseNewsAdapter):
    """Fetch from Papers with Code."""

    name = "paperswithcode"
    source_type = SourceType.PAPERSWITHCODE

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch trending papers from Papers with Code."""
        items = []

        try:
            url = "https://paperswithcode.com/"
            result = await self.fetcher.fetch(url)
            if result.success and result.status_code == 200:
                import re
                # Try multiple patterns for paper titles
                titles = re.findall(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</a>', result.content)
                if not titles:
                    titles = re.findall(r'<h2[^>]*>([^<]+)</h2>', result.content)
                if not titles:
                    titles = re.findall(r'<a[^>]*href="/paper/[^"]*"[^>]*>([^<]+)</a>', result.content)

                seen = set()
                for title in titles[:15]:
                    title_clean = title.strip()
                    if title_clean in seen or len(title_clean) < 10:
                        continue
                    seen.add(title_clean)

                    items.append({
                        "source": "paperswithcode",
                        "title": title_clean,
                        "url": "https://paperswithcode.com/",
                        "published_date": None,
                        "body": title_clean,
                        "raw": {"title": title_clean}
                    })
        except Exception as e:
            logger.warning(f"PapersWithCode fetch failed: {e}")

        return items

    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse PapersWithCode item."""
        return NewsItem(
            source=SourceType.PAPERSWITHCODE,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            category=Category.RESEARCH_PAPER,
            raw_data={"source": "paperswithcode"}
        )


class YouTubeAdapter(BaseNewsAdapter):
    """Fetch from YouTube channels via RSS feeds with retry + Data API v3 fallback."""

    name = "youtube"
    source_type = SourceType.YOUTUBE

    # Channels to track (name, channel_id)
    CHANNELS = [
        ("AI Explained", "UCR9jFEs7M_CudJNqT4p0DRg"),
        ("Two Minute Papers", "UCbf0DoKEXt0F8Jd8S-7p0DRg"),
        ("Yannic Kilcher", "UCZHmQk67mSJb09nC0F-9HDA"),
    ]

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch from YouTube with retry + fallback."""
        items = []
        youtube_key = self.config.get("youtube_api_key") if self.config else None

        for name, channel_id in self.CHANNELS:
            channel_items = await self._fetch_channel(name, channel_id, youtube_key)
            if channel_items:
                items.extend(channel_items)

        return items

    async def _fetch_channel(self, name: str, channel_id: str, youtube_key: str | None) -> list[dict[str, Any]]:
        """Fetch a single channel — RSS first, Data API fallback."""
        # 1. Try RSS feed with retries
        items = await self._fetch_rss(name, channel_id)
        if items:
            return items

        # 2. If RSS fails and we have API key, fallback to Data API
        if youtube_key:
            return await self._fetch_via_api(name, channel_id, youtube_key)

        # 3. Both failed — soft skip this cycle
        logger.warning(f"YouTube source {name} unavailable this cycle (RSS failed, no API key)")
        return []

    async def _fetch_rss(self, name: str, channel_id: str, max_retries: int = 2) -> list[dict[str, Any]]:
        """Fetch RSS with retry and backoff."""
        import feedparser

        for attempt in range(max_retries + 1):
            try:
                url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                result = await self.fetcher.fetch(url)

                if result.success and result.status_code == 200:
                    feed = feedparser.parse(result.content)
                    if feed.entries:
                        items = []
                        for entry in feed.entries[:5]:
                            items.append({
                                "source": "youtube",
                                "title": f"[{name}] {entry.get('title', 'Untitled')}",
                                "url": entry.get("link", ""),
                                "published_date": entry.get("published_parsed"),
                                "author": name,
                                "raw": entry
                            })
                        return items

                # 429 or empty — backoff and retry
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.warning(f"RSS attempt {attempt+1} for {name} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

        return []

    async def _fetch_via_api(self, name: str, channel_id: str, api_key: str) -> list[dict[str, Any]]:
        """Fallback: YouTube Data API v3 channels.list + playlistItems.list."""
        try:
            # Step 1: Get channel's uploads playlist
            channels_url = (
                f"https://www.googleapis.com/youtube/v3/channels"
                f"?part=contentDetails&id={channel_id}&key={api_key}"
            )
            result = await self.fetcher.fetch(channels_url)

            if not result.success or result.status_code != 200:
                return []

            data = json.loads(result.content)
            items_list = data.get("items", [])
            if not items_list:
                return []

            uploads_id = items_list[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
            if not uploads_id:
                return []

            # Step 2: Fetch recent videos from uploads playlist
            playlist_url = (
                f"https://www.googleapis.com/youtube/v3/playlistItems"
                f"?part=snippet&maxResults=5&playlistId={uploads_id}&key={api_key}"
            )
            result = await self.fetcher.fetch(playlist_url)

            if not result.success or result.status_code != 200:
                return []

            data = json.loads(result.content)
            api_items = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                video_title = snippet.get("title", "Untitled")
                video_id = snippet.get("resourceId", {}).get("videoId", "")
                published = snippet.get("publishedAt", "")

                api_items.append({
                    "source": "youtube",
                    "title": f"[{name}] {video_title}",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "published_date": published,
                    "author": name,
                    "raw": snippet
                })

            return api_items

        except Exception as e:
            logger.warning(f"Data API fallback for {name} failed: {e}")
            return []

    def parse_item(self, raw: dict[str, Any]) -> NewsItem:
        """Parse YouTube item."""
        pub_date = None
        raw_date = raw.get("published_date")

        # RSS format: time.struct_time
        if raw_date and hasattr(raw_date, "tm_year"):
            try:
                pub_date = datetime(*raw_date[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        # API format: ISO string "2024-01-01T00:00:00Z"
        elif raw_date and isinstance(raw_date, str):
            try:
                pub_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except ValueError:
                pass

        return NewsItem(
            source=SourceType.YOUTUBE,
            title=raw.get("title", "Untitled"),
            url=raw.get("url", ""),
            published_date=pub_date,
            category=Category.DISCUSSION,
            raw_data={"source": "youtube"}
        )


def get_all_adapters(config: dict[str, Any] | None = None) -> list[BaseNewsAdapter]:
    """Get all configured adapters."""
    return [
        GitHubAdapter(config),
        RedditAdapter(config),
        HackerNewsAdapter(config),
        ArXivAdapter(config),
        RSSFeedAdapter(config),
        HuggingFaceAdapter(config),
        YouTubeAdapter(config),
    ]
