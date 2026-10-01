"""Summarization module for news items."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from tracker_core.schema import NewsItem


logger = logging.getLogger(__name__)


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
            
            # Parse and assign summaries
            try:
                summaries = json.loads(summary)
                for j, item_summary in enumerate(summaries):
                    if j < len(batch):
                        batch[j].summary = item_summary.get("summary", "")
                        batch[j].dedup_key = item_summary.get("dedup_key", "")
            except json.JSONDecodeError:
                # Fallback: use raw summary
                lines = summary.strip().split("\n")
                for j, line in enumerate(lines[:len(batch)]):
                    if j < len(batch):
                        batch[j].summary = line.strip()
            
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
        # Use FreeLLMAPI (user's local backend) or default to free-tier model
        api_url = self.base_url or "http://localhost:3001/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error("Summarization unavailable (%s); preserving observed news", type(e).__name__)
            raise RuntimeError("AI summarization unavailable") from e
    
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
    if not summarizer.api_key:
        return summarizer.summarize_manually(items)
    
    # Try LLM summarization first
    try:
        items = await summarizer.summarize_items(items)
    except Exception as e:
        logger.warning(f"LLM summarization failed, using manual: {e}")
        items = summarizer.summarize_manually(items)
    
    return items
