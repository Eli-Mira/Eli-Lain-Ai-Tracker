"""Tests for news tracker summarizer."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from news_tracker.summarizer import Summarizer
from tracker_core.schema import NewsItem, SourceType


class TestSummarizer:
    """Tests for summarizer."""
    
    def test_build_prompt(self):
        """Test prompt building."""
        summarizer = Summarizer()
        
        items = [
            NewsItem(source=SourceType.GITHUB, title="GPT-4 released", url="https://example.com/1"),
            NewsItem(source=SourceType.REDDIT, title="AI discussion", url="https://example.com/2"),
        ]
        
        prompt = summarizer._build_prompt(items)
        
        assert "GPT-4 released" in prompt
        assert "AI discussion" in prompt
        assert "JSON" in prompt.upper()
    
    @pytest.mark.asyncio
    async def test_summarize_manually(self):
        """Test manual summarization fallback."""
        summarizer = Summarizer()
        
        items = [
            NewsItem(source=SourceType.GITHUB, title="New AI Model Released Today", url="https://example.com/1"),
        ]
        
        result = summarizer.summarize_manually(items)
        
        assert result[0].summary is not None
        assert len(result[0].summary) > 0
    
    @pytest.mark.asyncio
    async def test_call_llm_success(self):
        """Test LLM call with successful response."""
        summarizer = Summarizer(config={"api_key": "test-key", "base_url": "http://test.com/v1"})
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '[{"summary": "Test summary", "dedup_key": "test"}]'}}]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await summarizer._call_llm("Test prompt")
            
            assert "Test summary" in result
    
    @pytest.mark.asyncio
    async def test_call_llm_failure(self):
        """Test LLM call with failure."""
        summarizer = Summarizer()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API error")
            
            # Failure is not a successful AI response; the public wrapper supplies a labelled excerpt.
            with pytest.raises(RuntimeError, match="AI summarization unavailable"):
                await summarizer._call_llm("Test prompt")


@pytest.mark.asyncio
async def test_summarize_news_function():
    """Test the main summarize_news function."""
    from news_tracker.summarizer import summarize_news
    
    items = [
        NewsItem(source=SourceType.GITHUB, title="Test AI Model", url="https://example.com/1"),
    ]
    
    result = await summarize_news(items)
    
    assert len(result) == 1
    assert result[0].summary is not None
