#!/usr/bin/env python3
"""
DEUSPROOF DEFERRED RESOLVER
============================
The notarizer hit the register's hourly per-IP certification limit
("Hourly certification limit reached for this IP"). Files that could not be
sealed within their bounded retry budget were recorded as `deferred` — the run
continues, nothing is lost.

This script resolves the deferred set. It does NOT blind-poll:

1. It reads the register's own activity timestamp (`/api/stats/pulse` →
   `por_su_cuenta.ultima`) to learn WHEN the last successful certification
   happened. The hourly window therefore closes `ultima + 3600s`.
2. It waits until that window has actually passed before spending requests.
3. It seals the deferred files with the same bounded-retry rule, so a still-
   closed window defers again instead of blocking.

The API sends no `Retry-After` header, so the window has to be derived. The
derivation is the only thing that makes this efficient — without it, the
resolver would burn the same quota the notarizer just exhausted.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

PROGRESS = "/home/sah/.config/sah-vault/.deusproof-chain-progress.json"
NOTARIZER = "/home/sah/.hermes/scripts/kiswarm-chain-notarize.py"
PULSE = "https://deusproof.com/api/stats/pulse"
WINDOW_SECONDS = 3600
MAX_WAIT = 3000          # do not wait longer than ~50 min in one run


def last_activity():
    """Timestamp of our account's last certification, or None."""
    try:
        req = urllib.request.Request(PULSE, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            d = json.loads(resp.read())
        s = d.get("por_su_cuenta", {}).get("ultima")
        if not s:
            return None
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def deferred_set():
    if not os.path.exists(PROGRESS):
        return []
    try:
        d = json.load(open(PROGRESS))
    except Exception:
        return []
    return d.get("deferred", [])


def main():
    defer = deferred_set()
    if not defer:
        print("  nothing deferred — nothing to resolve")
        return 0

    print("  deferred files: {0}".format(len(defer)))
    for x in defer:
        print("    - {0}".format(x.get("file", "?")))

    last = last_activity()
    if last:
        opens_at = last + timedelta(seconds=WINDOW_SECONDS)
        now = datetime.now(timezone.utc)
        wait = (opens_at - now).total_seconds()
        print("  last successful certification: {0}".format(last.isoformat()))
        print("  window opens at:               {0}".format(opens_at.isoformat()))
        if wait > 0:
            if wait > MAX_WAIT:
                print("  window opens in {0:.0f}s — beyond this run, deferring to the next slot".format(wait))
                return 2
            print("  waiting {0:.0f}s for the window to open".format(wait))
            time.sleep(wait)
    else:
        print("  could not determine the window — attempting immediately")

    # The window should be open now. Re-run the notarizer, which resumes from
    # the progress file and will pick up anything still unsealed.
    r = subprocess.run([sys.executable, NOTARIZER], capture_output=True, text=True, timeout=2700)
    out = (r.stdout or "")[-2500:]
    print(out)

    # Report the new state
    try:
        d = json.load(open(PROGRESS))
        print("  SEALED total: {0}   deferred: {1}   errors: {2}".format(
            len(d.get("records", [])), len(d.get("deferred", [])), len(d.get("errors", []))))
        for x in d.get("deferred", []):
            print("    still deferred: {0}".format(x.get("file", "?")))
    except Exception as e:
        print("  could not read the progress file: {0}".format(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
