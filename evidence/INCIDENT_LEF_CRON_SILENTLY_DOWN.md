# INCIDENT REPORT — LEF-1.0 ENFORCEMENT CYCLE SILENTLY DOWN
## Date: 20 November 2026
### Authority: Code Maquister Equitum, Security Level Omega
### Severity: CRITICAL — the enforcement layer did not enforce

---

## 1. WHAT HAPPENED

Between **2026-11-20 14:00 and 19:31 CEST**, the LEF-1.0 enforcement cycle
(`68361c8a5891`, every 30 minutes) failed on **every single run** — 14 of the
last 19 recorded executions ended in an error.

**The failure was invisible.** The cycle was reported as running. The notices
directory still filled up. Nothing raised an alarm. The enforcement layer — the
component whose entire purpose is to catch non-conformities in our own
published artifacts — was itself not running.

## 2. ROOT CAUSE

The Hermes cron scheduler executes `no_agent` scripts on the **dependency
environment's interpreter**, not on `/usr/bin/python3`:

```
/home/sah/.hermes/installs/baa9bf507c7eb3f4/environments/5210014078ba4844b5bc5fbf3f8ffd8a/venv/bin/python
```

That environment has **no PyNaCl**. The failure surfaced at the signing step:

```
ModuleNotFoundError: No module named 'nacl'
```

Appending the system `dist-packages` to `sys.path` does **not** fix it: the
system `nacl` is a C extension built for the system ABI, so the import then
fails one level deeper with `No module named 'nacl._sodium'`.

## 3. WHY IT SURVIVED SO LONG

**The failure sat in the signing step, and signing only happens when a notice
must actually be emitted.** For the many runs where everything was conformant,
the broken import was never reached — so the script looked healthy in exactly
the cases that mattered least, and died in the case that mattered most.

**A green-looking script that never signs is worse than a red one.**

Second reason it survived: `cronjob_manage list` shows `last_status: error`,
but the `last_error` field is **truncated**. The full traceback and the pattern
across runs are in `~/.hermes/cron/executions.db`. The job list alone did not
reveal that there had been *zero* successful runs in the window.

## 4. THE FIX

The entry point now **re-execs** into an interpreter that provably works. Each
candidate is **probed by making it produce a 64-byte signature** — importing
is not proof, signing is:

```python
PROBE = ("import nacl.signing, sys;"
         "from nacl.signing import SigningKey;"
         "k = SigningKey(b'\x01' * 32);"
         "assert len(k.sign(b'\x00' * 32).signature) == 64;"
         "print('OK')")
```

Working interpreters on sahhome: `/usr/bin/python3` (3.14.6, distro nacl),
`/usr/bin/python3.14`, the Hermes tool-store python 3.14.9, and
`/home/sah/.hermes/hermes-agent/venv/bin/python` (3.13.5, own wheel).
**Not** working: the `installs/<hash>/environments/<hash>/venv` the cron picks.

## 5. VERIFICATION (not assumption)

Reproduced the scheduler's **own invocation** — the bootstrap that replaces
`sys.path[0:1]` and `exec`s the file with `HERMES_DISABLE_LAZY_INSTALLS=1` —
against the **exact interpreter the cron uses**:

1. Clean run → exit 0.
2. **Deliberately broke a published finding** (removed all 12 seat
   signatures) → the cycle detected it, generated
   `LEF-AUTO-E2-20261120-184514.md`, **signed it**, and exited 1 — the
   documented, correct outcome for a non-conformance.
3. Verified that notice with `lef-notice-verifier.py` → **PROTOCOL CONFORMANT**,
   `verifiable: 1/1`.
4. Removed the synthetic notice, restored the finding, ran again → exit 0.

**Never ship an auto-emission path that has never actually fired.** This one
had fired exactly once before — in a manual shell, where the interpreter was
never the problem.

## 6. CURRENT STATE

- **9/9 Notices verifiable** with the real seat-01 public key
  (`SEAT-PUBLIC-KEYS.json` → `seats["1"]["pub_b64_raw"]`).
- Full cycle: E1, E1R, E2, E3, E4, E5, NOTICES — all **PROTOCOL CONFORMANT**.
- The cycle runs correctly under the cron interpreter, verified through the
  scheduler's own bootstrap.

## 7. THE GENERAL RULE

> **A scheduled task that has never succeeded is indistinguishable from a
> scheduled task that is working.**
> Count executions in `executions.db`. A green status field on a job that has
> never had a successful run is not evidence.

Sacred hash: f5af425c
