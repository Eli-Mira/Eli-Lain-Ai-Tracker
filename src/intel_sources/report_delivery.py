"""Publish an already-sanitized, single-file report; verify before notifying.

No repository visibility changes, site creation, raw-input export, dotenv loading,
or retry of side-effecting requests. Errors and result objects contain safe codes
only, never server responses, request URLs containing tokens, or credentials.
"""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import logging
import os
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import socket
import time
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
import httpx

from .public_report import PUBLIC_SOURCES

MAX_HTML_BYTES = 4 * 1024 * 1024
MAX_API_BYTES = 128 * 1024
log = logging.getLogger(__name__)


def _debug() -> bool:
    """True when DELIVERY_DEBUG is set, with the logger level made explicit.

    `log.debug()` on a NOTSET logger inherits the root level (WARNING by
    default) and is silently dropped - which is exactly how the first
    host/status logging attempt vanished from CI. The level is set at call time
    rather than import time so it does not depend on when the variable appears.
    """
    if not os.getenv("DELIVERY_DEBUG"):
        return False
    log.setLevel(logging.DEBUG)
    return True

API_HOSTS = {"api.netlify.com", "api.telegram.org", "discord.com"}
NETLIFY_API = "https://api.netlify.com/api/v1"
ISO_TIME = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})"
Resolver = Callable[[str], Sequence[str]]


class DeliveryError(Exception):
    """Public exception: a fixed safe code plus optional channel receipts."""
    def __init__(self, code: str, *, result: DeliveryResult | None = None):
        super().__init__(code)
        self.code = code
        self.result = result


@dataclass(frozen=True, repr=False)
class DeliveryConfig:
    netlify_token: str
    site_id: str
    telegram_token: str
    telegram_chat_id: str
    discord_token: str
    discord_channel_id: str

    def __repr__(self) -> str:
        return "DeliveryConfig(<redacted>)"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> DeliveryConfig:
        env = os.environ if environ is None else environ
        names = ("NETLIFY_AUTH_TOKEN", "NETLIFY_SITE_ID", "TELEGRAM_BOT_TOKEN",
                 "TELEGRAM_CHAT_ID", "DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID")
        if any(not env.get(name) for name in names):
            raise DeliveryError("missing_config")
        return cls(*(env[name] for name in names))


@dataclass(frozen=True)
class ReportArtifact:
    data: bytes = field(repr=False)
    sha1: str
    sha256: str
    rendered_at: str
    observations: tuple[str, ...]
    source_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class HostedReport:
    url: str
    sha256: str
    deploy_id: str


@dataclass(frozen=True)
class ChannelReceipt:
    channel: str
    message_id: str | None
    confirmation: str
    error_code: str | None = None

    @property
    def confirmed(self) -> bool:
        return self.confirmation in {"receipt-confirmed", "independently-read-back"}


@dataclass(frozen=True)
class DeliveryResult:
    hosted: HostedReport
    brief: str
    telegram: ChannelReceipt
    discord: ChannelReceipt

    @property
    def success(self) -> bool:
        return self.telegram.confirmed and self.discord.confirmed


def load_artifact(export_dir: str | Path) -> ReportArtifact:
    directory = Path(export_dir)
    # Only the sanitized single-file export may be published. Deploying a
    # directory tree would expose state, databases or probe diagnostics.
    if not directory.is_dir() or any(entry.name != "index.html" for entry in directory.iterdir()):
        raise DeliveryError("unexpected_files")
    index = directory / "index.html"
    if not index.is_file() or index.is_symlink() or getattr(index.lstat(), "st_file_attributes", 0) & 0x400:
        raise DeliveryError("unexpected_files")
    data = index.read_bytes()
    soup = BeautifulSoup(data.decode("utf-8"), "html.parser")
    footer = soup.select_one("footer")
    text = footer.get_text(" ", strip=True) if footer else ""
    if "Public sanitized export of saved observations; not a fresh fetch." not in text:
        raise DeliveryError("invalid_artifact")
    rendered = re.findall(ISO_TIME, text)
    if len(rendered) != 1:
        raise DeliveryError("invalid_artifact")
    counts = Counter(row.get("data-source") for row in soup.select("#discoveries .discovery-item"))
    if any(source not in PUBLIC_SOURCES for source in counts):
        raise DeliveryError("invalid_artifact")
    observations = set()
    for node in soup.select("#discoveries .evidence li div"):
        match = re.fullmatch("observed_at: ?(" + ISO_TIME + ")", node.get_text(" ", strip=True))
        if match:
            observations.add(match[1])
    return ReportArtifact(data, hashlib.sha1(data).hexdigest(), hashlib.sha256(data).hexdigest(),
                          rendered[0], tuple(sorted(observations)), tuple(sorted(counts.items())))


