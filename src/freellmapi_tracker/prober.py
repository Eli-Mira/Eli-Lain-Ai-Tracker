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
# Pulls from freellmapi DB — keys are platform strings from api_keys
LIGHTWEIGHT_MODELS = {
    "cohere": "command-r-08-2024",          # c4ai-aya-expanse-32b works; command is faster
    "groq": "llama-3.1-8b-instant",
    "mistral": "codestral-2508",
    "cloudflare": "@cf/aisingapore/gemma-sea-lion-v4-27b-it",  # exists in DB
    "github": "gpt-4o-mini",               # GitHub Models free tier
    "cerebras": "llama-3.1-8b",
    "openrouter": "google/gemini-2.0-flash-exp:free",
    "zhipu": "glm-4.5-flash",              # confirmed in DB
    "agnes": "agnes-2.5-flash",            # confirmed in DB
    "aion": "aion-labs/aion-2.0",           # confirmed in DB
    "sealion": "aisingapore/Gemma-SEA-LION-v4-27B-IT",  # confirmed in DB
    "routeway": "glm-4.5-flash",           # generic fallback
    "navy": "deepseek-v4-flash",           # generic fallback
    "electronhub": "codestral-latest",     # generic fallback
    "bai": "codestral-latest",             # generic fallback
    "bazaarlink": "deepseek/deepseek-v4-flash-0731free:free",  # confirmed in DB
    "requesty": "google/gemma-4-31b-it",   # confirmed in DB
    "reka": "reka-flash",                  # key-based ID in DB (19)
    "anyapi": "codestral-latest",
    "huggingface": "CohereLabs/aya-expanse-32b",  # confirmed in DB
    "nvidia": "google/diffusiongemma-26b-a4b-it",  # confirmed in DB
    "opencode": "codestral-latest",
    "google": "gemini-2.5-flash",          # confirmed in DB
    "nara": "agnes-2.5-flash",             # confirmed in DB
    "llm7": "codestral-latest",            # confirmed in DB
    "xkiro": "mistralai/codestral-2508",   # confirmed in DB
    "unorouter": "deepseek-v4-flash:free", # confirmed in DB
    "waterfall": "glm-4.5-flash",
    "blaze": "gemini-2.0-flash",
    "custom": "MiniMax-M2",               # confirmed in DB
}

# Platform → list of fallback models (used when primary returns 404)
PLATFORM_FALLBACK_MODELS = {
    "cloudflare": ["@cf/qwen/qwen3-30b-a3b-fp8", "@cf/meta/llama-4-scout-17b-16e-instruct"],
    "groq": ["llama-3.1-8b-instant", "llama-3.3-70b-specdec"],
    "mistral": ["codestral-2508", "mistral-small-latest"],
    "google": ["gemini-2.5-flash", "gemini-3.5-flash"],
    "cohere": ["command-r-08-2024", "c4ai-aya-expanse-32b"],
}


def _get_model_for_platform(platform: str) -> str | None:
    """Return the best test model for a platform, or None."""
    return LIGHTWEIGHT_MODELS.get(platform)


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
        """Probe a single provider with a minimal request.

        Tries the primary model first; on 404 (model not in catalog)
        falls back to alternative models for that platform.
        """
        # Build ordered candidate list: requested > provider config > platform default > fallbacks
        candidates: list[str] = []
        if model:
            candidates.append(model)
        if provider.probe_model and provider.probe_model != model:
            candidates.append(provider.probe_model)
        default_model = LIGHTWEIGHT_MODELS.get(provider.platform)
        if default_model and default_model not in candidates:
            candidates.append(default_model)
        for fb in PLATFORM_FALLBACK_MODELS.get(provider.platform, []):
            if fb not in candidates:
                candidates.append(fb)

        if not candidates:
            return ProviderProbeResult(
                provider_platform=provider.platform,
                success=False,
                model_tested="none",
                error_type="config",
                error_message=f"No test model configured for platform {provider.platform}",
            )
        
        last_result: ProviderProbeResult | None = None
        for candidate in candidates:
            result = await self._do_probe(candidate, provider.platform)
            last_result = result
            # 404 = model not in this provider's catalog — try next candidate
            if result.http_status == 404:
                continue
            return result
        
        return last_result or ProviderProbeResult(
            provider_platform=provider.platform,
            success=False,
            model_tested=candidates[0],
            error_type="no_models",
            error_message="All candidate models returned 404 (not in catalog)",
        )
    
    async def _do_probe(self, test_model: str, platform: str) -> ProviderProbeResult:
        """Run a single probe request against freellmapi."""
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
                        provider_platform=platform,
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
                
                # Classify error type — ordered most-specific first
                classified_type = "unknown"
                msg_lower = err_msg.lower()
                # Auth errors: explicit 401 or auth/invalid/expired key patterns (avoid bare "keys" in rate-limit text)
                if response.status_code == 401 or any(kw in msg_lower for kw in ["invalid api key", "expired key", "authentication failed", "unauthorized", "api key not found", "invalid credentials"]):
                    classified_type = "auth"
                elif response.status_code == 402 or any(kw in msg_lower for kw in ["credit", "payment", "billing", "insufficient quota", "usage limit"]):
                    classified_type = "quota"
                elif response.status_code == 429 or "rate" in err_msg.lower():
                    classified_type = "rate_limit"
                elif 500 <= response.status_code < 600:
                    classified_type = "server_error"
                
                return ProviderProbeResult(
                    provider_platform=platform,
                    success=False,
                    model_tested=test_model,
                    http_status=response.status_code,
                    error_type=classified_type,
                    error_message=err_msg[:300],
                    response_time_ms=duration_ms,
                )
                
        except httpx.TimeoutException:
            return ProviderProbeResult(
                provider_platform=platform,
                success=False,
                model_tested=test_model,
                error_type="timeout",
                error_message=f"Request timed out after {self.timeout}s",
                response_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ProviderProbeResult(
                provider_platform=platform,
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