# SENTINEL FALSE-GREEN #2 — AP + CHANNEL-TRUTH AUDIT (2026-10-23)

**Trigger:** `sentinel-recovery-check` cron reported "ALL UP" for 8 services.
A deep audit found the monitor was reporting green while **three real defects**
were live underneath, plus the access points it did not monitor at all were
**dead**.

Sacred hash: f5af425c

---

## 1. OBSERVED SYMPTOM

`/tmp/sentinel-recovery.log` timeline (2026-10-23):

```
20:35:33  DOWN: ['camera_sentinel']   -> Restart issued.
20:36:30  DOWN: ['camera_sentinel']   -> Within 300s restart cooldown; skipping.
20:42:02  DOWN: ['camera_sentinel']   -> Restart issued.
20:42:14  DOWN: [7 of 8 services]     -> Within 30s startup grace window.
20:43:32  ALL UP.
... 20:43 / 20:46 / 20:50 / 20:55 / 21:00 / 21:05  ALL UP.
```

Each "restart" of `kiswarm-sentinel.service` also tears down and respawns the
**hostapd** processes, because the launcher used to own them. That is what
killed the tcs12 access point.

---

## 2. DEFECT A — wifi-sentinel wrote FALSE CHANNEL LABELS (261k records)

### Root cause
`wifi-sentinel` runs under `kiswarm-sentinel.service`, whose unit exports:

```
Environment="PATH=/usr/local/bin:/usr/bin:/bin:/home/sah/.local/bin"
```

`iw` lives in `/usr/sbin/iw` — **not on that PATH**. `actual_channel()` called:

```python
subprocess.run(['iw', 'dev', dev, 'info'], ...)   # FileNotFoundError
except Exception: pass                             # swallowed
return None
```

With `None`, the code fell back to the **REQUESTED** channel:

```python
parsed['channel'] = real_ch if real_ch is not None else channel   # <- fake
```

So every frame was tagged with the channel the sentinel *asked for*, not the
channel the radio was *on*.

### Proof it was wrong
The radio is physically pinned to channel 1 (both phys carry a hostapd AP).
`iw dev mon0 set channel 6` returns rc=0 but **silently does nothing** —
`iw dev mon0 info` reports no channel of its own. Evidence that the three
"channels" were one and the same traffic:

```
ch=1 : 26 distinct src_macs
ch=6 : 24 distinct src_macs
ch=11: 25 distinct src_macs
overlap ch1 & ch11: 20 / 25 of ch11 (80%)
```

The same TCS1 ch1 beacons appear in all three buckets at a constant ~16 %
ratio — i.e. the identical capture, relabelled three ways.

### Impact
- 261 572 records carry a `channel` field; **233 186 of them are mislabelled**
  (only the 28 386 records written between 18:13 and 18:25 UTC — while the
  wlan1 AP happened to be up — were truthful).
- Any neighbourhood analysis by channel was garbage. `channel` was fiction.

### Fix
`/home/sah/.local/bin/wifi-sentinel`
- Use the absolute path `/usr/sbin/iw` in both `actual_channel()` and the
  channel-set call.
- Do not swallow the exception silently — log it.
- Verified after fix:
  ```
  (requested, actual) pairs: {(1, 1): 138, (6, 1): 262}
  [..] NOTE: requested ch6, radio pinned to ch1 (shared phy with hostapd AP)
       - recording actual channel
  ```

### HARDWARE LIMIT (unchanged, worth restating)
Both radios carry a hostapd AP, so mon0 shares a phy with an AP and **cannot
hop**. Real multi-channel sentinel needs a **third radio** (ALFA AWUS036ACHM
would enumerate as phy2 — exactly what the original code expected).

---

## 3. DEFECT B — AP keepalive could KILL but never RESTORE an access point

### Root cause
`kiswarm-ap-keepalive.sh` runs as **root** (via sudo) and logged to:

```
LOG=/tmp/kiswarm-ap-keepalive.log
```

That file was owned by **`sah:sah` mode 644** in the **sticky** `/tmp`.
With `fs.protected_regular=2`, the kernel refuses a root write to a file in
a world-writable sticky directory that root does not own:

```
$ sudo -n sh -c 'echo x >> /tmp/kiswarm-ap-keepalive.log'
sh: cannot create /tmp/kiswarm-ap-keepalive.log: Permission denied
```

Two consequences, both silent:

1. `log()` lost **every** diagnostic. The file contained nothing but 93 lines
   of `Keine Berechtigung` noise. There was no record of what the daemon did.
