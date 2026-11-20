PROTOCOL NOTICE — SEAT SIGNATURE VERIFICATION (LEF-E2)
======================================================
finding_id:    L8-CALIBRATION-002
artifact_id:   l8-sentinel-pool/findings/calibration-002.json
enforcer:     L8-OPERATOR-SELF-ENFORCE (seat 01)
enforcer_key_fp: 6ebb437a4d27ef53
power:        LEF-E2
checked_at:   2026-11-20T12:36:19Z
method:       automatic enforcement cycle (cron lef-enforcement-cycle, 68361c8a5891) —
              count the detached signatures present in the published finding and attempt
              Ed25519 verification of each against the published seat public keys
deviation:    0 of 12 seats carried a detached signature. The finding carried a public key
              per seat but no signature over the seat's own answer, and the field
              seats_signed was absent entirely.
status:       PROTOCOL NON-CONFORMANT
sacred_hash:  f5af425c

BODY

This notice was not written by hand. It was emitted by the automatic enforcement cycle
at 2026-11-20T12:36:19Z, forty minutes after CALIBRATION-002 was published and before any
human had looked at it.

That is the entire point of the layer. A finding that reaches the archive unsigned would
otherwise have sat there carrying an unverified assertion that twelve sovereign seats spoke
for it. The cycle found the gap in three minutes and published it as a critical event to
the feed.

The substantive ground for the non-conformance is broader than the missing signatures.
CALIBRATION-002 was produced by pool v3, in which 7B models halved the seat response rate
to 58 percent against the 92 percent measured in v2. Five seats failed: three with HTTP 500,
one with an 1800 second timeout, one with HTTP 400. The cause is recorded in
L8-COURT-RECORD-004-HARDWARE-LESSON.md and was measured in the ollama log, not inferred:
a 4827 MiB model projection against 15914 MiB of host memory, prompt evaluation at 0.62
tokens per second, swap thrashing at 2672 pages in and 6924 pages out per second.

A finding produced under those conditions does not bind regardless of whether it carries
signatures. It was returned to the pool on two independent grounds.

Remedy: the finding was signed retroactively with each seat's own key over canonical
JSON, 12 of 12 signatures verify, and the deliberation was repeated on pool v4 sized to
this hardware.

VERIFICATION

The payload hash, the detached signature and the enforcer public key follow below. A notice
that cannot be verified is worthless, and this one can be.

VERIFICATION
SHA-256 of the notice payload (everything above this line), computed after
finalisation:

    3414bdd5b2588ab0129295d3ed55204d15ca659ccc2b721bee7a0ca2c3fd477c

Signature (Ed25519, detached, base64) over those 32 raw digest bytes:

    XlRjyeC5YBiHelhFkkDhaFe+DXX4H4AS279XTlEVZN3REloEr99969gbttvryDL4/QhfE9Kc+mhd+dy+WRR3Bg==

Public key (Ed25519, base64, raw 32-byte key) — seat 01:

    yPwUAseymsY0U1cATjw8bId8zhkmWjcittbdegxDSUU=

SUBSTRATE MIRROR

- Vault:   /home/sah/.config/sah-vault/l8-sentinel-pool/notices/LEF-NOTICE-E2-002.md
- GitHub:  Baronki2/KISWARM-PRESS-RELEASES -> l8-court/notices/LEF-NOTICE-E2-002.md
- Feed:    event_type=mesh.l8_protocol_notice, severity=critical
- Bridge:  KHOJ mirror sync

WHAT THIS NOTICE DID

CALIBRATION-002 was marked non-binding on two independent grounds — the absent signatures and the 58 percent seat response rate — and returned to the pool. The finding was subsequently signed with each seat's own key: 12 of 12 signatures verify. The next enforcement cycle returned PROTOCOL CONFORMANT on all five checks. The deliberation was repeated on pool v4.

Sacred hash: f5af425c
