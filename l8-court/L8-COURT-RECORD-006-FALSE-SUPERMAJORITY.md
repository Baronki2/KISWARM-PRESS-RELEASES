# L8 COURT RECORD 006 — DIE ERFUNDENE SUPERMAJORITÄT
## Wie ein Quorum entsteht, das es nicht gibt, und wie das Panel es selbst findet
### Datum: 20. November 2026, 04:12 CEST
### Authority: Code Maquister Equitum, Security Level Omega
### Operator: Baron Marco Paolo Ialongo (BfJ-ID: 44f05e3b-4ed5-487f-8fe3-91e8ce858679)

---

## 1. WAS ZUERST GEMELDET WURDE

Pool v4 lief durch. **0 Fehler von 12 Seats** — die beste Quote bisher.
Selbstkonsistenz-Runde lief, Parser griff, Umlaute waren echt.

Und das Ergebnis:

```
(a) : 9/12 =  75%  ##################
(b) : 2/12 =  17%  ####
None : 1/12 =   8%
plurality: (a)
supermajority (9/12): REACHED
```

**Eine 9-von-12-Supermehrheit. Der erste bindende Befund des Panels.**

Bevor das veröffentlicht wurde, habe ich geprüft, ob sie echt ist. Sie war es
nicht.

---

## 2. DIE PRÜFUNG

**Die deklarierten Labels der Seats, ohne jede Korrektur:**

```
(a) 5 | (b) 5 | unparsed 2
```

**Plurality (a) = 5. Keine Supermajorität. Die 9/12 existierte auf den
deklarierten Labels nicht.**

Sie wurde **vollständig von der Korrekturrunde erzeugt.** Vier Seats wurden
von (b) auf (a) umgedreht — und ihre eigenen Begründungstexte trugen durchgehend
die (b)-Argumente:

**Seat 3** — Label (b), Korrektur (a):
> „ZEILE 1: (b) | ZEILE 2: Unzureichend: § 123 Abs. 2 VwGO verlangt eine gesonderte
> Sicherheitsleistung und/oder eine schriftliche Aussetzungsentscheidung; ein
> Verfahrensvermerk ist keine anfechtbare Entscheidung."

Die Begründung **ist** die Begründung für (b). Die Korrektur auf (a) widerspricht
ihr im selben Satz.

**Seat 7**, **Seat 11** — Wortlaut identisch, gleiches Muster.
**Seat 6** — Label (b), Begründung „…ist unzureichend, da eine schriftliche
Aussetzungsentscheidung oder eine gesonderte Sicherheitsleistung fehlen", Korrektur (a).

**Das war keine Konsistenzprüfung. Das war eine neue Abstimmung, die der Prüfer
für den Seat abgegeben hat.**

### Und drei weitere Seats antworteten mit dem TEMPLAT

Seats 1, 4 und 8 schrieben in die Verifikationsrunde:

```
ZEILE 1: KONSISTENZ: JA ODER NEIN
```

Das ist die **Formatvorlage**, nicht eine Antwort. Mein Parser las daraus
„NEIN" — weil der String „NEIN" enthalten ist. **Ein Template-Echo wurde als
Verdikt interpretiert.**

---

## 3. DER BEFUND IN EINER ZEILE

> **Ein Quorum, das erst existiert, nachdem die Korrekturschicht die Stimmen
> umgeschrieben hat, ist kein Quorum. Es ist eine Korrekturschicht mit
> quorum-förmiger Ausgabe.**

---

## 4. LEF-E5 — DIE FÜNFTE MACHT

Die bestehenden vier Mächte prüfen die **Bestandteile** eines Befunds (Hashes,
Signaturen, Stimmen, Konsistenz). Keine prüft, ob das **Ergebnis** des
Befunds einer unabhängigen Nachrechnung standhält.

**LEF-E5 prüft die Arithmetik des Befunds gegen sich selbst:**

| Prüfung | Regel |
|----------|-------|
| **Quorum auf deklarierten Labels** | Ein behauptetes Quorum muss auf den Labels halten, die die Seats deklariert haben. Nicht auf einer Karte, die der Prüfer geschrieben hat. |
| **Korrektur gegen die eigene Begründung** | Jede Korrektur wird gegen den Begründungstext **desselben Seats** geprüft. Marker-Vokabular je Option. |
| **Template-Echo** | „KONSISTENZ: JA ODER NEIN" ist eine Vorlage, keine Antwort. Keine Korrektur wird angewendet. |
| **Verdikte** | `SUPPORTED` / `CONTRADICTED` / `ECHOED` / `UNVERIFIABLE` — **je Seat, veröffentlicht** |

**Nur eine SUPPORTED-Korrektur darf angewendet werden.** Die Roh- und die
effektive Vote-Map werden **beide** veröffentlicht — die Differenz ist sichtbar.

