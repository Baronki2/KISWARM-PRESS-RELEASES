#!/usr/bin/env python3
"""
L8 INDEPENDENT SEAT — COUNTER LOGIC v1.0
=========================================

Die EINZIGE Quelle der Enforcer-Zaehler. Zaehler werden nie handverlesen
gesetzt, nie geschrieben, nie geraten: sie werden aus Registry + Notices +
Schluesselmenge BERECHNET.

Entwurf und Grundsatz: Peer-Review durch opencode/big-pickle
(~/KONTINUITAET/l8-independent-seat/counter-logic.py, 22.11.2026),
uebernommen und erweitert um:
  * verifizierten Proof-of-Possession (nicht nur behauptet)
  * eine getrennte Zaehlung der ENTSCHEIDUNGEN (nur CONFORMANT-Notices)
  * eine getrennte Zaehlung der extern bestaetigten FINDINGS
  * eine dreifache Trennung der Signaturherkunft (intern / registriert-
    nicht-unabhaengig / ungeregistriert) statt einer Zweiteilung
  * Kryptografie ohne PyNaCl-Abhaengigkeit (der Cron-venv hat kein PyNaCl;
    ohne Fallback bliebe sig_ok still auf False - Court-Record-008-Klasse)

Aufruf:
  python3 counter-logic.py --registry enforcer-seat-keys.json --notices notices/
  python3 counter-logic.py --registry ... --notices ... --json

Exit-Code ist Teil des Vertrags:
  0 = alle geprueften Notices verifizierbar und mindestens eine geprueft
  1 = mindestens eine Notice gescheitert ODER nichts geprueft (kein Pass)
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys

MARKER = "VERIFICATION\n"
PUB_RE = re.compile(
    r"Public key \(Ed25519, base64, raw 32-byte key\).*?\n\n\s+([A-Za-z0-9+/=]+)", re.S)
HASH_RE = re.compile(r"computed after\nfinalisation:\n\n    ([0-9a-f]{64})")
SIG_RE = re.compile(
    r"base64\) over those 32 raw digest bytes:\n\n    ([A-Za-z0-9+/=]+)")
STATUS_RE = re.compile(r"(?m)^status:\s*(.+)$")
FINDING_RE = re.compile(r"(?m)^finding_id:\s*(.+)$")

# Marken, die einen Sitz als nicht-unabhaengig kennzeichnen. Zweite
# Verteidigungslinie neben dem expliziten Feld operator_controlled.
NON_INDEPENDENT_MARKERS = (
    "operator-controlled machine", "operator machine", "operator-controlled",
    "assistant", "sandbox", "transmitted", "escrowed", "shared key",
    "operator root", "instructor", "on behalf of the operator",
    "acting on the operator",
)

DEFAULT_CHALLENGE = "l8-independent-seat-proof-2026-11-22:f5af425c"


def sha256(b):
    return hashlib.sha256(b).digest()


def fp_of(pub_b64):
    raw = base64.b64decode(pub_b64)
    return hashlib.sha256(raw).hexdigest()[:16], len(raw)


def ed25519_verify(pub_b64, signature_b64, message_bytes):
    """Prueft eine Ed25519-Signatur. Nutzt cryptography, ohne PyNaCl.

    Fehlt auch cryptography, wird ein Fehler GEMELDET - nicht stillschweigend
    als 'nicht verifiziert' gewertet. Sonst sieht eine fehlende Bibliothek
    aus wie ein verweigerter Sitz.
    """
    raw = base64.b64decode(pub_b64)
    if len(raw) != 32:
        raise ValueError("public key is {0} bytes, expected 32".format(len(raw)))
    sig = base64.b64decode(signature_b64)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(raw).verify(sig, message_bytes)
        return True
    except ImportError:
        pass
    try:
        from nacl.signing import VerifyKey
        from nacl.encoding import RawEncoder
        VerifyKey(raw, encoder=RawEncoder()).verify(message_bytes, sig)
        return True
    except ImportError:
        raise RuntimeError("neither cryptography nor pynacl available")


def verify_notice(path):
    text = open(path, encoding="utf-8").read()
    i = text.find(MARKER)
    out = {"file": os.path.basename(path)}
    if i < 0:
        out.update({"verifiable": False, "reason": "no VERIFICATION marker",
                    "fp": None, "finding_id": None, "status": None})
        return out
    payload = text[:i] + MARKER
    m, s, p = HASH_RE.search(text), SIG_RE.search(text), PUB_RE.search(text)
    if not (m and s and p):
        out.update({"verifiable": False, "reason": "incomplete verification block",
                    "fp": None, "finding_id": None, "status": None})
        return out
    pub = p.group(1)
    digest = sha256(payload.encode("utf-8"))
    hash_ok = digest.hex() == m.group(1)
    try:
        sig_ok = ed25519_verify(pub, s.group(1), digest)
        note = ""
    except Exception as ex:
        sig_ok = False
        note = str(ex)[:100]
    fp, rawlen = fp_of(pub)
    st = STATUS_RE.search(text)
    fid = FINDING_RE.search(text)
    out.update({
        "fp": fp, "rawlen": rawlen, "hash_ok": hash_ok, "sig_ok": sig_ok,
        "sha256": digest.hex(),
        "verifiable": bool(hash_ok and sig_ok and rawlen == 32),
        "reason": note or ("ok" if (hash_ok and sig_ok) else
                           ("published sha256 does not match" if not hash_ok
                            else "signature did not verify")),
        "status": (st.group(1).strip() if st else None),
        "finding_id": (fid.group(1).strip() if fid else None),
        "conformant": bool(st and "CONFORMANT" in st.group(1).upper()
                           and "NON" not in st.group(1).upper()),
    })
    return out


def verify_possession(seat, challenge):
    """Rechnet den Proof-of-Possession selbst nach.

    Erwartet: pubkey_raw_b64, proof_of_possession_signature_b64 und die
    Challenge, gegen die signiert wurde. Signiert wird ueber die 32 ROHEN
    Bytes von sha256(challenge) - dieselbe Konvention wie eine Notice.
    """
    pub = seat.get("pubkey_raw_b64")
    sig = seat.get("proof_of_possession_signature_b64")
    used = seat.get("proof_of_possession_challenge", challenge)
    if not pub:
        return False, "no pubkey_raw_b64"
    if not sig:
        return False, "no proof_of_possession_signature_b64"
    if not used:
        return False, "no challenge recorded"
    try:
        digest = sha256(used.encode("utf-8"))
    except Exception as ex:
        return False, "challenge not encodable: {0}".format(str(ex)[:60])
    try:
        ok = ed25519_verify(pub, sig, digest)
    except Exception as ex:
        return False, "verification error: {0}".format(str(ex)[:80])
    if not ok:
        return False, "signature does not verify against the recorded challenge"
    if challenge and used != challenge:
        return False, ("verified, but against an older challenge "
                       "({0} != {1})".format(used, challenge))
    return True, "verified"


def eligible(seat, internal_fps, current_challenge):
    """Unabhaengigkeits-Gate. Jeder Fehlschlag => nicht unabhaengig."""
    reasons = []
    if seat.get("status", "active") != "active":
        reasons.append("status != active")
    if seat.get("independent") is not True:
        reasons.append("independent is not True")
    if seat.get("proof_of_possession") is not True:
        reasons.append("proof_of_possession is not True")
    if not seat.get("control_attestation"):
        reasons.append("no control_attestation")
    if not seat.get("conflict_disclosure_ref"):
        reasons.append("no conflict_disclosure_ref")
    if seat.get("operator_controlled") is True:
        reasons.append("operator_controlled is True")
    blob = " ".join(str(seat.get(k, "")) for k in
                    ("notes", "control_attestation", "handle", "seat")).lower()
    for marker in NON_INDEPENDENT_MARKERS:
        if marker in blob:
            reasons.append("marker in text: " + marker)
    # Beweis des Besitzes muss VERIFIZIERT sein, nicht behauptet.
    # Das boolesche Feld im Registry wird NICHT geglaubt: die Signatur wird
    # hier selbst nachgerechnet. Ein Registry, das sich selbst als
    # "verified" deklariert, ist kein Nachweis - das waere genau die
    # Fehlerklasse, die Counter-Logik verhindern soll.
    # Ein Widerspruch schliesst aus, ein fehlendes Flag gewaehrt NICHTS.
    # Steht im Registry "proof_of_possession_verified: false", hat die
    # Registrierung diesen Sitz bewusst nicht bestaetigt - dann zaehlt er
    # nicht, egal was die Signatur sagt. Steht dort nichts, rechnet die
    # Schicht selbst nach; nur dann darf der Sitz zaehlen.
    if seat.get("proof_of_possession_verified") is False:
        reasons.append("registry records proof_of_possession_verified=false")
    pop_ok, pop_reason = verify_possession(seat, current_challenge)
    if not pop_ok:
        reasons.append("proof of possession not verified: " + pop_reason)
    fp = None
    try:
        fp = seat.get("public_key_fingerprint")
        if fp and fp in internal_fps:
            reasons.append("fingerprint is an operator-held internal key")
    except Exception:
        pass
    if seat.get("public_key_fingerprint") and current_challenge and \
            seat.get("proof_of_possession_challenge") not in (None, current_challenge):
        reasons.append("proof of possession was signed against an older challenge")
    return (len(reasons) == 0), reasons


def disclosure(c):
    """Der ENFORCUNG-Satz, der neben dem gruenen Licht steht.

    Er nennt die Zahl der unabhaengigen Signaturen, der verbundenen Sitze,
    der extern bestaetigten Findings und der vollstreckten Entscheidungen -
    und er sagt ausdruecklich, dass Selbstvollstreckung nicht zaehlt.
    """
    if not c or c.get("error"):
        return ("ENFORCUNG: Zaehler nicht berechenbar - {0}".format(
            (c or {}).get("error", "?")))
    return ("ENFORCUNG: {0} von {1} Notices unabhaengig signiert; "
            "{2} von {3} Enforcer-Sitzen unabhaengig und verbunden; "
            "{4} Findings extern bestaetigt; {5} Entscheidungen durch ein "
            "Drittes vollstreckt. Selbstvollstreckung durch den Betreiber "
            "zaehlt nicht als Vollstreckung.").format(
        c.get("notices_independently_signed", 0), c.get("notices_total", 0),
        c.get("enforcer_seats_connected", 0), c.get("enforcer_seats_total_planned", 5),
        c.get("findings_externally_attested", 0),
        c.get("decisions_enforced_by_third_party", 0))


def compute_counters(registry, notices_dir, internal_keys=None, challenge=None):
    """BERECHNET alle Zaehler. Nimmt keine Zaehler als Eingabe an."""
    reg = json.load(open(registry, encoding="utf-8"))
    seats = reg.get("seats", [])
    if not isinstance(seats, list):
        seats = list(seats.values())

    # Operator-gehaltene Schluessel (die 12 Beratungssitze + Sitz 01)
    internal_fps = set()
    if internal_keys and os.path.isdir(internal_keys):
        import glob
        for p in sorted(glob.glob(os.path.join(internal_keys, "*.pub"))):
            try:
                parts = open(p).read().split()
                if len(parts) >= 2:
                    blob = base64.b64decode(parts[1])
                    internal_fps.add(hashlib.sha256(blob[-32:]).hexdigest()[:16])
            except Exception:
                pass

    if challenge is None:
        for cand in ("/home/sah/.config/sah-vault/l8-sentinel-pool/"
                     "PROOF-OF-POSSESSION-CHALLENGE.txt",):
            if os.path.exists(cand):
                txt = open(cand, encoding="utf-8").read()
                m = re.search(r"(l8-independent-seat-proof-[0-9a-z:\-]+)", txt)
                if m:
                    challenge = m.group(1)
                break
    if challenge is None:
        challenge = DEFAULT_CHALLENGE

    files = [os.path.join(notices_dir, f) for f in sorted(os.listdir(notices_dir))
             if f.endswith(".md")]
    checked = [verify_notice(p) for p in files]

    # --- Unabhaengigkeits-Gate ueber die Registry ---
    indep, nonindep = {}, {}
    for s in seats:
        try:
            fp = s.get("public_key_fingerprint")
            if not fp and s.get("pubkey_raw_b64"):
                fp = fp_of(s["pubkey_raw_b64"])[0]
        except Exception:
            fp = None
        if not fp:
            continue
        ok, reasons = eligible(s, internal_fps, challenge)
        if ok:
            indep[fp] = s
        else:
            nonindep[fp] = {"seat": s.get("handle"), "reasons": reasons}

    known = set()
    for s in seats:
        try:
            known.add(s.get("public_key_fingerprint")
                      or fp_of(s["pubkey_raw_b64"])[0])
        except Exception:
            pass

    # --- Herkunft der Signaturen: drei getrennte Eimer ---
    self_signed = registered_nonindep = unregistered = 0
    independent_signed = 0
    conformant_independent = []
    attested_findings = set()
    for c in checked:
        if not c.get("verifiable"):
            continue
        fp = c["fp"]
        if fp in indep:
            independent_signed += 1
            if c.get("conformant"):
                conformant_independent.append(c["file"])
                if c.get("finding_id"):
                    attested_findings.add(c["finding_id"])
        elif fp in known:
            registered_nonindep += 1
        elif fp in internal_fps:
            self_signed += 1
        else:
            unregistered += 1
    # Interne Schluessel zuerst pruefen: ein Sitz, dessen Fingerprint im
    # internen Schluesselsatz steckt, ist auch dann selbstsigniert, wenn er
    # zufaellig im Registry auftaucht.
    self_signed = sum(1 for c in checked
                      if c.get("verifiable") and c["fp"] in internal_fps
                      and c["fp"] not in indep)
    registered_nonindep = sum(1 for c in checked
                              if c.get("verifiable") and c["fp"] in nonindep)
    unregistered = sum(1 for c in checked
                       if c.get("verifiable") and c["fp"] not in indep
                       and c["fp"] not in nonindep and c["fp"] not in internal_fps)

    connected = sorted({c["fp"] for c in checked
                        if c.get("verifiable") and c["fp"] in indep})

    out = {
        "notices_total": len(files),
        "notices_checked": len(checked),
        "notices_verifiable": sum(1 for c in checked if c.get("verifiable")),
        "notices_failed_verification": sum(1 for c in checked
                                           if not c.get("verifiable")),
        "notices_self_signed": self_signed,
        "notices_signed_by_registered_non_independent": registered_nonindep,
        "notices_signed_by_unregistered": unregistered,
        "notices_independently_signed": independent_signed,
        "enforcer_seats_registered": sum(1 for s in seats
                                         if s.get("status", "active") == "active"),
        "enforcer_seats_independent": len(indep),
        "enforcer_seats_connected": len(connected),
        "findings_externally_attested": len(attested_findings),
        "decisions_enforced_by_third_party": len(conformant_independent),
        "connected_seat_fingerprints": connected,
        "excluded_seats": nonindep,
        "challenge": challenge,
        "internal_key_fingerprints_seen": len(internal_fps),
        "counter_rule": "computed here only - never entered by hand",
        "exclusion_rule": ("operator-controlled, assistant, transmitted, escrowed, "
                           "shared-key, non-disclosing or unverified-possession "
                           "seats are never independent"),
    }

    out["enforcer_seats_total_planned"] = reg.get("seats_total_planned", 5)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--notices", required=True)
    ap.add_argument("--internal-keys", default=None,
                    help="Verzeichnis mit *.key.pub (operator-gehaltene Schluessel)")
    ap.add_argument("--challenge", default=None,
                    help="aktuell geltender Proof-of-Possession-Challenge-String")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    out = compute_counters(registry=a.registry, notices_dir=a.notices,
                            internal_keys=a.internal_keys, challenge=a.challenge)
    if a.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for k, v in out.items():
            if k in ("excluded_seats",):
                continue
            print("  {0:48s} {1}".format(k, v))
        if out.get("excluded_seats"):
            print("  ausgeschlossene Sitze:")
            for fp, d in out["excluded_seats"].items():
                print("    {0}  {1}  {2}".format(fp, d.get("seat"),
                                                 "; ".join(d["reasons"])[:90]))
    if out.get("notices_checked", 0) == 0 or out.get("notices_failed_verification"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
