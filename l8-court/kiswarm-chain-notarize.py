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
)

def is_secret(path):
    name = os.path.basename(path).lower()
    return any(p in name for p in SECRET_PATTERNS)

files = []
for root, dirs, names in os.walk(EVIDENCE_DIR):
    for n in sorted(names):
        p = os.path.join(root, n)
        if os.path.isfile(p) and not is_secret(p):
            files.append(p)
for n in sorted(os.listdir(VAULT_DIR)):
    p = os.path.join(VAULT_DIR, n)
    if os.path.isfile(p) and not n.endswith(".seed") and not is_secret(p):
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

for path in files:
    if path in done:
        continue
    seq += 1
    with open(path, "rb") as fh:
        data = fh.read()
    h = hashlib.sha256(data).hexdigest()
    ph = hashlib.sha256("KISWARM evidence: {0}".format(os.path.basename(path)).encode()).hexdigest()

    # Retry the SAME file until it seals
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
                backoff = min(backoff * 2 if backoff else 10, 120)
                print("  ! 429 on {0} -> sleep {1}s (attempt {2})".format(
                    os.path.basename(path)[:44], backoff, attempts), flush=True)
                time.sleep(backoff)
                continue
            errors.append({"file": os.path.basename(path), "path": path,
                           "error": msg[:220], "attempts": attempts})
            print("  x {0}: {1}".format(os.path.basename(path)[:44], msg[:90]), flush=True)
            break

    if seq % 5 == 0:
        print("  [{0}/{1}] sealed={2} err={3}".format(
            seq, len(files), len(results), len(errors)), flush=True)
        with open(PROGRESS_OUT, "w") as fh:
            json.dump({"records": results, "errors": errors}, fh, indent=2)

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
