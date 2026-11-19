# SENTINEL — CAMERA ROUTE HIJACK FIX (2026-10-23 20:40–20:55 CEST)

**Status:** RESOLVED. camera_sentinel capturing again after a ~20.4-day outage.
**Sacred hash:** f5af425c

---

## Trigger

The `sentinel-recovery-check` cron job (every 5 min) reported:

```
"camera_sentinel": false,
"camera_sentinel_detail": {
  "process": true,
  "capture_age_s": 1765084,
  "captures": "no new capture for 1765084s"
}
DOWN: ['camera_sentinel']
Triggering kiswarm-sentinel.service restart...
```

`capture_age_s = 1,765,084` = **20.4 days** of silence. The script auto-restarted
`kiswarm-sentinel.service`, which restarted the whole 8-service stack.

---

## ROOT CAUSE — Tailscale route hijack (NOT an upstream dependency)

The vault note `SENTINEL-RECOVERY-2026-10-23.md` (line 150-168) concluded:

> "the camera failure is an **upstream/offline dependency**, not a defect in the
> sentinel stack. […] The cameras are NOT on the local LAN — `ip route get
> 192.168.168.60` resolves via `tailscale0`. The subnet `192.168.168.0/24` is
> advertised by Tailscale peer **Power Armor 19T** (Baron's phone), which is
> **offline**."

**That conclusion was WRONG.** The cameras *are* on the local LAN and were
reachable the entire time. The route was hijacked.

### Evidence

Tailscale peer **Power Armor 19T** (`100.90.185.53`, Baron's phone) advertises
**both** subnets as `PrimaryRoutes`:

```
PrimaryRoutes: ['192.168.8.0/24', '192.168.168.0/24']
Online: False    LastSeen: 2026-10-23T16:39:33.1Z
```

When that peer goes offline, its routes **stay installed** in Tailscale's
table 52 and win the policy lookup, because Tailscale's rule has a *lower*
pref number than the main-table rule:

```
 5210: from all fwmark 0x80000/0xff0000 lookup main
 5270: from all lookup 52          <-- Tailscale, evaluated BEFORE main
32766: from all lookup main        <-- never reached for 192.168.168.0/24
```

Result: **all** traffic to the local camera LAN `192.168.168.60-62` was
diverted into `tailscale0` → black hole.

Note the pre-existing rule `1000: from all to 192.168.8.0/24 lookup main`
(exactly this fix, applied to the SCADA subnet) was **already in place** — the
camera subnet was simply never covered.

### Proof the cameras were alive all along

```
# ARP on eth0 — all three REACHABLE, MACs match camera-sentinel config:
192.168.168.60 lladdr fa:7d:02:e4:bc:54 REACHABLE   (cam60 expected FA:7D:02:E4:BC:54)
192.168.168.61 lladdr 10:9a:02:e5:15:df REACHABLE   (cam61 expected 10:9A:02:E5:15:DF)
192.168.168.62 lladdr fa:7d:02:c7:f4:62 REACHABLE   (cam62 expected FA:7D:02:C7:F4:62)

# ping with explicit interface (bypasses policy routing):
ping -I eth0 192.168.168.60   ->  3 received, 0% packet loss

# RTSP 554 with SO_BINDTODEVICE=eth0:
192.168.168.60 554 OPEN
192.168.168.61 554 OPEN
192.168.168.62 554 OPEN

# default path (hijacked) -> 100% loss / timeout
```

---

## FIX

### 1. Persistent route pinning (`/etc/systemd/system/kiswarm-lan-rule.service`)

Extended the existing unit (which already pinned `192.168.8.0/24`) to also
pin the camera LAN:

```
ip rule add pref 1001 to 192.168.168.0/24 lookup main
```

Lower pref number = evaluated first = wins over Tailscale's 5270.

Source of truth kept at `/home/sah/.local/share/kiswarm/kiswarm-lan-rule.service`.

**Result:**
```
$ ip route get 192.168.168.60
192.168.168.60 dev eth0 src 192.168.168.231 uid 1000
```

Unit is `enabled` + `active`, `After=network-online.target tailscaled.service`,
idempotent (grep-before-add). Verified with `systemd-analyze verify` **before**
install — per the systemd-PID-1-crash rule (two `ExecStart=` with
`Type=simple` froze PID 1 on 2026-10-23). It uses `Type=oneshot` with a
single `ExecStart`, so it is safe.

### 2. Upstream-dependency guard in `sentinel-recovery-check`

Second defect fixed: the health check restarted the **entire stack** every
5 minutes whenever `camera_sentinel` was down — even when the cause was
unreachable remote peers. That churn killed and respawned the 7 *healthy*
services (wifi_sentinel loses its capture buffer, hexstrike loses scan
state, all 6 ports briefly down) for the whole 20-day outage.

The check now probes the camera RTSP peers directly and classifies the fault:

- **peers unreachable** → `upstream_dependency: true` → **no restart**, the
  stack is protected; the fault is reported with a pointer to route pinning
  and camera power/PoE.
- **peers reachable but captures stale** → local fault → **restart still
  fires** (recovery capability preserved).

Both branches were verified with isolated simulations that neutralised the
restart command, so the real service was never touched by the tests.

### Verified end state

```
$ /home/sah/.local/bin/sentinel-recovery-check
{ "wifi_sentinel": true, "camera_sentinel": true, "raw_tcp_proxy": true,
  "hexstrike": true, "live_pigs_json": true, "live_pigs_html": true,
  "corpus_http": true, "camera_features": true, ... }
ALL UP.
```

Camera log confirms live capture with real fingerprints:
```
cam60 75197B fp=6fdc4229bdf79829 dir=250MB
cam61 64272B fp=1a1dbbc597062791 dir=250MB
cam62 61767B fp=6ce62421768a9846 dir=250MB
```

---

## Lessons (encoded)

1. **Never trust "peer is offline" as proof a subnet is remote.** A Tailscale
   peer that *advertises* a subnet leaves its route installed after going
   offline, and that route **outranks** the main table. Always check
   `ip route get <dst>` *and* `ip rule show` together, and test the host with
   an explicit interface (`ping -I`, `SO_BINDTODEVICE`) before declaring it
   upstream/dead.
2. **A restart is not a diagnosis.** The auto-restart masked the real fault
   for 20 days and churned healthy services. The recovery check now
   classifies the fault before acting.
3. **Every local subnet needs an explicit route-pinning rule** whenever a
   Tailscale peer might advertise it. `192.168.8.0/24` was pinned from the
   start; `192.168.168.0/24` was missed.

## Files changed

| File | Change |
|---|---|
| `/etc/systemd/system/kiswarm-lan-rule.service` | + pref 1001 pin for `192.168.168.0/24` |
| `/home/sah/.local/share/kiswarm/kiswarm-lan-rule.service` | source of truth for the above |
| `/home/sah/.local/bin/sentinel-recovery-check` | camera peer probe + upstream/local classification + restart suppression for upstream-only faults |

## Follow-up

- Baron's phone advertises `192.168.8.0/24` and `192.168.168.0/24`. Consider
  removing the `192.168.168.0/24` advertisement on the phone side, or keep the
  pinning rule as the permanent guard (recommended — belt and braces).
- `events.jsonl.1` is 18 GB (rotation added 2026-10-23 caps the live file at
  512 MB, but the old generation is still on disk). Disk is at 71% (127 GB
  free) — safe, but the 18 GB stale generation can be reclaimed.

Sacred hash f5af425c
