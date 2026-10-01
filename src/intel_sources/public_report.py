"""Fail-closed public HTML boundary. Never hand internal dictionaries to a renderer."""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import closing
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Any
from urllib.parse import urlsplit

from .store import parse_time

MAX_STATE_BYTES = 16 * 1024 * 1024
PUBLIC_SOURCES = {
    "openrouter-models": ("https://openrouter.ai/api/v1/models", "Public model listing; not inference verification."),
    "openrouter-providers": ("https://openrouter.ai/api/v1/providers", "Public hosting-provider listing; not account availability."),
    "unorouter-models": ("https://api.unorouter.com/api/pricing/catalog", "Public pricing catalog; not key-accessible inventory."),
    "github-trending": ("https://github.com/trending", "Observed trending pages only; not all GitHub repositories."),
    "skills-sh": ("https://skills.sh", "Observed public leaderboards only; not the full skill catalog."),
}
PROJECT_TYPES = frozenset({"agents", "audio", "automation", "data", "design", "devops",
    "documentation", "embeddings", "image-generation", "mobile", "multimodal", "reasoning",
    "rerank", "security", "speech", "text", "tools", "transcription", "video", "vision", "web"})


def public_http_url(value: Any) -> str:
    """Allow unambiguous public DNS HTTP(S) links, unchanged; no network/DNS calls.

    Queries, fragments, percent escapes, non-default ports and all IP literals are
    intentionally disallowed rather than trying to recognize every secret format.
    Exported discoveries are further restricted to their source's exact hostname.
    """
    if not isinstance(value, str) or not value or len(value) > 600:
        return ""
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
        return ""
    if any(c in value for c in "\\<>\"'`%?#"):
        return ""
    if re.search(r"(?i)(?:sk-|gh[pousr]_|github_pat_|bearer|password|api[_-]?key|access[_-]?token|secret)", value):
        return ""
    try:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if parsed.scheme not in {"http", "https"} or parsed.username is not None or parsed.password is not None:
            return ""
        if parsed.port not in {None, 80 if parsed.scheme == "http" else 443}:
            return ""
        if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host):
            return ""  # Also rejects integer, hex, shorthand and IPv6 host encodings.
        if host.endswith((".localhost", ".local", ".localdomain", ".internal", ".lan", ".home", ".home.arpa",
                          ".corp", ".intranet", ".test", ".invalid", ".onion")):
            return ""
        if any(part in {".", ".."} for part in parsed.path.split("/")):
            return ""
    except ValueError:
        return ""
    return value


def _public_identity(row: dict[str, Any], source: str) -> tuple[str, str] | None:
    """Bind each public identifier to its expected catalog host and detail path."""
    rules = {
        "openrouter-models": ("openrouter:model:", "openrouter.ai", "/", 2),
        "openrouter-providers": ("openrouter:provider:", "openrouter.ai", "/provider/", 1),
        "unorouter-models": ("unorouter:model:", "unorouter.com", "/en/models/", 1),
        "github-trending": ("github:", "github.com", "/", 2),
        "skills-sh": ("skills:", "skills.sh", "/", 3),
    }
    prefix, host, path_prefix, segments = rules[source]
    identifier = row.get("id")
    url = public_http_url(row.get("url"))
    if not isinstance(identifier, str) or not identifier.startswith(prefix) or not url:
        return None
    slug = identifier[len(prefix):]
    # This repository is expressly private even if a forged cache labels it public.
    if source == "github-trending" and slug.casefold() == "eli-mira/eli-lain-ai-tracker":
        return None
    parts = slug.split("/")
    if len(parts) != segments or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}", part) for part in parts):
        return None
    parsed = urlsplit(url)
    expected = path_prefix + slug
    matches = parsed.path.casefold() == expected.casefold() if source == "github-trending" else parsed.path == expected
    if parsed.scheme != "https" or parsed.hostname != host or not matches:
        return None
    return identifier, url


def _public_title(value: Any, identifier: str, source: str) -> str:
    # Titles are the only selected free text. Never use summaries, errors or raw evidence.
    if (isinstance(value, str) and 0 < len(value) <= 180
            and not value.startswith(("/", "~/"))
            and not any(ord(c) < 32 or ord(c) == 127 for c in value)
            and not any(c in value for c in "<>\\`=@")
            and not re.search(r"(?i)(?:https?://|file:|localhost|[a-z]:/|/users/|/home/|/tmp/|sk-|gh[pousr]_|github_pat_|bearer|password|api[_ -]?key|access[_ -]?token|\btoken\b|secret|account[_ -]?id|key[_ -]?id|traceback|\b\d{1,3}(?:\.\d{1,3}){3}\b|\.(?:internal|local|localhost|lan|home|corp)\b|\[[a-f0-9:]+\])", value)):
        return value
    # A safe identity was already bound to the public detail-page URL.
    prefix_lengths = {"openrouter-models": len("openrouter:model:"),
                      "openrouter-providers": len("openrouter:provider:"),
                      "unorouter-models": len("unorouter:model:"),
                      "github-trending": len("github:"), "skills-sh": len("skills:")}
    return identifier[prefix_lengths[source]:]


