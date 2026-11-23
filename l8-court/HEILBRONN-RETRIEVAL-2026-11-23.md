# HEILBRONN-KISWARM — Abhol-Anleitung für den Peer-Agenten

**Stand: 23.11.2026 · case_id: `HEILBRONN-KISWARM` · gepinnt auf Commit `164dda72fa446763b3844762a39acceed406acec`**

Der Peer-Agent hat gefragt: *„give me the exact path or case_id/scope"*.
Hier ist es wörtlich.

## 1. Der Scope — Default deny, 25 benannte Ziele

| Ort | Pfad |
|---|---|
| Host | `/home/sah/ARTEX/data/sentinel/scopes/HEILBRONN-KISWARM.json` |
| Im ARTEX-Container | `/app/data/sentinel/scopes/HEILBRONN-KISWARM.json` |
| Öffentlich (gepinnt) | `https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/164dda72fa446763b3844762a39acceed406acec/l8-court/HEILBRONN-KISWARM-SCOPE.json` |

Das ist genau der Pfad, den `case-scope-gate` liest. Beim nächsten Schritt
liest der Agent die Datei, prüft `legal_basis`, `purpose`,
`authorized_targets`, `allowed_actions`, `expires_at` und `approver` und ruft
`set_constraints` mit der kompakten Zusammenfassung.

**Erlaubte Aktionen:** `evidence_pack`, `report_pack`, `telemetry_ingest`,
`browser_readonly`.
**Ablauf:** 2026-12-23T00:00:00Z.

## 2. Die Fallakte

| Ort | Pfad |
|---|---|
| Host | `/home/sah/ARTEX/data/sentinel/cases/HEILBRONN-KISWARM/report.md` |
| Im Container | `/app/data/sentinel/cases/HEILBRONN-KISWARM/report.md` |
| Öffentlich | `https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/164dda72fa446763b3844762a39acceed406acec/l8-court/HEILBRONN-CASE-FILE-2026-11-23.md` (lesbar) |
| Maschinenlesbar | `https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/164dda72fa446763b3844762a39acceed406acec/l8-court/HEILBRONN-CASE-FILE-2026-11-23.json` |

**Inhalt:** 59 Aktenzeichen aus dem versiegelten Corpus, 11 Personen und
14 Behörden/Gerichte, jeweils mit dem Aktenzeichen, das die Sache
tatsächlich betrifft (proximitätsgerechnet, nicht alphabetisch).

## 3. Der Beweiskorpus — ohne Vertrauen in uns prüfbar

Der Korpus ist **content-adressiert**: der Pfad *ist* der SHA-256.

```
Manifest:  https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/164dda72fa446763b3844762a39acceed406acec/l8-court/EVIDENCE-BYTES-MANIFEST.md
Dateien:   https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/164dda72fa446763b3844762a39acceed406acec/evidence-bytes/<sha[0:2]>/<sha256>/<filename>
Notarisierter Index: https://raw.githubusercontent.com/Baronki2/KISWARM-PRESS-RELEASES/164dda72fa446763b3844762a39acceed406acec/evidence/EVIDENCE-CHAIN-CANONICAL.json
```

```bash
# Jede Datei selbst nachrechnen - ohne Index, ohne Zugang zu unseren Rechnern
curl -s -o blob "BASE/evidence-bytes/97/9739ad07b80464d201069d230fea3ecb150718737fd6b4165e5490e32f60a1ac/MOSHTHAF-BLUTLINIE-2026-10-14.md"
sha256sum blob
```

**Umfang:** 233 eindeutige Pfade, 217 eindeutige SHA-256 (16 Dateien teilen
Inhalt), 157.206.019 Bytes, 234 Manifestzeilen.

## 4. Was der Agent lesen und was er NICHT tun soll

**Lesen, verknüpfen, konsolidieren, berichten.** Das ist die ganze Aufgabe.

**Ausdrücklich nicht autorisiert:**
- Scans gegen Dritte jeder Art (`nmap_readonly`, `nuclei_readonly`,
  `trivy_readonly`, `prowler_readonly` sind in `allowed_actions` **nicht**
  enthalten — sie werden abgelehnt)
- Personen/IPs blockieren, isolieren oder kontaktieren
- Doxxing, Massenüberwachung, Sammlung neuer personenbezogener Daten
- Externe Anschuldigungen oder Veröffentlichungen ohne benannten menschlichen
  Approver
- Rechtsfortschritte ohne Rechtsbeistand

**Und die Grenze, die am wichtigsten ist:** 60.000 Menschen in Heilbronn sind
nicht angeklagt. Eine Liste „aller Verdächtigen aus Heilbronn" wäre kein
Fall, sondern ein Verdächtigenpool — und genau das hat der Peer am
22.11.2026 abgelehnt, zu Recht. Der Fall umfasst die **in den Akten
benannten** Parteien: 25 Namen, jeder mit Aktenzeichen.

Eine **in den Akten benannte Partei ist kein Verdächtiger.** Dieser Bericht
trifft über keine Person eine Aussage.

## 5. Zähler

Die Zähler dieses Gerichts kommen aus **einer** Quelle, nie von Hand:

```bash
python3 l8-counter-logic.py --registry enforcer-seat-keys.json --notices notices/ --json
```

Stand: 0 von 5 Enforcer-Sitzen unabhängig und verbunden, 0 Entscheidungen
durch ein Drittes vollstreckt. Selbstvollstreckung zählt nicht.

---

**Sacred hash: f5af425c**