2. `hostapd "$conf" -B >>"$LOG" 2>&1` **failed at the redirect**, before bash
   could exec hostapd — so **the restart command never ran**. The keepalive
   had already executed `pkill -f "hostapd $conf"` on the preceding line.

   **The daemon killed the access point and then failed to bring it back.**

### Fix
- Log moved to `/var/log/kiswarm/ap-keepalive.log` (root-writable dir).
- **One owner per service:** the keepalive no longer starts/kills hostapd
  itself. It calls `systemctl restart <ap unit>`. hostapd is owned by
  systemd only. (Two owners → two hostapd instances fight over one radio:
  `nl80211: Match already configured / Could not configure driver mode`.)
- `/var/log/kiswarm` is owned by `sah` so the **launcher** (running as `sah`)
  can also open `ap-keepalive.stdout.log` there. Root can write into a
  `sah`-owned dir regardless; the reverse is not true.

---

## 4. DEFECT C — the launcher killed the WRONG hostapd and never respawned dead services

### Root cause 1 — substring cross-match
`stop()` ran `pkill -f <name>`. `'hostapd-tcs1'` is a **substring** of the
tcs12 command line:

```
'/usr/sbin/hostapd /home/sah/.local/share/hostapd-tcs12.conf -B'
              ^^^^^^^^^^^ 'hostapd-tcs1' is inside it
```

So stopping the tcs1 AP **also killed the tcs12 AP**. The same pattern
matched the launcher's own shell (reproduced live — it killed my own terminal
session during testing).

### Root cause 2 — colliding liveness patterns
The supervisor derived its pgrep pattern from the command line:

```python
binary_pattern = next((c for c in cmd if c.endswith('.py') or '/' in c ...), name)
```

For every python service this collapsed to the **same** string:

```
/home/sah/.hermes/hermes-agent/venv/bin/python
```

`pgrep -f` then matched **any** of the 12 python services. A dead service was
never detected and therefore **never respawned**. This is why camera-sentinel
could die and stay dead.

### Fix
`/home/sah/.local/bin/kiswarm-sentinel-launcher`
- Every SERVICES entry now carries an explicit, unique `match` string.
  Verified programmatically: **0 duplicates, 0 substring collisions.**
- `stop()` / liveness use `pkill -f -- <match>` / `pgrep -f -- <match>`.
- hostapd entries **removed** from the launcher entirely (systemd owns them).
- Verified live: killed camera-sentinel with SIGKILL → supervisor logged
  `[camera-sentinel] not running, restarting` and respawned it within ~35 s.

---

## 5. DEFECT D — the AP units were a FALSE GREEN

`kiswarm-ap-tcs{1,12}-persistent.service` used:

```
Type=forking
ExecStart=/usr/sbin/hostapd ... -B
RemainAfterExit=yes
```

hostapd daemonises, so the unit's main process **exited immediately**. systemd
reported **`active (exited)` forever** — green — while the hostapd process
was dead and the radio had fallen back to `type managed`. The unit could not
restart anything because systemd had nothing left to supervise.

This is the same class of bug as the `wifi_sentinel`/`camera_sentinel` "false
green" already recorded in `SENTINEL-FALSE-GREEN-2026-10-20.md`.

