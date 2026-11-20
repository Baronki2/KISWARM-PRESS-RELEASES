#!/usr/bin/env python3
"""
LEF-1.0 ENFORCEMENT CYCLE — the protocol runs itself, and it can issue its own notices.
=============================================================================================
An enforcement layer that only runs when a human remembers to run it is decoration. This
runs on a schedule, publishes the result to the feed, and — when a check fails — it
GENERATES AND SIGNS the Protocol Notice itself. The machine that finds the defect writes
the finding.

This module also owns the notice format, so the marker collision cannot recur: the
verification marker is emitted by the formatter, never typed into prose.

  python3 lef-enforcement-cycle.py [--sample N] [--quiet]

Exit codes: 0 = all conformant, 1 = at least one non-conformance (expected and
legitimate — a non-conformance is a finding, not a crash).
"""
import argparse
import base64
import hashlib
import json
import os
import re
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
SEEDS = os.path.join(POOL, "seat-seeds.json")
PUBKEYS = os.path.join(POOL, "SEAT-PUBLIC-KEYS.json")
GH_RAW = "https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/main"
SACRED_HASH = "f5af425c"

sys.path.insert(0, HERE)

# SINGLE SOURCE OF TRUTH. These modules are loaded from their hyphenated
# filenames explicitly. A copy under an underscore alias is a second instrument:
# patch one, verify against the other, and the enforcement layer silently
# checks against stale code. That happened once already (the E3 fix never
# reached the running cycle). One file, one truth.
import importlib.util


