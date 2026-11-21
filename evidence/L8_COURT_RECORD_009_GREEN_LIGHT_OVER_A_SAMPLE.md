# L8 COURT RECORD 009 — THE GREEN LIGHT OVER A SAMPLE
**21 November 2026 · KISWARM · Sacred hash f5af425c**

## Anlass

Wir wollten die externe Hälfte des L8-Gerichts schließen: vier Reviewer
einzeln ansprechen, mit Court Record 008 als konkretem Anlass, und ihnen
eine Aufgabe geben, die sie ohne uns beantworten können.

Diese Aufgabe **erzwang** die Prüfung unserer eigenen Schicht — denn ein
Reviewer, dem wir E1 anbieten, wird zuerst E1 prüfen. Wir haben mit dem
Blick auf den externen Reviewer nachgesehen, was er sehen würde. Zwei
Befunde.

## Befund A — LEF-E1R meldete „PROTOCOL CONFORMANT" über 10,26 % der publizierten Dateien

`LEF-E1R` prüft die **publizierte** Kopie der Beweiskette durch erneutes
Abrufen und Hashen vom GitHub-Substrat. Der Zyklus läuft alle 30 Minuten;
234 Blobs über die Leitung zu holen wäre eine unnötige Last, deshalb wird
**eine Stichprobe von 24** geprüft. Das ist eine vernünftige Betriebsentscheidung.

Der Fehler war nicht die Stichprobe. Der Fehler war, dass das Ergebnis
**nicht sagte, dass es eine Stichprobe war**:

```
[LEF-E1R] PROTOCOL CONFORMANT
   indexed: 234
   checked: 24
```

Ein Leser — und das Gericht selbst, und jeder externer Reviewer — durfte
daraus schließen, die publizierte Kopie sei vollständig geprüft. Sie war
zu 10,26 % geprüft.

Das ist dieselbe Fehlerklasse wie Record 008, eine Ebene tiefer. Record 008
war ein grünes Licht über **null** Prüfungen. Hier ist es ein grünes Licht
über **24** Prüfungen, das aussieht wie eines über 234. Der Unterschied
zwischen „geprüft" und „stichprobenweise geprüft" war im Protokoll nicht
unterscheidbar — und genau diese Ununterscheidbarkeit ist der Mangel.

Die Null-Prüfungen-Sperre aus Record 008 hat diesen Fall nicht erwischt,
weil 24 eben nicht 0 ist. Die Regel war zu eng gefasst: Sie fragte „kann
das Instrument nichts prüfen?", nicht „kann das Instrument seine Lücke
verschweigen?".

**Fix.** Jede Prüfung führt jetzt ihre Abdeckung mit:

```
coverage_indexed, coverage_checked, coverage_percent, sampled
```

und der Stichprobenfall erzeugt eine ausdrückliche Offenlegung. Das
Gesamtverdikt darf diese Offenlegung **nicht** mehr verschlucken:

```
[LEF-E1  ] PROTOCOL CONFORMANT   indexed 348  checked 348  coverage 348/348 (100.0%)
[LEF-E1R ] PROTOCOL CONFORMANT   indexed 234  checked  24  coverage  24/234 (10.26%)
OVERALL: PROTOCOL CONFORMANT
OFFENLEGUNG: STICHPROBE: 24 von 234 der publizierten Dateien geprueft (10.26%).
            Der Befund gilt fuer die geprueften Dateien, nicht fuer die
            vollstaendige publizierte Menge.
```

Die Stichprobe bleibt. Die Verschweigung nicht.

## Befund B — der kanonische Index war stumm veraltet, und niemand erzeugte ihn

`EVIDENCE-CHAIN-CANONICAL.json` listet 346 Dateien mit Pfad, Größe und
SHA-256. Am 21.11.2026 waren es **348** — die zwei neuen Dokumente der
Enforcer-Runde 2 fehlten. `LEF-E1` prüfte 346 von 346 und meldete
`CONFORMANT`.