def resolve_public_dns(host: str) -> Sequence[str]:
    return list({row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})


class _PinnedTransport(httpx.BaseTransport):
    """Connect only to validated global IPs; preserve the hostname for TLS SNI.

    Pools are separated by hostname to avoid sharing IP-origin TLS connections
    between differently authenticated names. Test transports never use sockets.
    """
    def __init__(self, resolver: Resolver, transport: httpx.BaseTransport | None):
        self.resolver = resolver
        self.test_transport = transport
        self.transports: dict[str, httpx.HTTPTransport] = {}
        self.allowed_hosts = set(API_HOSTS)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host not in self.allowed_hosts or request.url.scheme != "https" or request.url.port not in (None, 443):
            raise DeliveryError("unsafe_url")
        addresses = self.resolver(host)
        if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
            raise DeliveryError("unsafe_dns")
        pinned = httpx.Request(request.method, request.url.copy_with(host=addresses[0]),
                              headers=request.headers, stream=request.stream,
                              extensions={**request.extensions, "sni_hostname": host})
        inner = self.test_transport
        if inner is None:
            inner = self.transports.setdefault(host, httpx.HTTPTransport(verify=True, retries=0))
        return inner.handle_request(pinned)

    def close(self) -> None:
        for transport in self.transports.values():
            transport.close()
        if self.test_transport is not None:
            self.test_transport.close()


@contextmanager
def _quiet_http_logs():
    # httpx INFO logs contain the Telegram token in the request path. Never
    # enable wire logging inside this secret-bearing operation.
    loggers = [logging.getLogger(name) for name in ("httpx", "httpcore")]
    old = [logger.disabled for logger in loggers]
    for logger in loggers:
        logger.disabled = True
    try:
        yield
    finally:
        for logger, disabled in zip(loggers, old):
            logger.disabled = disabled


class _Session:
    def __init__(self, config: DeliveryConfig, transport: _PinnedTransport, client: httpx.Client):
        self.config, self.transport, self.client = config, transport, client

    def request(self, method: str, url: str, *, limit: int = MAX_API_BYTES, **kwargs) -> bytes:
        try:
            with self.client.stream(method, url, follow_redirects=False, **kwargs) as response:
                if not 200 <= response.status_code < 300:
                    if _debug():
                        # Host and status only: the URL path carries the Telegram
                        # token, so it must never reach a log line.
                        log.debug("delivery %s %s -> %s", method,
                                  urlsplit(url).hostname, response.status_code)
                    raise DeliveryError("http_status")
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > limit:
                        raise DeliveryError("response_too_large")
                return bytes(data)
        except DeliveryError:
            raise
        except Exception as error:
            # Never surface the response body or a token-bearing request URL.
            # httpx messages embed the request URL, which carries the token, so
            # only the exception CLASS is ever recorded - and only under
            # DELIVERY_DEBUG, which makes an otherwise opaque failure diagnosable.
            if _debug():
                log.debug("delivery request failed: %s", type(error).__name__)
            raise DeliveryError("request_failed") from None

    def api(self, method: str, url: str, **kwargs) -> dict:
        try:
            value = json.loads(self.request(method, url, **kwargs))
            if not isinstance(value, dict):
                raise ValueError
            return value
        except DeliveryError:
            raise
        except Exception as error:
            if _debug():
                log.debug("delivery api response invalid: %s", type(error).__name__)
            raise DeliveryError("invalid_response") from None

    def netlify(self, method: str, path: str, **kwargs) -> dict:
        return self.api(method, NETLIFY_API + path,
                        headers={"Authorization": "Bearer " + self.config.netlify_token,
                                 **kwargs.pop("headers", {})}, **kwargs)

    def host(self, artifact: ReportArtifact, attempts: int, interval: float,
             sleep: Callable[[float], None]) -> HostedReport:
        site = self.netlify("GET", f"/sites/{self.config.site_id}")
        if site.get("id") != self.config.site_id:
            raise DeliveryError("site_mismatch")
        created = self.netlify("POST", f"/sites/{self.config.site_id}/deploys",
                              json={"files": {"/index.html": artifact.sha1}, "draft": False})
        deploy = created["id"]
        if created.get("site_id") != self.config.site_id:
            raise DeliveryError("deploy_mismatch")
        if created.get("required"):
            self.netlify("PUT", f"/deploys/{deploy}/files/index.html", content=artifact.data,
                         headers={"Content-Type": "application/octet-stream"})
        for attempt in range(attempts):
            status = self.netlify("GET", f"/deploys/{deploy}")
            if status.get("id") != deploy or status.get("site_id") != self.config.site_id:
                raise DeliveryError("deploy_mismatch")
            if status.get("state") == "ready":
                break
            if attempt + 1 == attempts:
                raise DeliveryError("deploy_not_ready")
            sleep(interval)
        else:
            raise DeliveryError("deploy_not_ready")
        url = status["deploy_ssl_url"].rstrip("/") + "/"
        host = urlsplit(url).hostname
        if not host or not host.endswith(".netlify.app"):
            raise DeliveryError("unsafe_url")
        self.transport.allowed_hosts.add(host)
        actual = self.request("GET", url, limit=MAX_HTML_BYTES,
                              headers={"Accept": "text/html", "Cache-Control": "no-cache"})
        if hashlib.sha256(actual).hexdigest() != artifact.sha256:
            raise DeliveryError("html_mismatch")
        return HostedReport(url, artifact.sha256, deploy)

    def telegram(self, brief: str) -> ChannelReceipt:
        try:
            response = self.api("POST", "https://api.telegram.org/bot" + self.config.telegram_token + "/sendMessage",
                                json={"chat_id": self.config.telegram_chat_id, "text": brief,
                                      "link_preview_options": {"is_disabled": True}})
            result = response.get("result", {})
            identifier = result.get("message_id")
            if (response.get("ok") is not True or type(identifier) is not int or identifier <= 0
                    or result.get("chat", {}).get("id") != int(self.config.telegram_chat_id)
                    or result.get("text") != brief):
                raise DeliveryError("telegram_receipt_invalid")
            return ChannelReceipt("telegram", str(identifier), "receipt-confirmed")
        except DeliveryError as exc:
            return ChannelReceipt("telegram", None, "unconfirmed", exc.code)

    def discord(self, brief: str) -> ChannelReceipt:
        try:
            base = "https://discord.com/api/v10/channels/" + self.config.discord_channel_id + "/messages"
            headers = {"Authorization": "Bot " + self.config.discord_token}
            sent = self.api("POST", base, headers=headers,
                            json={"content": brief, "allowed_mentions": {"parse": [], "replied_user": False}})
            identifier = sent.get("id")
            if (not isinstance(identifier, str) or not re.fullmatch(r"[1-9]\d{16,19}", identifier)
                    or sent.get("channel_id") != self.config.discord_channel_id or sent.get("content") != brief):
                raise DeliveryError("discord_receipt_invalid")
            actual = self.api("GET", base + "/" + identifier, headers=headers)
            if (actual.get("id") != identifier or actual.get("channel_id") != self.config.discord_channel_id
                    or actual.get("content") != brief):
                raise DeliveryError("discord_readback_invalid")
            return ChannelReceipt("discord", identifier, "independently-read-back")
        except DeliveryError as exc:
            return ChannelReceipt("discord", None, "unconfirmed", exc.code)


