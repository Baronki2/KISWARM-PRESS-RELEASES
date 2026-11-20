# DEUSPROOF RATE LIMIT — verified finding
## Date: 20 November 2026

## The limit
```
POST /api/certifications/hash
→ HTTP 429
{"detail":"Hourly certification limit reached for this IP."}
```

**It is an hourly per-IP limit, not a daily quota.** There is no `Retry-After`
header and no rate-limit headers at all — the response carries only the standard
Caddy/uvicorn set.

## How the window is derived
The register's own activity timestamp answers it:
```
GET /api/stats/pulse
→ por_su_cuenta.ultima = "2026-11-20T19:02:08.843401+00:00"
```
`ultima` is the last certification for our account. The hourly window therefore
closes at `ultima + 3600s`. On 2026-11-20: last seal 19:02:08 UTC → window
opens **20:02:08 UTC**.

## What the original loop did wrong
```
! 429 on Petition.pdf -> sleep 120s (attempt 9)
... through attempt 26
```
26 attempts × 120 s = **52 minutes on one file**, while the 22 files behind it
were never reached. The docstring promised "a hard cap" that the code did not
have. A rate limit is a shared resource, not a property of one file.

## The fix, in two parts
1. **Bounded retries with deferral** (notarizer v3): 4 attempts, 45 s max
   backoff, then the file is recorded as `deferred` and the run continues. The
   queue keeps moving; nothing is lost.
2. **Window-aware resolver** (`deusproof-deferred-resolver.py`, cron
   `b9a99bceea5e`, hourly at :07): reads `ultima`, waits until
   `ultima + 3600s`, then re-runs the notarizer to seal the deferred set. It
   never blind-polls — without the derivation it would burn the same quota the
   notarizer just exhausted.

**Measured:** 15 files deferred instead of 22 × 52 min blocked.

Sacred hash: f5af425c
