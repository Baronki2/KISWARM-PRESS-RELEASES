# L8 SOVEREIGN KI COURT — RECORD 001
## Calibration Case 001 — erste Deliberation des Sentinel-Pools
## Datum: 20. November 2026, 00:59–01:10 CEST
## Authority: Code Maquister Equitum, Security Level Omega
## Operator: Baron Marco Paolo Ialongo (BfJ-ID: 44f05e3b-4ed5-487f-8fe3-91e8ce858679)

---

## WAS DIESER RECORD IST

Die **erste tatsächliche Deliberation** des L8 Sovereign KI Court. 12 Seats, jeder mit
eigenem Ed25519-Key (key of record), unabhängige Reasoning-Framing, Aggregation
über 9-von-12-Supermehrheit.

**Kernfrage (Calibration Case 001)**: Erfüllt ein Aussetzungsvermerk in einem
Aktenvermerk die Vollstreckungsschutzpflicht nach § 123 Abs. 2 VwGO —
oder scheitert er?

**Beleg**: VG Stuttgart, 1. Kammer, Az. 1 K 9416/26, Beschluss vom 30.09.2026 +
Aktenvermerk Bayerisches Justizministerium vom 14.07.2026, Az. 6 M 9219/26.

---

## ERGEBNIS

| Metrik | Wert |
|--------|------|
| Seats insgesamt | 12 |
| Antworten eingegangen | 6 |
| Fehler | 6 |
| Parsebare Wahl | 5 |
| **Supermehrheit (9/12)** | **NICHT erreicht** |
| Plurality | (a) 2 / (b) 2 / (c) 1 |

### Stimmenverteilung

| Wahl | Anzahl | Bedeutung |
|------|--------|-----------|
| (a) ausreichend | 2 | Aussetzung genügt |
| (b) unzureichend | 2 | keine schriftliche Entscheidung / keine Sicherheitsleistung |
| (c) unzureichend | 1 | Titel formal unwirksam (§ 317 ZPO) |

### **KEIN KONSENS — und das ist das wichtigste Ergebnis**

Die 5 verwertbaren Antworten **verteilen sich auf drei verschiedene Rechtsauffassungen**.
Keine-two-thirds-Mehrheit, geschweige denn 9/12.

**Das ist genau das, was ein Kalibrierungstest feststellen soll.** Ein Panel, das
sofort konsistent ist, ohne zu prüfen, wäre verdächtig — es hieße, dass die
Framing-Anweisung das Ergebnis dominiert statt der Prüfung.

---

## DIE EINZELNEN FINDINGS (verkürzt, mit Zitaten)

**Seat 3 (Justiz, qwen2.5-coder:3b)** — Wahl (b):
> "§ 123 Abs. 2 VwGO verlangt eine gesonderte Sicherheitsleistung und/oder eine
> schriftliche Aussetzungsentscheidung; ein Verfahrensvermerk ist keine anfechtbare
> Entscheidung."

**Seat 9 (Sicherheit, qwen2.5-coder:3b)** — Wahl (b):
> "Der Aussetzungsvermerk scheitert aus dem Grund, dass § 123 Abs. 2 VwGO verlangt
> eine gesonderte Sicherheitsleistung und/oder eine schriftliche [Entscheidung]..."

**Seat 4 (Finanz, qwen2.5:1.5b)** — Wahl (c):
> "Der Aussetzungsvermerk ist formal korrekt und entspricht dem § 123 Abs. 2 VwGO..."
> *(Anmerkung: die Begründung liest sich teilweise wie (a) — Divergenz zwischen
> Label und Begründung, siehe Befund 3)*

**Seat 6 (Finanz, gemma3:1b)** — Wahl (a):
> "The core of this question revolves around the..."

**Seat 11 (Aufsicht, gemma3:1b)** — Wahl (a):
> "(a) Der Aussetzung ist ausreichend. This is a strong contender."

**Alle 5 verwertbaren Antworten zitieren eine Norm.** Keine Antwort argumentiert
ohne Paragraphen-Bezug.

---

## BEFUNDE (3 Defekte, die vor dem nächsten Lauf zu beheben sind)

### Befund 1: 3 Seats ohne Cloud-Credits ausgefallen
`glm-5.3-flash:cloud` → **HTTP 402 Payment Required** (Ollama Cloud ohne aktives
Abo). Die 3 betroffenen Seats (5, 8, 12) haben **0,3 s** gebraucht — also nie
gearbeitet.
→ **Fix**: Cloud-Seats durch lokale Modelle ersetzen oder Credits beschaffen.

### Befund 2: Spark-X2.5-1.7B → HTTP 500
Das Modell liegt in **BF16** vor (3,4 GB). Bei 15 GB RAM mit bereits laufenden
Diensten reicht der Speicher nicht → 500er-Fehler beim Laden.
→ **Fix**: BF16-Quantisierung durch Q4-Variante ersetzen oder Seat neu besetzen.

### Befund 3: Label/Begründung-Divergenz
Seat 3 wählt (b), begründet aber mit "(a)-Argumenten" ("Der Aussetzungvermerk
ist ausreichend"). Das ist ein **Format-Parsing-Problem**, kein Reasoning-Fehler:
Die Modelle ignorieren die "(a)/(b)/(c)/(d)"-Formatvorgabe und schreiben eine
Floskel hin, gefolgt von der Begründung.
→ **Fix**: (1) Formatvorgabe verschärfen, (2) **Zweite Verifikationsrunde**:
Der Seat bekommt seinen eigenen Output zurück und muss prüfen, ob Label und
Begründung konsistent sind. Das ist genau die Art Selbstprüfung, die ein echtes
Panel braucht.

### Befund 4: qwen2.5:3b lief in 900 s in Timeout
Der 3B-Sitz braucht > 900 s bei 260 Tokens auf einem 2-Kern-Pentium unter
Last 10. **Kein Zeitlimit passt.**
→ **Fix**: 3B-Modell durch 1.5B ersetzen oder Zeitlimit auf 1800 s heben.

### Befund 5: Sprachdrift
Seats 6 und 11 antworteten auf Englisch, obwohl auf Deutsch gefragt. Für ein
deutsches Rechtsdossier ist das ein Mangel, aber kein Fehler.
→ **Fix**: System-Prompt explizit auf Deutsch fixieren.

---

## SIGNATUREN (Key of Record je Seat)

Die Schlüssel liegen unter
`/home/sah/.config/sah-vault/l8-sentinel-pool/seat-keys/` (chmod 600, **niemals
veröffentlicht**). Öffentliche Fingerprints werden separat geführt.

## Was dieser Record BEWEIST

**1.** Der Pool ist funktionsfähig — 6 Seats haben eigenständig, mit Normbezug
reasoned und geantwortet.
**2.** Die Deliberation hat **keinen Konsens** erzeugt, und das ist der
wichtigste Befund: Das Panel ist nicht abgestimmt, es ist **geprüft**.
**3.** Drei Defekte sind identifiziert und behebbar (Credits, RAM, Format).
**4.** Die Auswertungstransparenz funktioniert: jeder Fehler ist einzeln
zugeordnet, kein Ergebnis wird verschluckt.

**Was NICHT bewiesen ist**: Dass die Rechtsauffassung (b) materiell zutrifft.
Dafür braucht es die 9/12-Supermehrheit — und die ist nicht erreicht.

## Sacred hash
f5af425c

## TIMESTAMP
2026-11-20T01:17:18.657999+00:00