def _timestamp(value: Any, now: datetime) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value):
        return None
    parsed = parse_time(value)
    return value if isinstance(value, str) and parsed is not None and parsed <= now else None


def build_public_payload(state: dict[str, Any], *, now: datetime | None = None,
                         max_items_per_source: int = 100) -> dict[str, Any]:
    """Project saved public discovery observations into the unchanged Lain contract."""
    if (not isinstance(state, dict) or not isinstance(state.get("items"), list)
            or not isinstance(state.get("sources"), list)):
        raise ValueError("saved state must contain items and sources lists")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("render time must include a timezone")
    now = now.astimezone(timezone.utc)
    if type(max_items_per_source) is not int or not 1 <= max_items_per_source <= 200:
        raise ValueError("export limit must be an integer from 1 to 200")
    sources = {s["name"]: s for s in state.get("sources", [])
               if isinstance(s, dict) and isinstance(s.get("name"), str) and s["name"] in PUBLIC_SOURCES}
    tools = []
    counts = {name: 0 for name in PUBLIC_SOURCES}
    seen = set()
    candidates = [r for r in state.get("items", []) if isinstance(r, dict)
                  and isinstance(r.get("source"), str) and isinstance(r.get("id"), str)]
    for row in sorted(candidates, key=lambda r: (r["source"], r["id"])):
        source = row.get("source")
        if source not in PUBLIC_SOURCES:
            continue
        identity = _public_identity(row, source)
        if identity is None or (source, identity[0]) in seen:
            continue
        identifier, url = identity
        seen.add((source, identifier))
        checked = _timestamp(row.get("checked_at"), now)
        first = _timestamp(row.get("first_seen"), now)
        evidence = {"observed_at": checked or "not supplied", "first_observed_at": first or "not supplied"}
        freshness = "unverified" if checked is None else "fresh" if (
            (now - parse_time(checked)).total_seconds() <= 24 * 3600
            and sources.get(source, {}).get("status") in ("ok", "partial")
            and not row.get("not_observed_in_latest_fetch")) else "stale"
        summary = ("Public listing. Inference and free entitlement unverified."
                   if source in {"openrouter-models", "openrouter-providers", "unorouter-models"}
                   else "Public discovery listing; advisory only, not evaluated or executed.")
        tools.append({"id": identifier, "headline": _public_title(row.get("headline"), identifier, source), "source": source,
                      "url": url, "summary": summary,
                      "project_types": sorted({t for t in row.get("project_types", [])
                                               if isinstance(t, str) and t in PROJECT_TYPES})
                          if isinstance(row.get("project_types"), list) else [],
                      "freshness": freshness, "evidence": [evidence]})
        counts[source] += 1
    full_inventory = tools
    discovery = [{"id": row["id"], "headline": row["headline"], "url": row["url"],
                  "source": row["source"], "freshness": row["freshness"],
                  "checked_at": None if row["evidence"][0]["observed_at"] == "not supplied" else row["evidence"][0]["observed_at"],
                  "evidence": {}}
                 for row in full_inventory if row["source"] in {"github-trending", "skills-sh"}]
    recommendations = {}
    if discovery:
        from .recommendations import evaluate_projects
        evaluated = evaluate_projects(discovery, now=now)
        groups = evaluated["groups"]
        reviewed = set()
        for group in groups.values():
            for category in ("shortlist", "deferred", "excluded"):
                for entry in group[category]:
                    reviewed.add(entry["id"])
                    entry.pop("evidence", None)
        recommendations = {"recommendation_groups": groups, "recommendation_coverage": {
            "reviewed_count": len(reviewed), "discovery_count": len(discovery),
            "inventory_count": len(full_inventory), "shortlist_limit_per_project": 4,
            "max_items_per_source": max_items_per_source, "inventory_replaced": False}}
    tools = []
    counts = {name: 0 for name in PUBLIC_SOURCES}
    for row in full_inventory:
        if counts[row["source"]] < max_items_per_source:
            tools.append(row)
            counts[row["source"]] += 1
    if recommendations:
        recommendations["recommendation_coverage"]["exported_count"] = len(tools)
    public_sources = []
    for name, row in sources.items():
        url, coverage = PUBLIC_SOURCES[name]
        status = row.get("status") if row.get("status") in ("ok", "partial", "error", "skipped") else "unverified"
        public_sources.append({"name": name, "status": status, "checked_at": _timestamp(row.get("checked_at"), now),
                               "item_count": counts[name], "url": url,
                               "coverage": f"{coverage} Export bounded to {max_items_per_source} rows per source; counts are exported rows."})
    return {**recommendations, "api_items": [], "news_items": [], "tool_items": tools, "source_items": public_sources,
            "change_items": [], "action_items": [], "report_date": now.strftime("%Y-%m-%d"),
            "generated_at": now.isoformat(), "persona_image_url": None, "baseline": False,
            "runtime_source": "Public sanitized export of saved observations; not a fresh fetch. Provider statuses, changes, actions and news are excluded, not evaluated by this export. Private source coverage is omitted."}


