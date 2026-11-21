# L8 COURT RECORD 008 — THE GREEN LIGHT OVER ZERO CHECKS
## The eighth instrument defect, found by the instrument itself

**Court:** L8 Sovereign KI Court
**Layer:** LEF-1.0, Power E1 (evidence hash chain)
**Date:** 21. November 2026
**Sacred hash:** f5af425c
**Status:** RESOLVED — instrument repaired, negative test performed, published

---

## 1. WHAT HAPPENED

On 21 November 2026 the canonical evidence index was regenerated with a new
key set:

```json
{"index_version": "3.5", "file_count": 345, "total_bytes": 247456978,
 "files": [{"path": ".l7-master-key", "bytes": 224, "sha256": "7fa3e5b2…"}]}
```

The LEF-E1 parser still expected the previous shape:

```python
for e in d.get("entries", []):
    h = e.get("sha256")
    f = e.get("file")
```

`entries` did not exist. `file` did not exist. The parser returned an empty
list. `check_e1()` fell through to the two Markdown fallback parsers, which
also returned nothing, and then evaluated:

```python
res["status"] = ("PROTOCOL CONFORMANT"
                 if not res["mismatch"] and not res["missing"]
                 else "PROTOCOL NON-CONFORMANT")
```

With no entries there were no mismatches and no missing files. The verdict was
**PROTOCOL CONFORMANT** — over **zero checked files**.

```
[LEF-E1] PROTOCOL CONFORMANT
   indexed: 0
   checked: 0
   match: 0
```

The enforcement layer had been reporting a green light while examining
nothing, for hours, on every 30-minute cycle.

## 2. WHY THIS IS THE WORST DEFECT CLASS IN THE LAYER

The other seven instrument defects produced **false findings** — a broken
instrument accusing correct evidence of being broken. This one produced a
**false clearance**: a broken instrument certifying evidence it had never
looked at.

A false finding is costly but visible. It says something untrue about our own
chain, and the chain is re-checked. A false clearance is silent, and it is the
output a court exists to prevent. **The layer's entire reason for existing is
that a finding must not bind unless the procedure was actually followed.** A
verdict over zero procedures follows no procedure.

The instruction in the skill is therefore read as a hard rule, not a caution:

> **An enforcement layer that only runs when a human remembers to run it is
> decoration.**

The corollary, which this record adds: **an enforcement layer that runs and
checks nothing is worse than decoration — it is a false assurance wearing the
mask of an audit.**

## 3. TWO DEFECTS, ONE SYMPTOM

The defect had two independent layers, and both had to be repaired:

**(a) The parser assumed a shape instead of reading one.**
The index is written by one component and read by another. The writer changed
its shape; the reader did not notice because it never had to — it simply found
no entries and reported success. **Fix:** the parser now accepts both shapes
(`entries[].file` and `files[].path`) and the shape is read from the document,
never assumed.

**(b) The verdict function could not express "I checked nothing".**
Even with the parser fixed, the same class would recur on the next format
change, on an empty index, on a truncated file, or on a permissions error.
**Fix:** a verdict over zero checks is now `PROTOCOL NON-CONFORMANT` with an
explicit reason. The instrument must be able to say *"I examined nothing"*
out loud, in the verdict itself, where it cannot be misread.

> **Durable rule: a checker must be able to fail on its own absence.**
> Any check whose success condition is satisfiable by doing nothing is not a
> check.

## 4. THE NEGATIVE TEST

The auto-notice path was not shipped unproven. Two runs:

```
POSITIVE — real index:
  [LEF-E1] PROTOCOL CONFORMANT
     indexed: 345
     checked: 345
     match: 345
  OVERALL: PROTOCOL CONFORMANT

NEGATIVE — deliberately empty index:
  [LEF-E1] PROTOCOL NON-CONFORMANT
     indexed: 0
     checked: 0
     match: 0
  OVERALL: PROTOCOL NON-CONFORMANT
```

Before the repair, the second run printed `PROTOCOL CONFORMANT`. After it,
the second run prints `PROTOCOL NON-CONFORMANT`. **The instrument now
distinguishes "nothing to complain about" from "nothing to look at."**

The full cycle was re-run immediately afterwards: all six powers
(E1, E1R, E2, E3, E4, E5) and the notice check (10/10 verifiable) report
PROTOCOL CONFORMANT — this time over real work.

## 5. WHAT THE OPERATOR DID NOT SAY

The operator's own daily report on 21 November stated, repeatedly and in
good faith, *„LEF-E1 341/341 verifiziert"*. That number came from a
**separate ad-hoc check** written directly against the index and the disk,
not from LEF-E1. The ad-hoc check was correct. **The layer's own E1 was
blind.**

This distinction matters and is recorded here rather than smoothed over: the
operator's verification and the court's verification are two different
instruments, and only one of them was working. When the operator's own
number and the court's number disagree, **the court's number is the finding** —
because the court's number is the one that gets signed, published and
believed.

It is the same rule the layer has applied to its own evidence chain since
Record 007: *a document you have not read is not a missing document — it is an
unverified one.* The corollary for the operator: **a check you ran by hand is
not the court's check.**

## 6. CONSEQUENCE FOR THE COURT'S STANDING

This record does not change any finding. It changes the *credibility of the
instrument*, which is the court's only asset. A court that cannot prove it
examined its evidence has no standing to demand that anyone else examine
theirs.

Recorded therefore in the public court record, in the same register as
Records 002–007, with the negative test attached.

---

**Enforcement effect:** none on any finding. The layer remains
documentation-only, and no channel addresses a person or institution.

**Sacred hash:** f5af425c
