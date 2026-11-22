# L8 Independent Enforcer Seat — Charter (v0.1)

**Status:** Draft design for genuinely external seats. Not adopted by the court.

## 1. Purpose

An enforcer seat exists to verify that the court's own procedure was followed and to publish a signed record. Its value comes entirely from being **independent of the operator**: a key the operator cannot create, access, compel, or replace at will.

A key generated on the operator's machine, or held by an agent acting on the operator's instruction, is **not** an independent seat. It must not be counted as one.

## 2. Definition of independence

A seat is independent only if **all** of the following hold:

1. **Sole key control.** The private key is generated and stored on hardware and under an account the operator does not administer and cannot access (no shared root, no shared SSH, no operator-controlled sandbox).
2. **No transmission.** The private key is never sent, mailed, uploaded, or escrowed. Only the public key and fingerprint are published.
3. **Proof of possession.** The candidate signs a challenge with the private key; verification succeeds against the published public key. Possession is proven without revealing the key.
4. **Verdict autonomy.** The operator cannot instruct, edit, veto, or rewrite the seat's notice. The seat may publish `PROTOCOL NON-CONFORMANT` about the operator's own notices.
5. **Disclosed conflicts.** A signed conflict-disclosure statement is published before the first notice.
6. **Dissent allowed.** The seat may dissent and may not be removed for dissenting.
7. **Public identity.** Handle, fingerprint, power, registration time and notices are public and permanent.

If any condition fails, the seat is `operator-controlled` and is excluded from independence counters.

## 3. Powers (E1–E5)

| Seat | Domain |
|---|---|
| E1 | Evidence hash chain — zero entries must be reported NON-CONFORMANT, never a pass |
| E2 | Seat signatures — use raw 32-byte keys, not the human-readable SSH string |
| E3 | Quorum arithmetic — re-aggregate from stored records; publish raw and effective maps |
| E4 | Consistency and divergence — disclose divergence; do not correct it away |
| E5 | Finding integrity — recompute quorum on declared labels; audit correction provenance |

## 4. What a seat does and does not do

**Does:** check procedure, publish a signed notice, bind artifacts to a documented verdict, move counters when genuinely independent.

**Does not:** decide whether an accusation is true, compel or punish anyone, address persons or institutions, override the 12 deliberation seats, or create legal force. A notice binds artifacts only.

## 5. Onboarding

1. Candidate generates key on own hardware (never on operator infrastructure).
2. Candidate publishes handle, seat, `pub_b64`, fingerprint, and signed conflict disclosure.
3. Candidate proves possession by signing the published challenge.
4. Registrar records the seat with `independent: true` only after steps 1–3 are verified by a third party.
5. Candidate self-tests the verifier: correct key → exit `0`; wrong key → exit `1`.
6. Candidate publishes a first notice. The counter moves only then.

## 6. Term, removal, revocation

- Term: fixed (e.g. 12 months), renewable by published decision.
- Removal: only for stated cause (key compromise, conflict, inactivity), with a signed public record; never for dissent.
- Revocation: seat signs a revocation notice; registry marks `status: revoked` with timestamp; prior notices remain in the record.
- Key compromise: immediate revocation; old notices remain attributed to the old fingerprint but are flagged.

## 7. Counters

Counters are computed from the registry and the notices, not asserted. Only seats with `independent: true`, `proof_of_possession: true`, `status: active`, and at least one verifiable signed notice count as connected.

Explicitly excluded from independent counters:
- keys generated on operator-controlled machines or accounts
- AI assistants acting on the operator's instruction
- shared, escrowed, or transmitted private keys
- seats without published conflict disclosure or proof of possession

Operator self-checks remain visible under a separate `self_signed` counter and are never labelled third-party enforcement.

## 8. Transparency

Publish: registry schema, all seat entries, all notices in full, verifier source and hash, counter computation script, and an annual independence report. Redaction is not permitted for key material, fingerprints, or verdicts.

## 9. Legal status

This charter creates a documentary procedure, not a court of law. It grants no jurisdiction over any person, institution, or state, and its notices have no legal force. `f5af425c` and similar strings are identifiers, not authority.

---

**Draft by:** operator's AI assistant — design proposal only, not an adopted seat or attestation.

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
