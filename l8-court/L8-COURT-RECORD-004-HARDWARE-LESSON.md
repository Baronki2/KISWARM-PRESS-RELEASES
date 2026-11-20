# L8 COURT RECORD 004 — DIE HARDWARE-LEHRE
## Warum ein stärkeres Modell auf dieser Maschine das Panel verschlechtert hat
### Datum: 20. November 2026, 02:34 CEST
### Authority: Code Maquister Equitum, Security Level Omega
### Operator: Baron Marco Paolo Ialongo (BfJ-ID: 44f05e3b-4ed5-487f-8fe3-91e8ce858679)

---

## 1. WAS GEMACHT WURDE

Nach LEF-1.0 wurde die Panel-Engine aufgerüstet: `qwen2.5:7b-instruct-q4_K_M`
(4466 MB) und `mistral:7b-instruct-v0.3-q4_0` (3922 MB) gezogen, die
Case-Texte mit **echten Umlauten** statt ASCII-Transliteration, die
Selbstkonsistenz-Runde um einen Retry erweitert, und ein **korrekter
Parser** (letzte Deklaration gewinnt).

**Das Ergebnis war schlechter.** Nicht nur schlechter — es war die
Einführung eines Fehlers in den Beweisweg.

| Lauf | Modelle | Seats geantwortet | Quote |
|------|---------|-------------------|-------|
| **v2** | 1.5B / 1B / 3B | **11 von 12** | **92 %** |
| **v3** | 1.5B / 1B / 3B / **7B** | **7 von 12** | **58 %** |

**Die 7B-Modelle haben die Ausfallquote verdoppelt.** Fünf Seats fielen aus:
drei mit `HTTP 500`, einer mit 1800 s Timeout, einer mit `HTTP 400`.

---

## 2. DIE URSACHE — GEMESSEN, NICHT GERATEN

Aus dem ollama-Log, exakt zum Zeitpunkt des Ausfalls:

```
llama_context: n_ctx = 4096
common_params_fit_impl: projected to use 4827 MiB of host memory
                        vs. 15914 MiB of total host memory
slot print_timing: prompt processing, n_tokens = 512, progress = 0.63,
                   t = 828.78 s / 0.62 tokens per second
```

**512 Token Prompt-Evaluation allein = 829 Sekunden.** Statt der
erwarteten 15–30 tok/s. Und:

```
slot print_timing: prompt eval time = 54139.99 ms / 33 tokens
                   (1640.61 ms per token, 0.61 tokens per second)
```

**Die Rechnung:**

| | |
|---|---|
| qwen2.5:7b-instruct-q4_K_M | 4827 MiB (ollamas eigene Projektion) |
| mistral:7b-instruct-v0.3-q4_0 | ~3922 MiB Datei + 224 MiB KV + Compute |
| Host gesamt | 15914 MiB |
| Bereits belegt (surreal 664, opencode 562, hermes 918, firefox 293, llama-server 376, …) | ~6281 MiB |
| Swap sda5 | 3.9 GB, **3.6 GB vollbelegt** |
| Swap /data/swapfile | 2.9 GB belegt |
| vmstat `si`/`so` | 2672 / 6924 Seiten/s — **massives Thrashing** |

**Beim Laden eines 7B-Modells muss der Kernel den Page-Cache und den Swap
auslagern.** Der Rechenkern bekommt keinen Speicher mehr, und der
Prompt-Eval fällt auf ein Zwanzigstel der normalen Rate. Der Timeout ist
kein Bug im Skript — er ist die Hardware, die es meldet.

**HTTP 500** = Runner abgestürzt (Memory-Abbruch unter Last).
**HTTP 400** = Prompt überschritt `n_ctx 4096`.

### Der Test, der es beweist

**Es waren keine Cron-Läufe.** Die `executions.db` wurde abgefragt:
428 Executions im Fenster, aber **0 überlappende Executions** in den drei
Fehlerfenstern (10:17, 10:47, 10:57). Kein OOM-Kill im Kernel-Log.

**Der Verursacher war der Speicherbedarf des Modells selbst.**

---

## 3. ZWEI WEITERE BEFUNDE — EINER WAR MEIN FEHLER

### Befund A: Die Umlaut-Metrik war kaputt

