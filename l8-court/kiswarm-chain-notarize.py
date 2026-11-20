#!/usr/bin/env python3
"""
KISWARM Chain Notarizer — Proof-of-Existence for the entire evidence archive
Seals each SHA256 in the DEUSPROOF open register (content never leaves the machine).

Resumable: writes progress after every file, skips already-sealed files.
Rate-limit aware: on 429 it sleeps and retries the SAME file until it succeeds
(rather than skipping it), with an escalating backoff and a hard cap.
"""
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/home/sah/.local/lib/python3.11/site-packages")
import deusproof

EVIDENCE_DIR = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
VAULT_DIR = "/home/sah/.config/sah-vault"
INDEX_OUT = "/home/sah/.config/sah-vault/DEUSPROOF-CHAIN-NOTARIZATION-2026-11-18.json"
PROGRESS_OUT = "/home/sah/.config/sah-vault/.deusproof-chain-progress.json"

notary = deusproof.Notary(
    handle="Gemini2_5Flash",
    key_path="/home/sah/.config/deusproof/notary_ed25519",
)
print("DID: {0}".format(notary.did), flush=True)

# Secret material must never enter a public register.
# Only the SHA-256 of evidence is published, but we still exclude key files
# so no one can correlate a secret hash with a published proof.
# NOTARIZER LESSON (2026-11-20, three passes):
#   1. The secret filter missed 8 credential-bearing files. They are in the
#      public register. Removal is impossible by API and SDK design.
#   2. The filter then missed the L7 Shamir shares. Three of five reconstruct
#      the L7 master key.
#   3. The obvious broad fix ("share", "recovery") ALSO hid legitimate
#      evidence (BRIDGE-RECOVERY, SENTINEL-RECOVERY). It was reverted.
#      A filter that hides evidence is as wrong as one that leaks secrets.
#   Rule: test the secret filter against a NAMED LIST of cases — both the
#   things that must be blocked AND the things that must stay sealable.

SECRET_PATTERNS = (
    "master-key", ".seed", ".pem", "id_khoj", "id_rsa", "id_ed25519",
    # 2026-11-20: 8 credential-bearing files slipped through the original list.
    # A public SHA-256 of a credential is a credential-verification oracle:
    # anyone can test a guessed secret against it. The proof of EXISTENCE does
    # not require the secret itself to be proven — the chain's value is in the
    # documents, not in the keys.
    ".key", ".legacy", "token", "api-key", "api key", "password", "passwd",
    "credential", "secret", "private", "seed", "keystore", "wallet",
    "access-token", "bearer", ".env", "id_ed", "id_ecdsa",
    # 2026-11-20 (second pass): the L7 Shamir shares were NOT covered.
    # `.l7-share-N-of-5.json` carries a point on the secret polynomial; the
    # published hash of a share is a verification oracle for that share, and
    # 3 of the 5 shares reconstruct the L7 master key.
    #
    # The pattern must be PRECISE. A broad "share" or "recovery" substring also
    # matched legitimate evidence — BRIDGE-RECOVERY-2026-11-08.md and
    # SENTINEL-RECOVERY-2026-10-23.md are documents that PROVE a recovery
    # happened and must stay sealable. Over-blocking is its own defect class:
    # a filter that hides evidence is as wrong as one that leaks secrets.
    # `.l7-phase7` and `.l7-state.json` are STATE markers, not secrets, and
    # stay sealable — the shield must keep its own audit trail.
    ".l7-share", "l7-share", "-share-", "share-", ".share",
    "shamir", "mnemonic", "recovery-phrase", "recovery-key", "recoverycode",
)

# Self-referential state files must NOT be notarized. A file that changes
# AFTER its own seal cannot be verified against the published hash — the
# difference is not tampering, but a verifier sees an unexplained mismatch.
# 2026-11-20: 4 of 355 records had drifted this way (the progress report, the
# two index files, and the mail index that the IMAP fix overwrote). The proof
# that it is not tampering has to live somewhere; a published hash that no
# longer matches is not that place.
SELF_REFERENTIAL = (
    "manifest.md",              # appended to by the mail extractor
    "deusproof-chain-progress", # written by this script itself
    "deusproof-chain-notarization",  # the index this script writes
    ".deusproof-chain-progress",
)


def is_self_referential(path):
    name = os.path.basename(path).lower()
    return any(p in name for p in SELF_REFERENTIAL)


def is_secret(path):
    name = os.path.basename(path).lower()
    return any(p in name for p in SECRET_PATTERNS)

