"""Local verification artifact builder: internal + public renders from saved data only."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src/tracker-core"))

from intel_sources.public_report import build_public_payload, export_public_report
from intel_sources.recommendations import evaluate_projects
from tracker_core.reporter_html import LainReporter

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
CATEGORIES = ("shortlist", "deferred", "excluded")


def main(out_dir: Path) -> None:
    state = json.loads((ROOT / "data/intel_state.json").read_text(encoding="utf-8"))
    evaluated = evaluate_projects(state["items"], now=NOW)
    groups = evaluated["groups"]
    reviewed = {entry["id"] for group in groups.values() for category in CATEGORIES
                for entry in group[category]}
    internal = LainReporter().save(
        out_dir / "internal" / "elain_project_shortlists.html", api_items=[], tool_items=state["items"],
        report_date="2026-10-01", generated_at="12:00 UTC",
        runtime_source="Local verification render from saved inventory",
        recommendation_groups=groups,
        recommendation_coverage={**evaluated["coverage"], "inventory_count": evaluated["inventory_count"],
                                 "reviewed_count": len(reviewed)})
    # Reuse the real fail-closed export path so the CSP/no-referrer public artifact is verified too.
    payload = build_public_payload(state, now=NOW, max_items_per_source=25)
    public = export_public_report(ROOT / "data/intel_state.json", ROOT / "data/news.db",
                                  out_dir / "public", now=NOW, max_items_per_source=25)
    print(json.dumps({
        "internal": {"path": str(internal), "sha256": hashlib.sha256(internal.read_bytes()).hexdigest(),
                     "bytes": internal.stat().st_size, "tool_items": len(state["items"]),
                     "shortlists": {key: len(group["shortlist"]) for key, group in groups.items()},
                     "deferred": {key: len(group["deferred"]) for key, group in groups.items()},
                     "excluded": {key: len(group["excluded"]) for key, group in groups.items()},
                     "reviewed_count": len(reviewed), "discovery_count": evaluated["coverage"]["discovery_count"]},
        "public": {"path": str(public), "sha256": hashlib.sha256(public.read_bytes()).hexdigest(),
                   "bytes": public.stat().st_size, "exported": len(payload["tool_items"]),
                   "coverage": payload["recommendation_coverage"]},
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
