# L8 COURT RECORD 011 — THE SEAL WAS ON THE PATH, NOT ON THE CONTENT
**21 November 2026 · KISWARM · Sacred hash f5af425c**

## Anlass

Die Verarbeitung des Hintergrundlaufs zu Court Record 010 meldete eine
Detailabweichung, die in der Meldung selbst unterging: der Notarizer meldete
`resuming: 491 already sealed`, obwohl **eine** Datei in derselben Minute
geändert worden war — der Runde-2-Record mit dem Nachtrag über die drei
externen Antworten.

Ein Instrument, das meldet „bereits versiegelt", während die Datei sich
gerade geändert hat, ist ein Instrument, das eine Frage beantwortet, die
nicht gestellt wurde.

## Der Befund

**Der Notarizer versiegelte den PFAD, nicht den INHALT.**

```python
done = {r["path"] for r in results ...}      # ← nur der Pfad
...
if path in done:
    continue                                  # ← überspringen
```

Eine Datei, die nach ihrer Versiegelung verändert wurde, wurde deshalb
**nie neu versiegelt**. Das öffentliche Register trug weiter den alten Hash,
der kanonische Index führte den neuen.

Gemessen (`kette-stale-records-pruefung.py`, über absolute Pfade, nicht über
Basisnamen — die erste Messung lief über Basisnamen und war deshalb wertlos,
weil MANIFEST.md und Co. in Vault-Root und Evidenzordner doppelt vorkommen):

| | vorher | nach der Reparatur |
|---|---|---|
| Index-Dateien ohne belegten Register-Record | **14 von 350** | 9 (alle bewusst ausgeschlossen) |
| Records, deren Datei sich seither geändert hat | **20** | 3 (alle selbstreferenziell) |

Die 14 zerfielen in 6 L7-Secret-Dateien, 2 Credential-Hash-Dokumente,
`MANIFEST.md` (selbstreferenziell) und **6 echte Lücken**:
`BERICHTIGUNG_ICC_ANKLAGE_2026_11_21.pdf`,
`ERGÄNZUNG_SOFTIGE_BESCHWERDE_793_ZPO_2026_11_21.pdf`,
`KERNARGUMENT_KORRIGIERTE_LINIE_2026_11_21.md`,
`KORREKTUR_LINIE_21_11_2026_VAULT_VERMERK.md`,
`L8_ENFORCER_ROUND2_2026_11_21.md`, `MANIFEST.md`.

## Warum es so lange unentdeckt blieb

Weil **E1 zwei von drei Instanzen verglich**.

Die Beweiskette existiert dreifach:

1. auf der Platte,
2. im kanonischen Index `EVIDENCE-CHAIN-CANONICAL.json`,
3. **versiegelt im öffentlichen DEUSPROOF-Register**.

E1 verglich (1) gegen (2) — beides aktuell, also 350/350 `CONFORMANT`.
Instanz (3) war nie Teil der Prüfung. Ein vollständiger Check über zwei von
drei Ausfertigungen ist ein vollständiger Check über eine veraltete Menge:
genau die Klasse aus Court Record 009 und 010, eine Ebene tiefer.

Und die vierte Instanz? Die **GitHub-Kopie** des kanonischen Index
(`evidence/EVIDENCE-CHAIN-CANONICAL.json`). Die wurde ebenfalls nie
maschinell gegen (2) verglichen.

## Die Reparatur — zwei Teile

**Teil 1: Das Siegel bindet den Inhalt.**

```python
done = {(r["path"], r.get("sha256")) for r in results ...}
...
if (path, h) in done:
    continue
```

Gleicher Inhalt → übersprungen. Geänderter Inhalt → **neu versiegelt**. Das
Register ist append-only, also bleibt der alte Record stehen und der neue
kommt dazu. Genau das ist die richtige Semantik: das Register belegt nicht
„diese Datei ist versiegelt", sondern „dieser Inhalt ist zu diesem Zeitpunkt
beglaubigt".

Ergebnis: 17 Pfade neu versiegelt, 491 → 508 Records, 0 Fehler, 0 deferred.

**Teil 2: E1 prüft alle Instanzen gegeneinander.**

Jeder Index-Eintrag wird jetzt gegen das öffentliche Register geprüft:

```
attested               341    im Register mit dem aktuellen Hash belegt
attested_excluded        9    bewusst nicht versiegelt (Begruendung unten)
attested_unattested      0    ← das ist die Zahl, die vorher fehlte
```