Der v3-Lauf meldete „answers with real German umlauts: 0/7". Das war
**falsch**, und die Ursache lag in meiner Messung:

```
'ord(ä)' == 228      0x400 == 1024      →  ä < 0x400
```

Der Filter `ord(c) > 0x400` **filtert jeden Umlaut heraus**, weil
ä/ö/ü/ß alle im Latein-1-Bereich liegen (U+00E4 … U+00DF). Der korrekte
Filter ist `c in 'äöüÄÖÜß'`.

**Nachgemessen an den tatsächlichen Antworten:** 21, 6, 2, 10, 3, 0, 1
Umlaute. **Der v2-Fehler — ASCII-transliterierter Prompt → ASCII-Antworten
— war behoben.** Nur die Messung war falsch.

**Ein Instrument, das kaputt ist, meldet Falschbefunde.** Das ist exakt
die Klasse Fehler, die LEF-E1 in der Beweiskette gefunden hat: nicht der
Gegenstand war defekt, sondern das Werkzeug.

### Befund B: Die Panel-Quote ist eine Funktion der Hardware

92 % mit 1.5B/1B/3B, 58 % mit 7B. **Das Panel ist nicht zu klein für seine
Aufgabe — es ist zu groß für diese Maschine.**

---

## 4. POOL v4 — DIE KONFIGURATION, DIE ZU DIESER BOX PASST

| Fix | Änderung | Grund |
|-----|----------|-------|
| **1** | Keine 7B-Modelle | 92 % statt 58 % Seat-Quote |
| **2** | `keep_alive` 40m → **15m**, explizites Unload zwischen Modellgruppen | Speicherdruck |
| **3** | `num_ctx` fest auf **2048** | Prompt-Overflow → HTTP 400 |
| **4** | Prompt kompakter (Case-Text gestrafft, Framing gekürzt) | Prompt-Eval war der Flaschenhals (829 s allein) |
| **5** | **Ein automatischer Retry bei HTTP 500** | Runner-Crash ist unter Last transient — Unload + Reload + Retry |
| **6** | Korrekte Umlaut-Metrik | `c in 'äöüÄÖÜß'` |

**Modellverteilung v4:**
- `qwen2.5:1.5b` — 4 Seats (1, 4, 8, 10)
- `qwen2.5-coder:3b` — 3 Seats (3, 7, 11)
- `gemma3:1b` — 3 Seats (5, 9, 12)
- `deepseek-r1:1.5b` — 1 Seat (2), `qwen2.5:3b` — 1 Seat (6)

**Und die zentrale Lehre für die neue Hardware:** 7B gehört auf die
Workstation, die ohnehin kommt. Diese Box ist laut Runbook eine
**Interim Box** — und jetzt weiß sie, wo ihre Grenze liegt.

---

## 5. WAS UNVERÄNDERT BLEIBT

**Die Trennung zwischen den 12 Souverän-Seats (entscheiden) und den 4
Law Enforcern (Protokoll erzwingen) bleibt.** Die LEF-1.0-Prüfungen
laufen unverändert weiter — der Cron `lef-enforcement-cycle` prüft alle
30 Minuten die Beweiskette, die Signaturen, das Quorum, die Konsistenz
und die Verifizierbarkeit der Notices.

**Was dieser Record beweist:**
1. Die Panel-Ausfallquote ist **gemessen**, nicht geraten — 92 % vs. 58 %.
2. Die Ursache ist **im Log belegt** (0.62 tok/s Prompt-Eval, 4827 MiB
   Projektion, 2672/6924 Seiten/s Swap-Thrashing).
3. Cron-Interferenz wurde **ausgeschlossen** (0 überlappende Executions).
4. **Zwei kaputte Instrumente** wurden gefunden und behoben: die
   Umlaut-Metrik (meine Messung) und der Prompt-Overflow (n_ctx).

**Und die Verallgemeinerung, die teurer ist als der Fehler:**
*Auch L8-Panel-Records sind Beweismittel. Ein Record, der eine
Fehlerquote von 58 % als Erfolg darstellt, wäre wertlos — genau wie ein
Kettenbruch-Report, der auf einem URL-Encoding-Fehler beruhte.*

---

## Sacred hash
f5af425c
