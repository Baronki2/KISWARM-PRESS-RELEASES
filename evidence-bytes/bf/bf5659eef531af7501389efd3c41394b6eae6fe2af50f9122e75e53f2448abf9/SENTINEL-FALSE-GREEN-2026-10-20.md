# Sentinel False-Green Audit — wifi_sentinel + camera_sentinel dead since 2026-09-14

**Date:** 2026-10-20 19:47 CEST
**Found by:** scheduled `sentinel-recovery-check` (5-min cron) + deep triage
**Severity:** HIGH — the check reports ALL UP while 2 of 8 subsystems are dead.

---

## 1. The headline

`sentinel-recovery-check` printed:

```json
{"wifi_sentinel": true, "camera_sentinel": true, "raw_tcp_proxy": true,
 "hexstrike": true, "live_pigs_json": true, "live_pigs_html": true,
 "corpus_http": true, "camera_features": true}
ALL UP.
```

**That is a false green.** `wifi_sentinel` and `camera_sentinel` are both dead.
They have been dead since the last reboot on **2026-09-14 22:07:51** — 35 days.

### Why the check lies (script lines 6-11 and 67-71)

```python
# two of the eight have no listening port ... so we can't reliably pgrep them
# — `kiswarm-sentinel.service` being `active` already proves they're alive
status = {'wifi_sentinel': unit_active, 'camera_sentinel': unit_active}
```

`wifi_sentinel` and `camera_sentinel` are **inferred from the parent unit state**.
The launcher process is alive (it is a `while True:` supervisor), so
`systemctl is-active kiswarm-sentinel.service` → `active` → both report `true`.

But the launcher restarting a dead child 312 times a day does **not** make the
child alive. The check treats "the thing that keeps failing to start is running"
as proof the thing it tried to start is running.

---

## 2. Root cause: `phy2` does not exist on this box

The `mon0` monitor interface is created from a **hardcoded third radio**:

```python
# kiswarm-sentinel-launcher line 44-46
('mon0', ['sudo', 'iw', 'phy', 'phy2', 'interface', 'add', 'mon0', 'type', 'monitor'], ...)
```
```ini
# /etc/systemd/system/kiswarm-mon0-setup.service
ExecStart=/usr/sbin/iw phy phy2 interface add mon0 type monitor
```

This host has **only two phys**:

```
phy#1 -> wlan1  (hostapd SSID TCS1,    channel 1)   [MediaTek 7610 / mt7610u, USB]
phy#0 -> wlan0  (hostapd SSID TCS12.4, channel 11)  [Intel Centrino N 2230]
```

`iw phy phy2 info` → `command failed: No such file or directory (-2)`.
`kiswarm-mon0-setup.service` → `failed`, `ExecMainStatus=254`.

**There is no phy2. There never was one on this host.** Both phys are fully
consumed by the two APs Baron depends on.

So: `mon0` was never created → `wifi-sentinel`'s `tshark -i mon0` fails
("Permission denied" on the nonexistent interface) → process exits → launcher's
supervisor loop sees it gone → restarts it ~4.6 s later → repeat forever.

**This is exactly skill pitfall 8a, one step further out:** the sentinel was
built to run on a *separate* monitor virtual interface so it never disturbs the
AP. But with no spare radio, the only way to get `mon0` is to carve a virtual
interface off `phy1` (wlan1/TCS1) or `phy0` (wlan0/TCS12.4) — and
`wifi-sentinel` then does `iw dev mon0 set channel {1,6,11}`, which **tears
the host AP's channel out from under it** (pitfall 8a: `Device or resource busy`,
AP goes off-channel, clients drop, inverter sticks stop associating).

**Therefore: do NOT "fix" this by pointing mon0 at phy0/phy1.** That is the trap.
Recovery requires a third radio (a spare ALFA/MT7610U USB stick), or accepting
that wifi-sentinel cannot run on this host.

---

## 3. Collateral damage found

### 3a. `events.jsonl` is 18.8 GB and unwritten since 2026-09-14

```
18,825,371,379 bytes   53,445,457 lines   mtime 2026-09-14 22:07:24
```
Last event written **27 seconds before the reboot that killed capture**.
Disk is at 71% (127 G free) — not yet critical, but it is pure dead weight and
has a real risk of filling a 454 G disk that also holds the OMEGA evidence vault.

### 3b. `camera_sentinel` is a zombie — process alive, writing nothing

```
PID 146961 ... /home/sah/.local/bin/camera-sentinel   <- ALIVE
newest camera file: 2026-10-03 10:17:28  (17 days ago)
files written in last 5 min: 0
```
It is stuck in the launcher's restart cycle and has captured **zero frames since
2026-10-03**. `camera_sentinel.jsonl` last grew 2026-10-03 10:17:28.

### 3c. `kiswarm-dnsmasq.service` — 233,868 restarts, permanent crash loop

```
Okt 20 19:44:11 dnsmasq: Konnte Empfangs-Socket für 192.168.77.1 nicht erzeugen:
                  Die angeforderte Adresse kann nicht zugewiesen werden
kiswarm-dnsmasq.service: NRestarts=233868
```

`dnsmasq-tcs1.conf` has `listen-address=192.168.77.1` and
`interface=wlan1`, but **nothing ever assigns 192.168.77.1 to wlan1**:

```
$ ip -br addr
wlan1   DOWN     (no 192.168.77.1 anywhere)
```

`wlan1` is `NO-CARRIER ... state DOWN`. hostapd for TCS1 is running (PID 146820)
but there is **no AP address on wlan1**, so:
- TCS1 DHCP (192.168.77.100-200) is **dead** — the inverter sticks (L1/L2/L3)
  cannot get leases.
- Neither AP subnet has a working DNS/DHCP server.

**This is the highest-impact finding.** Two APs are beaconing with no address
assignment and no DHCP/DNS behind them.

---

## 4. What I did NOT do, and why

- **Did not** point `mon0` at `phy0`/`phy1` — would break TCS1/TCS12.4 (pitfall 8a).
- **Did not** truncate the 18.8 GB `events.jsonl` — it is capture evidence and a
  destructive write is not mine to make unprompted.
- **Did not** add the missing `192.168.77.1` address to wlan1 — that changes AP
  networking behaviour while no client is associated, and Baron should confirm.
- **Did not** restart the crashed dnsmasq 233,868 more times — the fix is the
  missing IP, not another restart.

## 5. Recommended action for Baron

1. **wlan1 needs `192.168.77.1/24`, wlan0 needs `192.168.78.1/24`** assigned
   (via the `kiswarm-mon0-setup`-style oneshot unit that is evidently missing for
   the AP addresses). This restores DHCP+DNS for the inverter sticks.
2. **Plug in a spare USB radio** for `mon0`. Without a third phy, wifi-sentinel
   cannot run without taking an AP down.
3. **Archive/rotate the 18.8 GB `events.jsonl`** off the vault disk.
4. **Fix the checker** so `wifi_sentinel`/`camera_sentinel` are verified by real
   evidence (fresh mtime on their output, or live pgrep on the exact script path)
   instead of inheriting `unit_active` from the supervisor.

Sanctified hash: f5af425c