Ein Eintrag, der weder belegt noch bewusst ausgeschlossen ist, ergibt
`PROTOCOL NON-CONFORMANT` mit Namen. Die Liste der Ausschlüsse steht an
**einer** Stelle (`EXCLUDED_FROM_ATTESTATION` im Verifier) und ist im
Notarizer gespiegelt.

**Die Ausschlüsse und ihre Gründe:**

| Muster | Grund |
|---|---|
| `.l7-master-key`, `.l7-share-*` | Der öffentliche Hash eines Shamir-Shares ist ein Verifikations-Orakel für genau dieses Share; drei der fünf Shares rekonstruieren den L7-Masterschlüssel. |
| `SECURITY_INCIDENT_CREDENTIAL_HASHES*` | Ein veröffentlichter Hash eines Credential-Hashes ist ein Verifikations-Orakel für das Credential. |
| `manifest.md`, `deusproof-chain-progress`, `deusproof-chain-notarization`, `evidence-chain-canonical` | Selbstreferentielle Zustandsdateien: sie ändern sich **nach** ihrem eigenen Siegel. Ein veröffentlichter Hash, der nie mehr passt, sieht für einen Prüfer wie Manipulation aus — und ist es nicht. |

Überblockieren ist derselbe Defekt wie Leaking: ein Filter, der Beweise
versteckt, ist genauso falsch wie einer, der Secrets preisgibt. Deshalb ist
die Ausschlussliste benannt, begründet und an einer Stelle.

## Endstand

```
LEF-E1  declared 350  indexed 350  checked 350  match 350  skipped 0
        attested 341  excluded 9  unattested 0     coverage 100.0%
        → PROTOCOL CONFORMANT
LEF-E1R declared 234  indexed 234  checked 24      → Stichprobe, offengelegt
Übrige Mächte E2, E3, E4, E5: PROTOCOL CONFORMANT
Notices: 10/10 verifizierbar
Gesamtverdikt: PROTOCOL CONFORMANT (mit Offenlegung)
```

## Die Regeln

1. **Ein Siegel bindet den Inhalt, nicht den Pfad.** „Bereits versiegelt"
   ist nur eine Antwort auf die Frage „bereits mit DIESEM Inhalt versiegelt".
2. **Eine Kette mit drei Ausfertigungen wird über alle drei geprüft.**
   Ein Check über zwei von drei Instanzen ist ein Check über eine veraltete
   Menge — und der Defekt sitzt genau dort, wo niemand hinsieht.
3. **Ein erneuter Lauf, der „nichts zu tun" meldet, ist ein Befund, wenn
   sich in derselben Minute eine Datei geändert hat.** Das „resuming: N
   already sealed" war die Oberfläche, unter der der Fehler lag.
4. **Ein Ausschluss ist eine Begründung, keine Ausrede.** Jede Datei, die
   nicht versiegelt wird, steht mit Grund in einer benannten Liste.

## Die vierte Klasse an einem Abend

| Record | Klasse | Wie gefunden |
|---|---|---|
| 008 | grünes Licht über null Prüfungen | intern (Prüfung gegen leeren Index) |
| 009 | grünes Licht über einer Stichprobe, ohne Offenlegung | intern (Prüfung der eigenen Offenlegung) |
| 010 | Floor gegen die Parsermenge statt gegen die Dokumentmenge | **von außen** (eon_jack) |
| 011 | Siegel am Pfad statt am Inhalt | intern (Nachprüfung der Hintergrundmeldung) |

Alle vier sind dieselbe Familie: **ein Instrument, das eine Aussage macht,
ohne die Menge zu nennen, gegen die es steht.** Der common fix ist in allen
vieren derselbe: die Menge benennen, die Abdeckung melden und die Lücke
benennen, die bleibt.

## Dateien

- `~/.hermes/scripts/kiswarm-chain-notarize.py` — Siegel-Schlüssel (Pfad, sha256)
- `~/.hermes/scripts/lef-verifier.py` — `EXCLUDED_FROM_ATTESTATION`, Registerabgleich
- `~/.hermes/scripts/lef-enforcement-cycle-main.py` — Registerpfad
- `~/.hermes/scripts/kette-stale-records-pruefung.py` — die Messung
- `~/.hermes/scripts/kette-widerspruchspruefung.py` — der erste, grobe Abgleich
- `~/.config/sah-vault/DEUSPROOF-CHAIN-NOTARIZATION-2026-11-18.json` — 508 Records
