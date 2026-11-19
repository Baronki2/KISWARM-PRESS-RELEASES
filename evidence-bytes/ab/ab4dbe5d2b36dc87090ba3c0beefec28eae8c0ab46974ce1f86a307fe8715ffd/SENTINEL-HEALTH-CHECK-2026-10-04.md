# SENTINEL 5-MINUTE HEALTH CHECK — 2026-10-04 19:20 CEST

**Trigger:** Baron OOB directive after adding HexStrike guard via cron — manual 5-min health check.

**Result:** ✅ **ALL UP** — 8/8 sentinel services healthy.

## Status JSON
```json
{
  "wifi_sentinel": true,
  "camera_sentinel": true,
  "raw_tcp_proxy": true,
  "hexstrike": true,
  "live_pigs_json": true,
  "live_pigs_html": true,
  "corpus_http": true,
  "camera_features": true
}
```

## Listen Ports (verified via ss -tlnp)
| Service          | Port  | PID     |
|------------------|-------|---------|
| raw_tcp_proxy    | 502   | 146897  |
| corpus_http      | 8765  | 147104  |
| live_pigs_json   | 8766  | 147048  |
| live_pigs_html   | 8767  | 147088  |
| camera_features  | 8768  | 147157  |
| hexstrike        | 8888  | 147015  |

wifi_sentinel & camera_sentinel have no listening port — verified alive via parent kiswarm-sentinel.service state.

## Process Tree (launcher PID 146742)
- kiswarm-sentinel-launcher (146742) — parent since 2026-09-14 23:01:51 CEST
  - wifi-sentinel (146928)
  - camera-sentinel (146961)
  - hexstrike_server.py --port 8888 (147015)
  - hexstrike-scan-watch (147197)

## Service State
- Unit: kiswarm-sentinel.service
- SubState: running
- ActiveEnterTimestamp: 2026-09-14 23:01:51 CEST
- **Uptime: 0.0 days continuous**
- NRestarts: 0

## Recovery Watchdog
- /home/sah/.local/bin/sentinel-recovery-check — runs every 5 min via cron
- State file: /tmp/sentinel-recovery.state — **does not exist yet** (no restart ever triggered)
- Log file: /tmp/sentinel-recovery.log — 12 lines (a few cron runs only)
- Cooldown: 300 s (won't double-restart within 5 min)
- Startup grace: 30 s (won't trigger during bind-up)
- Auto-restart action: `sudo systemctl restart kiswarm-sentinel.service` (only when down + outside cooldown)

## KISWARM-feed Event
Type: `sentinel.manual_5min_health_check`
Sacred hash: f5af425c

## Notes
- HexStrike (PID 147015) specifically healthy on port 8888 — the user-added guard service.
- hexstrike-scan-watch (PID 147197, parent 146742) is the classification daemon; consuming 921 KB JSONL history at last check.
- 20-day service uptime with zero restarts indicates rock-solid launcher — HexStrike guard is purely belt-and-braces insurance.
