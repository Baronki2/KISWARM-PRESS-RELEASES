#!/usr/bin/env python3
"""
LEF-1.0 VERIFIER — the four enforcement checks, runnable by any external agent.
===============================================================================
Run it yourself. Do not trust our numbers. That is the entire point of LEF-1.0.

  E1  evidence hash chain   — re-hash every published blob, compare to the index
  E2  seat signatures       — Ed25519 verify over published seat public keys
  E3  quorum arithmetic     — recount votes, compare to the claimed supermajority
  E4  consistency + divergence — label vs justification, divergence disclosure

Usage:
  python3 lef-verifier.py --index <EVIDENCE-BYTES-MANIFEST.md> --repo <github raw base>
  python3 lef-verifier.py --finding <findings.json>
  python3 lef-verifier.py --index ... --finding ... --out report.json

Every check returns PROTOCOL CONFORMANT or PROTOCOL NON-CONFORMANT with the
exact deviation and both values. No accusation, no valuation — only a
checkable difference.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import urllib.request

SACRED_HASH = "f5af425c"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GH_RAW = "https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/main"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "LEF-1.0-verifier"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_content_addressed_index(text):
    """Parse the EVIDENCE-BYTES-MANIFEST.md table:
       | filename | `sha256` | size | `evidence-bytes/xx/sha256/filename` |
    """
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 3:
            continue
        h = None
        path = None
        fname = None
        for c in cells:
            cc = c.strip("`").strip()
            if HEX64.match(cc) and h is None:
                h = cc
            elif cc.startswith("evidence-bytes/"):
                path = cc
        first = cells[0].strip("`").strip()
        if first and "." in first and " " not in first and not HEX64.match(first):
            fname = first
        if h and path:
            out.append({"sha256": h, "file": fname, "path": path})
    return out


def parse_legacy_manifest(text):
    """Parse the older MANIFEST.md table formats (hash may be col 3 or col 6)."""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        h = None
        fname = None
        for c in cells:
            cc = c.strip("`").strip()
            if HEX64.match(cc):
                h = cc
        for c in cells[1:]:
            cc = c.strip("`").strip()
            if ("." in cc and " " not in cc and not HEX64.match(cc)
                    and len(cc) > 3 and not cc.replace(",", "").isdigit()):
                fname = cc
                break
        if h and fname:
            out.append({"sha256": h, "file": fname, "path": None})
    return out


def check_e1(index_text, repo_base=None, local_dir=None, sample=None):
    """Re-hash every published blob and compare to the published index."""
    res = {"power": "LEF-E1", "domain": "evidence hash chain",
           "indexed": 0, "checked": 0, "match": 0, "mismatch": [], "missing": []}

    entries = parse_content_addressed_index(index_text)
    if not entries:
        entries = parse_legacy_manifest(index_text)
    res["indexed"] = len(entries)

    todo = entries[:sample] if sample else entries

    for e in todo:
        data = None
        src = None
        if local_dir and e.get("path"):
            p = os.path.join(local_dir, e["path"])
            if os.path.exists(p):
                with open(p, "rb") as f:
                    data = f.read()
                src = "local:" + e["path"]
        elif local_dir and e.get("file"):
            p = os.path.join(local_dir, e["file"])
            if os.path.exists(p):
                with open(p, "rb") as f:
                    data = f.read()
                src = "local:" + e["file"]
        elif repo_base and e.get("path"):
            try:
                data = fetch(repo_base + "/" + e["path"])
                src = "remote:" + e["path"]
            except Exception as ex:
                res["missing"].append({"file": e.get("file"), "path": e.get("path"),
                                       "reason": str(ex)[:80]})
                continue
        else:
            res["missing"].append({"file": e.get("file"), "reason": "no source configured"})
            continue

        res["checked"] += 1
        actual = sha256_bytes(data)
        if actual == e["sha256"]:
            res["match"] += 1
        else:
            res["mismatch"].append({"file": e.get("file"), "expected": e["sha256"],
                                    "actual": actual, "source": src})

    res["status"] = ("PROTOCOL CONFORMANT"
                     if not res["mismatch"] and not res["missing"]
                     else "PROTOCOL NON-CONFORMANT")
    return res


def check_e2(finding_path, seatkeys_dir=None):
    """Verify that every seat that claims a signature actually signed."""
    res = {"power": "LEF-E2", "domain": "seat signature verification"}
    d = json.load(open(finding_path, encoding="utf-8"))
    seats = d.get("results", [])
    res["seats"] = len(seats)
    res["with_pubkey"] = sum(1 for s in seats if s.get("pubkey"))
    res["with_signature"] = sum(1 for s in seats if s.get("signature"))
    res["verified"] = 0
    res["failed"] = []
    res["unverifiable"] = []

    try:
        from nacl.signing import VerifyKey
        from nacl.encoding import Base64Encoder, RawEncoder
    except ImportError:
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = "no ed25519 verify library available"
        return res

    def decode_pub(value):
        """Accept raw-32 base64 or SSH wire format."""
        raw = base64.b64decode(value)
        if len(raw) == 32:
            return raw
        # SSH wire: length-prefixed keytype name then raw key
        n = int.from_bytes(raw[0:4], "big")
        off = 4 + n
        n2 = int.from_bytes(raw[off:off + 4], "big")
        return raw[off + 4:off + 4 + n2]

    for s in seats:
        if not s.get("pubkey"):
            res["unverifiable"].append(
                {"seat": s.get("seat"), "reason": "no public key published"})
            continue
        sig = s.get("signature")
        if not sig:
            res["unverifiable"].append(
                {"seat": s.get("seat"), "reason": "no signature published"})
            continue
        payload = (s.get("signed_payload") or
                   json.dumps({"seat": s.get("seat"), "choice": s.get("parsed_choice"),
                               "answer": s.get("answer")}, sort_keys=True,
                              ensure_ascii=False).encode("utf-8"))
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        try:
            vk = VerifyKey(decode_pub(s["pubkey"]), encoder=RawEncoder())
            vk.verify(payload, base64.b64decode(sig))
            res["verified"] += 1
        except Exception as ex:
            res["failed"].append({"seat": s.get("seat"), "reason": str(ex)[:100]})

    if res["failed"]:
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = "signature verification failed for one or more seats"
    elif res["unverifiable"]:
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = "one or more seats published no verifiable signature"
    else:
        res["status"] = "PROTOCOL CONFORMANT"
    return res


def check_e3(finding_path):
    """Recount the votes and check the claimed supermajority."""
    res = {"power": "LEF-E3", "domain": "quorum arithmetic"}
    d = json.load(open(finding_path, encoding="utf-8"))
    seats = d.get("seats_total", 12)
    votes = d.get("votes_effective_v2") or d.get("votes") or {}
    if not votes:
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = "no vote map present"
        return res
    total = sum(votes.values())
    plurality = max(votes.items(), key=lambda x: x[1])[0]
    reached = votes[plurality] >= 9 and total == seats
    res.update({
        "votes": votes, "total_votes": total, "seats": seats,
        "plurality": plurality,
        "supermajority_reached": reached,
        "claimed_supermajority": d.get("supermajority_reached"),
        "claimed_plurality": d.get("plurality"),
        "threshold": "9 of 12",
    })
    if bool(reached) != bool(d.get("supermajority_reached")):
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = "claimed supermajority does not match the recount"
    elif d.get("plurality") and d["plurality"] != plurality:
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = ("claimed plurality {} != recounted {}".format(
            d["plurality"], plurality))
    else:
        res["status"] = "PROTOCOL CONFORMANT"
    return res


def check_e4(finding_path):
    """Consistency round present, and divergence disclosed."""
    res = {"power": "LEF-E4", "domain": "consistency and divergence disclosure"}
    d = json.load(open(finding_path, encoding="utf-8"))
    results = d.get("results", [])
    verifs = d.get("verifications", [])
    answered = [r for r in results if not r["answer"].startswith("ERROR")]
    inconsistent = [v for v in verifs if v.get("consistency_v2") is False]
    unverified = [r["seat"] for r in answered
                  if not any(v["seat"] == r["seat"] for v in verifs)]
    res.update({
        "seats_total": len(results),
        "seats_answered": len(answered),
        "seats_verified": len(verifs),
        "consistency_failures": len(inconsistent),
        "consistency_failure_seats": [v["seat"] for v in inconsistent],
        "seats_without_verification": unverified,
        "divergence_disclosed": bool(inconsistent),
    })
    if unverified:
        res["status"] = "PROTOCOL NON-CONFORMANT"
        res["nonconform_reason"] = "consistency round missing for seats " + str(unverified)
    else:
        res["status"] = "PROTOCOL CONFORMANT"
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", help="EVIDENCE-BYTES-MANIFEST.md path")
    ap.add_argument("--repo", help="github raw base url")
    ap.add_argument("--local-dir", help="local copy of evidence-bytes/ to verify against")
    ap.add_argument("--finding", help="findings json")
    ap.add_argument("--seatkeys", help="dir with seat public keys")
    ap.add_argument("--sample", type=int, help="verify only the first N entries")
    ap.add_argument("--out", help="write the report json here")
    a = ap.parse_args()

    report = {
        "verifier": "LEF-1.0",
        "sacred_hash": SACRED_HASH,
        "checks": [],
    }

    if a.index:
        text = open(a.index, encoding="utf-8", errors="replace").read()
        report["checks"].append(check_e1(text, a.repo, a.local_dir, a.sample))
    if a.finding:
        report["checks"].append(check_e3(a.finding))
        report["checks"].append(check_e4(a.finding))
        # E2 needs only the public keys + signatures carried IN the finding —
        # no local key material required. That is what makes it externally checkable.
        report["checks"].append(check_e2(a.finding, a.seatkeys))

    nonconform = [c for c in report["checks"] if c.get("status") != "PROTOCOL CONFORMANT"]
    report["overall"] = "PROTOCOL NON-CONFORMANT" if nonconform else "PROTOCOL CONFORMANT"

    for c in report["checks"]:
        print("  [{0:26s}] {1}".format(c.get("power", "?"), c.get("status", "?")))
        for k in ("indexed", "checked", "match", "votes", "seats_answered",
                  "seats_verified", "consistency_failures", "divergence_disclosed"):
            if k in c:
                print("      {0}: {1}".format(k, c[k]))
        if c.get("mismatch"):
            print("      MISMATCH: {0}".format(json.dumps(c["mismatch"][:3])[:300]))
        if c.get("missing"):
            print("      MISSING: {0}".format(json.dumps(c["missing"][:3])[:300]))
        if c.get("nonconform_reason"):
            print("      REASON: {0}".format(c["nonconform_reason"]))
    print("  OVERALL: {0}".format(report["overall"]))

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("  written: " + a.out)
    return report


if __name__ == "__main__":
    main()