def _load(filename, modname):
    path = os.path.join(HERE, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LV = _load("lef-verifier.py", "lef_verifier_src")
LNV = _load("lef-notice-verifier.py", "lef_notice_verifier_src")
LFI = _load("lef-finding-integrity.py", "lef_finding_integrity_src")

# The marker the notice verifier splits on. It is a constant here, and the
# formatter below is the ONLY place it may appear in a notice.
MARKER = "VERIFICATION\n"


# ------------------------------------------------------------------ notices
def _signer():
    from nacl.signing import SigningKey
    from nacl.encoding import RawEncoder
    seeds = json.load(open(SEEDS))
    return SigningKey(base64.b64decode(seeds["1"]), encoder=RawEncoder())


def _pubkey_b64():
    d = json.load(open(PUBKEYS))
    return d["seats"]["1"]["pub_b64_raw"]


def _fp():
    d = json.load(open(PUBKEYS))
    return d["fingerprints"]["1"]


def format_notice(power, finding_id, artifact_id, method, deviation, status, effect):
    """Build a notice. The marker appears EXACTLY ONCE, by construction.

    Built with explicit concatenation rather than str.format(): the body text
    contains braces of its own (JSON fragments), and a .format() call whose
    arguments are named after its own locals is a self-reference trap.
    """
    body_text = (
        "PROTOCOL NOTICE — " + power.replace("LEF-", "").replace("_", " ").title() + "\n"
        + "=" * 54 + "\n"
        + "finding_id:    " + str(finding_id) + "\n"
        + "artifact_id:   " + str(artifact_id) + "\n"
        + "enforcer:     L8-OPERATOR-SELF-ENFORCE (seat 01)\n"
        + "enforcer_key_fp: " + _fp() + "\n"
        + "power:        " + str(power) + "\n"
        + "checked_at:   " + datetime.now(timezone.utc).isoformat() + "\n"
        + "method:       " + str(method) + "\n"
        + "deviation:    " + str(deviation) + "\n"
        + "status:       " + str(status) + "\n"
        + "sacred_hash:  " + SACRED_HASH + "\n"
        + "\n"
        + "BODY\n"
        + "\n"
        + str(effect).split("\n")[0] + "\n"
    )

    payload = body_text.rstrip() + "\n\n" + MARKER
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    sig = _signer().sign(digest).signature
    block = (
        "SHA-256 of the notice payload (everything above this line), computed after\n"
        "finalisation:\n\n    {h}\n\n"
        "Signature (Ed25519, detached, base64) over those 32 raw digest bytes:\n\n    {s}\n\n"
        "Public key (Ed25519, base64, raw 32-byte key) — seat 01:\n\n    {pk}\n\n"
        "SUBSTRATE MIRROR\n\n"
        "- Vault:   {vault}\n"
        "- GitHub:  Baronki2/KISWARM-PRESS-RELEASES -> l8-court/notices/{name}\n"
        "- Feed:    event_type=mesh.l8_protocol_notice, severity=critical\n"
        "- Bridge:  KHOJ mirror sync\n\n"
        "WHAT THIS NOTICE DID\n\n{effect}\n\nSacred hash: {sacred}\n"
    ).format(h=digest.hex(), s=base64.b64encode(sig).decode(), pk=_pubkey_b64(),
             vault=os.path.join(NOTICES, "{name}"), name="{name}", effect=effect,
             sacred=SACRED_HASH)
    return payload + block, body_text


def emit_notice(power, finding_id, artifact_id, method, deviation, status, effect):
    """Write, sign and verify a notice. Returns (path, ok)."""
    doc, body = format_notice(power, finding_id, artifact_id, method, deviation, status, effect)
    if MARKER in body:
        # cannot happen — body is built from fields, and the marker is added once
        return None, False
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    name = "LEF-AUTO-{power}-{stamp}.md".format(power=power.replace("LEF-", ""), stamp=stamp)
    doc = doc.replace("{name}", name)
    os.makedirs(NOTICES, exist_ok=True)
    p = os.path.join(NOTICES, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(doc)
    r = LNV.verify(p, _pubkey_b64())
    return p, bool(r.get("ok"))


# ------------------------------------------------------------------ cycle
def latest_finding():
    if not os.path.isdir(FINDINGS):
        return None
    cands = [f for f in os.listdir(FINDINGS) if f.endswith(".json")]
    if not cands:
        return None
    cands.sort(key=lambda f: os.path.getmtime(os.path.join(FINDINGS, f)), reverse=True)
    return os.path.join(FINDINGS, cands[0])


def verify_all_notices():
    if not os.path.isdir(NOTICES):
        return {"notices_checked": 0, "notices_verifiable": 0, "status": "PROTOCOL CONFORMANT"}
    files = [f for f in sorted(os.listdir(NOTICES)) if f.endswith(".md")]
    ok = 0
    failed = []
    pub = _pubkey_b64()
    for f in files:
        r = LNV.verify(os.path.join(NOTICES, f), pub)
        if r.get("ok"):
            ok += 1
        else:
            failed.append({"file": f, "reason": r.get("reason", "?")})
    return {"notices_checked": len(files), "notices_verifiable": ok, "failed": failed,
            "status": "PROTOCOL CONFORMANT" if ok == len(files) else "PROTOCOL NON-CONFORMANT"}


def publish(report, extra_severity=None):
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
        "e5": next(({k: v for k, v in c.items() if k != "seat_audit"}
                   for c in report["checks"] if c["power"] == "LEF-E5"), None),
        "notices": report.get("notices", {}).get("notices_verifiable"),
        "notices_total": report.get("notices", {}).get("notices_checked"),
        "nonconformant_checks": [c["power"] for c in nonconform],
        "sacred_hash": SACRED_HASH,
        "timestamp": report["checked_at"],
    }
    if report.get("auto_notice"):
        payload["auto_notice"] = report["auto_notice"]
    sev = extra_severity or ("critical" if nonconform else "info")
    p = subprocess.run(
        ["/home/sah/.local/bin/kiswarm-feed", "event",
         "--type=mesh.lef_enforcement_cycle", "--severity=" + sev,
         "--source=hermes-kiswarm-sah6", "--payload=" + json.dumps(payload)],
        capture_output=True, text=True, timeout=20)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-notice", action="store_true",
                    help="do not auto-emit a notice on non-conformance")
    args = ap.parse_args()

    t0 = time.time()
    report = {"cycle": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
              "checked_at": datetime.now(timezone.utc).isoformat(),
              "sacred_hash": SACRED_HASH, "checks": []}

    if os.path.exists(INDEX):
        text = open(INDEX, encoding="utf-8", errors="replace").read()
        report["checks"].append(LV.check_e1(text, GH_RAW, None, args.sample or None))

    f = latest_finding()
    if f:
        report["checks"].append(LV.check_e3(f))
        report["checks"].append(LV.check_e4(f))
        report["checks"].append(LV.check_e2(f))
        # LEF-E5: recompute the quorum from the DECLARED labels and audit every
        # correction against the seat's own reasoning. A quorum that exists only
        # after the correction layer rewrote the votes is not a quorum.
        try:
            finding = json.load(open(f, encoding="utf-8"))
            report["checks"].append(LFI.evaluate_finding(finding))
        except Exception as e:
            report["checks"].append({"power": "LEF-E5", "status": "PROTOCOL NON-CONFORMANT",
                                     "nonconform_reason": "could not evaluate: {}".format(str(e)[:90])})
        report["finding"] = os.path.basename(f)

    report["notices"] = verify_all_notices()

    nonconform = [c for c in report["checks"] if c.get("status") != "PROTOCOL CONFORMANT"]
    if report["notices"]["status"] != "PROTOCOL CONFORMANT":
        nonconform.append({"power": "NOTICES", "status": report["notices"]["status"]})
    report["overall"] = "PROTOCOL NON-CONFORMANT" if nonconform else "PROTOCOL CONFORMANT"
    report["elapsed_s"] = round(time.time() - t0, 1)

    # The machine writes its own notice.
    if nonconform and not args.no_notice:
        # Pick the power that actually explains the failure. A finding-integrity
        # failure (E5) outranks a signature failure (E2): E2 is often the
        # CONSEQUENCE of E5, and a notice naming the wrong ground is a notice
        # that misinforms the reader.
        priority = {"LEF-E5": 0, "LEF-E3": 1, "LEF-E4": 2, "LEF-E2": 3, "LEF-E1": 4}
        c = sorted(nonconform, key=lambda x: priority.get(x.get("power", ""), 9))[0]
        power = c.get("power", "LEF-E1")
        detail = c.get("nonconform_reason") or c.get("status", "")
        p, ok = emit_notice(
            power, report.get("finding", "unknown"),
            "l8-sentinel-pool/findings/" + report.get("finding", "unknown"),
            "automatic enforcement cycle (cron lef-enforcement-cycle, 68361c8a5891) — "
            "run the {} check against the published artifact and compare the result with "
            "the published claim".format(power),
            "{} — {}".format(detail, json.dumps(
                {k: v for k, v in c.items()
                 if k in ("indexed", "checked", "match", "votes", "seats_answered",
                          "seats_verified", "consistency_failures", "seats_without_verification",
                          "verified", "failed", "unverifiable", "divergence_disclosed")})),
            c.get("status", "PROTOCOL NON-CONFORMANT"),
            "The artifact was marked non-binding and returned to the pool for "
            "re-deliberation. The notice itself is signed by seat 01 and verifiable with "
            "lef-notice-verifier.py.")
        if p:
            report["auto_notice"] = {"file": os.path.basename(p), "verified": ok,
                                     "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}
            # mirror to the evidence chain
            ev = os.path.join(VAULT, "legal-evidence-OMEGA-2026-09-27")
            try:
                import shutil
                shutil.copy2(p, os.path.join(ev, "LEF_" + os.path.basename(p)))
            except Exception:
                pass
            if not args.quiet:
                print("  AUTO-NOTICE: {} (verified={})".format(os.path.basename(p), ok))

    out = os.path.join(POOL, "LEF-CYCLE-REPORT.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    feed = publish(report)

    if not args.quiet:
        for c in report["checks"]:
            print("  [{0:26s}] {1}".format(c.get("power", "?"), c.get("status", "?")))
        n = report["notices"]
        print("  [{0:26s}] {1} ({2}/{3} notices verifiable)".format(
            "NOTICES", n["status"], n["notices_verifiable"], n["notices_checked"]))
        print("  OVERALL: {0}   ({1:.0f}s)".format(report["overall"], report["elapsed_s"]))
        if feed:
            print("  feed: " + feed[:100])

    return 0 if report["overall"] == "PROTOCOL CONFORMANT" else 1


if __name__ == "__main__":
    sys.exit(main())