def build_brief(artifact: ReportArtifact, hosted: HostedReport) -> str:
    observed = "not supplied" if not artifact.observations else artifact.observations[0]
    if len(artifact.observations) > 1:
        observed += " to " + artifact.observations[-1]
    counts = "; ".join(f"{source}: {count}" for source, count in artifact.source_counts) or "none"
    return (f"Lain public report\nRender: {artifact.rendered_at}\nSaved observations: {observed}\n"
            f"Exported discoveries: {sum(count for _, count in artifact.source_counts)} ({counts}).\n"
            "Saved data, not a fresh fetch. Listings are metadata only; inference, free entitlement, "
            "and tool/skill suitability are unverified. Provider statuses, changes, actions and news excluded.\n"
            f"Verified HTML: {hosted.url}")


def deliver_report(export_dir: str | Path, *, environ: Mapping[str, str] | None = None,
                   transport: httpx.BaseTransport | None = None, resolver: Resolver = resolve_public_dns,
                   poll_attempts: int = 30, poll_interval: float = 1.0,
                   sleep: Callable[[float], None] = time.sleep) -> DeliveryResult:
    """Require verified hosting and BOTH channels. Raises on any partial delivery.

    An exception with .result records per-channel outcomes; Telegram's official
    sendMessage receipt is not an independent message readback. No send retries.
    transport/resolver/sleep injection is for deterministic protocol tests only.
    """
    config = DeliveryConfig.from_env(environ)
    artifact = load_artifact(export_dir)
    pinned = _PinnedTransport(resolver, transport)
    try:
        with _quiet_http_logs(), httpx.Client(transport=pinned, timeout=20.0, trust_env=False,
                                              follow_redirects=False) as client:
            session = _Session(config, pinned, client)
            hosted = session.host(artifact, poll_attempts, poll_interval, sleep)
            brief = build_brief(artifact, hosted)
            result = DeliveryResult(hosted, brief, session.telegram(brief), session.discord(brief))
            if not result.success:
                raise DeliveryError("channel_failure", result=result)
            return result
    except DeliveryError:
        raise
    except Exception:
        raise DeliveryError("delivery_failed") from None
