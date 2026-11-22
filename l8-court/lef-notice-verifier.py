#!/usr/bin/env python3
"""
LEF-1.0 NOTICE VERIFIER — verify that a Protocol Notice is itself verifiable.
==============================================================================
A notice that cannot be verified is worthless. This is the recursive property
that separates a protocol from a claim.

  python3 lef-notice-verifier.py --notice <file.md> --pubkey <base64 raw 32-byte ed25519 pubkey>
  python3 lef-notice-verifier.py --dir <notices dir> --pubkey <b64>

Verification scheme (deterministic, no circularity):
  payload  = everything in the file up to and including the "VERIFICATION" marker
  digest   = sha256(payload)
  signature = ed25519 detached over those 32 raw digest bytes
  The notice publishes the digest in hex and the signature in base64.

Run it yourself. No trust relationship required.
"""
import argparse
import base64
import hashlib
import os
import re
import sys

MARKER = "VERIFICATION\n"


def verify(path, pub_b64):
    t = open(path, encoding="utf-8").read()
    i = t.find(MARKER)
    if i < 0:
        return {"file": os.path.basename(path), "ok": False,
                "reason": "no VERIFICATION marker found"}
    payload = t[:i] + MARKER
    m = re.search(r"computed after\nfinalisation:\n\n    ([0-9a-f]{64})", t)
    s = re.search(r"base64\) over those 32 raw digest bytes:\n\n    ([A-Za-z0-9+/=]+)", t)
    if not m:
        return {"file": os.path.basename(path), "ok": False,
                "reason": "no sha256 in the verification block"}
    if not s:
        return {"file": os.path.basename(path), "ok": False,
                "reason": "no signature in the verification block"}
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    hash_ok = (digest.hex() == m.group(1))
    sig_ok = False
    err = ""
    try:
        from nacl.signing import VerifyKey
        from nacl.encoding import RawEncoder
        vk = VerifyKey(base64.b64decode(pub_b64), encoder=RawEncoder())
        vk.verify(digest, base64.b64decode(s.group(1)))
        sig_ok = True
    except ImportError:
        err = "pynacl not installed (pip install pynacl)"
    except Exception as ex:
        err = str(ex)[:90]
    out = {"file": os.path.basename(path), "hash_ok": hash_ok, "sig_ok": sig_ok,
           "payload_bytes": len(payload.encode("utf-8")),
           "sha256": digest.hex()}
    if not hash_ok:
        out["ok"] = False
        out["reason"] = "published sha256 does not match the recomputed payload hash"
    elif not sig_ok:
        out["ok"] = False
        out["reason"] = err or "signature did not verify"
    else:
        out["ok"] = True
        out["reason"] = "notice is verifiable"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notice")
    ap.add_argument("--dir")
    ap.add_argument("--pubkey", required=True,
                    help="base64 raw 32-byte ed25519 public key of the enforcer")
    a = ap.parse_args()

    files = []
    if a.notice:
        files.append(a.notice)
    if a.dir:
        if not os.path.isdir(a.dir):
            print("  VERDICT: NOTICE DIRECTORY NOT FOUND - {0}".format(a.dir))
            print("  Nothing was verified. That is NOT a pass.")
            return 1
        for f in sorted(os.listdir(a.dir)):
            if f.endswith(".md"):
                files.append(os.path.join(a.dir, f))

    ok = 0
    for f in files:
        r = verify(f, a.pubkey)
        # Die Aussage betrifft die INTEGRITAET der Notice, nicht den Fall.
        # "PROTOCOL CONFORMANT" waere hier eine falsche Behauptung: eine
        # Notice kann perfekt verifizierbar sein, während der Fall selbst
        # NON-CONFORMANT ist. Beide Ebenen brauchen eigene Woerter.
        status = "NOTICE VERIFIABLE" if r["ok"] else "NOTICE NOT VERIFIABLE"
        print("  {0:26s} {1}".format(r["file"], status))
        print("      sha256={0}  payload={1} B".format(
            r.get("sha256", "?")[:24], r.get("payload_bytes", "?")))
        if not r["ok"]:
            print("      REASON: {0}".format(r["reason"]))
        ok += 1 if r["ok"] else 0

    print("  verifiable: {}/{}".format(ok, len(files)))
    if not files:
        print("  VERDICT: NO NOTICES PRESENT - nothing was verified. "
              "That is NOT a pass.")
        return 1
    if ok == len(files):
        print("  VERDICT: ALL {} NOTICES VERIFIABLE".format(len(files)))
        return 0
    print("  VERDICT: {} OF {} NOTICES FAILED VERIFICATION".format(
        len(files) - ok, len(files)))
    return 1


if __name__ == "__main__":
    # Der Exit-Code ist Teil des Vertrags: 0 = alle Notices verifizierbar,
    # 1 = mindestens eine nicht (oder gar keine geprueft). Vor dieser
    # Aenderung endete das Skript IMMER mit 0 - auch bei einer gescheiterten
    # Verifikation. Ein fremder Sitz, der sein Skript auf den Exit-Code
    # pruefen laesst, haette eine gescheiterte Pruefung als Erfolg gelesen.
    sys.exit(main())