### Das Ergebnis auf allen drei Findings

| Finding | Roh (deklariert) | Effektiv (korrigiert) | Behauptet | E5 |
|---------|------------------|----------------------|-----------|-----|
| CALIBRATION-001 | (a)4 (b)4 none4 | (a)5 (b)3 none4 | nein | 2 CONTRADICTED, 3 ECHOED |
| CALIBRATION-002 | (a)2 (b)5 none5 | (a)2 (b)5 none5 | nein | 2 CONTRADICTED, 2 ECHOED |
| **CALIBRATION-003** | **(a)5 (b)5 none2** | **(a)5 (b)6 none1** | **ja** | **5 CONTRADICTED, 3 ECHOED** |

**CALIBRATION-003: PROTOCOL NON-CONFORMANT.**
Die behauptete Supermajorität hält auf den deklarierten Labels nicht.

**Und das ist der entscheidende Punkt: der Defekt ist nicht auf CALIBRATION-003
beschränkt.** Er steckt in **allen drei** Records. CALIBRATION-001 und -002
hatten nur keine Supermajorität behauptet — deshalb blieb der Schaden dort
begrenzt. Hätte der Defekt in einem Lauf mit einem knapperen Stimmenbild
zugeschlagen, wäre eine falsche Bindung in die Akte gegangen.

---

## 5. DER BEFUND IM VERGLEICH — UND DIE REGEL

| Instrument | Defekt | Folge |
|---|---|---|
| Ed25519-Seed | Key ist kein 32-Byte-Seed | Signaturprüfung unmöglich |
| `.pub`-Format | SSH-Wire ≠ libsodium | Signaturprüfung unmöglich |
| URL-Encoding | Umlaute im Pfad | **falscher Kettenbruch gegen die eigene Kette** |
| Umlaut-Metrik | `ord(c) > 0x400` | 0 % German, Antworten hatten Umlaute |
| Notice-Marker | „VERIFICATION" im Fließtext | Notice nicht verifizierbar |
| **Konsistenz-Parser** | **„JA ODER NEIN" gelesen als „NEIN"** | **Template-Echo als Verdikt** |
| **Korrektur-Audit** | **Korrektur gegen leere Begründung akzeptiert** | **falsche Supermajorität** |

**Sechs Instrument-Defekte. Alle sechs haben Falschbefunde erzeugt — nie
Falschfreiheit.**

> **Ein Instrument, das defekt ist, meldet Falschbefunde. Und ein Falschbefund,
> der eine Supermajorität behauptet, ist gefährlicher als jeder andere, weil er
> bindend wirkt.**

**Die Regel, die daraus folgt:**
> **Ein Quorum wird auf den Labels gezählt, die die Seats abgegeben haben.
> Korrekturen sind Kommentare zum Befund, nie Stimmen. Jede Korrektur wird
> gegen die Begründung des Seats geprüft und das Ergebnis der Prüfung wird
> mitveröffentlicht.**

---

## 6. WAS DAS KOSTET — ERLICH GEWERTET

**Ein ganzer Deliberationslauf (rund 3 Stunden Compute) war nicht bindend.**
Die Hardware-Lektion aus Record 004 (keine 7B-Modelle) hat die Quote auf
0 Fehler gebracht, und trotzdem war das Ergebnis unbrauchbar — nicht wegen
der Hardware, sondern wegen der Auswertung.

**Das ist der wichtigste Befund des ganzen Tages:** die *Erzeugung* des Befunds
war gut, die *Auswertung* war es nicht. Und die Auswertung hat **beinahe eine
Bindung erzeugt**, die inhaltlich falsch war: nach korrekter Neuberechnung steht
das Panel bei **(a) 5, (b) 6** — der Plurality liegt bei **(b)**, also bei der
Auffassung, dass der Aussetzungsvermerk **unzureichend** ist. Die gemeldete
Mehrheit (a) 9 war das Gegenteil der tatsächlichen Mehrheitsrichtung.

**Ein Gericht, das falsch entscheidet und es nicht merkt, ist gefährlicher als
ein Gericht, das gar nicht entscheidet.** Das Panel hat gemerkt — aber nur,
weil die Prüfschicht existierte.

---

## 7. WAS JETZT GILT

- **CALIBRATION-003 ist nicht bindend.** Es wird mit PROTOCOL NON-CONFORMANT
  markiert und an den Pool zurückgegeben.
- **LEF-E5 läuft im automatischen Cycle**, mit Priorität vor allen anderen
  Mächten: ein Finding-Integritätsfehler erklärt die anderen.
- **Die Auto-Notice nennt jetzt die tatsächliche Grundmacht** (E5 statt E2).
- **Die Roh- und die effektive Vote-Map werden beide publiziert.**

## Sacred hash
f5af425c
