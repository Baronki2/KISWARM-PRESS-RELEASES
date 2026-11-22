#!/usr/bin/env python3
"""
LEF-1.1 ENFORCER SEAT KIT — die Referenzimplementierung des Seat-Specs.

Ein externer Agent braucht genau drei Dinge, um ein verbundener
Law-Enforcer-Sitz zu werden:

  1. seinen Schluessel (hier: erzeugen, aber der private bleibt bei ihm)
  2. die Notice byte-genau im richtigen Format
  3. einen Selbsttest, der beweist, dass seine Werkzeuge fremde Notices
     verifizieren koennen, BEVOR er mit eigenem Schluessel signiert

Dieses Skript macht alle drei. Es ist der ausgefuehrte Beweis, dass der
Seat-Spec funktioniert.

  python3 lef-enforcer-seat-kit.py --selftest            # Werkzeug beweisen
  python3 lef-enforcer-seat-kit.py --demo                # Ende-zu-Ende-Demo
  python3 lef-enforcer-seat-kit.py --notice <file.md> --pubkey <b64>

WICHTIG: --demo erzeugt einen WEGWERF-Schluessel und registriert ihn NICHT.
Eine Registrierung waere eine Behauptung ohne Fremdsignatur - genau die
Sache, die der Layer verhindert.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

MARKER = "VERIFICATION\n"
RE_HASH = re.compile(r"computed after\nfinalisation:\n\n    ([0-9a-f]{64})")
RE_SIG = re.compile(r"base64\) over those 32 raw digest bytes:\n\n    ([A-Za-z0-9+/=]+)")

POOL = "/home/sah/.config/sah-vault/l8-sentinel-pool"
NOTICES = os.path.join(POOL, "notices")


def payload_of(text):
    i = text.find(MARKER)
    if i < 0:
        raise ValueError("no VERIFICATION marker")
    return text[:i] + MARKER


def sign_payload(payload, private_key):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return digest, private_key.sign(digest)


def build_notice(power, finding_id, artifact_id, enforcer, fp, method,
                 deviation, status, body, priv_b64, pub_b64):
    # Die Payload ist EXAKT: alles vor der ersten Zeile "VERIFICATION"
    # zuzueglich des Markers selbst. Wer den Marker in den signierten
    # Teil einbaut und zusaetzlich anhaengt, signiert eine andere Bytesfolge
    # als der Verifier berechnet - und der Notice ist unbrauchbar, ohne
    # dass irgendwo ein Fehler sichtbar wird. Genau das ist beim ersten
    # Demo-Lauf passiert.
    pre = (
        "PROTOCOL NOTICE — " + power.replace("LEF-", "").replace("_", " ").title()
        + "\n" + "=" * 54 + "\n"
        + "finding_id:    " + str(finding_id) + "\n"
        + "artifact_id:   " + str(artifact_id) + "\n"
        + "enforcer:     " + str(enforcer) + "\n"
        + "enforcer_key_fp: " + str(fp) + "\n"
        + "power:        " + str(power) + "\n"
        + "checked_at:   " + datetime.now(timezone.utc).isoformat() + "\n"
        + "method:       " + str(method) + "\n"
        + "deviation:    " + str(deviation) + "\n"
        + "status:       " + str(status) + "\n"
        + "sacred_hash:  f5af425c\n"
        + "\n"
        + "BODY\n\n"
        + body.strip() + "\n\n")
    ver_head = ("VERIFICATION\n"
                + "SHA-256 of the notice payload (everything above this line), computed after\n"
                + "finalisation:\n\n")
    payload = pre + MARKER
    digest, sig = sign_payload(payload, priv_b64)
    head = pre + ver_head
    text = (head + "    " + digest.hex() + "\n\n"
            + "Signature (Ed25519, detached, base64) over those 32 raw digest bytes:\n\n"
            + "    " + base64.b64encode(sig).decode() + "\n\n"
            + "Public key (Ed25519, base64, raw 32-byte key) — seat external:\n\n"
            + "    " + pub_b64 + "\n")
    return text


def verify_notice(text, pub_b64):
    payload = payload_of(text)
    m = RE_HASH.search(text)
    s = RE_SIG.search(text)
    if not (m and s):
        return False, "kein Hash/keine Signatur im Block"
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    if digest.hex() != m.group(1):
        return False, "Payload-Hash weicht ab"
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64)).verify(
            base64.b64decode(s.group(1)), digest)
        return True, "verifiziert"
    except Exception as ex:
        return False, str(ex)[:80]


def selftest():
    """Beweist: die Werkzeuge koennen eine FREMDE Notice verifizieren."""
    print("=== WERKZEUG-SELBSTTEST (fremde Notice verifizieren) ===")
    ok = 0
    total = 0
    for f in sorted(os.listdir(NOTICES)):
        if not f.endswith(".md"):
            continue
        total += 1
        text = open(os.path.join(NOTICES, f), encoding="utf-8", errors="replace").read()
        pub = re.search(r"raw 32-byte key\)[^\n]*\n\n    ([A-Za-z0-9+/=]+)", text)
        if not pub:
            print("   XX {} -> kein Pubkey im Notice".format(f[:40]))
            continue
        good, why = verify_notice(text, pub.group(1))
        ok += good
        print("   {} {} -> {}".format("OK" if good else "XX", f[:40], why))
    print("   {}/{} Notices verifiziert".format(ok, total))
    return ok == total and total > 0


def demo():
    """Ende-zu-Ende: Schluessel erzeugen, Notice bauen, signieren, pruefen."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    print("=== ENDE-ZU-ENDE-DEMO (Wegwerf-Schluessel, NICHT registriert) ===")
    priv = Ed25519PrivateKey.generate()
    raw = priv.public_key().public_bytes(serialization.Encoding.Raw,
                                         serialization.PublicFormat.Raw)
    pub_b64 = base64.b64encode(raw).decode()
    fp = hashlib.sha256(raw).hexdigest()[:16]
    print("   pubkey_raw_b64 : {}".format(pub_b64))
    print("   fingerprint    : {}".format(fp))

    body = (
        "Demonstration des Seat-Specs. Diese Notice wurde mit einem "
        "WEGWERF-Schluessel erzeugt, der ausdruecklich NICHT im Register "
        "enforcer-seat-keys.json steht und den Enforcer-Sitz deshalb NICHT "
        "verbindet. Sie dient als ausgefuehrter Beweis, dass der Spec "
        "ausfuehrbar ist: Notice bauen, 32 Roh-Digest-Bytes detached "
        "signieren, Payload-Hash nachrechnen, eigene Notice verifizieren.")
    text = build_notice(
        "LEF-E5", "L8-CALIBRATION-001", "l8-sentinel-pool/findings/calibration-001.json",
        "SEAT-SPEC-REFERENCE-IMPLEMENTATION (demo key, not registered)",
        fp, "execute the published seat spec end to end and verify the result",
        "none — this is a demonstration of the mechanism, not a finding",
        "PROTOCOL CONFORMANT", body,
        priv, pub_b64)
    out = "/home/sah/.hermes/cache/scratch/LEF-SEAT-SPEC-DEMO-NOTICE.md"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(text)
    good, why = verify_notice(text, pub_b64)
    print("   Notice geschrieben: {} ({} B)".format(out, len(text)))
    print("   Selbstpruefung der eigenen Notice: {} ({})".format(
        "OK" if good else "FEHLER", why))
    # Gegenprobe: ein fremder Schluessel darf NICHT verifizieren
    other = Ed25519PrivateKey.generate()
    oraw = other.public_key().public_bytes(serialization.Encoding.Raw,
                                           serialization.PublicFormat.Raw)
    bad, why2 = verify_notice(text, base64.b64encode(oraw).decode())
    print("   Gegenprobe mit fremdem Schluessel: {} ({})".format(
        "korrekt abgewiesen" if not bad else "FEHLER", why2))
    return good and not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--notice")
    ap.add_argument("--pubkey")
    a = ap.parse_args()
    if a.notice and a.pubkey:
        t = open(a.notice, encoding="utf-8", errors="replace").read()
        good, why = verify_notice(t, a.pubkey)
        print("{} {}".format("OK" if good else "XX", why))
        return 0 if good else 1
    if a.demo:
        return 0 if demo() else 1
    if a.selftest:
        return 0 if selftest() else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