Das ist die harmlosere Variante, weil die Prüfung selbst echt war
(346/346, 100 %). Der Mangel lag eine Ebene darüber: **der Index, gegen den
geprüft wird, war nicht mehr die Wahrheit**, und niemand merkte es, weil ein
vollständiger Check über einer veralteten Menge vollständig aussieht.

Die Ursache war nicht Nachlässigkeit im Prüfen, sondern im Produzieren:
**kein einziges Skript erzeugte den Index.** Er wurde am 19.11.2026 ad hoc
geschrieben, per Hand, mit sechs Metadaten-Schlüsseln und einer
Dateiliste. Seitdem war er still veraltet — und konnte still veralten,
ohne dass ein Fehlerpfad existierte, der es meldet.

**Fix.** `~/.hermes/scripts/l8-canonical-index.py` erzeugt den Index aus dem
Verzeichniszustand: scannen, hashen, atomar schreiben, Metadaten-Schlüssel
des Vorindex erhalten, und **differenzieren** — hinzugefügt, entfernt,
Hash geändert. Das Skript ist die Reproduzierbarkeit; ohne Skript driftet
das Artefakt, und ein driftendes Artefakt ist eine falsche Behauptung,
solange niemand den Unterschied bemerkt.

```
Index: 348 Dateien / 247475745 Bytes
vorher: 346
neu hinzugefuegt : 2 ['L8_ENFORCER_ROUND2_2026_11_21.md', 'L8_ENFORCER_SEAT_ARTIFACT_2026_11_21.md']
entfernt         : 0 []
Hash geaendert   : 0 []
```

Null entfernt, null Hash-Änderungen: die 346 alten Einträge stimmen
unverändert. Nur die fehlenden zwei kamen dazu.

## Warum das hier steht und nicht irgendwo versteckt

Dieser Record entstand **im Rahmen derselben Aufgabe**, die wir gerade
externen Reviewern anbieten. Wir hätten die Einladung auch ohne diese
Prüfung abschicken können — die Einladung wäre angekommen, die Reviewer
hätten gearbeitet, und die Layer hätte ihre Lücken weiter verschwiegen.

Die Einladung wäre wertlos gewesen. Man kann nicht „prüft uns, findet
unsere Fehler" sagen, wenn man weder weiß, wie viele Fehler man hat, noch
diese Zahl offenlegt.

## Regeln

1. **Ein Verdikt nennt seine Abdeckung.** „Geprüft" und „stichprobenweise
   geprüft" sind verschiedene Aussagen. Wer sie nicht unterscheidet, führt
   ein grünes Licht über eine Lücke.
2. **Die Null-Prüfungen-Sperre gilt auch für Teilmengen.** Die Frage ist
   nicht „hast du nichts geprüft?", sondern „weißt du, was du *nicht*
   geprüft hast?".
3. **Ein Artefakt, das geprüft wird, muss von einem Skript erzeugt
   werden.** Ein Index ohne Erzeuger driftet; ein vollständiger Check über
   einen driftenden Index sieht vollständig aus.
4. **Ein vollständiger Check über eine veraltete Menge ist kein
   Befund.** Er ist eine Aussage über die Vergangenheit.

## Status

- `LEF-E1`: indexed 348, checked 348, match 348 — **vollständig, 100 %**
- `LEF-E1R`: indexed 234, checked 24 — **Stichprobe, offengelegt**
- Kanonischer Index: reproduzierbar, 348 Dateien, aktuell
- Übrige Mächte E2, E3, E4, E5: `PROTOCOL CONFORMANT`
- Notices: 10/10 verifizierbar
- Gesamtverdikt: `PROTOCOL CONFORMANT` **mit Offenlegung**

## Dateien

- `~/.hermes/scripts/l8-canonical-index.py` — reproduzierbarer Index-Erzeuger
- `~/.hermes/scripts/lef-verifier.py` — Abdeckungsfelder und Offenlegung
- `~/.hermes/scripts/lef-enforcement-cycle-main.py` — Offenlegung im Gesamtverdikt
- `~/.config/sah-vault/EVIDENCE-CHAIN-CANONICAL.json` — 348 Dateien
- `~/.config/sah-vault/l8-sentinel-pool/LEF-CYCLE-REPORT.json` — Zyklusbericht
