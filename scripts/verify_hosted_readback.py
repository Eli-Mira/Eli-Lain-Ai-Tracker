"""Attempt an exact-bytes readback of the hosted artifact.

Prints only status/size/hash — never the body. Tries several network paths so a
single blocked route is distinguishable from a genuinely unreachable site.
"""

import hashlib
import socket
import ssl
import sys
import urllib.request

URL = "https://eli-lain-intel.netlify.app/"
LOCAL = "public/index.html"


def via_urllib(timeout=30):
    request = urllib.request.Request(URL, headers={"User-Agent": "eli-lain-verify/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def via_curl(timeout=60):
    import subprocess
    done = subprocess.run(
        ["curl", "-sS", "--max-time", str(timeout), "--ipv4", "-o", "-",
         "-w", "\n__STATUS__%{http_code}", URL],
        capture_output=True, text=True)
    if done.returncode != 0:
        return None, done.stderr.strip()[:200]
    body, _, status = done.stdout.rpartition("\n__STATUS__")
    return int(status or 0), body.encode("utf-8", "replace")


def main():
    local = open(LOCAL, "rb").read()
    local_hash = hashlib.sha256(local).hexdigest()
    print("local  ", local_hash, len(local))

    try:
        addresses = {info[4][0] for info in socket.getaddrinfo("eli-lain-intel.netlify.app", 443)}
        print("resolved", sorted(addresses))
    except OSError as error:
        print("dns failed:", error)

    for name, fetch in (("urllib", via_urllib), ("curl", via_curl)):
        try:
            status, body = fetch()
        except Exception as error:  # noqa: BLE001
            print(f"{name:8} EXCEPTION {type(error).__name__}: {str(error)[:120]}")
            continue
        if status is None:
            print(f"{name:8} FAILED {body}")
            continue
        if not isinstance(body, bytes):
            body = str(body).encode()
        digest = hashlib.sha256(body).hexdigest()
        print(f"{name:8} status={status} bytes={len(body)} sha256={digest} "
              f"match={digest == local_hash}")
        if status == 200 and digest == local_hash:
            print("VERIFIED: hosted bytes are byte-identical to the local export")
            return 0
    print("NOT VERIFIED: could not obtain matching hosted bytes")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())