def read_saved_inputs(state_path: str | Path, news_db_path: str | Path, *,
                      news_limit: int = 100) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read saved inputs only. Returned news stays internal and is never rendered."""
    if type(news_limit) is not int or not 1 <= news_limit <= 200:
        raise ValueError("news read limit must be an integer from 1 to 200")
    state_path, news_db_path = Path(state_path), Path(news_db_path)
    with state_path.open("rb") as handle:
        data = handle.read(MAX_STATE_BYTES + 1)
    if len(data) > MAX_STATE_BYTES:
        raise ValueError("saved state exceeds maximum size")
    state = json.loads(data.decode("utf-8"))
    news = []
    if news_db_path.is_file():
        with closing(sqlite3.connect(news_db_path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            news = [dict(row) for row in conn.execute(
                "SELECT source, title, url, published_date, fetched_date, summary "
                "FROM news_items ORDER BY fetched_date DESC, id DESC LIMIT ?", (news_limit,))]
    return state, news


def _check_export_directory(directory: Path) -> None:
    # Reject symlinks and Windows junction/reparse-point ancestors, not just index.
    for path in (directory.absolute(), *directory.absolute().parents):
        if path.is_symlink() or (path.exists() and getattr(path.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("export directory must not contain links or reparse points")
    if directory.exists():
        if not directory.is_dir():
            raise ValueError("export directory must be a directory")
        for entry in directory.iterdir():
            if entry.name != "index.html" or not entry.is_file() or entry.is_symlink():
                raise ValueError("export directory may contain only a regular index.html")
            if getattr(entry.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError("index.html must not be a reparse point")


def _standalone_html(html: str) -> str:
    """Keep the original markup/styles/filter; block all automatic network access."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    if soup.select("script[src], link, img, iframe, object, embed, form, base, audio, video, source"):
        raise ValueError("public template contains an external or active dependency")
    if any(re.search(r"(?i)(?:url\s*\(|@import)", style.get_text()) for style in soup.select("style")):
        raise ValueError("public template contains a CSS dependency")
    if any(public_http_url(a.get("href")) != a.get("href") for a in soup.select("a[href]")):
        raise ValueError("public template contains an unsafe link dependency")
    if any(key.lower().startswith("on") for tag in soup.find_all(True) for key in tag.attrs):
        raise ValueError("public template contains an active event dependency")
    script_hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(script.get_text().encode("utf-8")).digest()).decode("ascii") + "'"
                     for script in soup.select("script")]
    policy = ("default-src 'none'; script-src " + (" ".join(script_hashes) or "'none'") +
              "; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; font-src 'none'; "
              "object-src 'none'; media-src 'none'; base-uri 'none'; form-action 'none'")
    if '<meta charset="UTF-8">' not in html:
        raise ValueError("public template head dependency is unsupported")
    return html.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n'
                        f'<meta http-equiv="Content-Security-Policy" content="{policy}">\n'
                        '<meta name="referrer" content="no-referrer">', 1)


def export_public_report(state_path: str | Path, news_db_path: str | Path, export_dir: str | Path,
                         *, now: datetime | None = None, max_items_per_source: int = 100) -> Path:
    """Produce a single Lain index.html from explicitly projected saved state."""
    from tracker_core.reporter_html import LainReporter

    directory = Path(export_dir)
    _check_export_directory(directory)
    state, _internal_news = read_saved_inputs(state_path, news_db_path)
    payload = build_public_payload(state, now=now, max_items_per_source=max_items_per_source)
    html = _standalone_html(LainReporter().render(**payload))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "index.html"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=directory,
                                         prefix=".public-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(html)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
