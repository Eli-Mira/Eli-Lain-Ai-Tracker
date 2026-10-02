"""Summarization module for news items."""

from __future__ import annotations

import json
import logging
from urllib.parse import urlsplit
from datetime import datetime, timezone
from typing import Any

import httpx

from tracker_core.schema import NewsItem


logger = logging.getLogger(__name__)

DEFAULT_API_URL = "http://localhost:3001/v1/chat/completions"

# Enough headroom for a reasoning model to think and still return the JSON array.
MAX_COMPLETION_TOKENS = 4096
DEFAULT_COMPLETION_TOKENS = 1000

REASONING_MARKERS = ("minicpm", "deepseek", "qwq", "r1", "thinking", "reason")

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _is_loopback(url: str) -> bool:
    """True when the endpoint is on this machine and needs no credential."""
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return False
    return host.lower() in _LOOPBACK_HOSTS



class Summarizer:
    """Generate summaries for news items using LLM."""
    
    def __init__(self, config: dict[str, Any] | None = None):
        """
        Args:
            config: Configuration dict with keys:
                - model: Model name (default: "free-tier")
                - api_key: API key (optional, uses env if not provided)
                - base_url: API base URL (optional)
        """
        self.config = config or {}
        self.model = self.config.get("model", "free-tier")
        self.api_key = self.config.get("api_key")
        self.base_url = self.config.get("base_url")
        # A keyless endpoint must be LOCAL. Ollama and FreeLLMAPI both serve an
        # OpenAI-compatible /v1/chat/completions on loopback with no credential,
        # which is how this project stays free. A remote endpoint with no key is
        # still refused: that would be an uncredentialed call to a third party.
        self.endpoint = self.base_url or DEFAULT_API_URL
        self.keyless_endpoint = _is_loopback(self.endpoint)
        # Reasoning-style local models need a larger completion budget and reject
        # an explicit low temperature.
        self.model_reasoning = any(
            marker in str(self.model).lower() for marker in REASONING_MARKERS)
        self.max_tokens = self.config.get(
            "max_tokens", MAX_COMPLETION_TOKENS if self.model_reasoning else DEFAULT_COMPLETION_TOKENS)
    
    async def summarize_items(
        self,
        items: list[NewsItem],
        batch_size: int = 5
    ) -> list[NewsItem]:
        """
        Generate summaries for news items in batches.
        
        Args:
            items: List of NewsItem to summarize
            batch_size: Number of items to summarize per API call
            
        Returns:
            List of NewsItem with summaries filled in
        """
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Build prompt
            prompt = self._build_prompt(batch)
            
            # Call summarization API
            summary = await self._call_llm(prompt)
            
            # Validate the complete batch before mutating any observed item.
            # Raw lines, partial arrays and wrong types are not summaries.
            try:
                summaries = json.loads(summary)
                if not isinstance(summaries, list) or len(summaries) != len(batch):
                    raise ValueError("invalid batch")
                for row in summaries:
                    if not isinstance(row, dict) or any(
                        not isinstance(row.get(key), str) or not row[key].strip()
                        for key in ("summary", "dedup_key")
                    ):
                        raise ValueError("invalid summary")
            except (ValueError, TypeError):
                raise RuntimeError("AI summarization response invalid") from None
            for item, row in zip(batch, summaries):
                item.summary = row["summary"].strip()
                item.dedup_key = row["dedup_key"].strip()

            logger.info(f"Summarized items {i+1}-{min(i+batch_size, len(items))}/{len(items)}")
        
        return items
    
    def _build_prompt(self, items: list[NewsItem]) -> str:
        """Build prompt for summarization."""
        item_texts = []
        for item in items:
            text = f"- {item.title}"
            if item.summary:
                text += f"\n  Context: {item.summary[:200]}"
            if item.category:
                text += f"\n  Category: {item.category.value}"
            item_texts.append(text)
        
        prompt = f"""You are a news aggregator. Summarize each item in 1-2 sentences maximum.

Items to summarize:
{chr(10).join(item_texts)}

Return JSON array with objects containing:
- "summary": brief 1-2 sentence summary
- "dedup_key": short key for deduplication (first 30 chars of title, lowercased)

Example output:
[{{"summary": "OpenAI released GPT-4o, a new multimodal model...", "dedup_key": "openai releases gpt-4o"}}, ...]

Only return valid JSON, no markdown formatting."""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API for summarization."""
        # Defaults to the local router; both it and Ollama are keyless.
        api_url = self.endpoint
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            # Some local models (verified: minicpm5-2b-q8) spend the entire
            # budget on internal reasoning tokens and then return EMPTY content
            # with finish_reason "length", for a 167-token prompt. That is not a
            # malformed response, it is a starved budget - so the budget has to
            # leave room for reasoning plus the JSON array. Costs nothing: local
            # inference is not billed per token.
            "max_tokens": self.max_tokens,
        }
        # Reasoning models reject an explicit temperature of 0.3 on some
        # backends; only send it when it is meaningful.
        if not self.model_reasoning:
            payload["temperature"] = 0.3
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                if choice.get("finish_reason", "stop") != "stop" or choice["message"].get("refusal"):
                    raise ValueError("incomplete response")
                content = choice["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("invalid response content")
                return content
        except Exception as e:
            logger.error("Summarization unavailable (%s); preserving observed news", type(e).__name__)
            raise RuntimeError("AI summarization unavailable") from None
    
    def summarize_manually(self, items: list[NewsItem]) -> list[NewsItem]:
        """Fallback: generate simple summaries without LLM."""
        for item in items:
            if not item.summary:
                item.summary = "Title excerpt (not AI summary): " + item.title
        return items


async def summarize_news(
    items: list[NewsItem],
    config: dict[str, Any] | None = None
) -> list[NewsItem]:
    """
    Main function to summarize news items.
    
    Args:
        items: List of NewsItem to summarize
        config: Optional configuration
        
    Returns:
        List of NewsItem with summaries
    """
    summarizer = Summarizer(config)
    # Opt-in stays opt-in. An EMPTY config means the caller never enabled AI
    # summaries (the CLI default, and every non-opt-in path), and must make zero
    # requests - that guarantee is load-bearing, so a reachable default endpoint
    # must not switch it on by itself.
    #
    # "The endpoint needs no credential" and "we are allowed to call it" are two
    # different questions. Answering the first must not silently answer the second.
    if not config:
        return summarizer.summarize_manually(items)
    # Within an explicitly enabled setup, a keyless LOCAL endpoint is legitimate
    # (Ollama/FreeLLMAPI need no credential). A keyless REMOTE endpoint is not,
    # because that would be an uncredentialed call to a third party.
    if not summarizer.api_key and not summarizer.keyless_endpoint:
        return summarizer.summarize_manually(items)
    
    # Try LLM summarization first
    try:
        items = await summarizer.summarize_items(items)
    except Exception as e:
        logger.warning("LLM summarization failed (%s); using observed excerpts", type(e).__name__)
        items = summarizer.summarize_manually(items)
    
    return items
