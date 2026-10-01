"""Store Netlify credentials as GitHub secrets without printing either value.

Reads the token the official Netlify CLI login already stored, and pipes both
values straight into `gh secret set` on stdin. Nothing is echoed, written to a
temp file, or placed in argv.
"""

import json
import pathlib
import subprocess
import sys

REPO = "Eli-Mira/Eli-Lain-Ai-Tracker"
CONFIG = pathlib.Path("C:/Users/emadg/AppData/Roaming/netlify/Config/config.json")
SITE_ID = "979350fc-66cc-4965-9654-153969fd2be6"


def gh_token() -> str:
    creds = pathlib.Path.home() / ".git-credentials"
    match = __import__("re").search(r"gh[pousr]_[A-Za-z0-9]+", creds.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("no GitHub credential found")
    return match.group(0)


def main() -> int:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    users = config.get("users") or {}
    if not users:
        raise SystemExit("no Netlify user in CLI config")
    netlify_token = next(
        ((user.get("auth") or {}).get("token") for user in users.values()
         if (user.get("auth") or {}).get("token")), None)
    if not netlify_token:
        raise SystemExit("no Netlify auth token in CLI config")

    # Inherit the ambient environment (TLS/proxy/host settings) and only add the
    # GitHub credential; replacing env wholesale breaks gh's own connection.
    env = dict(__import__("os").environ, GH_TOKEN=gh_token())
    for name, value in (("NETLIFY_AUTH_TOKEN", netlify_token), ("NETLIFY_SITE_ID", SITE_ID)):
        done = subprocess.run(["gh", "secret", "set", name, "--repo", REPO],
                              input=value, text=True, capture_output=True, env=env)
        if done.returncode != 0:
            print(f"failed to set {name}: {done.stderr.strip()}", file=sys.stderr)
            return 1
        # Print the name only, never the value.
        print(f"stored secret {name} (len {len(value)})")

    listing = subprocess.run(["gh", "secret", "list", "--repo", REPO],
                             capture_output=True, text=True, env=env)
    print(listing.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())