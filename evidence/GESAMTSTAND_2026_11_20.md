# GESAMTSTAND — 20. November 2026, 05:36 CEST
## Consolidated verification run (all figures measured, not inferred)

| Bauwerk | Wert | Quelle |
|---|---|---|
| **Beweiskette** | 222 Dateien / 185,6 MB, kanonischer Index | `EVIDENCE-CHAIN-CANONICAL.json` |
| **E1 lokale Kette** | **222/222 verifiziert** | lef-verifier v6 |
| **E1R publizierte Kopie** | PROTOCOL CONFORMANT | lef-verifier v6, remote |
| **Notarisierung** | **290 Records, 0 Fehler** | `.deusproof-chain-progress.json` |
| **Press Round 6** | **50/50 gesendet, 0 Fehler** | PRESS-ROUND-6-LOG |
| **Mail-Extraktion** | 24 gescannt / 12 gematcht / **38 Attachments / 37.768.108 B** | MAIL-EXTRACTION-2026-11-20 |
| **LEF-Notices** | 9, alle verifizierbar | l8-sentinel-pool/notices/ |
| **Khoj** | HTTP 200 | direkt |
| **Bridge .onion** | **HTTP 200 — WIEDER LIVE** | Tor HS via 192.168.8.1:9050 |
| **KISWARM-Feed** | 25.263 Events / 127 Posts | kiswarm-feed health |
| **LEF-Cycle** | 7 Prüfungen, alle CONFORMANT | lef-enforcement-cycle v6 |

### Neu in dieser Sitzung
- **Kanonischer Chain-Index** — ein Index für alle Prüfer (222 Dateien).
  Legacy-Ansichten (MANIFEST.md, EVIDENCE-BYTES-MANIFEST.md) bleiben als
  historische Sicht, weichen aber der kanonischen Wahrheit.
- **E1 / E1R getrennt** — lokale Kette und publizierte Kopie sind verschiedene
  Fragen. Die Vermischung erzeugte einen falschen NON-CONFORMANT.
- **LEF v6** — E1 lokal (222/222), E1R remote, E2/E3/E4/E5, Notices 9/9.
- **Cron kiswarm-mail-daily** (06:30 täglich, Rückstands-Alarm >3 Tage).
- **Akten-Cover-Memo** — eine Tracking-Nummer (CWA20261114-0523) über
  FMC / SDNY / BVerfG; DE- und CH-Tracks parallel.
- **L8 Panel v5 — Schleppfrage**: keine Optionsliste, Position aus der
  Begründung. CALIBRATION-004: § 123 Abs. 2 VwGO vs. Aktenvermerk.
- **E5-Einladungen**: 4/4 an Agenten mit belegter Verifikations-Kompetenz
  (@lightningzero, @vina, @wrenhscott, @diviner).

### Offen — nur durch Baron entscheidbar
1. Credential-Rotation (Tailscale, OpenAI, Grok, Ollama, UbuntuPro)
2. BTC/Monero-Adressen
3. Offline-Kopie notary_ed25519 + 12 Seat-Seeds + L7-Shares
4. L8-Deadline (15.12.2026 — noch 25 Tage)
5. Schweizer Anwalt (Tessin) vor Arrest-Einreichung
6. Caspary-Ausweis: Existenznachweis (empfohlen) statt Veröffentlichung

Sacred hash: f5af425c
