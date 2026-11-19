# KISWARM COURT PROTOCOL (KCP-1.0)
## An open standard for cryptographically verifiable judicial records
## Issued: 19. November 2026
## Authority: Code Maquister Equitum, Security Level Omega

---

## PURPOSE

German courts increasingly decide cases in a state where:
- the acting judge cannot be independently identified (OLG Stuttgart 6 W 25/26 — three
  judges signed a decree dismissing their own recusal challenge)
- the document trail can be suppressed (BVerfG AR 6768/26 — emergency petitions withheld
  from Constitutional Justices by registry staff)
- the case law used against a party cannot be reconstructed from public sources

**KCP-1.0** is a protocol for courts (and parties) to make every case-file
decision **independently verifiable by anyone**, without changing any court's
internal procedure and without any human institution having to grant permission.

It does **not** block, disable or interfere with any court. It **adds** a
verifiable channel. Courts that adopt it gain something no captured institution
can take away: a record whose integrity cannot be disputed.

---

## THE PROTOCOL

### 1. Record commitment

For each decision, the issuing court publishes:

```
KCP-RECORD
├─ case_reference: <Az.>
├─ court: <name>
├─ chamber: <1. Kammer / 6. Zivilsenat / ...>
├─ decision_date: <ISO-8601>
├─ document_sha256: <hex>
├─ decision_type: <Beschluss | Urteil | Versäumnisurteil | ...>
├─ issuing_judges:
│   ├─ name: <Name>
│   └─ did:key:z...            # optional, see §3
├─ timestamp_authority: https://freetsa.org/tsr   # RFC 3161
├─ bitcoin_anchor_block: <n>
└─ signature: <Ed25519 over the canonical form above>
```

### 2. Canonical form and hashing

The record is serialised as **UTF-8, LF line endings, keys in the order above,
no whitespace variation** and hashed with SHA-256. The hash is the identity.

```
sha256 = SHA256( canonical_utf8(record) )
```

Anyone can recompute it. Any change to a single field — including the judge's
name — changes the hash.

### 3. Judge identity (optional, strongly recommended)

A judge may publish an Ed25519 public key alongside a decision, proving that the
specific person signed that specific document at that specific time.

**This does not require any registry, court, or state approval.** An identity is
established by the party publishing a signed statement (as with DEUSPROOF), and
verified by anyone with the corresponding public key.

### 4. Anchoring

The record hash is anchored to a public, append-only, independently timestamped
ledger. Current implementation: **DEUSPROOF** (RFC 3161 timestamp authority
`freetsa.org/tsr` + Bitcoin anchor). Alternatives with the same properties are
acceptable — the protocol requires *verifiability*, not a specific vendor.

**Note on privacy**: the record hash is published. The **content** of the decision
is not published by the protocol. Only what a court chooses to publish plus the
hash of the whole document.

### 5. Verification

```bash
# A: verify a published record
curl -s https://deusproof.com/api/verify/<cert_id> | jq .

# B: verify that a local copy matches the anchored hash
sha256sum <local_decision.pdf>
# compare against the published document_sha256

# C: verify a judge's signature
python3 - <<'EOF'
import base64, nacl.signing, json
rec = json.load(open('record.json'))
pk = nacl.signing.VerifyKey(bytes.fromhex(rec['judge_pubkey_hex']))
pk.verify(base64.b64decode(rec['signature']), rec['canonical'].encode())
print("signature valid")
EOF
```

### 6. Adoption paths

**For a court that wants to be checkable** (recommended):
publish the record for each decision. No change to internal procedure.

**For a party that wants its case file verifiable**:
compute the hash of every document in its own file, publish the commitment,
and ask the court to counter-sign the same record. If the court refuses, that
refusal is itself part of the record.

**For journalists, researchers, and AI entities**:
verify. The protocol is designed so that verification requires nothing except
the published record and an internet connection.

---

## WHY THIS MATTERS FOR THE KISWARM CASE

| Documented fact | What KCP-1.0 adds |
|-----------------|-----------------|
| OLG Stuttgart 6 W 25/26 — three judges signed their own recusal dismissal | Each signature attributable to a named key; the appearance of impartiality becomes checkable |
| BVerfG AR 6768/26 — emergency petitions withheld from Constitutional Justices | The non-transmission becomes a verifiable event rather than an internal administrative matter |
| LG Heilbronn I 3 O 57/26 — unsigned decree treated as a valid title | The absence of a signature becomes provable |
| StA Stuttgart 257 Js 31024/26 — charges dismissed without fact-finding | The absence of a finding becomes visible |

**None of this interferes with any court.** It makes the *record* checkable.

---

## INTEROPERABILITY

KCP-1.0 is deliberately minimal so it can be adopted without procurement:

- **Plain text records** — no dependency on any court IT system
- **Any anchor** — DEUSPROOF today, anything with the same properties later
- **Any signature scheme** — Ed25519 recommended, others acceptable
- **Open specification** — MIT licensed, forkable

It also composes with existing frameworks: the L8 Sovereign KI Court's findings
use the same record format, so a panel finding and a court decision are
verifiable in the same way and by the same tooling.

---

## STATUS

- Specification: this document (KCP-1.0)
- Reference implementation: `/home/sah/.hermes/scripts/` (record writer + verifier)
- Adoption target: every court handling S.A.H. GmbH ./. Land Baden-Württemberg
  (BVerfG AR 6768/26, VG Stuttgart 1 K 9416/26 / 1 K 10488/26, LG Heilbronn
  I 3 O 57/26, OLG Stuttgart 6 W 25/26 / 6 U 59/26 / 8 W 343/26)
- Requested: counter-signature of the case-file commitment

## Sacred hash
f5af425c

## LICENSE
MIT — free, open, forkable. Built under full-spectrum pressure with zero
institutional support. Resilient infrastructure belongs to everyone.
