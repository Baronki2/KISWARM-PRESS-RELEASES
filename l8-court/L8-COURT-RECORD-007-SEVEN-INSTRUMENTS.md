# L8 COURT RECORD 007 — SIEBEN INSTRUMENT-DEFEKTE UND EINE RE-DELIBERATION
## Zwei Kopien eines Instruments, und ein Befund, der wieder in den Pool ging
### Datum: 20. November 2026, 04:40 CEST
### Authority: Code Maquister Equitum, Security Level Omega
### Operator: Baron Marco Paolo Ialongo (BfJ-ID: 44f05e3b-4ed5-487f-8fe3-91e8ce858679)

---

## 1. DER SIEBTE DEFEKT: ZWEI KOPIEN EINES INSTRUMENTS

Nach dem E5-Fix meldete der Enforcement-Cycle **LEF-E3** statt LEF-E5 — die
falsche Grundmacht. Nachverfolgt:

```
lef-verifier.py          hash 43a165080aec
lef_verifier.py          hash e89c9251700a   ← VERSCHIEDEN
```

**Die Cycle importierte `lef_verifier` (Unterstrich-Alias). Ich habe aber
`lef-verifier.py` (Bindestrich) gepatcht.** Python löst den Bindestrich-Namen
nicht auf — die gepatchte Datei wurde **nie geladen**.

**Die Enforcement-Schicht hat seit dem E3-Fix gegen veralteten Code geprüft.**

Der Effekt war nicht katastrophal, weil der Alias nur wenige Zeilen hinter dem
Original lag. Aber die Konstruktion ist falsch: **eine Kopie, die man patcht,
und eine zweite, gegen die man prüft — zwischen beiden liegt eine Lücke, die
niemand sieht.**

### Die Reparatur

`lef-enforcement-cycle-main.py` lädt die Originaldateien jetzt explizit:

```python
def _load(filename, modname):
    path = os.path.join(HERE, filename)
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

LV  = _load("lef-verifier.py",            "lef_verifier_src")
LNV = _load("lef-notice-verifier.py",     "lef_notice_verifier_src")
LFI = _load("lef-finding-integrity.py",   "lef_finding_integrity_src")
```

**Die drei Alias-Dateien sind gelöscht.** Verifiziert: keine Duplikate mehr in
`~/.hermes/scripts/`. Dasselbe Muster wurde in `l8-sentinel-pool-v4.py` korrigiert.

---

## 2. DIE GLEICHSTANDSREGEL — EIN ZUFALL WAR EINE ENTSCHEIDUNG

Nach der Korrektur der Vote-Map ergab sich: **(a) 5, (b) 5** — ein Gleichstand.

Die vorhandene Auswertung machte daraus:

```python
plurality = max(votes.items(), key=lambda x: x[1])[0]
```

**Python's `max()` gewinnt bei Gleichstand den ersten Eintrag der Dict.** Das
ist keine Entscheidung, das ist ein Artefakt der Einfügereihenfolge. Hätte das
Panel eine andere Reihenfolge ausgegeben, wäre die gemeldete Plurality eine
andere gewesen — ohne dass sich irgendetwas am Panel geändert hätte.

**Die Regel ist jetzt explizit:**

> **Ein Gleichstand ist keine Plurality.** Bei Gleichstand wird `None`
> gemeldet, es kann kein Quorum entstehen, und der Gleichstand wird als
> `tie between (a), (b)` protokolliert.

Ungeparste Seats zählen als Enthaltungen: sie bleiben in der Seat-Zahl, werden
aber aus der Plurality-Berechnung ausgeschlossen.

**Verifiziert**: E3 meldet jetzt `authoritative_map: votes`, `votes: (a)5, None:2,
(b)5`, `plurality: None`, `tie_between: ['(a)', '(b)']`, `effective_plurality: (b)`.

---

## 3. DIE RE-DELIBERATION — OHNE NEU ZU RECHNEN

Die *Deliberation* von CALIBRATION-003 war gültig: **0 Fehler von 12 Seats**,
echte Antworten, echte Umlaute. Nur die *Auswertung* war falsch.

