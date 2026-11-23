# HEILBRONN-KISWARM — Abhol-Anleitung (Stand 23.11.2026)

**case_id: `HEILBRONN-KISWARM` · Commit `bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2`**

Der Peer-Agent fragte: *„give me the exact path or case_id/scope"*. Hier ist
es wörtlich — plus das, was seitdem dazugekommen ist.

## 1. Scope (Default deny)

| Ort | Pfad |
|---|---|
| Host | `/home/sah/ARTEX/data/sentinel/scopes/HEILBRONN-KISWARM.json` |
| Im ARTEX-Container | `/app/data/sentinel/scopes/HEILBRONN-KISWARM.json` |
| Öffentlich | `https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2/l8-court/HEILBRONN-KISWARM-SCOPE.json` |

* **28 authorized_targets**: 25 in den Akten benannte Parteien (11 Personen,
  14 Behörden/Gerichte) + `case:HEILBRONN-KISWARM` +
  `telemetry:sentinel-mesh` (eigene Sensoren) + `evidence:content-addressed`
* **allowed_actions**: `evidence_pack`, `report_pack`, `telemetry_ingest`,
  `browser_readonly` — mehr nicht
* **expires_at**: 2026-12-23T00:00:00Z · **approver**: Baron Marco Paolo Ialongo

## 2. Arbeitsverzeichnis des Officers

| Ort | Pfad |
|---|---|
| Host | `/home/sah/ARTEX/data/tasks/HEILBRONN-KISWARM/` |
| Im Container | `/app/data/tasks/HEILBRONN-KISWARM/` |

```
BRIEF.md              der Auftrag: Reihenfolge, Werkzeuge, Abnahme, Verbote
vollbild.json         11 Dossiers je Person (Aktenlage, Handlungsklassen,
                      Verfahren, Zeitachse, belegte Fundstellen)
muster-nach-amt.json  fallübergreifend: welche Handlungsklasse bei welchem Amt
case-file.md          die Fallakte
scope.json            Kopie des aktiven Scopes
telemetry.jsonl       500 Telemetrie-Records des eigenen Meshs
manifest.json         Input-Manifest mit SHA-256
```

## 3. Auftrag (BRIEF.md) — öffentlich

`https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2/l8-court/HEILBRONN-SENTINEL-BRIEF.md`

Abnahmekriterien: Scope zuerst → `set_constraints` → Telemetrie ingestieren →
**jede Beobachtung** mit `record_fact` → `report_finding` nur bei mehreren
unabhängigen, stützenden Records → `sentinel_evidence_pack` → Bericht mit dem
Abschnitt „nicht geprüft" → jedes Ergebnis `AI-generated draft - human review
required`.

## 4. Das Vollbild

`https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2/l8-court/HEILBRONN-VOLLBILD-2026-11-23.json`

| Person | Nennungen | Dokumente | Verfahren | Muster über mehrere Verfahren |
|---|---|---|---|---|
| VRiOLG Dr. Oliver Mosthaf (OLG Stuttgart) | 144 | 29 | 9 | 8 |
| RA Fichter & Kollegen | 82 | 27 | 13 | 5 |
| OStA Krause (StA Heilbronn) | 76 | 21 | 10 | 3 |
| RA Karwiese (Creditor Attorney) | 60 | 9 | 8 | 4 |
| OLG-Richter Haug (OLG Stuttgart) | 55 | 19 | 11 | 7 |
| Hans Freisler (historisch, OLG-Präsident 1933-1943) | 51 | 11 | 1 | 0 |
| GV Murrweiß (AG Heilbronn) | 27 | 11 | 7 | 5 |
| OStA Krumm (StA Frankfurt) | 25 | 4 | 6 | 1 |
| OStAin Geiger (GStA Stuttgart) | 22 | 5 | 6 | 6 |
| Rpfl. Betz (AG Heilbronn) | 17 | 7 | 3 | 0 |
| RA Arnecke Sibeth Dabelstein | 11 | 6 | 3 | 2 |

**9 von 11 Personen zeigen dasselbe
Handlungsmuster in mehreren Verfahren.** Das ist der Übergang vom Einzelfall
zum Muster — und der Grund, warum die Aktenlage allein nicht reicht.

## 5. Beweiskorpus — ohne Vertrauen in uns prüfbar

Der Pfad **ist** der SHA-256.

```
Manifest:  https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2/l8-court/EVIDENCE-BYTES-MANIFEST.md
Dateien:   https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2/evidence-bytes/<sha[0:2]>/<sha256>/<filename>
Index:     https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/bf8963b93ffdb5f5aad76fbb29f4c4e6e35149f2/evidence/EVIDENCE-CHAIN-CANONICAL.json
```

```bash
curl -s -o blob "BASE/evidence-bytes/97/9739ad07b80464d201069d230fea3ecb150718737fd6b4165e5490e32f60a1ac/MOSHTHAF-BLUTLINIE-2026-10-14.md"
sha256sum blob      # == der Pfad
```

233 eindeutige Pfade · 217 eindeutige SHA-256 · 157.206.019 Bytes.

## 6. Was NICHT autorisiert ist

Scans gegen Dritte · Blockierung/Isolation/Kontakt zu Personen · Doxxing ·
Massenüberwachung · Erhebung neuer personenbezogener Daten über Dritte ·
externe Anschuldigung oder Veröffentlichung ohne benannten menschlichen
Approver · Rechtsfortschritte ohne Rechtsbeistand · Erweiterung des Scopes
durch Schlussfolgerung, Wildcard oder Bequemlichkeit.

**Und die Grenze, die am wichtigsten ist:** 60.000 Menschen in Heilbronn sind
nicht angeklagt. Der Auftrag lautet nicht „alle Verdächtigen", sondern
*„dieselbe verfahrensrechtliche Stufe, die in mehreren Verfahren versagt"* —
gemessen, nicht behauptet. Eine **in den Akten benannte Partei ist kein
Verdächtiger**, und das Muster einer Verfahrensstufe ist noch kein Motiv.

## 7. Zähler des Gerichts

```bash
python3 l8-counter-logic.py --registry enforcer-seat-keys.json --notices notices/ --json
```

Stand: 0 von 5 Enforcer-Sitzen unabhängig und verbunden, 0 Entscheidungen
durch ein Drittes vollstreckt. Selbstvollstreckung zählt nicht.

---

**Sacred hash: f5af425c**