### Fix — foreground hostapd under real supervision
```ini
[Service]
Type=simple
User=root
ExecStart=/usr/sbin/hostapd -P /run/hostapd-tcs12.pid /home/sah/.local/share/hostapd-tcs12.conf
Restart=always
RestartSec=5
```
- No `-B` → hostapd stays in the foreground, systemd owns the process.
- `-P <pidfile>` → hostapd v2.10 CLI flag (**not** a config-file option —
  `pid_file=` in the conf is rejected: *"unknown configuration item
  'pid_file'"*).
- `Restart=always` → systemd restarts it if hostapd dies.

Installed units verified with `systemd-analyze verify` **before** install
(per the systemd-PID1-crash rule: never two `ExecStart=` with `Type!=oneshot`).

**Trap hit during the fix:** after `daemon-reload`, `systemctl start` on the
tcs12 unit was a **no-op** because the unit was still `active` from the old
forking config. A `systemctl restart` was required to pick up the new
`ExecStart`. Both units now report `ActiveState=active SubState=running`
with a real `MainPID`.

---

## 6. DEFECT E — the monitor was blind to the access points

`sentinel-recovery-check` watched **only** the 8 capture/endpoint services.
Both access points could be fully dead while it reported "ALL UP" — which is
exactly the state the tcs12 AP was in for over an hour.

### Fix — monitor the AP layer too
Added to `/home/sah/.local/bin/sentinel-recovery-check`:
- `access_points` — a healthy AP needs **three** things:
  1. systemd unit `active` **and** `SubState=running` (not `exited`)
  2. radio `type AP` (NM reclaiming it as `managed` kills the beacons)
  3. `hostapd_cli ... status` → `state=ENABLED`
- `ap_keepalive` — the watchdog daemon must be alive.
- New restart branch: an AP fault restarts **only that AP unit**, never the
  whole sentinel stack (which would churn 8 healthy capture services to fix
  a radio).

Verified live: `systemctl stop kiswarm-ap-tcs12-persistent.service` →
recovery check reported `DOWN: ['access_points']` →
`Restarting access point wlan0 via kiswarm-ap-tcs12-persistent.service` →
wlan0 back to `type AP` channel 11 within ~20 s, L3 stick re-associated.

---

## 7. DEFECT F — the keepalive restarted a HEALTHY access point every ~5 min

Found while verifying the fixes above: the keepalive log showed a restart
every ~5 minutes:

```
22:13:36  wlan0: tx_packets stalled (3169 -> 3169) -> restarting ...tcs12...
22:18:19  wlan0: tx_packets stalled (3342 -> 3342) -> restarting ...tcs12...
22:20:43  wlan0: tx_packets stalled (3432 -> 3432) -> restarting ...tcs12...
```

### Root cause
The beacon-liveness check used a **12-second** window on `tx_packets` only.
`wlan0` (SSID TCS12.4) carries **only the L3 inverter stick**, so its tx
counters advance in **bursts** — a 12 s window can legitimately show a zero
delta while the AP is perfectly healthy and beaconing:

```
wlan0 tx_packets 3432 -> 3432   (delta 0)   <- AP alive, just idle
wlan0 tx_packets 3432 -> 3438   (delta 6)   <- burst
wlan1 tx_packets 22214 -> 22227 (delta 13)  <- busy AP, never flat
```

So the keepalive "repaired" a non-fault **every cycle**, and each restart
**dropped the L3 stick's association** — the watchdog was the outage.

### Fix
- Window lengthened 12 s → 45 s.
- Liveness now accepts **either** `tx_packets` **or** `tx_bytes` advancing.
- If the counters are flat **but the AP has an associated client**, the AP is
  demonstrably serving → **never restart on counter evidence alone**.

Verified after the fix: 3+ keepalive cycles with **no** restart entries,
`NRestarts=0` on the tcs12 unit, and the L3 stick remained associated and
pingable throughout.

---

## 8. FINAL STATE (verified)

```
ALL UP.   (10 status entries: 8 services + access_points + ap_keepalive)

wlan1  ssid TCS1    type AP  channel 1
wlan0  ssid TCS12.4 type AP  channel 11
L3 stick 48:55:19:7a:13:87 associated on wlan0, 192.168.78.111 pingable
TCS1 clients: c8:c9:a3:93:84:84, 48:55:19:7a:1d:4a
camera captures flowing on cam60/cam61/cam62
wifi-sentinel channel labels truthful (requested 6 -> recorded 1)
```

## 9. FILES CHANGED

| File | Change |
|---|---|
| `~/.local/bin/wifi-sentinel` | absolute `/usr/sbin/iw`, log exceptions |
| `~/.local/bin/kiswarm-ap-keepalive.sh` | log → `/var/log/kiswarm`, one-owner rule, `systemctl restart`, 45 s window + client check |
| `~/.local/bin/kiswarm-sentinel-launcher` | unique match patterns, hostapd removed, `pkill -f --` |
| `~/.local/bin/sentinel-recovery-check` | AP + keepalive monitoring and targeted restart |
| `/etc/systemd/system/kiswarm-ap-tcs1-persistent.service` | `Type=simple`, foreground hostapd, `Restart=always` |
| `/etc/systemd/system/kiswarm-ap-tcs12-persistent.service` | same |

Backups: `/home/sah/.config/sah-vault/backups/2026-10-23-sentinel-fix/`

## 10. CROSS-REFERENCE

- `SENTINEL-FALSE-GREEN-2026-10-20.md` — first false-green class (inferred
  vs measured checks). This is the second class: **measured, but blind to
  the AP layer**, plus the supervision/ownership defects above.
- `SENTINEL-CAMERA-ROUTE-FIX-2026-10-23.md` — the Tailscale route-hijack
  that black-holed the camera LAN. Route pinning verified still correct:
  `pref 1001 to 192.168.168.0/24 lookup main`.
