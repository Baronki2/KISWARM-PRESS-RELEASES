# L8 COURT RECORD 005 — DIE MASCHINE SCHREIBT IHREN EIGENEN BEFUND
## Das Enforcement ist nicht mehr Dokumentation, sondern Ausführung
### Datum: 20. November 2026, 02:43 CEST
### Authority: Code Maquister Equitum, Security Level Omega
### Operator: Baron Marco Paolo Ialongo (BfJ-ID: 44f05e3b-4ed5-487f-8fe3-91e8ce858679)

---

## 1. DER URSPRUNG: EINE Notice, DIE SICH NICHT VERIFIZIEREN KONNT

Beim Bau der automatischen Notice-Erzeugung passierte etwas, das die Schicht
über sich selbst beweist:

**Die erste Version der Notice `LEF-NOTICE-E2-002` verifizierte NICHT.**
`hash_ok=False`, `sig_ok=False`.

Ursache: Mein Notice-Fließtext enthielt das Wort **"VERIFICATION"** — als
Satz: *„The payload hash, the detached signature and the enforcer public key
follow below."* Nein, der Satz war harmlos. Der Problemtext war der
Absatz darüber, der die Sektion *"VERIFICATION"* als Überschrift
vorankündigte.

**Der Verifier teilt das Dokument am ersten Vorkommen des Markers.** Das
erste Vorkommen lag im Fließtext, nicht an der Sektion. Also wurde ab der
falschen Stelle gehasht — und die Prüfsumme passte nicht.

**Ein Notice, der sich nicht verifizieren kann, ist wertlos.** Das ist die
rekursive Eigenschaft, die ich in LEF-1.0 §7 festgehalten habe. Hier hat
sie sich an meinem eigenen Dokument bewiesen.

### Die Reparatur ist strukturell, nicht kosmetisch

**Die Notice-Formatierung wurde aus dem Hand-Schreiben in die Maschine
verlagert.** `format_notice()` in `lef-enforcement-cycle-main.py` erzeugt den
Text. Der Marker ist eine Konstante im Code und kann **nur an einer Stelle**
erscheinen — im Formatter. Der Fließtext kann ihn nicht erzeugen, weil er
aus Feldern zusammengesetzt wird.

**Ein Instrument kann keinen Falschbefund mehr produzieren, wenn es den
Fehler nicht mehr machen kann.**

---

## 2. ZWEI WEITERE BUGS, DIE DABEI AUFFielen

| # | Bug | Ursache |
|---|-----|---------|
| 1 | `UnboundLocalError: body` | Der `.format()`-Aufruf referenzierte seine eigene lokale Variable im Argument `body_text=body`. Umbenennen half nicht — der Ausdruck referenziert sich selbst. **Fix: explizite String-Konkatenation statt `.format()`.** |
| 2 | `NameError: body` | Der `return`-Wert referenzierte die entfernte Variable. |

**Beide sind Beispiele für dieselbe Klasse: ein Werkzeug, das sich auf sich
selbst bezieht.** Ein Fehler in der Instrumentenebene wird als Befund in der
Sachebene gemeldet. Das ist exakt die Verwechslung, die LEF-E1 in der
Beweiskette gemacht hat (URL-Encoding → falscher Kettenbruch) und die die
kaputte Umlaut-Metrik gemacht hat (`ord(c) > 0x400` → 0 % German).

**Drei Befunde, drei verschiedene Ausprägungen derselben Grundregel:**
> *Wenn das Instrument defekt ist, meldet es Falschbefunde. Prüfe das
> Instrument, bevor du den Gegenstand verurteilst.*

---

## 3. WAS JETZT FUNKTIONIERT — BEWIESEN, NICHT BEHAUPTET

**Test:** Die Signaturen aus dem Finding entfernt → Cycle laufen lassen →
Notice erzeugt → Notice verifiziert → Finding wiederhergestellt → Cycle sauber.

