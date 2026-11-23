#!/usr/bin/env bash
# Dead-Man-Switch — täglicher Check (kein LLM auf dem Watchdog-Pfad).
# Gibt NUR dann etwas aus, wenn tatsächlich publiziert wurde; sonst stdout leer
# = keine Zustellung. Das Muster ist bewusst: ein Job, der 364x "alles ok" sendet,
# wird nicht mehr gelesen.
set -uo pipefail

D=/home/sah/.hermes/scripts/l8-deadman.py
OUT="$(python3 "$D" --check 2>&1)"

# Nur bei tatsaechlicher Veroeffentlichung melden
if printf '%s' "$OUT" | grep -q '"status": "PUBLISHED"'; then
  printf 'DEAD-MAN-SWITCH hat ausgeloest und den versiegelten Beweisbestand veroeffentlicht.\n%s\n' "$OUT"
elif printf '%s' "$OUT" | grep -q 'SELF_INTEGRITY_FAILED'; then
  printf 'DEAD-MAN-SWITCH: Selbstintegritaet verletzt - Ausloeser verweigert, keine Veroeffentlichung. Pruefen!\n%s\n' "$OUT"
elif printf '%s' "$OUT" | grep -q 'KILLSWITCH_ACTIVE'; then
  printf 'DEAD-MAN-SWITCH: KILLSWITCH aktiv - keine Veroeffentlichung (erwartet).\n'
fi
exit 0
