# Bootcamp Router R-0001 — Reference Design (gl-be6500-1)
# Captured 2026-09-13 during forensic investigation

# === Identity ===
Tailscale IP:      100.96.141.9
Hostname:          GL-BE6500
Tailscale name:    gl-be6500-1
Firmware:          OpenWrt 23.05-SNAPSHOT (ipq53xx/generic, aarch64_cortex-a53_neon-vfpv4)
Kernel:            5.4.213
First boot:        2026-08-10 18:53 (uptime 34 days as of capture)
Site ID:           P01000 (bootcamp/development/Eigenbetrieb)
Fleet role:        lighthouse + proxy + web (reference site, tier: primary)
Fleet registered:  2026-08-13T12:04:00Z

# === Network ===
LAN IP:            192.168.10.1/24 (customized, NOT factory 192.168.8.1)
WAN IP:            192.168.4.2/24 (static, gateway 192.168.4.1)
Hardware MAC:      94:83:c4:b9:c5:b9 (eth0/WAN), :bb (eth1.1/LAN)

# === Open ports (Tailscale-routable only) ===
22    SSH (dropbear 2022.82-6, PasswordAuth=on, RootPasswordAuth=on)
53    DNS (dnsmasq on br-lan / WAN / tailscale0)
80    nginx (vendor SPA)
443   nginx (vendor HTTPS)
2222  (not seen)
502   (not running — picea proxy on 8890 instead)
8080  LuCI (HTTP) — standard OpenWrt admin
8443  LuCI (HTTPS) — standard OpenWrt admin
8890  picea-proxy (JWT-auth'd Picea-Cloud API mirror, public metainfo unauth'd)
8891  picea-web (dashboard SPA, JWT-gated /api/v1, GET /health is public)
8892  picea-mcp (JWT-gated, requires /etc/picea_mcp_token)
8893  picea-lighthouse (HMAC + cmd key auth from /etc/picea_lighthouse_*.key)
8894  (not seen)
9090  (not seen)

# === SSH access (root) ===
# Paste via `nano` + chmod 600 by Baron. Do not echo in chat.
# Single SSH key in /etc/dropbear/authorized_keys (placed Aug 10 by Baron):
#   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINMrBRLaEparggLfuw5jfdLny2K08MspjJ228manD31l opencode-router-admin
#   fingerprint: SHA256:1hyGy9nS6dIp5jZC57ySHcoc0WUKurrYg9yWIbBREyU
# See /home/sah/.config/sah-vault/SSH-AUTHORIZED-KEYS-FLEET.md for full key inventory

# === Tailscale ===
Tailnet:           kiswarmkirouter@gmail.com
Advertised routes: 192.168.10.0/24 (LAN), 192.168.4.0/24 (WAN — be careful)
Node key:          (Tailscale-managed, in /etc/tailscale/)

# === Paired devices on P01000 ===
# Returns from /picea/v1/paired_devices?site_id=P01000
# (Public endpoint, no auth required for read)
1   jfcktkycvg    paired 2026-01-12 13:24:06 UTC
2   fghkkl        paired 2026-01-12 20:14:35 UTC
3   KIAPI         paired 2026-07-21 09:20:33 UTC
4   Johannes      paired 2026-09-09 21:19:48 UTC  (THE SPY, per Baron)

# === picea config keys ===
# Returns from /picea/v1/config?site_id=P01000 (public read)
# Distinguishing bootcamp from production Nordhorn:
#   bootcamp (P01000):  hydrogen_reserve=0.0,  ventilation_target=16.0, has_solar_ac=False, has_immersion_heater=True
#   nordhorn (P00058):  hydrogen_reserve=10.0, ventilation_target=21.0, has_solar_ac=True,  has_immersion_heater=False

# === Internal /etc/ files ===
/etc/picea_proxy.json          (1533 bytes, modified Aug 11 22:16, mode 0600)
/etc/picea_mcp_token           (33 bytes, Aug 10 16:00, mode 0600)
/etc/picea_lighthouse_cmd.key  (48 bytes, Aug 12 13:36, mode 0600)
/etc/picea_lighthouse_hmac.key (48 bytes, Aug 12 13:36, mode 0600)
/etc/picea_proxy.key           (not present — newer security practice)

# === /root/picea/ tree ===
/root/picea/picea_proxy_v2.py         (30733 bytes, Aug 11 16:30, mode 0755)
/root/picea/picea_web.py              (30898 bytes, Aug 13 12:04, mode 0755)
/root/picea/picea_lighthouse.py       (36341 bytes, Aug 13 12:04, mode 0755)
/root/picea/picea_mcp_server.py       (3996 bytes, Aug 10 16:02, mode 0644)
/root/picea/backup_install.sh         (3173 bytes, Aug 12 13:37, mode 0755)
/root/picea/watchdog.sh               (500 bytes, Aug 10 15:39, mode 0755)
/root/picea/KI_COMM_BRIDGE.md         (2037 bytes, Aug 11 21:55, mode 0600)
/root/picea/fleet_registry.json       (1224 bytes, Aug 13 12:04, mode 0644)
/root/picea/lighthouse_audit.log      (1837 bytes, Aug 13 11:56, mode 0644, 12 entries, last entry: PC-LAGER backup trigger)
/root/picea/support_requests/         (empty)
/root/picea/dashboards/               (15 HTML files including PICEA-AGENTS.md, mcp_hilfe.html, energy_flow.html, etc)

# === /mnt mounts ===
/mnt/picea-backup/install/         (daily snapshot tarballs from backup_install.sh cron)
/mnt/picea-history/picea_archive/  (CSV archives, last one 2026-08-17.csv)

# === Daily backups (visible backup.log entries) ===
# 03:15 cron runs /root/picea/backup_install.sh which produces install/YYYYMMDD_HHMMSS/
# Retention policy: max 10 backups kept, oldest deleted on each run
# Most recent backups: 20260904_031500 through 20260913_031500

# === Known agent IDs for SSH pattern matching ===
# SSH from this box (100.125.180.61) to bootcamp appears in logread as fingerprint
#   SHA256:1hyGy9nS6dIp5jZC57ySHcoc0WUKurrYg9yWIbBREyU
# This is the only key that has EVER logged into the bootcamp router across its 34-day uptime.

# === Forensic pivot for any future spy investigation ===
# 1. SSH logread - look for new fingerprints
# 2. /etc/dropbear/authorized_keys - look for new key entries (mtime is the smoking gun)
# 3. /etc/picea_proxy.json - JWT secret could be exfiltrated via dashboard compromise
# 4. /etc/picea_lighthouse_*.key - lighthouse cmd/hmac keys
# 5. /root/picea/lighthouse_audit.log - look for new entries after Aug 13 (gap = audit was broken)
# 6. /var/log/nginx/error.log - WebSocket reconnect spam from 192.168.10.200
# 7. /var/log/dropbear (NOT present on this OpenWrt, it's a busybox thing) - dropbear logs to logread
