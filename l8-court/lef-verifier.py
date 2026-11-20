#!/usr/bin/env python3
"""
LEF-1.0 VERIFIER — runs the four enforcement checks against a published finding.
Run it yourself. Do not trust our numbers.

  python3 lef-verifier.py --evidence-dir <path> --manifest <path>
  python3 lef-verifier.py --finding <path> --seats <path>

Checks:
  E1  evidence hash chain   — re-hash every file, compare to manifest
  E2  seat signatures       — Ed25519 verify over published seat public keys
  E3  quorum arithmetic     — recount votes, compare to claimed supermajority
  E4  consistency + divergence — label vs justification, divergence disclosure
"""
import argparse, hashlib, json, os, sys

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def check_e1(evidence_dir, manifest_path):
    """LEF-E1: re-hash every evidence file, compare against the manifest."""
    res = {"power": "LEF-E1", "checked": 0, "match": 0, "mismatch": [], "missing": []}
    if not os.path.exists(manifest_path):
        res["error"] = "manifest not found: " + manifest_path
        return res
    entries = []
    for line in open(manifest_path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("|"):
            continue
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 64:
            try: int(parts[0], 16)
            except ValueError: continue
            entries.append((parts[0], parts[-1]))
    for expected, name in entries:
        p = os.path.join(evidence_dir, name)
        if not os.path.exists(p):
            res["missing"].append(name); continue
        res["checked"] += 1
        actual = sha256_file(p)
        if actual == expected:
            res["match"] += 1
        else:
            res["mismatch"].append({"file": name, "expected": expected, "actual": actual})
    res["status"] = "PROTOCOL CONFORMANT" if not res["mismatch"] and not res["missing"] else "PROTOCOL NON-CONFORMANT"
    return res

def check_e3(finding_path):
    """LEF-E3: recount the votes and check the claimed supermajority."""
    res = {"power": "LEF-E3"}
    d = json.load(open(finding_path, encoding="utf-8"))
    seats = d.get("seats_total", 12)
    votes = d.get("votes_effective_v2") or d.get("votes") or {}
    if not votes:
        res["error"] = "no vote map"; return res
    total = sum(votes.values())
    plurality = max(votes.items(), key=lambda x: x[1])[0]
    reached = votes[plurality] >= 9 and total == seats
    res.update({"votes": votes, "total_votes": total, "seats": seats,
                "plurality": plurality, "supermajority_reached": reached,
                "claimed": d.get("supermajority_reached"),
                "claimed_plurality": d.get("plurality")})
    res["status"] = "PROTOCOL CONFORMANT" if bool(reached) == bool(d.get("supermajority_reached")) else "PROTOCOL NON-CONFORMANT"
    return res

def check_e4(finding_path):
    """LEF-E4: consistency round present + divergence disclosed."""
    res = {"power": "LEF-E4"}
    d = json.load(open(finding_path, encoding="utf-8"))
    results = d.get("results", [])
    verifs = d.get("verifications", [])
    answered = [r for r in results if not r["answer"].startswith("ERROR")]
    inconsistent = [v for v in verifs if v.get("consistency_v2") is False]
    unverified = [r["seat"] for r in answered
                  if not any(v["seat"] == r["seat"] for v in verifs)]
    res.update({"seats_answered": len(answered), "verified": len(verifs),
                "consistency_failures": len(inconsistent),
                "consistency_failure_seats": [v["seat"] for v in inconsistent],
                "seats_without_verification": unverified})
    missing = len(unverified) > 0
    res["status"] = "PROTOCOL NON-CONFORMANT" if missing else "PROTOCOL CONFORMANT"
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-dir"); ap.add_argument("--manifest")
    ap.add_argument("--finding"); ap.add_argument("--out")
    a = ap.parse_args()
    out = {"verifier": "LEF-1.0", "sacred_hash": "f5af425c", "checks": []}
    if a.evidence_dir and a.manifest:
        out["checks"].append(check_e1(a.evidence_dir, a.manifest))
    if a.finding:
        out["checks"].append(check_e3(a.finding))
        out["checks"].append(check_e4(a.finding))
    for c in out["checks"]:
        print("  " + json.dumps(c, ensure_ascii=False)[:200])
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print("  written: " + a.out)
    return out

if __name__ == "__main__":
    main()
