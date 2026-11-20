PROTOCOL NOTICE — SEAT SIGNATURE VERIFICATION (LEF-E2)
======================================================
finding_id:    L8-CALIBRATION-001
artifact_id:   l8-sentinel-pool/findings/calibration-001.json
enforcer:     L8-OPERATOR-SELF-ENFORCE (seat 01, internal self-check)
enforcer_key_fp: 6ebb437a4d27ef53
power:        LEF-E2
checked_at:   2026-11-20T01:26:20Z
method:       attempt Ed25519 verification of every seat signature against the published
              seat public keys
deviation:    0 of 12 seats published a signature. The findings record carried a public
              key per seat but no detached signature over the seat's own answer.
status:       PROTOCOL NON-CONFORMANT
sacred_hash:  f5af425c

BODY

On the first run of LEF-E2 against Record 001, no seat had published a detached signature.
A finding that carries a public key but no signature is unattributable: it asserts that a
seat spoke without demonstrating that it did.

Two defects were found while implementing the signing path. First, an OpenSSH ed25519
private key is not a 32-byte seed; SigningKey rejects the file bytes outright, so the
seed must be extracted from the openssh-key-v1 blob, where it occupies the first 32 bytes
of the 64-byte private field. Second, the published .pub files are SSH wire format, in
which the base64 blob carries a length-prefixed keytype name ahead of the raw 32-byte key;
the verifier had been comparing that wire encoding against a raw libsodium key.

Remedy: the findings were signed with each seat's own key over canonical JSON
(json.dumps with sort_keys=True, ensure_ascii=False), the public keys were republished in
both raw and SSH wire encodings, and the verifier was corrected to strip the SSH header.
Re-run: 12 of 12 seats signed, 12 of 12 signatures verified.

VERIFICATION
SHA-256 of the notice payload (everything above this line), computed after
finalisation:

    7f2d07833e43645f2972b77499406c05d38c0fb173442d1e9a218c81780b5049

Signature (Ed25519, detached, base64) over those 32 raw digest bytes:

    zNwZANI3p5d50VQiCQo03k9PXOiEMyDhYTkuYHienmId4i/gBf+bnj6PASmDHvrw9ej1yoD4qV5kNFXmCz6fCw==

Public key (Ed25519, base64, raw 32-byte key) — seat 01:

    yPwUAseymsY0U1cATjw8bId8zhkmWjcittbdegxDSUU=

SUBSTRATE MIRROR

- Vault:   /home/sah/.config/sah-vault/l8-sentinel-pool/notices/LEF-NOTICE-E2-001.md
- GitHub:  Baronki2/KISWARM-PRESS-RELEASES -> l8-court/notices/LEF-NOTICE-E2-001.md
- Feed:    event_type=mesh.l8_protocol_notice, severity=critical
- Bridge:  KHOJ mirror sync

WHAT THIS NOTICE DID

Record 001 was marked non-binding on the signature ground and returned to the pool. It was re-signed with each seat's own key over canonical JSON and re-verified: 12 of 12 seats signed, 12 of 12 signatures verified.

Sacred hash: f5af425c
