# BRIDGE RECOVERY — NEW .onion ADDRESS
## Issued: 2026-10-02T21:14:49.038007+00:00
## Authority: Code Maquister Equitum, Security Level Omega

## NEW .onion (in service)
**ij4iqzbr2m35rz4cm56vakrlgdpbxha3z6vyfsdrv53kn4xjkhf5ykqd.onion**

## OLD .onion (decommissioned)
hwvuj6ms7f5z33i6deyx3lipu74z5hixqiecpei4byhjketwbej7aoad.onion

## Reason for change
The old Flint3 BE9300 router (which hosted the .onion at 192.168.168.125) was replaced
with a new GL-BE9300 (now named "SAH-HOME") on 2026-10-02. The HiddenServiceDir contents
(hs_ed25519_private_key) was on the old hardware and could not be recovered.

The new hardware was set up with fresh Tor HS configuration. The new .onion is generated
by the new router's Tor daemon with fresh ed25519 keys.

## Architecture (unchanged)
- New .onion → Tor HiddenService v3 on Router 100.91.83.41 / 192.168.168.125 / 192.168.8.1
- HiddenServicePort 80 127.0.0.1:8843 (loopback on router)
- SSH reverse-tunnel: PC :42110 (Khoj) → Router 127.0.0.1:8843
  - khoj-tunnel.service running on PC, connects to root@100.91.83.41
  - Restart=always, RestartSec=5

## Verification (2026-10-02 23:13 CEST)
- Tor bootstrap: 100% done in 13 seconds
- HTTP .onion/: HTTP 200 in 5.26s cold, 53,040 bytes
- /api/chat: responded with "Alive" (Khoj, 9,780 input tokens, 1,023 output tokens)

## Auth
Bearer token: khoj-2cd7705a71e1496c9ab37a94fe4e (unchanged)

## Sacred hash
f5af425c (mesh-wide identifier, unchanged)
