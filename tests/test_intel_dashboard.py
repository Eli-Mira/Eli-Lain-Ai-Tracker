"""Tests for intel_sources.dashboard module - strict TDD."""
from __future__ import annotations

import json
import tempfile
import threading
import time
from pathlib import Path

import pytest

from intel_sources.settings import default_settings, save_settings


@pytest.fixture
def temp_dirs():
    """Create temporary directories for settings and history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        settings_path = tmp_path / "settings.json"
        history_dir = tmp_path / "history"
        history_dir.mkdir()
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        # Create minimal cockpit template
        (templates_dir / "intel_cockpit.html").write_text(
            '<html><body><input name="csrf_token" value="{{ csrf_token }}"></body></html>',
            encoding="utf-8"
        )
        yield {
            "tmp_path": tmp_path,
            "settings_path": settings_path,
            "history_dir": history_dir,
            "templates_dir": templates_dir,
        }


@ pytest.fixture
def server(temp_dirs):
    """Start a test server and yield its base URL."""
    from intel_sources.dashboard import serve_dashboard, _scan_state

    scan_called = {"count": 0, "settings": None, "event": threading.Event()}

    def run_scan(settings):
        scan_called["count"] += 1
        scan_called["settings"] = settings
        scan_called["event"].set()
        return {"status": "started"}

    srv = serve_dashboard(
        settings_path=str(temp_dirs["settings_path"]),
        history_dir=str(temp_dirs["history_dir"]),
        run_scan=run_scan,
        host="127.0.0.1",
        port=0,  # random port
        templates_dir=str(temp_dirs["templates_dir"]),
    )

    # Wait for server to start
    time.sleep(0.5)

    # Actually get the port from server
    port = srv.server_address[1]
    base_url = f"http://127.0.0.1:{port}"

    yield {
        "base_url": base_url,
        "server": srv,
        "scan_called": scan_called,
    }

    # Reset shared scan state before shutdown
    with _scan_state["lock"]:
        _scan_state["running"] = False

    srv.shutdown()
    srv.server_close()


def _get_csrf_token(base_url: str) -> str:
    """Helper to fetch a fresh CSRF token from the cockpit page."""
    import urllib.request
    import re

    req = urllib.request.Request(f"{base_url}/")
    req.add_header("Origin", "http://127.0.0.1:8768")
    req.add_header("Host", "127.0.0.1:8768")

    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode()
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        assert match, "CSRF token not found in template"
        return match.group(1)


class TestDashboardServer:
    """Tests for the dashboard HTTP server."""

    def test_server_binds_localhost_only(self, server):
        """Server should only bind to 127.0.0.1, not 0.0.0.0."""
        assert server["server"].server_address[0] == "127.0.0.1"

    def test_get_settings_returns_validated_settings(self, server):
        """GET /api/settings returns validated settings with all fields."""
        import urllib.request

        req = urllib.request.Request(f"{server['base_url']}/api/settings")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data["schema_version"] == 1
            assert "sources" in data
            assert "topics" in data
            assert "priorities" in data
            assert "categories" in data
            assert "max_items" in data
            assert "max_age_days" in data
            assert "min_score" in data
            assert "schedule" in data

    def test_get_settings_requires_origin_host(self, server):
        """GET /api/settings requires Origin and Host headers."""
        import urllib.request
        from urllib.error import HTTPError

        req = urllib.request.Request(f"{server['base_url']}/api/settings")
        # No Origin/Host headers

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected request without Origin/Host")
        except HTTPError as e:
            assert e.code == 403

    def test_get_settings_rejects_wrong_origin(self, server):
        """GET /api/settings rejects wrong Origin."""
        import urllib.request
        from urllib.error import HTTPError

        req = urllib.request.Request(f"{server['base_url']}/api/settings")
        req.add_header("Origin", "http://evil.com")
        req.add_header("Host", "127.0.0.1:8768")

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected request with wrong Origin")
        except HTTPError as e:
            assert e.code == 403

    def test_post_settings_requires_csrf_token(self, server):
        """POST /api/settings requires X-CSRF-Token header."""
        import urllib.request
        from urllib.error import HTTPError

        data = json.dumps({"schema_version": 1, "max_items": 3}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/settings",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                # No X-CSRF-Token
            },
        )

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected request without CSRF token")
        except HTTPError as e:
            assert e.code == 403

    def test_post_settings_validates_and_saves(self, server):
        """POST /api/settings validates, saves, and returns exact saved settings."""
        import urllib.request

        # First get a CSRF token from the cockpit page
        csrf_token = _get_csrf_token(server["base_url"])

        # Now POST settings with CSRF token
        data = json.dumps({"schema_version": 1, "max_items": 3}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/settings",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            saved = json.loads(resp.read().decode())
            assert saved["schema_version"] == 1
            assert saved["max_items"] == 3
            # Should have all fields with defaults filled
            assert "sources" in saved
            assert "topics" in saved
            assert "priorities" in saved
            assert "categories" in saved
            assert "max_age_days" in saved
            assert "min_score" in saved
            assert "schedule" in saved

    def test_post_settings_rejects_invalid_data(self, server):
        """POST /api/settings rejects invalid settings data."""
        import urllib.request
        from urllib.error import HTTPError

        # Get CSRF token
        csrf_token = _get_csrf_token(server["base_url"])

        # POST invalid settings
        data = json.dumps({"schema_version": 1, "max_items": 0}).encode()  # out of bounds
        req = urllib.request.Request(
            f"{server['base_url']}/api/settings",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected invalid settings")
        except HTTPError as e:
            assert e.code == 400

    def test_post_settings_conflict_when_scan_running(self, server):
        """POST /api/settings returns 409 when scan is running."""
        import urllib.request
        from urllib.error import HTTPError

        # Start a scan first
        server["scan_called"]["event"].clear()

        # Get CSRF token for scan
        csrf_token = _get_csrf_token(server["base_url"])

        # Start scan
        data = json.dumps({}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/scan",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

        # Wait for scan to start
        server["scan_called"]["event"].wait(timeout=1)

        # Now try to POST settings - should get 409
        # Need a fresh CSRF token since the previous one was consumed
        fresh_csrf = _get_csrf_token(server["base_url"])
        data = json.dumps({"schema_version": 1, "max_items": 5}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/settings",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": fresh_csrf,
            },
        )

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected settings change during scan")
        except HTTPError as e:
            assert e.code == 409


class TestStatusEndpoint:
    """Tests for GET /api/status endpoint."""

    def test_status_returns_standard_fields(self, server):
        """GET /api/status returns running, status, last_error, last_report."""
        import urllib.request

        req = urllib.request.Request(f"{server['base_url']}/api/status")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert "running" in data
            assert "status" in data
            assert "last_error" in data
            assert "last_report" in data
            # No traceback in status fields
            assert "traceback" not in str(data).lower()


class TestScanEndpoint:
    """Tests for POST /api/scan endpoint."""

    def test_scan_single_flight(self, server):
        """POST /api/scan is single-flight - only one scan at a time."""
        import urllib.request
        from urllib.error import HTTPError

        # Get CSRF token for first scan
        csrf_token = _get_csrf_token(server["base_url"])

        # Start first scan
        data = json.dumps({}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/scan",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

        # Try to start second scan - should get 409
        # Need fresh CSRF token
        fresh_csrf = _get_csrf_token(server["base_url"])
        req2 = urllib.request.Request(
            f"{server['base_url']}/api/scan",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": fresh_csrf,
            },
        )

        try:
            urllib.request.urlopen(req2)
            pytest.fail("Should have rejected second concurrent scan")
        except HTTPError as e:
            assert e.code == 409

    def test_scan_calls_injected_callback(self, server):
        """POST /api/scan calls the injected run_scan callback with settings."""
        import urllib.request

        # Get CSRF token
        csrf_token = _get_csrf_token(server["base_url"])

        # Start scan
        data = json.dumps({}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/scan",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200

        # Wait for callback
        server["scan_called"]["event"].wait(timeout=2)

        assert server["scan_called"]["count"] == 1
        assert server["scan_called"]["settings"] is not None
        assert server["scan_called"]["settings"]["schema_version"] == 1

    def test_no_scan_on_start(self, server):
        """Scan is NOT automatically started on server start."""
        assert server["scan_called"]["count"] == 0


class TestHistoryEndpoint:
    """Tests for GET /api/history and report serving."""

    def test_history_returns_reports_list(self, server, temp_dirs):
        """GET /api/history returns list of completed reports."""
        import urllib.request

        # Create a test report file
        report_file = temp_dirs["history_dir"] / "report_20260101_120000.html"
        report_file.write_text("<html>Test Report</html>")

        req = urllib.request.Request(f"{server['base_url']}/api/history")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert "reports" in data
            assert isinstance(data["reports"], list)
            assert len(data["reports"]) >= 1
            report = data["reports"][0]
            assert "id" in report
            assert "report_date" in report
            assert "generated_at" in report
            assert "selected_count" in report
            assert "url" in report
            assert report["url"].startswith("/reports/")

    def test_report_serving_safe_no_traversal(self, server, temp_dirs):
        """Report serving at /reports/<id>.html is safe from path traversal."""
        import urllib.request
        from urllib.error import HTTPError

        # Create a test report
        report_file = temp_dirs["history_dir"] / "report_20260101_120000.html"
        report_file.write_text("<html>Test Report</html>")

        # Valid request
        req = urllib.request.Request(f"{server['base_url']}/reports/report_20260101_120000.html")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert "Test Report" in resp.read().decode()

        # Path traversal attempt
        req = urllib.request.Request(f"{server['base_url']}/reports/../../etc/passwd")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected path traversal")
        except HTTPError as e:
            assert e.code in (400, 403, 404)


class TestCockpitTemplate:
    """Tests for serving the cockpit template."""

    def test_serves_cockpit_template_with_csrf(self, server):
        """GET / serves intel_cockpit.html with csrf_token."""
        import urllib.request

        req = urllib.request.Request(f"{server['base_url']}/")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            html = resp.read().decode()
            assert "csrf_token" in html
            # Should not leak any browser auth
            assert "password" not in html.lower()
            assert "secret" not in html.lower()

    def test_oversized_request_rejected(self, server):
        """Requests with oversized bodies are rejected."""
        import urllib.request
        from urllib.error import HTTPError

        # Get CSRF token
        csrf_token = _get_csrf_token(server["base_url"])

        # POST oversized body (> 1MB)
        oversized = json.dumps({"data": "x" * 2_000_000}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/settings",
            data=oversized,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected oversized request")
        except HTTPError as e:
            assert e.code == 413


class TestSecurityHeaders:
    """Tests for security headers and protections."""

    def test_no_cors_headers(self, server):
        """Responses should not have CORS headers."""
        import urllib.request

        req = urllib.request.Request(f"{server['base_url']}/api/settings")
        req.add_header("Origin", "http://127.0.0.1:8768")
        req.add_header("Host", "127.0.0.1:8768")

        with urllib.request.urlopen(req) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            assert "access-control-allow-origin" not in headers
            assert "access-control-allow-credentials" not in headers

    def test_rejects_unknown_keys_in_settings(self, server):
        """POST /api/settings rejects unknown keys."""
        import urllib.request
        from urllib.error import HTTPError

        # Get CSRF token
        csrf_token = _get_csrf_token(server["base_url"])

        # POST with unknown key
        data = json.dumps({"schema_version": 1, "unknown_key": "value"}).encode()
        req = urllib.request.Request(
            f"{server['base_url']}/api/settings",
            data=data,
            method="POST",
            headers={
                "Origin": "http://127.0.0.1:8768",
                "Host": "127.0.0.1:8768",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
        )

        try:
            urllib.request.urlopen(req)
            pytest.fail("Should have rejected unknown key")
        except HTTPError as e:
            assert e.code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
