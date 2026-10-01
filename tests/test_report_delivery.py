"""Deterministic protocol tests. MockTransport is not a live deployment."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

SITE = "3970e0fe-8564-4903-9a55-c5f8de49fb8b"
DEPLOY = "abc123"
URL = "https://abc123--report-fixture.netlify.app/"
ENV = {
    "NETLIFY_AUTH_TOKEN": "test-netlify-token",
    "NETLIFY_SITE_ID": SITE,
    "TELEGRAM_BOT_TOKEN": "123456:TEST_TELEGRAM_TOKEN",
    "TELEGRAM_CHAT_ID": "-1001234567890",
    "DISCORD_BOT_TOKEN": "TEST_DISCORD_TOKEN",
    "DISCORD_CHANNEL_ID": "123456789012345678",
}


def module():
    assert importlib.util.find_spec("intel_sources.report_delivery") is not None, "verified delivery module is missing"
    from intel_sources import report_delivery
    return report_delivery


@pytest.fixture
def artifact_dir(tmp_path):
    from intel_sources.public_report import build_public_payload, _standalone_html
    from tracker_core.reporter_html import LainReporter
    state = {"sources": [{"name": "github-trending", "status": "ok", "checked_at": "2026-09-30T10:00:00+00:00"}],
             "items": [{"source": "github-trending", "id": "github:example/tool", "headline": "Safe tool",
                        "url": "https://github.com/example/tool", "checked_at": "2026-09-30T10:00:00+00:00"}]}
    payload = build_public_payload(state, now=datetime(2026, 10, 1, 12, tzinfo=timezone.utc))
    directory = tmp_path / "public"
    directory.mkdir()
    (directory / "index.html").write_text(_standalone_html(LainReporter().render(**payload)), encoding="utf-8")
    return directory


class Protocol:
    def __init__(self, data):
        self.data = data
        self.calls = []
        self.brief = None
        self.override = None

    def __call__(self, request):
        self.calls.append(request)
        # The real pipeline pins DNS to a global IP, retaining Host and TLS SNI.
        assert request.url.host == "8.8.8.8"
        host = request.headers["host"]
        assert request.extensions["sni_hostname"] == host
        if self.override:
            response = self.override(request)
            if response is not None:
                return response
        path = request.url.path
        if host == "api.netlify.com":
            assert request.headers["authorization"] == "Bearer " + ENV["NETLIFY_AUTH_TOKEN"]
            if request.method == "GET" and path == f"/api/v1/sites/{SITE}":
                return httpx.Response(200, json={"id": SITE, "name": "report-fixture"})
            if request.method == "POST" and path == f"/api/v1/sites/{SITE}/deploys":
                body = json.loads(request.content)
                assert body["files"] == {"/index.html": hashlib.sha1(self.data).hexdigest()}
                assert body["draft"] is False
                assert not body.get("functions")
                return httpx.Response(201, json={"id": DEPLOY, "site_id": SITE,
                                              "required": [hashlib.sha1(self.data).hexdigest()], "required_functions": []})
            if request.method == "PUT" and path == f"/api/v1/deploys/{DEPLOY}/files/index.html":
                assert request.content == self.data
                assert request.headers["content-type"] == "application/octet-stream"
                return httpx.Response(200, json={"path": "/index.html"})
            if request.method == "GET" and path == f"/api/v1/deploys/{DEPLOY}":
                return httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": "ready",
                                              "deploy_ssl_url": URL.rstrip("/")})
        if host == "abc123--report-fixture.netlify.app":
            assert request.method == "GET" and path == "/"
            assert "authorization" not in request.headers
            assert "cookie" not in request.headers
            return httpx.Response(200, content=self.data, headers={"content-type": "text/html; charset=utf-8"})
        if host == "api.telegram.org":
            assert request.method == "POST" and path == "/bot" + ENV["TELEGRAM_BOT_TOKEN"] + "/sendMessage"
            body = json.loads(request.content)
            self.brief = body["text"]
            assert body["chat_id"] == ENV["TELEGRAM_CHAT_ID"]
            assert "parse_mode" not in body
            assert body["link_preview_options"] == {"is_disabled": True}
            return httpx.Response(200, json={"ok": True, "result": {"message_id": 42,
                                          "chat": {"id": int(ENV["TELEGRAM_CHAT_ID"])}, "text": self.brief}})
        if host == "discord.com":
            assert request.headers["authorization"] == "Bot " + ENV["DISCORD_BOT_TOKEN"]
            if request.method == "POST" and path == "/api/v10/channels/" + ENV["DISCORD_CHANNEL_ID"] + "/messages":
                body = json.loads(request.content)
                assert body["content"] == self.brief
                assert body["allowed_mentions"] == {"parse": [], "replied_user": False}
                return httpx.Response(200, json={"id": "999999999999999999", "channel_id": ENV["DISCORD_CHANNEL_ID"], "content": self.brief})
            if request.method == "GET" and path == "/api/v10/channels/" + ENV["DISCORD_CHANNEL_ID"] + "/messages/999999999999999999":
                return httpx.Response(200, json={"id": "999999999999999999", "channel_id": ENV["DISCORD_CHANNEL_ID"], "content": self.brief})
        raise AssertionError("Unexpected protocol request")


class Guard(Protocol):
    def __init__(self, data, respond):
        super().__init__(data)
        self.respond = respond

    def __call__(self, request):
        override = self.respond(request)
        if not override:
            return super().__call__(request)
        self.calls.append(request)
        return override


def run(directory, protocol, **kwargs):
    return module().deliver_report(directory, environ=ENV, transport=httpx.MockTransport(protocol),
                                   resolver=lambda host: ["8.8.8.8"], sleep=lambda seconds: None, **kwargs)


def test_missing_config_fails_closed_before_any_request(artifact_dir):
    protocol = Protocol((artifact_dir / "index.html").read_bytes())
    env = dict(ENV, DISCORD_CHANNEL_ID="")
    with pytest.raises(module().DeliveryError) as caught:
        module().deliver_report(artifact_dir, environ=env,
                                transport=httpx.MockTransport(protocol), resolver=lambda host: ["8.8.8.8"])
    assert caught.value.code == "missing_config"
    assert protocol.calls == []


def test_unexpected_files_in_export_directory_fail_closed(artifact_dir, tmp_path):
    directory = tmp_path / "leaky"
    directory.mkdir()
    (directory / "index.html").write_text((artifact_dir / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    (directory / "news.db").write_bytes(b"PRIVATE_DB_CANARY")
    protocol = Protocol((artifact_dir / "index.html").read_bytes())
    with pytest.raises(module().DeliveryError) as caught:
        module().deliver_report(directory, environ=ENV, transport=httpx.MockTransport(protocol),
                                resolver=lambda host: ["8.8.8.8"])
    assert caught.value.code == "unexpected_files"
    assert protocol.calls == []


def test_deployed_html_mismatch_stops_before_any_notification(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.headers["host"] == "abc123--report-fixture.netlify.app"
                     and httpx.Response(200, content=data + b"<!-- tampered -->"))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "html_mismatch"
    assert protocol.brief is None
    assert not any(r.headers["host"] in {"api.telegram.org", "discord.com"} for r in protocol.calls)


def test_redirecting_hosted_url_is_not_followed(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.headers["host"] == "abc123--report-fixture.netlify.app"
                     and httpx.Response(302, headers={"location": "https://example.com/"}))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "http_status"


def test_private_or_foreign_hosted_url_is_rejected(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.url.path == "/api/v1/deploys/" + DEPLOY
                     and httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": "ready",
                                                   "deploy_ssl_url": "https://evil.example.com/"}))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "unsafe_url"


def test_non_global_dns_answer_is_rejected(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Protocol(data)
    with pytest.raises(module().DeliveryError) as caught:
        module().deliver_report(artifact_dir, environ=ENV, transport=httpx.MockTransport(protocol),
                                resolver=lambda host: ["127.0.0.1"])
    assert caught.value.code == "unsafe_dns"
    assert protocol.calls == []


def test_partial_channel_failure_fails_closed_with_receipts(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.headers["host"] == "discord.com" and r.method == "POST"
                     and httpx.Response(403, json={"message": "PRIVATE_DISCORD_ERROR_CANARY"}))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "channel_failure"
    result = caught.value.result
    assert result.telegram.confirmation == "receipt-confirmed"
    assert result.discord.confirmation == "unconfirmed"
    assert result.discord.error_code == "http_status"
    assert result.success is False
    # No retry: exactly one Discord attempt and no second Telegram post.
    assert [r.method for r in protocol.calls if r.headers["host"] == "discord.com"] == ["POST"]


def test_discord_readback_mismatch_is_not_reported_as_delivered(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.headers["host"] == "discord.com" and r.method == "GET"
                     and httpx.Response(200, json={"id": "999999999999999999",
                                                   "channel_id": ENV["DISCORD_CHANNEL_ID"], "content": "PRIVATE_EDIT_CANARY"}))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "channel_failure"
    assert caught.value.result.discord.confirmation == "unconfirmed"
    assert caught.value.result.discord.error_code == "discord_readback_invalid"


def test_telegram_without_official_readback_is_receipt_confirmed_only(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Protocol(data)
    result = run(artifact_dir, protocol)
    assert result.telegram.confirmation == "receipt-confirmed"
    assert not any(r.headers["host"] == "api.telegram.org" and r.method == "GET" for r in protocol.calls)


def test_brief_stays_within_limit_and_carries_no_markdown_or_unsafe_text(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    result = run(artifact_dir, Protocol(data))
    brief = result.brief
    assert len(brief) < 1500
    assert "PRIVATE_" not in brief and "://github.com" not in brief
    assert not any(mark in brief for mark in ("*", "_", "`", "[", "#", "<"))
    assert brief.count(URL) == 1


def test_secrets_never_appear_in_errors_or_receipts(artifact_dir, caplog):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.headers["host"] == "api.telegram.org"
                     and httpx.Response(401, json={"description": "PRIVATE_TELEGRAM_ERROR_CANARY"}))
    with pytest.raises(module().DeliveryError) as caught:
        with caplog.at_level("DEBUG"):
            run(artifact_dir, protocol)
    combined = str(caught.value) + str(caught.value.result) + repr(caught.value.result) + caplog.text
    assert caught.value.code == "channel_failure"
    assert caught.value.result.telegram.error_code == "http_status"
    for secret in ENV.values():
        assert secret not in combined
    for canary in ("PRIVATE_TELEGRAM_ERROR_CANARY", "PRIVATE_DISCORD_ERROR_CANARY"):
        assert canary not in combined


def test_oversized_hosted_response_is_refused(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.headers["host"] == "abc123--report-fixture.netlify.app"
                     and httpx.Response(200, content=b"x" * (4 * 1024 * 1024 + 1)))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "response_too_large"


def test_deploy_state_is_polled_with_backoff_and_never_assumed_ready(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    states = iter(["preparing", "processing"])
    protocol = Guard(data, lambda r: r.url.path == "/api/v1/deploys/" + DEPLOY
                     and httpx.Response(200, json={"id": DEPLOY, "site_id": SITE, "state": next(states),
                                                   "deploy_ssl_url": URL.rstrip("/")}))
    slept = []
    with pytest.raises(module().DeliveryError) as caught:
        module().deliver_report(artifact_dir, environ=ENV, transport=httpx.MockTransport(protocol),
                               resolver=lambda host: ["8.8.8.8"], sleep=slept.append, poll_attempts=2)
    assert caught.value.code == "deploy_not_ready"
    assert slept == [1.0]
    assert not any(r.headers["host"] in {"api.telegram.org", "discord.com"} for r in protocol.calls)


def test_foreign_deploy_id_in_status_is_rejected(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Guard(data, lambda r: r.url.path == "/api/v1/deploys/" + DEPLOY
                     and httpx.Response(200, json={"id": "PRIVATE_DEPLOY_CANARY", "site_id": SITE,
                                                   "state": "ready", "deploy_ssl_url": URL.rstrip("/")}))
    with pytest.raises(module().DeliveryError) as caught:
        run(artifact_dir, protocol)
    assert caught.value.code == "deploy_mismatch"
    assert "PRIVATE_DEPLOY_CANARY" not in str(caught.value)


def test_real_sanitized_export_delivers_a_bounded_brief(artifact_dir, tmp_path_factory):
    real = Path(__file__).parent.parent / "public"
    if not (real / "index.html").is_file():
        pytest.skip("no exported public/index.html in this worktree")
    directory = tmp_path_factory.mktemp("real") / "public"
    directory.mkdir()
    data = (real / "index.html").read_bytes()
    (directory / "index.html").write_bytes(data)
    if len(list(directory.iterdir())) != 1:
        pytest.skip("export directory holds more than the single sanitized file")
    result = run(directory, Protocol(data))
    assert result.hosted.sha256 == hashlib.sha256(data).hexdigest()
    assert len(result.brief) < 1500
    assert result.brief.count(URL) == 1
    assert "metadata only" in result.brief and "not a fresh fetch" in result.brief


def test_cli_reports_safe_failure_code_and_no_credentials(artifact_dir, capsys, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("publish_report_cli", Path(__file__).parent.parent / "scripts/publish_report.py")
    assert spec is not None, "publish_report CLI is missing"
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setenv("NETLIFY_AUTH_TOKEN", "cli-netlify-secret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "cli-telegram-secret")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "cli-discord-secret")
    monkeypatch.setattr(cli, "deliver_report", lambda *a, **k: (_ for _ in ()).throw(
        cli.DeliveryError("channel_failure")))
    code = cli.main(["--export-dir", str(artifact_dir), "--json"])
    captured = capsys.readouterr()
    assert code == 1
    assert "channel_failure" in captured.out
    assert "secret" not in captured.out + captured.err


def test_single_file_digest_readback_then_both_channel_receipts(artifact_dir):
    data = (artifact_dir / "index.html").read_bytes()
    protocol = Protocol(data)
    result = run(artifact_dir, protocol)
    assert result.success is True
    assert result.hosted.url == URL
    assert result.hosted.sha256 == hashlib.sha256(data).hexdigest()
    assert result.telegram.confirmation == "receipt-confirmed"
    assert result.telegram.message_id == "42"
    assert result.discord.confirmation == "independently-read-back"
    assert result.discord.message_id == "999999999999999999"
    assert len(result.brief) < 1500
    assert "Render: 2026-10-01T12:00:00+00:00" in result.brief
    assert "Saved observations: 2026-09-30T10:00:00+00:00" in result.brief
    assert "github-trending: 1" in result.brief
    assert "metadata only" in result.brief
    assert "not a fresh fetch" in result.brief
    assert URL in result.brief
    assert [r.headers["host"] for r in protocol.calls] == ["api.netlify.com"] * 4 + [
        "abc123--report-fixture.netlify.app", "api.telegram.org", "discord.com", "discord.com"]
    assert (artifact_dir / "index.html").read_bytes() == data


def test_unexpected_transport_exception_is_reported_by_class_only(monkeypatch, caplog):
    """A swallowed exception must still be diagnosable without leaking the URL.

    The delivery path deliberately replaces every unexpected exception with a
    safe `request_failed` code, which made a real CI failure impossible to
    diagnose. When DELIVERY_DEBUG is set, the exception *class name* is logged
    so the failure is identifiable; the message and URL never are, because
    httpx messages embed the token-bearing request URL.
    """
    import logging

    from intel_sources.report_delivery import DeliveryError, _Session, _quiet_http_logs

    class Exploding:
        def stream(self, *args, **kwargs):
            raise RuntimeError("connect failed for https://api.telegram.org/bot123:SECRET/")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    session = _Session(None, None, Exploding())
    monkeypatch.setenv("DELIVERY_DEBUG", "1")
    with caplog.at_level(logging.DEBUG, logger="intel_sources.report_delivery"):
        with _quiet_http_logs():
            with pytest.raises(DeliveryError) as caught:
                session.request("GET", "https://api.telegram.org/bot123:SECRET/sendMessage")
    assert caught.value.code == "request_failed"
    logged = caplog.text
    assert "RuntimeError" in logged
    assert "SECRET" not in logged
    assert "SECRET" not in str(caught.value)


def test_debug_log_identifies_host_and_status_without_token(monkeypatch, caplog):
    """The failure record must say WHICH host answered with WHICH status.

    Knowing only that an exception occurred left a real deploy failure
    undiagnosable. Log method, hostname and status code - never the path,
    which carries the Telegram token, and never the body.
    """
    import logging

    from intel_sources.report_delivery import DeliveryError, _Session, _quiet_http_logs

    class Response:
        status_code = 404

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def iter_bytes(self):
            return iter([b""])

    class Client:
        def stream(self, method, url, **kwargs):
            return Response()

    session = _Session(None, None, Client())
    monkeypatch.setenv("DELIVERY_DEBUG", "1")
    with caplog.at_level(logging.DEBUG, logger="intel_sources.report_delivery"):
        with _quiet_http_logs():
            with pytest.raises(DeliveryError) as caught:
                session.request("GET", "https://api.telegram.org/bot123:SECRET/sendMessage")
    assert caught.value.code == "http_status"
    logged = caplog.text
    assert "api.telegram.org" in logged, "the failing host must be identifiable"
    assert "404" in logged, "the failing status must be identifiable"
    assert "SECRET" not in logged
    assert "/bot123" not in logged, "the token-bearing path must never be logged"


def test_debug_log_emits_even_when_root_logger_is_at_warning(monkeypatch, caplog):
    """DEBUG must survive a default WARNING root logger.

    The first attempt at host/status logging never appeared in CI at all:
    `log.debug()` on a logger with no level of its own inherits the root
    logger's WARNING, so the line was silently dropped and the failure stayed
    opaque. The delivery logger must set its own level under DELIVERY_DEBUG.
    """
    import logging

    from intel_sources.report_delivery import DeliveryError, _Session, _quiet_http_logs, log

    class Response:
        status_code = 503

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def iter_bytes(self):
            return iter([b""])

    class Client:
        def stream(self, method, url, **kwargs):
            return Response()

    root = logging.getLogger()
    previous = root.level
    root.setLevel(logging.WARNING)
    try:
        monkeypatch.setenv("DELIVERY_DEBUG", "1")
        session = _Session(None, None, Client())
        with caplog.at_level(logging.DEBUG, logger="intel_sources.report_delivery"):
            with _quiet_http_logs():
                with pytest.raises(DeliveryError):
                    session.request("GET", "https://eli-lain-intel.netlify.app/")
        # Assert the emitted record, not logger internals: pytest's caplog
        # context resets handler levels on exit, so `log.level` afterwards is
        # not evidence of anything.
        records = [r for r in caplog.records if r.name == log.name]
        assert records, "the delivery logger must emit a record"
        assert records[-1].getMessage() == (
            "delivery GET eli-lain-intel.netlify.app -> 503")
    finally:
        root.setLevel(previous)


def test_pinned_address_prefers_reachable_ipv4_and_reports_families():
    """Pin a reachable address, and prefer IPv4 when a host is dual-stack.

    The transport pinned `addresses[0]` from getaddrinfo, whose ordering is
    platform-dependent: this Windows host returns IPv4 only, while a
    dual-stack CI runner may order an unreachable IPv6 literal first. Pinning
    one arbitrary answer turned that into an opaque ConnectError.

    Every candidate must still be validated as global - preferring IPv4 is an
    ordering choice, not a relaxation of the DNS safety rule.
    """
    import ipaddress

    from intel_sources.report_delivery import DeliveryError, _PinnedTransport

    answers = ["2606:4700::1", "104.18.32.7", "172.64.80.1"]
    seen = {}

    class Recorder:
        def handle_request(self, request):
            seen["host"] = request.url.host
            raise RuntimeError("stop here")

        def close(self):
            pass

    # api.netlify.com is in the module allowlist, so this exercises pinning
    # rather than the allowlist guard.
    transport = _PinnedTransport(lambda host: answers, Recorder())
    request = httpx.Request("GET", "https://api.netlify.com/api/v1/user")
    with pytest.raises(RuntimeError):
        transport.handle_request(request)

    pinned = seen["host"].strip("[]")
    assert ipaddress.ip_address(pinned).version == 4, "must prefer a reachable IPv4 literal"
    assert pinned == "104.18.32.7"

    # Preferring IPv4 is an ordering choice, not a relaxation: a non-global
    # answer anywhere in the set is still refused outright.
    unsafe = _PinnedTransport(lambda host: ["2606:4700::1", "127.0.0.1"], Recorder())
    with pytest.raises(DeliveryError) as caught:
        unsafe.handle_request(httpx.Request("GET", "https://api.netlify.com/api/v1/user"))
    assert caught.value.code == "unsafe_dns"
