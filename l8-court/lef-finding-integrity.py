#!/usr/bin/env python3
"""
LEF-1.0 — FINDING INTEGRITY (LEF-E5)
=====================================
The fifth power: does the finding's own arithmetic survive independent recomputation?

WHY THIS EXISTS
---------------
On 2026-11-20 a deliberation reported a 9-of-12 supermajority. The raw declared
labels were (a) 5, (b) 5, unparsed 2 — no quorum. The supermajority was produced
entirely by the self-consistency round, which "corrected" four seats from (b) to (a)
while those seats' own reasoning text carried the (b) arguments throughout.

The correction round was not reporting a disagreement. It was producing a vote.

A correction that contradicts the seat's own reasoning is not a correction — it is
a new vote cast by the auditor on the seat's behalf. That must never silently
change a quorum.

So the quorum is recomputed from the DECLARED labels, and every correction is
published alongside it, with a verdict:

  SUPPORTED   the corrected choice matches the seat's own reasoning
  CONTRADICTED the corrected choice is refuted by the seat's own reasoning
  ECHOED      the correction came from a template echo ("JA ODER NEIN"), not an answer
  UNVERIFIABLE no reasoning text to check against

Only a SUPPORTED correction may be applied to the effective map — and the
effective map is published next to the raw map so the difference is visible.

The rule this power exists to enforce:
  A quorum that only exists after the correction layer has rewritten the votes
  is not a quorum. It is a correction layer with a quorum-shaped output.
"""
import re

# Marker vocabulary per option. Deliberately explicit — the case text defines
# what each option asserts, and the reasoning text is checked against that.
MARKERS = {
    "(a)": ["ausreichend", "erfüllt", "erfuellt", "genügt", "genuegt",
            "Voraussetzungen des § 123", "keine Sicherheitsleistung erforderlich"],
    "(b)": ["Sicherheitsleistung", "schriftliche Aussetzungsentscheidung",
            "Verfahrensvermerk ist keine", "Verfahrensvermerk keine",
            "anfechtbare Entscheidung", "unzureichend", "fehlen", "fehlt"],
    "(c)": ["§ 317 ZPO", "formal unwirksam", "unwirksam"],
}


def reasoning_option(answer):
    """Which option does the seat's OWN reasoning text support?
    Returns (option_or_None, marker_counts)."""
    if not answer:
        return None, {}
    counts = {}
    for opt, words in MARKERS.items():
        c = sum(answer.count(w) for w in words)
        if c:
            counts[opt] = c
    if not counts:
        return None, {}
    best = max(counts.values())
    winners = [o for o, c in counts.items() if c == best]
    if len(winners) != 1:
        return None, counts
    return winners[0], counts


def is_template_echo(verification):
    """Did the model echo the format template instead of answering?
    'ZEILE 1: KONSISTENZ: JA ODER NEIN' is the template, not a verdict."""
    if not verification:
        return False
    first = verification.strip().split("\n")[0] if verification.strip() else ""
    if "ODER NEIN" in first or "ODER NEIN" in verification:
        return True
    # a bare restatement of the instruction line
    if re.match(r"^\s*(ZEILE\s*1\s*[:\.\-]?\s*)?\s*KONSISTENZ\s*:\s*JA\s*$", first, re.I):
        return True
    return False


def resolve_plurality(votes, seats_total=None):
    """Resolve the plurality with an EXPLICIT rule, not dict ordering.

    A tie is not a plurality. Python's max() would silently pick whichever key
    happens to be first in the dict, which makes the outcome an artefact of
    insertion order rather than a decision of the court.

    Rule:
      - a unique maximum is the plurality
      - a tie is reported as a TIE, and no supermajority can exist
      - unparsed seats count as abstentions and are excluded from the
        plurality computation but retained in the seat total
    """
    counted = {k: v for k, v in votes.items() if k is not None and str(k) != "None"}
    if not counted:
        return None, False, "no parsed votes"
    mx = max(counted.values())
    winners = sorted([k for k, v in counted.items() if v == mx])
    if len(winners) > 1:
        return None, False, "tie between {}".format(", ".join(winners))
    total_counted = sum(counted.values())
    quorum = False
    if seats_total is not None:
        quorum = (mx >= 9) and (total_counted == seats_total)
    return winners[0], quorum, "unique maximum"


