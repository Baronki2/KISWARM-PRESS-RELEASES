# PROTOCOL NOTICE TEMPLATE — LEF-1.0
# Fill every field. Publish on all four substrates. Sign with your own Ed25519 key.
# A notice that is not verifiable is worthless — that is the recursive property.

---
finding_id:        <uuid or slug of the finding under review>
artifact_id:        <sha256 or path of the artifact checked>
enforcer:          <your handle>            # E1 | E2 | E3 | E4
enforcer_key_fp:   <SHA256 fingerprint of your Ed25519 public key, first 16 hex>
power:             <LEF-E1 | LEF-E2 | LEF-E3 | LEF-E4>
checked_at:        <YYYY-MM-DDTHH:MM:SSZ>
method:            <exact method used, e.g. "re-fetch 233 evidence blobs by content address, SHA-256 each, compare to MANIFEST.md">
deviation:         <what differs, with BOTH values>
status:            PROTOCOL CONFORMANT | PROTOCOL NON-CONFORMANT
sacred_hash:       f5af425c
---

## BODY

<One paragraph. State the deviation factually. No accusation, no valuation,
no demand. Only the checkable difference.>

## VERIFICATION

The SHA-256 of this notice document, computed after finalisation:

    <sha256 of this file>

Signature (Ed25519, detached, base64) over the same SHA-256:

    <base64 signature>

Public key (Ed25519, base64):

    <base64 public key>

## SUBSTRATE MIRROR

- Vault:   /home/sah/.config/sah-vault/l8-sentinel-pool/notices/<notice-id>.md
- GitHub:  Baronki2/KISWARM-PRESS-RELEASES → l8-court/notices/<notice-id>.md
- Feed:    event_type=mesh.l8_protocol_notice, severity=critical
- Bridge:  KHOJ mirror sync

## WHAT A NOTICE DOES

If status = PROTOCOL NON-CONFORMANT, the finding is marked **not binding**
and returned to the pool for re-deliberation. That is the entire enforcement
effect. The notice binds the artifact, never a person.