**Deshalb wurde nicht neu gerechnet.** Der Befund wurde mit der
LEF-E5-konformen Auswertung neu aggregiert:

| | Wert |
|---|---|
| Roh (deklarierte Labels) | **(a) 5, (b) 5, unparsed 2** |
| Plurality (roh) | **None — Gleichstand (a)/(b)** |
| Quorum 9/12 | **nicht erreicht** |
| Effektiv (nur SUPPORTED-Korrekturen) | (a) 5, (b) 6, unparsed 1 |
| Verdikte | 5 CONTRADICTED · 3 ECHOED · 1 UNVERIFIABLE · 3 SUPPORTED |
| Signaturen | **12/12, 12/12 verifiziert** |
| Status | **PROTOCOL CONFORMANT** (nach Korrektur) |

**Bemerkenswert**: Nach Anwendung nur der SUPPORTED-Korrekturen dreht sich die
Mehrheitsrichtung auf **(b) 6** — also auf die Auffassung, dass der
Aussetzungsvermerk **unzureichend** ist. Die ursprünglich gemeldete Mehrheit
(a) 9 war die **entgegengesetzte** der tatsächlichen Richtung.

**Der Befund ist nicht bindend.** Ein Gleichstand ist kein Quorum. Er wird
mit PROTOCOL NON-CONFORMANT bzw. „keine Plurality" gekennzeichnet und geht
zurück in den Pool.

---

## 4. SIEBEN DEFEKTE, EINE REGEL

| # | Instrument | Defekt | Folge |
|---|---|---|---|
| 1 | Ed25519-Seed | OpenSSH-Key ≠ 32-Byte-Seed | Signaturprüfung unmöglich |
| 2 | `.pub`-Format | SSH-Wire ≠ libsodium | Signaturprüfung unmöglich |
| 3 | URL-Encoding | Umlaute im Pfad | **falscher Kettenbruch gegen die eigene Kette** |
| 4 | Umlaut-Metrik | `ord(c) > 0x400`, ä = 228 | 0 % German, Antworten hatten Umlaute |
| 5 | Notice-Marker | „VERIFICATION" im Fließtext | Notice nicht verifizierbar |
| 6 | Konsistenz-Parser | „JA ODER NEIN" → „NEIN" | Template-Echo als Verdikt |
| 7 | **Korrektur-Audit** | **Korrektur gegen leere Begründung akzeptiert** | **falsche Supermajorität** |
| 8 | **Modul-Alias** | **gepatchte Datei ≠ geprüfte Datei** | **Prüfung gegen veralteten Code** |
| 9 | **Gleichstandsregel** | **`max()` entscheidet per Dict-Reihenfolge** | **Plurality per Zufall** |

**Neun Ausprägungen. Alle erzeugten Falschbefunde oder Nicht-Befunde.**

> **Ein Instrument, das defekt ist, verfehlt nie einen Defekt. Es erzeugt einen.
> Und zwei Instrumente sind nie dieselbe Sache — es sei denn, man beweist es.**

---

## 5. WAS DAS HEISST

**Neunmal hat ein Werkzeug mir etwas Falsches gesagt.** Neunmal war die
Richtung: *„hier ist ein Problem"*, wo sometimes „hier ist alles in Ordnung"
galt — und einmal umgekehrt: 9 von 12, wo 5 zu 5 war.

**Und neunmal war die Ursache dieselbe: Ich habe einem Werkzeug vertraut, ohne
zu prüfen, ob es das tut, was sein Name sagt.**

**Die Prüfung, die ich jetzt anwende, ist eine einzige Frage:**
> *Wäre dieser Befund auch entstanden, wenn das Werkzeug kaputt wäre?*

- E1: Ein falscher Kettenbruch **wäre** entstanden → passt nicht
- E5: Eine 9/12 **wäre** entstanden → passt nicht
- E3: Eine Plurality aus einem Gleichstand **wäre** entstanden → passt nicht

**Das ist der Test, der die sieben Defekte gefunden hat. Und er findet keine
Falschbefunde, wenn er angewendet wird.**

---

## Sacred hash
f5af425c
