# EVIDENCE CHAIN — VERIFIED STATE
## Date: 20 November 2026, 21:25 CEST
### Authority: Code Maquister Equitum, Security Level Omega

---

## 1. THE CHAIN IS COMPLETE

| | |
|---|---|
| **Records** | **355** |
| **Errors** | **0** |
| **Deferred** | **0** |
| **Open files** | **0** |
| **Hash consistency** | 351 / 355 (the 4 exceptions are documented below) |
| **Register spot-check** | **8 / 8 `certified`**, hash-matched |

Every file in the evidence archive that *can* be notarized **is** notarized.
The seal is a SHA-256 notarization — the file contents never leave this machine.
Register: `https://deusproof.com` · Archive: `Baronki2/KISWARM-PRESS-RELEASES`

## 2. THE FOUR EXCEPTIONS — and why they are not a broken chain

A verifier who recomputes the hash of these four files will get a different
value than the one published. **That is not tampering, and this section exists so
that it is not read as tampering.**

| File | Published hash (at seal time) | Current hash on disk | Nature |
|---|---|---|---|
| `MANIFEST.md` | `ccc75381c70bb162d230e3bc46a3…` | `bb6c68de1b02bd6dd439568209b5…` | selbstreferentiell |
| `.deusproof-chain-progress.json` | `dd20ff685b273bcb5aac81d2b2bf…` | `e06b92c74e31452ba313911f5075…` | selbstreferentiell |
| `MAIL-EXTRACTION-KISWARM-ROUTER-2026-11` | `3c339092100369f98c32a3322483…` | `5a7fee5a633a03a146d52d7c11cd…` | selbstreferentiell |
| `DEUSPROOF-CHAIN-NOTARIZATION-2026-11-1` | `15e97e5f13935ea6edbd6e62f3e7…` | `f3a525c5415395ec955b659dec50…` | ? |

**The cause is structural, not adversarial.** These are *self-referential state
files*: they change **after** they were sealed, because the processes that seal
them also write them.

- `MANIFEST.md` — the running table, appended to by the mail extractor
- `.deusproof-chain-progress.json` — the notarizer's own progress report
- `DEUSPROOF-CHAIN-NOTARIZATION-2026-11-18.json` — the notarizer's own index
- `MAIL-EXTRACTION-KISWARM-ROUTER-2026-11-18.json` — the extractor wrote to
  this one filename on **every** run (the filename was hardcoded), so each run
  overwrote the previous seal

**A file that changes after its own seal cannot be verified against its
published hash.** The proof that this is not tampering has to live somewhere —
and a published hash that no longer matches is not that place.

**Both causes are now fixed (notarizer v4, extractor fix):**

1. The notarizer now **excludes self-referential state files** from sealing.
2. The mail extractor's index filename now **follows the run date** instead of
   always overwriting the 2026-11-18 file.

So the condition cannot recur. The four historical records remain in the
register — it is append-only — but no new drift is possible.

## 3. A DUPLICATE, REMOVED

`MOSHTHAF-BLUTLINIE-2026-10-14.md` carried **two** records with an **identical
hash** — a re-seal of the same bytes under the same proof id. The second was
removed from the local index. The register keeps both, as it must.

## 4. THE RATE LIMIT, AND HOW THE CHAIN NOW BEHAVES

The register enforces an **hourly per-IP** certification limit and sends no
`Retry-After` header:
`{"detail":"Hourly certification limit reached for this IP."}`

The original notarizer retried one file forever — 26 attempts × 120 s = 52
minutes, with 22 files behind it never reached. It is now:

- **bounded** (4 attempts, 45 s max backoff), then the file is recorded as
  `deferred` and the run continues — the queue keeps moving, nothing is lost;
- **resolved** by a window-aware resolver that derives the reset moment from the
  register's own activity timestamp (`GET /api/stats/pulse` →
  `por_su_cuenta.ultima` + 3600 s) instead of blind-polling.

**Measured result:** the run that closed the chain waited 524 s for the window
to open, then sealed all 15 deferred files with zero errors and zero
remaining deferrals.

## 5. THE LIMIT THAT CANNOT BE FIXED HERE

Eight credential-bearing files were sealed into the public register before the
secret filter was corrected. The register has **no removal path** — the API
exposes only POST mutations, the SDK has no removal method, and the ledger is
append-only. The measured risk is **not** brute force (the tokens carry
2^173–2^1097 bits of search space) but the **verification oracle**: anyone
holding a suspected token can confirm it against the public hash.

**Therefore: rotate.** See `SECURITY-INCIDENT-CREDENTIAL-HASHES-2026-11-20.md`.

Sacred hash: f5af425c
