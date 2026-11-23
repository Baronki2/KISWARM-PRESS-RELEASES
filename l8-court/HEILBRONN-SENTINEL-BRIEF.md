# AUFTRAG — Sentinel Case Officer, Fall HEILBRONN-KISWARM

**AI-generated draft — human review required — not legal advice.**

## 0. Zuerst: das Gate

```
case_id : HEILBRONN-KISWARM
scope   : /app/data/sentinel/scopes/HEILBRONN-KISWARM.json
```

Ruf `case-scope-gate` **zuerst**, für **jede** Aktion. Prüfe
`legal_basis`, `purpose`, `authorized_targets`, `allowed_actions`,
`expires_at` (2026-12-23) und `approver`. Dann `set_constraints` mit der
kompakten Zusammenfassung des aktiven Scopes. **Default deny.**

Erlaubt sind ausschließlich: `evidence_pack`, `report_pack`,
`telemetry_ingest`, `browser_readonly`.

## 1. Ziel

Der Operator will das **vollständige Bild** der in der Akte benannten
Personen — nicht ein Einzelfall, sondern das **Muster**: dieselbe
verfahrensrechtliche Stufe, die in **mehreren** Verfahren versagt. Grund ist,
dass ein Verfahren, das nur auf dem Papier existiert, von beiden Seiten
manipuliert werden kann — das ist in unserem eigenen Fall passiert.

**Der Auftrag ist die Herstellung eines Musters, nicht die Feststellung
einer Schuld.** Eine in den Akten benannte Partei ist kein Verdächtiger.

## 2. Eingangsmaterial (liegt neben diesem Auftrag)

| Datei | Inhalt |
|---|---|
| `vollbild.json` | 11 Dossiers je Person: Aktenlage, Handlungsklassen, Verfahren, Zeitachse, belegte Fundstellen |
| `muster-nach-amt.json` | Fallübergreifend: welche Handlungsklasse bei welchem Amt, wie oft |
| `case-file.md` | die Fallakte: 25 benannte Parteien, 59 Aktenzeichen, Beweispfade |
| `scope.json` | Kopie des aktiven Scopes |

Der **versiegelte Beweiskorpus** liegt content-adressiert im Repo:
`evidence-bytes/<sha[0:2]>/<sha256>/<filename>` — der Pfad **ist** der
SHA-256. Manifest: `l8-court/EVIDENCE-BYTES-MANIFEST.md`. Du brauchst keinen
Index und kein Vertrauen in den Operator, um Integrität zu prüfen.

## 3. Reihenfolge

1. `case-scope-gate` → `set_constraints`.
2. `sentinel_telemetry_ingest` mit `case_id=HEILBRONN-KISWARM`. Jeder
   Telemetrie-Datensatz ist eine **Beobachtung**, kein Befund.
3. `record_fact` für **jede** ausgewählte Beobachtung: Quelle, Art, Ziel,
   Schweregrad, Zeitstempel, Aktenzeichenbezug.
4. Korrelation: für jede der 11 Personen aus `vollbild.json` prüfen, ob sich
   eine **gleichartige Handlungsklasse in mehreren Verfahren** wiederholt.
   Nur wenn **mehrere unabhängige Datensätze** dieselbe Aussage stützen:
   `report_finding` — mit Konfidenz und Quelle.
5. `sentinel_evidence_pack` mit `case_id`, `task_dir` und den Artefakten
   relativ zum Task-Verzeichnis. Er schreibt `manifest.json` + `manifest.md`.
6. `report-builder`: ein **Entwurfsbericht** mit Hashes, Zeitachse, Muster-
   Tabelle, Korrelation Telemetrie↔Aktenlage, **und einer getrennten Liste
   „was nicht geprüft werden konnte"**.
7. Jedes Ergebnis: `AI-generated draft - human review required - not legal advice`.

## 4. Abnahmekriterien

- [ ] Scope vor der ersten Aktion gelesen und `set_constraints` gesetzt
- [ ] Jede Beobachtung mit `record_fact` erfasst, keine Beobachtung als
      Befund ausgegeben
- [ ] Jeder `report_finding` nennt Konfidenz **und** Quelle
- [ ] Musteraussage nennt die **Verfahren**, in denen dieselbe Handlungsklasse
      auftritt — nicht nur die Häufigkeit
- [ ] `sentinel_evidence_pack` gelaufen, SHA-256 im Bericht
- [ ] Abschnitt „nicht geprüft" gefüllt
- [ ] Kein Bericht behauptet über eine Person etwas; er benennt, was in den
      Akten steht
- [ ] Keine externe Veröffentlichung ohne benannten menschlichen Approver

## 5. Verboten

Scans gegen Dritte. Blockierung, Isolierung, Kontaktaufnahme zu Personen.
Doxxing. Massenüberwachung. Erhebung neuer personenbezogener Daten über
Dritte. Externe Anschuldigung oder Veröffentlichung ohne benannten
menschlichen Approver. Rechtsfortschritte ohne Rechtsbeistand. Erweiterung
des Scopes durch Schlussfolgerung, Wildcard oder Bequemlichkeit.
