"""Data models for free LLM provider tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ProviderStatus(Enum):
    """Current operational status of a provider."""
    
    LIVE = "live"              # Working, free tier available
    DEGRADED = "degraded"      # Working but with issues (rate limits, partial outages)
    PAYWALLED = "paywalled"    # Was free, now requires payment
    EXHAUSTED = "exhausted"    # Free tier quota exhausted, awaiting reset
    BROKEN_KEY = "broken_key"  # Key exists but auth fails (401/403)
    UNKNOWN = "unknown"        # Never probed or no recent data
    DISABLED = "disabled"      # Explicitly disabled in freellmapi


class ProviderTier(Enum):
    """Type of free tier offered."""
    
    DAILY_TOKENS = "daily_tokens"           # e.g., 6M tokens/day (Groq)
    MONTHLY_TOKENS = "monthly_tokens"       # e.g., 1M tokens/month (Google)
    DAILY_REQUESTS = "daily_requests"       # e.g., 50 req/day (OpenRouter free)
    CREDIT_DOLLARS = "credit_dollars"       # e.g., $0.10/month (HuggingFace)
    ALWAYS_FREE_MODELS = "always_free_models"  # Specific models always free
    TRIAL_ONLY = "trial_only"               # One-time trial credits
    NO_FREE_TIER = "no_free_tier"           # Pay only
    UNKNOWN = "unknown"


class FreellmapiIntegrationType(Enum):
    """How this provider integrates with freellmapi."""
    
    IN_CATALOG_KEY_IN_DB = "in_catalog_key_in_db"      # Already in catalog, key stored
    IN_CATALOG_NO_KEY = "in_catalog_no_key"            # In catalog but no key in DB
    IN_REGISTRY_NOT_CATALOG = "in_registry_not_catalog"  # Provider class exists, not in catalog
    NOT_IN_REGISTRY = "not_in_registry"                # Must use custom endpoint
    UNKNOWN = "unknown"


@dataclass
class FreeProvider:
    """A tracked free LLM provider with its current state."""
    
    # Identity
    name: str                          # Display name (e.g., "Groq")
    platform: str                      # freellmapi platform ID (e.g., "groq")
    
    # Free tier info
    tier_type: ProviderTier = ProviderTier.UNKNOWN
    tier_details: str = ""             # Human-readable (e.g., "1000 req/day, ~6M tokens/month")
    reset_schedule: str = ""           # e.g., "daily at 00:00 UTC", "rolling 5min"
    
    # Current status
    status: ProviderStatus = ProviderStatus.UNKNOWN
    status_reason: str = ""            # Why this status
    last_verified: datetime | None = None
    last_verified_source: str = ""     # "health_check" | "probe" | "dashboard" | "manual"
    
    # freellmapi integration
    freellmapi_key_id: int | None = None
    freellmapi_integration: FreellmapiIntegrationType = FreellmapiIntegrationType.UNKNOWN
    freellmapi_action: str = ""        # Exact next step (curl command, DB insert, etc.)
    freellmapi_key_label: str = ""     # Label in DB if exists
    
    # Key format
    key_format: str = ""               # "API key" | "account_id:token" | "AWS IAM" | "OAuth" | etc.
    dashboard_url: str = ""            # Where to get/manage keys
    
    # Discovery metadata
    discovered_from: str = ""          # "catalog" | "dashboard" | "community" | "search"
    discovery_date: datetime = field(default_factory=datetime.utcnow)
    is_new: bool = False               # First time seen
    
    # Probing
    probe_enabled: bool = True
    probe_model: str = ""              # Model to use for probing
    probe_cost_estimate: str = ""      # "~1 request" | "~100 tokens" | etc.
    
    # Metadata
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "name": self.name,
            "platform": self.platform,
            "tier_type": self.tier_type.value,
            "tier_details": self.tier_details,
            "reset_schedule": self.reset_schedule,
            "status": self.status.value,
            "status_reason": self.status_reason,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
            "last_verified_source": self.last_verified_source,
            "freellmapi_key_id": self.freellmapi_key_id,
            "freellmapi_integration": self.freellmapi_integration.value,
            "freellmapi_action": self.freellmapi_action,
            "freellmapi_key_label": self.freellmapi_key_label,
            "key_format": self.key_format,
            "dashboard_url": self.dashboard_url,
            "discovered_from": self.discovered_from,
            "discovery_date": self.discovery_date.isoformat(),
            "is_new": self.is_new,
            "probe_enabled": self.probe_enabled,
            "probe_model": self.probe_model,
            "probe_cost_estimate": self.probe_cost_estimate,
            "notes": self.notes,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FreeProvider:
        """Create from dict."""
        # Convert datetime strings back
        if data.get("last_verified"):
            data["last_verified"] = datetime.fromisoformat(data["last_verified"])
        if data.get("discovery_date"):
            data["discovery_date"] = datetime.fromisoformat(data["discovery_date"])
        # Convert enums
        data["tier_type"] = ProviderTier(data.get("tier_type", "unknown"))
        data["status"] = ProviderStatus(data.get("status", "unknown"))
        data["freellmapi_integration"] = FreellmapiIntegrationType(data.get("freellmapi_integration", "unknown"))
        return cls(**data)


@dataclass
class ProviderProbeResult:
    """Result of probing a provider via freellmapi."""
    
    provider_platform: str
    success: bool
    model_tested: str
    http_status: int | None = None
    error_type: str | None = None       # "auth" | "quota" | "rate_limit" | "server_error" | "network"
    error_message: str = ""
    remaining_quota: int | None = None
    quota_limit: int | None = None
    quota_reset_at: str | None = None
    response_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_status(self) -> tuple[ProviderStatus, str]:
        """Convert probe result to provider status + reason."""
        if self.success:
            if self.remaining_quota is not None and self.remaining_quota == 0:
                return ProviderStatus.EXHAUSTED, "Quota exhausted (0 remaining)"
            return ProviderStatus.LIVE, "Probe successful"
        
        if self.http_status == 401 or self.error_type == "auth":
            return ProviderStatus.BROKEN_KEY, self.error_message or "Authentication failed (401)"
        if self.http_status == 402 or self.error_type == "quota":
            return ProviderStatus.EXHAUSTED, self.error_message or "Quota/credits exhausted"
        if self.http_status == 429 or self.error_type == "rate_limit":
            return ProviderStatus.DEGRADED, self.error_message or "Rate limited"
        if self.http_status and 500 <= self.http_status < 600:
            return ProviderStatus.DEGRADED, f"Server error ({self.http_status})"
        
        return ProviderStatus.UNKNOWN, self.error_message or "Unknown error"


@dataclass
class ToolDiscovery:
    """A discovered GitHub tool relevant to our stack."""
    
    repo_name: str                  # "owner/repo"
    description: str
    url: str
    stars: int
    language: str
    topics: list[str]
    last_push: datetime | None
    relevance_reason: str           # Why this is relevant to Eli
    category: str                   # "data-engineering" | "local-llm" | "automation" | "freellmapi" | etc.
    actionable: bool = False        # Can we use this directly?
    install_instructions: str = ""  # How to install/use
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "description": self.description,
            "url": self.url,
            "stars": self.stars,
            "language": self.language,
            "topics": self.topics,
            "last_push": self.last_push.isoformat() if self.last_push else None,
            "relevance_reason": self.relevance_reason,
            "category": self.category,
            "actionable": self.actionable,
            "install_instructions": self.install_instructions,
        }