```
AUTO-NOTICE: LEF-AUTO-E2-20261120-124233.md (verified=True)
  [LEF-E1] PROTOCOL CONFORMANT
  [LEF-E3] PROTOCOL CONFORMANT
  [LEF-E4] PROTOCOL CONFORMANT
  [LEF-E2] PROTOCOL NON-CONFORMANT
  [NOTICES] PROTOCOL CONFORMANT (5/5 notices verifiable)
  OVERALL: PROTOCOL NON-CONFORMANT   exit=1
```

Und die erzeugte Notice:

```
PROTOCOL NOTICE — E2
======================================================
finding_id:    calibration-002.json
artifact_id:   l8-sentinel-pool/findings/calibration-002.json
enforcer:     L8-OPERATOR-SELF-ENFORCE (seat 01)
enforcer_key_fp: 6ebb437a4d27ef53
power:        LEF-E2
checked_at:   2026-11-20T12:42:33.967687+00:00
method:       automatic enforcement cycle (cron lef-enforcement-cycle, 68361c8a5891) — ...
deviation:    one or more seats published no verifiable signature — {"verified": 0, ...
status:       PROTOCOL NON-CONFORMANT
```

**Verifikation der selbst erzeugten Notice:**
```
LEF-AUTO-E2-20261120-124233.md: verify=True hash_ok=True sig_ok=True
sha256(payload)=cd746c4ce0809a84163d532a0d161f62fcb3c256b61531c63d097a76f14bab8c
```

**Die Maschine hat den Befund gefunden, den Notice-Text geschrieben, mit dem
Seat-01-Key signiert, die Signatur geprüft und das Ergebnis in den Feed
gemeldet.** Kein menschliches Eingreifen zwischen Fehler und Veröffentlichung.

Nach dem Restore: `OVERALL: PROTOCOL CONFORMANT`, **6/6 Notices verifizierbar**.

---

## 4. WAS DAS FÜR DIE ARCHITEKTUR HEISST

| Vorher | Nachher |
|---|---|
| Notices von Hand geschrieben | Notices von der Maschine erzeugt |
| Format-Fehler möglich (Marker-Kollision) | Format-Fehler **strukturell ausgeschlossen** |
| Eine Abweichung, die niemand sieht, bleibt unentdeckt | Cycle alle 30 Min, Abweichung → Notice → Feed |
| Der Betreiber ist der einzige Autor der Notices | Die Maschine ist Autorin und Prüferin zugleich |

**Und das Entscheidende**: Die Notice-Autorisierung ist jetzt **nicht mehr
meine Behauptung**, sondern eine Signatur, die jeder mit dem
Publizierten Public Key prüfen kann. Genau wie die Beweiskette.

**Der Kreis schließt sich:**

| Ebene | Träger | Geprüft von |
|-------|--------|-------------|
| Evidenz | 234 Blobs, content-adressiert | LEF-E1, jeder |
| Finding | 12 Seat-Signaturen | LEF-E2, jeder |
| Quorum | 9/12-Nachzählung | LEF-E3, jeder |
| Konsistenz | Selbstkonsistenz-Runde | LEF-E4, jeder |
| **Notice** | **Seat-01-Signatur über Payload-Digest** | **jeder, mit `lef-notice-verifier.py`** |
| **Der Layer selbst** | **alle 30 Minuten, automatisch** | **jeder, der den Cron liest** |

---

## 5. WAS DAS NICHT BEWEIST

**1.** Dass die 4 externen Agenten die Sitze annehmen. Weiterhin 0 von 4.
**2.** Dass diese Box eine 9/12-Supermehrheit hervorbringt. Der Lauf auf
pool v4 steht aus.
**3.** Dass die automatische Notice-Erzeugung mit *menschlichem* Fehlertext
umgehen kann — die Deviation-Zeile ist maschinell erzeugt und kann
unleserlich werden (JSON-Fragmente). Für ein externes Enforcern-Briefing
muss das lesbar formatiert werden.

---

## Sacred hash
f5af425c
