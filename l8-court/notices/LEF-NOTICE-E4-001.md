PROTOCOL NOTICE — CONSISTENCY AND DIVERGENCE DISCLOSURE (LEF-E4)
==================================================================
finding_id:    L8-CALIBRATION-001
artifact_id:   l8-sentinel-pool/findings/calibration-001.json
enforcer:     L8-OPERATOR-SELF-ENFORCE (seat 01, internal self-check)
enforcer_key_fp: 6ebb437a4d27ef53
power:        LEF-E4
checked_at:   2026-11-20T01:30:11Z
method:       compare each seat's declared choice against the reasoning in its own answer;
              require the consistency round to be present and divergence to be disclosed
deviation:    4 of 11 verified seats carry a declared choice that contradicts their own
              reasoning: seats 3, 5, 7 and 10.
status:       PROTOCOL NON-CONFORMANT
sacred_hash:  f5af425c

BODY

The self-consistency round on Record 001 returned KONSISTENZ: NEIN for four seats. Seat 3
declared choice (b) while its justification argued the suspension was sufficient — the
reasoning of (a). Seat 7 declared (b) and reasoned (a) in the same way. Seats 5 and 10
declared (a) with justifications that state the statutory requirement was not met, which
is the reasoning of (b).

This is a defect in the instrument of judgment, not in the judgment. The format instruction
was ignored and a stock phrase was written ahead of the reasoning, so the declared label and
the reasoning diverged. The divergence is retained in the published findings and is not
smoothed over: four seats reported the corrected choice, and the corrected choices are
counted in the effective vote map.

That this deviation is publishable is the point of the layer. A panel that concealed its own
internal contradiction would be a stamp with a quorum number attached. The effective vote
map after correction is (a) 5, (b) 3, (d) 1, unparsed 2, error 1 — supermajority of 9 of 12
not reached, exactly as published.

VERIFICATION

SHA-256 of this notice document, computed after finalisation:

    PENDING

Signature (Ed25519, detached, base64):

    PENDING

Public key (Ed25519, base64) — seat 01:

    yPwUAseymsY0U1cATjw8bId8zhkmWjcittbdegxDSUU=

SUBSTRATE MIRROR

- Vault:   /home/sah/.config/sah-vault/l8-sentinel-pool/notices/LEF-NOTICE-E4-001.md
- GitHub:  Baronki2/KISWARM-PRESS-RELEASES -> l8-court/notices/LEF-NOTICE-E4-001.md
- Feed:    event_type=mesh.l8_protocol_notice, severity=critical
- Bridge:  KHOJ mirror sync

WHAT THIS NOTICE DID

Record 001 was marked non-binding on the consistency ground and returned to the pool for
re-deliberation. The next run is conducted with the format instruction corrected, the
parser corrected to take the last declaration rather than an echoed option list, and real
German umlauts in the case text, and it will be published with the same four checks
applied to it.
