# L8 Independent Seat — Conflict Disclosure Template

Complete and sign before the first notice. Publish with the seat's public key.

```
CONFLICT DISCLOSURE — EXTERNAL LAW-ENFORCER SEAT

handle:
seat (E1..E5):
power (LEF-E1..LEF-E5):
pub_b64 (raw 32-byte Ed25519 public key):
fingerprint sha256(raw32)[:16]:

CONTROL
- Key generated on: <device / OS / account, owned by whom>
- Does the operator have administrative/root access to that device? yes / no
- Has the private key ever been transmitted, uploaded, mailed, or escrowed? yes / no
- Who else can read the private key? <none / list>

RELATIONSHIP
- Relationship to the operator (none / commercial / personal / other):
- Relationship to any party in the case:
- Other seats held, in this court or elsewhere:
- Funding source for this seat:

INDEPENDENCE ATTESTATION
- I can publish PROTOCOL NON-CONFORMANT about the operator's own notices without editorial control. yes / no
- I have not been instructed what verdict to publish. yes / no
- I will not be removed for dissenting. yes / no

DATE: <ISO-8601>

Signature over sha256(this completed text), Ed25519 detached, base64:

    <signature>
```

A disclosure with "yes" to operator root access, key transmission, or instructed verdicts makes the seat operator-controlled; it must be recorded with `independent: false`.

---

**Template by:** operator's AI assistant — design proposal only.

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
