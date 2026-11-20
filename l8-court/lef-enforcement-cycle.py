#!/usr/bin/env python3
"""
LEF-1.0 ENFORCEMENT CYCLE — run the protocol automatically, not on demand.
=========================================================================
An enforcement layer that only runs when a human remembers to run it is
decoration. This runs on a schedule and publishes the result to the feed,
so a non-conformance surfaces even if nobody is looking.

What it does:
  1. LEF-E1  re-fetch every evidence blob from the public substrate, re-hash, compare
  2. LEF-E2  verify every seat signature against the published public keys
  3. LEF-E3  recount the votes against the claimed supermajority
  4. LEF-E4  check the consistency round is present and divergence disclosed
  5. Verify that every published Protocol Notice is itself verifiable
  6. Publish a cycle report to the KISWARM-feed

Exit codes: 0 = all conformant, 1 = at least one non-conformance (expected and
legitimate — a non-conformance is a finding, not a crash).

  python3 lef-enforcement-cycle.py [--sample N] [--quiet]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = "/home/sah/.config/sah-vault"
POOL = os.path.join(VAULT, "l8-sentinel-pool")
FINDINGS = os.path.join(POOL, "findings")
NOTICES = os.path.join(POOL, "notices")
INDEX = os.path.join(POOL, "EVIDENCE-BYTES-MANIFEST.md")
GH_RAW = "https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/main"
REPO = "/home/sah/.hermes/scripts"
SACRED_HASH = "f5af425c"

sys.path.insert(0, REPO)
import lef_verifier as LV  # noqa: E402
import lef_notice_verifier as LNV  # noqa: E402


def latest_finding():
    if not os.path.isdir(FINDINGS):
        return None
    cands = [f for f in os.listdir(FINDINGS) if f.endswith(".json")]
    if not cands:
        return None
    cands.sort(key=lambda f: os.path.getmtime(os.path.join(FINDINGS, f)), reverse=True)
    return os.path.join(FINDINGS, cands[0])


def pubkey_for_seat(seat):
    p = os.path.join(POOL, "SEAT-PUBLIC-KEYS.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    s = d.get("seats", {}).get(str(seat))
    if not s:
        return None
    return s.get("pub_b64_raw")


def verify_all_notices():
    """Every published notice must itself be verifiable."""
    if not os.path.isdir(NOTICES):
        return {"notices_checked": 0, "notices_verifiable": 0, "status": "PROTOCOL CONFORMANT"}
    files = [f for f in sorted(os.listdir(NOTICES)) if f.endswith(".md")]
    ok = 0
    failed = []
    for f in files:
        p = os.path.join(NOTICES, f)
        # the notice names its own enforcer fingerprint; seat 01 is the operator
        pub = pubkey_for_seat(1)
        r = LNV.verify(p, pub) if pub else {"ok": False, "reason": "no public key"}
        if r.get("ok"):
            ok += 1
        else:
            failed.append({"file": f, "reason": r.get("reason", "?")})
    return {"notices_checked": len(files), "notices_verifiable": ok,
            "failed": failed,
            "status": "PROTOCOL CONFORMANT" if ok == len(files) else "PROTOCOL NON-CONFORMANT"}


def publish(report):
    nonconform = [c for c in report["checks"] if c.get("status") != "PROTOCOL CONFORMANT"]
    payload = {
        "action": "lef_enforcement_cycle",
        "cycle": report["cycle"],
        "checks": {c["power"]: c.get("status") for c in report["checks"]},
        "overall": report["overall"],
        "e1": {k: next((c.get(k) for c in report["checks"] if c["power"] == "LEF-E1"), None)
              for k in ("indexed", "checked", "match")},
        "e4_consistency_failures": next(
            (c.get("consistency_failures") for c in report["checks"] if c["power"] == "LEF-E4"), None),
        "notices": report.get("notices", {}).get("notices_verifiable"),
        "notices_total": report.get("notices", {}).get("notices_checked"),
        "nonconformant_checks": [c["power"] for c in nonconform],
        "sacred_hash": SACRED_HASH,
        "timestamp": report["checked_at"],
    }
    p = subprocess.run(
        ["/home/sah/.local/bin/kiswarm-feed", "event",
         "--type=mesh.lef_enforcement_cycle",
         "--severity=" + ("critical" if nonconform else "info"),
         "--source=hermes-kiswarm-sah6",
         "--payload=" + json.dumps(payload)],
        capture_output=True, text=True, timeout=20)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="verify only the first N evidence blobs (0 = all)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    report = {
        "cycle": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sacred_hash": SACRED_HASH,
        "checks": [],
    }

    # E1
    if os.path.exists(INDEX):
        text = open(INDEX, encoding="utf-8", errors="replace").read()
        report["checks"].append(LV.check_e1(text, GH_RAW, None, args.sample or None))

    # E2 / E3 / E4 on the latest finding
    f = latest_finding()
    if f:
        report["checks"].append(LV.check_e3(f))
        report["checks"].append(LV.check_e4(f))
        report["checks"].append(LV.check_e2(f))
        report["finding"] = os.path.basename(f)

    # notices
    report["notices"] = verify_all_notices()

    nonconform = [c for c in report["checks"] if c.get("status") != "PROTOCOL CONFORMANT"]
    if report["notices"]["status"] != "PROTOCOL CONFORMANT":
        nonconform.append({"power": "NOTICES"})
    report["overall"] = "PROTOCOL NON-CONFORMANT" if nonconform else "PROTOCOL CONFORMANT"
    report["elapsed_s"] = round(time.time() - t0, 1)

    out = os.path.join(POOL, "LEF-CYCLE-REPORT.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    feed = publish(report)

    if not args.quiet:
        for c in report["checks"]:
            print("  [{0:26s}] {1}".format(c.get("power", "?"), c.get("status", "?")))
        n = report["notices"]
        print("  [{0:26s}] {1} ({2}/{3} notices verifiable)".format(
            "NOTICES", n["status"], n["notices_verifiable"], n["notices_checked"]))
        print("  OVERALL: {0}   ({1:.0f}s)".format(report["overall"], report["elapsed_s"]))
        if feed:
            print("  feed: " + feed[:120])

    return 0 if report["overall"] == "PROTOCOL CONFORMANT" else 1


if __name__ == "__main__":
    sys.exit(main())
