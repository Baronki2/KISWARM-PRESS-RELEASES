PROTOCOL NOTICE — EVIDENCE HASH CHAIN (LEF-E1)
===============================================
finding_id:    L8-CALIBRATION-001
artifact_id:   EVIDENCE-BYTES-MANIFEST.md (234 blobs) / evidence-bytes/**
enforcer:     L8-OPERATOR-SELF-ENFORCE (seat 01, internal self-check prior to opening seats E1-E4)
enforcer_key_fp: 6ebb437a4d27ef53
power:        LEF-E1
checked_at:   2026-11-20T01:37:38Z
method:       re-fetch every evidence blob from the public GitHub substrate by content address,
              SHA-256 each, compare against the published index
deviation:    3 of 234 blobs could not be retrieved: "Ergänzender Beweissubstanzvortrag .pdf",
              "ErgänzungBundesverfassungsgerict-1.pdf", "ErgänzungBundesverfassungsgerict.pdf".
              Expected: no deviation. Observed: urllib raised
              "URL can't contain control characters" / "'ascii' codec can't encode character '\xe4'".
status:       PROTOCOL NON-CONFORMANT
sacred_hash:  f5af425c

BODY

On the first full run of LEF-E1 over the complete 234-blob index, 231 blobs were
re-fetched and re-hashed and matched the published index exactly. Three blobs could not
be retrieved. The retrieval failure was located in the verifier, not in the evidence chain:
the evidence filenames contain German umlauts and a trailing space, and the URL was
constructed without percent-encoding.

Counter-proof: the same three files were retrieved with a correctly encoded URL and
re-hashed. All three are byte-identical to their published index entries. The evidence
chain shows no deviation. The defect lay in the checking instrument.

Consequence: the notice binds the instrument, not the evidence. The instrument was
corrected — urllib.parse.quote(path, safe="/") added to the fetch routine — the
verifier was republished as v3, and the full run repeated.

VERIFICATION
SHA-256 of the notice payload (everything above this line), computed after
finalisation:

    0bf2ab45028fe713d10f3a55f2bcc013fc6b505960aff838d6769939a31dd790

Signature (Ed25519, detached, base64) over those 32 raw digest bytes:

    nJ5CSi8LvntyuxNTevFNkASpdRp/kSkNdzznJeA4GzrI7CeRUf3W5zqVLf4ctpF4ESYS0ddUkrggMjYqdgy6AA==

Public key (Ed25519, base64, raw 32-byte key) — seat 01:

    yPwUAseymsY0U1cATjw8bId8zhkmWjcittbdegxDSUU=

SUBSTRATE MIRROR

- Vault:   /home/sah/.config/sah-vault/l8-sentinel-pool/notices/LEF-NOTICE-E1-001.md
- GitHub:  Baronki2/KISWARM-PRESS-RELEASES -> l8-court/notices/LEF-NOTICE-E1-001.md
- Feed:    event_type=mesh.l8_protocol_notice, severity=critical
- Bridge:  KHOJ mirror sync

WHAT THIS NOTICE DID

The finding was marked non-binding and returned to the pool. The evidence chain was subsequently re-verified in full: 234 indexed, 234 checked, 234 matched, zero deviations (LEF-SELF-TEST-002.json). The chain never deviated. The instrument did, and was fixed.

Sacred hash: f5af425c