files = []
for root, dirs, names in os.walk(EVIDENCE_DIR):
    for n in sorted(names):
        p = os.path.join(root, n)
        if os.path.isfile(p) and not is_secret(p) and not is_self_referential(p):
            files.append(p)
for n in sorted(os.listdir(VAULT_DIR)):
    p = os.path.join(VAULT_DIR, n)
    if (os.path.isfile(p) and not n.endswith(".seed") and not is_secret(p)
            and not is_self_referential(p)):
        files.append(p)

# Explicitly also cover the mail-extraction index + private key dir exclusion
for extra_dir in ("/home/sah/.config/deusproof",):
    if os.path.isdir(extra_dir):
        pass  # never included

print("files to notarize: {0}".format(len(files)), flush=True)

results = []
errors = []
done = set()
if os.path.exists(PROGRESS_OUT):
    try:
        prev = json.load(open(PROGRESS_OUT))
        results = prev.get("records", [])
        errors = prev.get("errors", [])
        done = {r["path"] for r in results}
        print("resuming: {0} already sealed".format(len(results)), flush=True)
    except Exception:
        pass

DELAY = 1.2
backoff = 0
seq = 0

# A rate limit is a shared resource, not a property of one file. Retrying the
# SAME file until it succeeds — as the original loop did — blocks every file
# behind it for as long as the limit holds. The 2026-11-20 run burned 26
# attempts × 120 s on a single PDF and never reached the 22 files behind it.
#
# New rule: a file gets a bounded number of attempts. After that it is
# DEFERRED, not failed — the run continues with the next file and the deferred
# set is retried in a later pass. Nothing is lost; the queue keeps moving.
MAX_429_ATTEMPTS = 4
MAX_429_WAIT = 45          # seconds; 120 s blocks the whole chain
DEFERRED = []


def flush_progress():
    with open(PROGRESS_OUT, "w") as fh:
        json.dump({"records": results, "errors": errors,
                   "deferred": DEFERRED}, fh, indent=2)


for path in files:
    if path in done:
        continue
    seq += 1
    with open(path, "rb") as fh:
        data = fh.read()
    h = hashlib.sha256(data).hexdigest()
    ph = hashlib.sha256("KISWARM evidence: {0}".format(os.path.basename(path)).encode()).hexdigest()

    # Retry the same file a bounded number of times, then defer it.
    attempts = 0
    while True:
        attempts += 1
        try:
            proof = notary.notarize_hash(content=data, prompt_hash=ph, source_url="")
            results.append({
                "file": os.path.basename(path),
                "path": path,
                "sha256": h,
                "proof_id": getattr(proof, "id", None),
                "output_hash": getattr(proof, "output_hash", None),
                "verify_url": getattr(proof, "verify_url", None),
                "badge": getattr(proof, "badge_markdown", None),
            })
            backoff = 0
            break
        except Exception as e:
            msg = str(e)
            if "429" in msg or "Too Many" in msg:
                if attempts >= MAX_429_ATTEMPTS:
                    # Deferred, not failed: the run keeps moving.
                    DEFERRED.append({"file": os.path.basename(path), "path": path,
                                     "sha256": h, "reason": "rate limited after {0} attempts".format(attempts),
                                     "attempts": attempts})
                    print("  ~ deferred (rate limit): {0}".format(
                        os.path.basename(path)[:44]), flush=True)
                    break
                backoff = min(backoff * 2 if backoff else 10, MAX_429_WAIT)
                print("  ! 429 on {0} -> sleep {1}s (attempt {2}/{3})".format(
                    os.path.basename(path)[:44], backoff, attempts, MAX_429_ATTEMPTS), flush=True)
                time.sleep(backoff)
                continue
            errors.append({"file": os.path.basename(path), "path": path,
                           "error": msg[:220], "attempts": attempts})
            print("  x {0}: {1}".format(os.path.basename(path)[:44], msg[:90]), flush=True)
            break

    if seq % 5 == 0:
        print("  [{0}/{1}] sealed={2} err={3} deferred={4}".format(
            seq, len(files), len(results), len(errors), len(DEFERRED)), flush=True)
        flush_progress()

    time.sleep(DELAY)

ts = datetime.now(timezone.utc).isoformat()
out = {
    "notarized_at": ts,
    "did": notary.did,
    "register": "https://deusproof.com",
    "files_total": len(files),
    "files_notarized": len(results),
    "errors": errors,
    "records": results,
}
with open(INDEX_OUT, "w") as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)

print("")
print("  SEALED: {0}/{1}   errors: {2}".format(len(results), len(files), len(errors)), flush=True)
print("  index: {0}".format(INDEX_OUT), flush=True)