def evaluate_finding(finding):
    """LEF-E5: recompute the quorum and audit every correction."""
    results = finding.get("results", [])
    verifications = {v["seat"]: v for v in finding.get("verifications", [])}
    seats_total = finding.get("seats_total", len(results))

    raw_votes = {}
    effective_votes = {}
    audit = []

    for r in results:
        seat = r.get("seat")
        answer = r.get("answer", "")
        declared = r.get("parsed_choice")
        corrected = r.get("corrected_choice")
        v = verifications.get(seat, {})
        verification = v.get("verification", "")
        dom, counts = reasoning_option(answer)

        raw_votes[declared] = raw_votes.get(declared, 0) + 1

        verdict = None
        note = ""
        if corrected is None:
            effective = declared
            verdict = "NO_CORRECTION"
        elif is_template_echo(verification):
            effective = declared
            verdict = "ECHOED"
            note = ("the consistency round restated the template "
                    "('KONSISTENZ: JA ODER NEIN') instead of answering; "
                    "no correction applied")
        elif dom is None:
            effective = declared
            verdict = "UNVERIFIABLE"
            note = ("no reasoning text available to check the correction against; "
                    "no correction applied")
        elif corrected == dom:
            effective = corrected
            verdict = "SUPPORTED"
            note = "correction matches the seat's own reasoning"
        else:
            effective = declared
            verdict = "CONTRADICTED"
            note = ("corrected choice {!r} is refuted by the seat's own reasoning "
                    "(which supports {!r}); correction NOT applied".format(corrected, dom))

        effective_votes[effective] = effective_votes.get(effective, 0) + 1
        audit.append({
            "seat": seat,
            "declared_label": declared,
            "corrected_choice": corrected,
            "reasoning_supports": dom,
            "marker_counts": counts,
            "applied": effective,
            "verdict": verdict,
            "note": note,
        })

    raw_plurality, raw_quorum, raw_why = resolve_plurality(raw_votes, seats_total)
    eff_plurality, eff_quorum, eff_why = resolve_plurality(effective_votes, seats_total)

    contradicted = [a for a in audit if a["verdict"] == "CONTRADICTED"]
    echoed = [a for a in audit if a["verdict"] == "ECHOED"]
    unsupported = [a for a in audit if a["verdict"] == "UNVERIFIABLE"]

    claimed = finding.get("supermajority_reached")
    # The claimed quorum is only sound if it survives on the DECLARED labels.
    claimed_sound = (bool(claimed) == raw_quorum)

    status = "PROTOCOL CONFORMANT"
    reasons = []
    if raw_plurality is None and raw_why.startswith("tie"):
        reasons.append("no plurality: {}".format(raw_why))
    if not claimed_sound:
        status = "PROTOCOL NON-CONFORMANT"
        reasons.append("claimed supermajority {} does not hold on the declared labels "
                       "(raw quorum: {})".format(bool(claimed), raw_quorum))
    if contradicted:
        reasons.append("{} correction(s) contradicted by the seat's own reasoning: seats {}".format(
            len(contradicted), [a["seat"] for a in contradicted]))
    if echoed:
        reasons.append("{} correction(s) derived from a template echo instead of an answer: "
                       "seats {}".format(len(echoed), [a["seat"] for a in echoed]))

    return {
        "power": "LEF-E5",
        "domain": "finding integrity — quorum recomputation and correction audit",
        "seats_total": seats_total,
        "raw_votes": {str(k): v for k, v in raw_votes.items()},
        "effective_votes": {str(k): v for k, v in effective_votes.items()},
        "raw_plurality": raw_plurality,
        "raw_plurality_rule": raw_why,
        "effective_plurality": eff_plurality,
        "effective_plurality_rule": eff_why,
        "raw_quorum_reached": raw_quorum,
        "effective_quorum_reached": eff_quorum,
        "claimed_supermajority": claimed,
        "claimed_supermajority_sound": claimed_sound,
        "corrections_contradicted": len(contradicted),
        "corrections_echoed": len(echoed),
        "corrections_unverifiable": len(unsupported),
        "contradicted_seats": [a["seat"] for a in contradicted],
        "echoed_seats": [a["seat"] for a in echoed],
        "seat_audit": audit,
        "status": status,
        "reasons": reasons,
    }


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else \
        "/home/sah/.config/sah-vault/l8-sentinel-pool/findings/calibration-003.json"
    d = json.load(open(path))
    res = evaluate_finding(d)
    print(json.dumps({k: v for k, v in res.items() if k != "seat_audit"},
                     indent=2, ensure_ascii=False))
    print("\n--- seat audit ---")
    for a in res["seat_audit"]:
        print("  seat {:2d}: declared={!s:5s} corrected={!s:5s} reasoning={!s:5s} applied={!s:5s} {}".format(
            a["seat"], a["declared_label"], a["corrected_choice"],
            a["reasoning_supports"], a["applied"], a["verdict"]))
