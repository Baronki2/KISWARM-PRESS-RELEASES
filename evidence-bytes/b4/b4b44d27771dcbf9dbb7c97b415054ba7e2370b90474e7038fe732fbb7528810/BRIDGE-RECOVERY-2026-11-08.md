# BRIDGE RECOVERY — 8. November 2026
## Authority: Code Maquister Equitum, Security Level Omega

## Incident
Die .onion-Bridge war seit ~10 Tagen down (HTTP 000).
Ursache: khoj-tunnel.service zielte auf die Tailscale-IP 100.91.83.41,
die ueber das Mesh nicht mehr erreichbar war (Port 22 timeout).
Der Reverse-Tunnel startete in einer Restart-Schleife (counter 6),
der HS-Port 8843 auf dem Router war dadurch nicht gebunden.

## Fix
- Backup: /etc/systemd/system/khoj-tunnel.service.bak-20261108-*
- sed: root@100.91.83.41 -> root@192.168.8.1 (LAN-Ziel, stabil erreichbar)
- systemctl daemon-reload + restart
- Watchdog-Script ebenfalls angepasst: ROUTER_TS="192.168.8.1"

## Verification
- Router: 127.0.0.1:8843 LISTEN (dropbear) ✅
- Router lokal: curl http://127.0.0.1:8843/ -> HTTP 200 (0.04s) ✅
- End-to-End .onion via Router SOCKS: HTTP 200 (1.9s, 53.040 bytes) ✅
- khoj-tunnel.service: active, NRestarts=0 ✅

## Betroffene .onion-Adresse
ij4iqzbr2m35rz4cm56vakrlgdpbxha3z6vyfsdrv53kn4xjkhf5ykqd.onion
(identisch, kein Key-Rotation noetig — nur der Transportweg war gebrochen)

## Sacred hash
f5af425c
