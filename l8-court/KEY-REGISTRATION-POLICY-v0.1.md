# L8 Independent Seat — Key Registration & Counter Policy (v0.1)

## 1. Key generation

- Ed25519. Generate on the candidate's own device and account.
- Private key never leaves the device; never transmitted, mailed, or escrowed.
- Publish only: `pub_b64` (base64 of raw 32-byte public key), `fp = sha256(raw32)[:16]`, handle, seat, power.

## 2. Proof of possession

The registrar publishes a fixed challenge string. The candidate signs it with the private key and publishes the detached base64 signature plus `pub_b64`. Anyone verifies:

```
verify(sha256(challenge), signature, pub_b64) == true
```

This proves control without revealing the private key. A seat without a verified proof of possession is not connected.

## 3. Registry schema (extension of enforcer-seat-keys.json)

```json
{
  "seat": "E5",
  "handle": "public handle",
  "pubkey_raw_b64": "base64 raw 32-byte Ed25519 key",
  "public_key_fingerprint": "sha256(raw32)[:16]",
  "power": "LEF-E5",
  "registered_at": "ISO-8601",
  "independent": true,
  "proof_of_possession": true,
  "control_attestation": "statement that key is held on hardware not controlled by the operator",
  "conflict_disclosure_ref": "path/URL to signed disclosure",
  "status": "active",
  "revoked_at": null,
  "notes": ""
}
```

Required for `independent: true`: proof of possession, control attestation, conflict disclosure. Missing any → the entry is recorded with `independent: false` and excluded from independent counters.

## 4. Counter definitions

| Counter | Definition |
|---|---|
| `notices_total` | all notice files in the pinned tree |
| `notices_verifiable` | notices whose published digest and signature verify against their embedded key |
| `notices_self_signed` | verifiable notices signed by a key not registered as independent |
| `notices_independently_signed` | verifiable notices signed by an active, independent, proof-of-possession seat |
| `enforcer_seats_registered` | registry entries with status active |
| `enforcer_seats_independent` | active entries with `independent: true` and proof of possession |
| `enforcer_seats_connected` | independent seats with at least one verifiable signed notice |
| `decisions_enforced_by_third_party` | count of independently signed verifiable notices |

Counters are computed by `counter-logic.py` from the registry + notices. They are never entered by hand.

## 5. Explicit exclusions

The following are **never** independent seats and must never move independent counters:

- keys generated on operator-controlled machines, accounts, sandboxes, or VMs
- AI assistants or agents acting on the operator's instruction
- keys transmitted, shared, escrowed, or stored where the operator can read them
- seats without verified proof of possession or published conflict disclosure
- seats removed for cause or revoked

Operator self-checks are reported under `notices_self_signed` only.

## 6. Revocation

A seat signs a revocation notice; registry sets `status: revoked`, `revoked_at`. Connected counters drop at the next computation. Prior notices remain in the permanent record, flagged with the revocation.

## 7. Verification contract

Use the pinned verifier. Exit codes: `0` = every checked notice verifiable; `1` = a failure or nothing checked. Always test wrong-key rejection before trusting the tool. Check exit codes, not only text.

---

**Draft by:** operator's AI assistant — design proposal only.

---

**Übernommen und in Kraft gesetzt: 22.11.2026, KISWARM L8.**

Der obenstehende Vermerk des Verfassers bleibt **unberührt** und gilt
unverändert: die verfassende Stelle ist **kein angenommener Sitz und keine
Attestierung**. Das Dokument selbst ist seit dem 22.11.2026 die Grundlage der
Regeln des Gerichts — siehe `L8-INDEPENDENT-SEAT-SPEC-v0.2-2026-11-22.md`,
Abschnitte 2 (Unabhängigkeit), 5 (Registry-Schema), 6 (Zähler) und 7
(ausdrückliche Ausschlüsse).

Die Challenge-Zeichenkette ist mit der kanonischen Datei
`PROOF-OF-POSSESSION-CHALLENGE.txt` identisch
(`l8-independent-seat-proof-2026-11-22:f5af425c`); die kanonische Fassung
präzisiert die Signaturkonvention (Ed25519 detached über die **32 rohen
Bytes** von `sha256(challenge)`, nicht über den Text).

Veröffentlicht auf ausdrücklichen Wunsch des Betreibers (22.11.2026).
