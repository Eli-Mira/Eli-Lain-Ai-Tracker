"""Prober for testing freellmapi providers."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

import httpx

from .models import FreeProvider, ProviderProbeResult, ProviderStatus


logger = logging.getLogger(__name__)


# Default lightweight test prompts per provider category
DEFAULT_TEST_PAYLOAD = {
    "messages": [{"role": "user", "content": "1"}],
    "max_tokens": 5,
}

# Best lightweight model per platform for low-cost probing
LIGHTWEIGHT_MODELS = {
    "cloudflare": "@cf/qwen/qwen3-30b-a3b-fp8",
    "groq": "llama-3.1-8b-instant",
    "google": "gemini-2.0-flash-exp",
    "reka": "reka-flash",
    "mistral": "mistral-small-latest",
    "cohere": "command-r-08-2024",
    "huggingface": "meta-llama/Llama-3.2-3B-Instruct",
    "openrouter": "google/gemini-2.0-flash-exp:free",
    "cerebras": "llama3.1-8b",
    "nvidia": "meta/llama-3.1-8b-instruct",
    "zhipu": "glm-4-flash",
    "custom": "MiniMax-Text-01",
}


class AutoProber:
    """Probe freellmapi providers with lightweight requests."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        api_key: str | None = None,
        timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        # Use env var or default from freellmapi settings
        self.api_key = api_key or os.getenv(
            "FREELLMAPI_API_KEY",
            "freellmapi-3ca5aa78c8e314ef2b93cc1d44874178c944a709c783b241"
        )
        self.timeout = timeout
    
    async def probe_provider(
        self,
        provider: FreeProvider,
        model: str | None = None,
    ) -> ProviderProbeResult:
        """Probe a single provider with a minimal request."""
        # Pick model
        test_model = model or provider.probe_model or LIGHTWEIGHT_MODELS.get(provider.platform)
        if not test_model:
            return ProviderProbeResult(
                provider_platform=provider.platform,
                success=False,
                model_tested="none",
                error_type="config",
                error_message=f"No test model configured for platform {provider.platform}",
            )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": test_model,
            "messages": [{"role": "user", "content": "1"}],
            "max_tokens": 5,
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Success
                if response.status_code == 200:
                    # Extract quota headers if present
                    remaining = self._extract_remaining(response.headers)
                    limit = self._extract_limit(response.headers)
                    reset_at = response.headers.get("x-ratelimit-reset") or response.headers.get("x-ratelimit-reset-requests")
                    
                    return ProviderProbeResult(
                        provider_platform=provider.platform,
                        success=True,
                        model_tested=test_model,
                        http_status=200,
                        remaining_quota=remaining,
                        quota_limit=limit,
                        quota_reset_at=reset_at,
                        response_time_ms=duration_ms,
                    )
                
                # Handle errors
                try:
                    err_json = response.json()
                    err_msg = err_json.get("error", {}).get("message", response.text)
                    err_type = err_json.get("error", {}).get("type", "unknown")
                    err_code = err_json.get("error", {}).get("code", "")
                except Exception:
                    err_msg = response.text[:200]
                    err_type = "raw_error"
                    err_code = ""
                
                # Classify error type
                classified_type = "unknown"
                if response.status_code == 401 or "auth" in err_msg.lower() or "key" in err_msg.lower():
                    classified_type = "auth"
                elif response.status_code == 402 or "credit" in err_msg.lower() or "payment" in err_msg.lower() or "exhaust" in err_msg.lower():
                    classified_type = "quota"
                elif response.status_code == 429 or "rate" in err_msg.lower():
                    classified_type = "rate_limit"
                elif 500 <= response.status_code < 600:
                    classified_type = "server_error"
                
                return ProviderProbeResult(
                    provider_platform=provider.platform,
                    success=False,
                    model_tested=test_model,
                    http_status=response.status_code,
                    error_type=classified_type,
                    error_message=err_msg[:300],
                    response_time_ms=duration_ms,
                )
                
        except httpx.TimeoutException:
            return ProviderProbeResult(
                provider_platform=provider.platform,
                success=False,
                model_tested=test_model,
                error_type="timeout",
                error_message=f"Request timed out after {self.timeout}s",
                response_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ProviderProbeResult(
                provider_platform=provider.platform,
                success=False,
                model_tested=test_model,
                error_type="network",
                error_message=str(e)[:300],
                response_time_ms=int((time.time() - start_time) * 1000),
            )
    
    async def probe_all(
        self,
        providers: list[FreeProvider],
        concurrency: int = 3,
        delay_between: float = 0.5,
    ) -> dict[str, ProviderProbeResult]:
        """Probe all enabled providers with rate limiting."""
        results: dict[str, ProviderProbeResult] = {}
        sem = asyncio.Semaphore(concurrency)
        
        async def _probe_one(p: FreeProvider):
            if not p.probe_enabled:
                return
            async with sem:
                await asyncio.sleep(delay_between)
                logger.info(f"Probing provider: {p.name} ({p.platform})")
                res = await self.probe_provider(p)
                results[p.platform] = res
        
        tasks = [_probe_one(p) for p in providers if p.probe_enabled]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    def _extract_remaining(self, headers: httpx.Headers) -> int | None:
        """Extract remaining quota from response headers."""
        candidates = [
            "x-ratelimit-remaining-requests",
            "x-ratelimit-remaining-tokens",
            "x-ratelimit-remaining",
            "ratelimit-remaining",
        ]
        for c in candidates:
            val = headers.get(c)
            if val is not None:
                try:
                    return int(val)
                except ValueError:
                    pass
        return None
    
    def _extract_limit(self, headers: httpx.Headers) -> int | None:
        """Extract quota limit from response headers."""
        candidates = [
            "x-ratelimit-limit-requests",
            "x-ratelimit-limit-tokens",
            "x-ratelimit-limit",
            "ratelimit-limit",
        ]
        for c in candidates:
            val = headers.get(c)
            if val is not None:
                try:
                    return int(val)
                except ValueError:
                    pass
        return None