"""Main tracker: loads existing providers from freellmapi DB and probes/verifies them."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import FreeProvider, ProviderStatus, ProviderTier, FreellmapiIntegrationType, ProviderProbeResult
from .prober import AutoProber


logger = logging.getLogger(__name__)


class FreeProviderTracker:
    """Track and verify freellmapi providers' free tier status."""
    
    # Provider-specific knowledge base for tier details and key IDs
    PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
        "cohere": {
            "tier_type": ProviderTier.TRIAL_ONLY,
            "tier_details": "Trial pool (~100 requests), not recoverable without paid key",
            "reset_schedule": "Never (trial pool exhausted)",
        },
        "groq": {
            "tier_type": ProviderTier.DAILY_TOKENS,
            "tier_details": "1000 req/day, ~6M tokens/month on Llama/GPT models",
            "reset_schedule": "Daily at 00:00 UTC",
        },
        "mistral": {
            "tier_type": ProviderTier.MONTHLY_TOKENS,
            "tier_details": "Free experiment pool, usage varies by model",
            "reset_schedule": "Monthly",
        },
        "cloudflare": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "10,000 neurons/day (~5K-10K tokens), requires account_id:token format",
            "reset_schedule": "Daily at midnight PT",
        },
        "github": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "Free GPT models via GitHub Models, limited context",
            "reset_schedule": "Per-request limit applies",
        },
        "cerebras": {
            "tier_type": ProviderTier.NO_FREE_TIER,
            "tier_details": "Was free, now behind paywall (2026-09-28)",
            "reset_schedule": "N/A (paywalled)",
        },
        "openrouter": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "50 req/day free (or 1000/day after $10 purchase)",
            "reset_schedule": "Daily, account-wide across all :free models",
        },
        "zhipu": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "Free Zhipu GLM models available",
            "reset_schedule": "Unknown (no quota headers)",
        },
        "agnes": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "Agnes AI models, likely free tier available",
            "reset_schedule": "Unknown",
        },
        "aion": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "Aion Labs free models",
            "reset_schedule": "Unknown",
        },
        "sealion": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "SEA-LION daily free tier",
            "reset_schedule": "Daily",
        },
        "routeway": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "Routeway free daily tier",
            "reset_schedule": "Daily",
        },
        "navy": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "Navy AI daily free tier",
            "reset_schedule": "Daily",
        },
        "electronhub": {
            "tier_type": ProviderTier.CREDIT_DOLLARS,
            "tier_details": "Weekly credit allocation",
            "reset_schedule": "Weekly",
        },
        "bai": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "BAI AI free models",
            "reset_schedule": "Unknown",
        },
        "bazaarlink": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "BazaarLink daily free tier (DeepSeek-V4-Flash)",
            "reset_schedule": "Daily",
        },
        "requesty": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "Requesty free tier",
            "reset_schedule": "Unknown",
        },
        "reka": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "300 requests per 5-minute rolling window",
            "reset_schedule": "Rolling 5-minute window",
        },
        "anyapi": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "AnyAPI free tier",
            "reset_schedule": "Unknown",
        },
        "huggingface": {
            "tier_type": ProviderTier.CREDIT_DOLLARS,
            "tier_details": "$0.10/month free routed credit (~1-3M tokens), renews monthly",
            "reset_schedule": "Monthly (1st of each month)",
        },
        "nvidia": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "NVIDIA NIM free tier with limited models",
            "reset_schedule": "Unknown",
        },
        "opencode": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "OpenCode promo tier",
            "reset_schedule": "Unknown",
        },
        "google": {
            "tier_type": ProviderTier.MONTHLY_TOKENS,
            "tier_details": "~1M tokens/month free (Gemini Flash/Pro)",
            "reset_schedule": "Monthly",
        },
        "nara": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "NaraRouter free daily tier",
            "reset_schedule": "Daily",
        },
        "llm7": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "LLM7 anonymous free tier",
            "reset_schedule": "Unknown",
        },
        "xkiro": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "xKiro free daily tier",
            "reset_schedule": "Daily",
        },
        "unorouter": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "UnoRouter free tier (may have quotas)",
            "reset_schedule": "Unknown",
        },
        "waterfall": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "Waterfall community free tier",
            "reset_schedule": "Daily",
        },
        "blaze": {
            "tier_type": ProviderTier.DAILY_REQUESTS,
            "tier_details": "Blaze daily free tier",
            "reset_schedule": "Daily",
        },
        "custom_minimax": {
            "tier_type": ProviderTier.ALWAYS_FREE_MODELS,
            "tier_details": "MiniMax free tier (custom endpoint)",
            "reset_schedule": "Unknown",
        },
    }
    
    # Key IDs mapping from freellmapi DB
    KEY_ID_MAP: dict[str, int] = {
        "cohere": 1,
        "groq": 2,
        "mistral": 3,
        "cloudflare": 4,
        "github": 5,
        "cerebras": 6,
        "openrouter": 7,
        "zhipu": 8,
        "agnes": 9,
        "aion": 10,
        "sealion": 11,
        "routeway": 12,
        "navy": 14,
        "electronhub": 15,
        "bai": 16,
        "bazaarlink": 17,
        "requesty": 18,
        "reka": 19,
        "anyapi": 20,
        "huggingface": 23,
        "nvidia": 24,
        "opencode": 25,
        "google": 26,
        "nara": 27,
        "llm7": 29,
        "xkiro": 31,
        "unorouter": 32,
        "waterfall": 33,
        "blaze": 34,
    }
    
    def __init__(
        self,
        freellmapi_db_path: str | Path = "./data/freeapi.db",
        state_path: str | Path = "./data/provider_state.json",
    ):
        self.db_path = Path(freellmapi_db_path)
        self.state_path = Path(state_path)
        self.providers: dict[str, FreeProvider] = {}
        self.probe_results: dict[str, ProviderProbeResult] = {}
    
    def load_from_db(self) -> int:
        """Load existing providers from freellmapi SQLite DB."""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            rows = cur.execute("SELECT platform, label, status, enabled FROM api_keys").fetchall()
            loaded = 0
            
            for row in rows:
                platform = row["platform"]
                if platform not in self.providers:
                    provider = self._build_provider_from_db(platform, row)
                    self.providers[platform] = provider
                    loaded += 1
            
            conn.close()
            logger.info(f"Loaded {loaded} providers from freellmapi DB")
            return loaded
            
        except FileNotFoundError:
            logger.error(f"freellmapi DB not found at {self.db_path}")
            return 0
        except Exception as e:
            logger.error(f"Failed to load providers from DB: {e}")
            return 0
    
    def _build_provider_from_db(self, platform: str, row: Any) -> FreeProvider:
        """Build FreeProvider from DB row."""
        key_info = self.PROVIDER_REGISTRY.get(platform, {})
        key_id = self.KEY_ID_MAP.get(platform)
        
        # Determine integration type
        if key_id and row["enabled"] == 1:
            if platform in ["cohere", "groq", "mistral", "cloudflare", "github", 
                          "cerebras", "openrouter", "zhipu", "huggingface", "google"]:
                integration = FreellmapiIntegrationType.IN_CATALOG_KEY_IN_DB
            elif platform in ["reka", "waterfall", "blaze", "custom_minimax"]:
                integration = FreellmapiIntegrationType.IN_REGISTRY_NOT_CATALOG
            else:
                integration = FreellmapiIntegrationType.IN_CATALOG_KEY_IN_DB
        else:
            integration = FreellmapiIntegrationType.IN_CATALOG_NO_KEY
        
        status = ProviderStatus.LIVE if row["status"] == "healthy" and row["enabled"] else ProviderStatus.DISABLED
        
        return FreeProvider(
            name=key_info.get("tier_details", platform).split("(")[0].strip(),
            platform=platform,
            tier_type=key_info.get("tier_type", ProviderTier.UNKNOWN),
            tier_details=key_info.get("tier_details", ""),
            reset_schedule=key_info.get("reset_schedule", ""),
            status=status,
            freellmapi_key_id=key_id,
            freellmapi_integration=integration,
            freellmapi_key_label=row["label"] if row["label"] else "",
            probe_enabled=True,
            probe_model=LIGHTWEIGHT_MODELS.get(platform, ""),
        )
    
    async def update_providers(self) -> list[FreeProvider]:
        """Update all tracked providers with latest status."""
        updates = []
        
        for platform, provider in self.providers.items():
            # Check if we should probe
            if provider.probe_enabled and provider.status in (ProviderStatus.LIVE, ProviderStatus.UNKNOWN):
                result = await self._probe_single(provider)
                if result:
                    status, reason = result.to_status()
                    provider.status = status
                    provider.status_reason = reason
                    provider.last_verified = datetime.now(timezone.utc)
                    provider.last_verified_source = "probe"
                    
                    # Update action recommendation
                    provider.freellmapi_action = self._generate_action(provider, result)
            
            updates.append(provider)
        
        return updates
    
    async def _probe_single(self, provider: FreeProvider) -> ProviderProbeResult | None:
        """Probe a single provider and return result."""
        prober = AutoProber()
        return await prober.probe_provider(provider)
    
    def _generate_action(self, provider: FreeProvider, result: ProviderProbeResult) -> str:
        """Generate actionable next steps based on probe result."""
        status, reason = result.to_status()
        
        if status == ProviderStatus.LIVE:
            return "No action needed - free tier active"
        elif status == ProviderStatus.BROKEN_KEY:
            return f"Key invalid ({result.http_status}). Get new key from: {self._get_dashboard_url(provider.platform)}"
        elif status == ProviderStatus.EXHAUSTED:
            if provider.tier_type == ProviderTier.CREDIT_DOLLARS and "monthly" in provider.reset_schedule.lower():
                return f"Credit exhausted. Resets monthly (next renewal: {provider.reset_schedule})"
            elif provider.tier_type == ProviderTier.DAILY_TOKENS:
                return f"Daily quota exhausted. Resets daily at {provider.reset_schedule}"
            return f"Quota exhausted ({reason}). Check provider dashboard for limits."
        elif status == ProviderStatus.PAYWALLED:
            return f"Provider moved behind paywall. Remove key or switch to paid tier."
        elif status == ProviderStatus.DEGRADED:
            return f"Provider degraded ({reason}). May recover automatically."
        else:
            return f"Status unknown ({reason}). Verify manually."
    
    def _get_dashboard_url(self, platform: str) -> str:
        """Get provider dashboard URL for key management."""
        dashboards = {
            "cloudflare": "https://dash.cloudflare.com/",
            "groq": "https://console.groq.com/keys",
            "cohere": "https://dashboard.cohere.com/api-keys",
            "mistral": "https://console.mistral.ai/api-keys",
            "google": "https://aistudio.google.com/apikey",
            "zhipu": "https://open.bigmodel.cn/usercenter/apikeys",
            "huggingface": "https://huggingface.co/settings/tokens",
        }
        return dashboards.get(platform, f"https://{platform}.com/")
    
    def save_state(self):
        """Persist provider state to JSON."""
        state = {
            "providers": {p.platform: p.to_dict() for p in self.providers.values()},
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        logger.info(f"Saved provider state to {self.state_path}")
    
    def load_state(self):
        """Load persisted provider state."""
        if self.state_path.exists():
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            for platform, pdata in data.get("providers", {}).items():
                if platform not in self.providers:
                    self.providers[platform] = FreeProvider.from_dict(pdata)
            logger.info(f"Loaded {len(self.providers)} providers from state")


# Light weight models map (shared with prober)
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