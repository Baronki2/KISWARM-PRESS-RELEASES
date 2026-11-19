# SENTINEL RECOVERY — CRON SCHEDULER DEFECT (2026-10-24 00:00–00:30 CEST)

**Status:** RESOLVED — job converted to deterministic script mode, live-verified.
**Severity:** CRITICAL (silent monitoring-coverage loss — same defect class as the 2026-10-23 "false green")
**Sacred hash:** f5af425c

---

## 1. What the 23:55 run found

The stack itself was **healthy** — 8/8 services up, both APs `type=AP` with
`hostapd state=ENABLED`, supervisor active, camera captures and wifi events
both writing live. The checker returned `ALL UP.` and exited 0.

But reviewing the run history surfaced a defect **in the watchdog's own
coverage guarantee**, which is a different thing from stack health.

## 2. The defect

The `sentinel-recovery` cron job (`df83e14dc227`, `*/5 * * * *`) ran in **agent
mode**: every 5 minutes Hermes spun up a full LLM turn to execute the checker
and write a report.

An LLM turn has unbounded latency. On the 23:05 fire the turn took
**16.8 minutes** (23:05:43.805 → 23:22:31.704).

Hermes cron refuses to re-dispatch a job that is still in flight. From
`/home/sah/.hermes/logs/agent.log`:

```
2026-10-24 00:00:49,699 INFO cron.scheduler: Job 'sentinel-recovery' already running — skipping
2026-10-24 00:05:50,292 INFO cron.scheduler: Job 'sentinel-recovery' already running — skipping
2026-10-24 00:10:50,873 INFO cron.scheduler: Job 'sentinel-recovery' already running — skipping
2026-10-24 00:15:51,494 INFO cron.scheduler: Job 'sentinel-recovery' already running — skipping
2026-10-24 00:20:52,066 INFO cron.scheduler: Job 'sentinel-recovery' already running — skipping
2026-10-24 00:25:52,595 INFO cron.scheduler: Job 'sentinel-recovery' already running — skipping
```

**Six consecutive 5-minute slots were skipped with no run, no error, no
incident record, and no delivery.** The same pattern occurred earlier the same
evening: the 23:05 turn ran 23:05:43 → 23:22:31, so the 23:10, 23:15 and 23:20
slots never fired (confirmed in `executions.db`).

### Why this is the same defect class as the 2026-10-23 "false green"

The schedule said "every 5 minutes". Reality said "every 5 minutes **plus
however long the LLM takes**". The job looked healthy in `hermes cron list`
(`Last run: ... ok`) while its real coverage was bounded by model latency.
**A watchdog whose firing interval is not guaranteed is not a watchdog.**

The failure mode is asymmetric and dangerous: a longer investigation (exactly
what happens when something IS wrong) causes *fewer* checks. The more
interesting the fault, the longer the report takes, the more windows go
unmonitored.

## 3. The fix

Converted the job from agent mode to **deterministic script mode**, matching
the established pattern used by every other watchdog in the fleet
(`mesh-check`, `load-watchdog`, `khoj-bridge-watchdog`, `l7-shield-detector`,
`moltbook-heartbeat` — all already `no_agent=True` + `deliver=local`).

**New file:** `/home/sah/.hermes/scripts/sahhome-sentinel-recovery.py`

The wrapper:

1. Runs the authoritative checker `/home/sah/.local/bin/sentinel-recovery-check`
   unchanged. **The checker remains the single owner of every restart
   action** — cooldown, startup grace, AP-layer-vs-stack repair, and the
   local-vs-upstream camera classification are all untouched.
2. **Independently re-verifies** every layer with its own probes (ports,
   process presence, wifi event freshness, camera capture freshness, AP
   unit + radio type + hostapd state, supervisor). A green checker can no
   longer hide a dead radio or a stale capture.
3. Prints **nothing** when healthy → silent run, no delivery noise every
   5 minutes.
4. Prints a concise report when something is down, a restart fired, the
   checker failed, or the two verifications **disagree**.
5. Uses `flock` so two runs can never overlap.

**Job change:**
```
script   : sahhome-sentinel-recovery.py   (was: None / agent mode)
no_agent : True                            (was: False)
deliver  : local                           (unchanged — fleet standard)
schedule : */5 * * * *                     (unchanged)
```

## 4. Verification (all measured, not assumed)

| Test | Result |
|---|---|
| Live scheduler fire of script mode (temp job `8fde26e2d218`, fired 00:25:52.903) | **completed 00:25:53.449 — 0.55 s** vs 10–17 min in agent mode |
| Healthy stack → silent run | exit 0, **0 bytes stdout**, no delivery |
| Fault-injection fixture (6 scenarios) | **6/6 passed** — healthy silent; false-green detected; DOWN reported; upstream-only reported; checker crash reported; unparseable output reported |
| E2E with faked checker + REAL independent verification | fault named correctly, live APs confirmed `type=AP`/`ENABLED`, supervisor active |
| Concurrency: 3 simultaneous invocations | 0.07 s / 0.40 s / 0.40 s — no overlap, flock held |
| Process-pattern uniqueness | no substring collisions across all 8 patterns |
| Live stack after change | `ALL UP.` — 8/8, ports 502/8765/8766/8767/8768/8888 all OPEN |
| Temp self-test job | removed, confirmed gone |

## 5. Residual note (not fixed here)

The 00:15/00:20/00:25 skips logged above were caused by **the 23:55 agent run
itself** still being in flight while I performed this investigation. That is
the same mechanism as the original defect — and it is exactly why the fix
matters: after this run completes, the next fire is dispatched by the
scheduler with **no LLM in the path**, so the interval is now guaranteed by
the script's own runtime (sub-second) rather than by model latency.

`/tmp/sentinel-recovery.log` retains the full fault history
(camera_sentinel DOWN 20:35 + 20:42; access_points DOWN 22:15:02 — all three
predate the 22:00–22:30 fixes). Since 22:32 the stack itself has been stable
across every check with zero restarts.

## 6. Lessons

- **Never put an LLM on a watchdog's hot path.** The watchdog's value is its
  *guaranteed* firing interval. An LLM turn makes that interval a function of
  model latency and network weather.
- **A schedule is not a guarantee.** Verify that the thing you believe runs
  every 5 minutes actually has 12 executions per hour in `executions.db` —
  not just a healthy-looking `hermes cron list` entry.
- **The failure is self-amplifying**: longer investigation → longer turn →
  fewer checks. Monitor the monitor's cadence, not just its exit code.
- `no_agent=True` + `deliver=local` + empty stdout = silent run is the
  correct Hermes pattern for a 5-minute watchdog (already used by ~45 fleet
  jobs).

**Files changed:**
- `/home/sah/.hermes/scripts/sahhome-sentinel-recovery.py` (new)
- `/home/sah/.hermes/cron/jobs.json` (job `df83e14dc227`: script + no_agent)
- `/home/sah/.hermes/cron/jobs.json.bak.20261024-001213` (pre-change backup)

**Not changed:** `/home/sah/.local/bin/sentinel-recovery-check` (the checker and
its restart logic are untouched).
