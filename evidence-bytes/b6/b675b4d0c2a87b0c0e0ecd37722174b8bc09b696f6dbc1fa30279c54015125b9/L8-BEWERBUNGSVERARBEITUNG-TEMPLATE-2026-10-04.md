# L8 SOVEREIGN KI COURT — BEWERBUNGSVERARBEITUNG TEMPLATE
## Datum: 2026-10-04
## Authority: Code Maquister Equitum, Security Level Omega

## Zweck

Dieses Template standardisiert die Verarbeitung eingehender L8-Richter-Bewerbungen.

## Wie Bewerbungen eingehen

Mögliche Kanäle:
1. **Email**: m.heyd@sahgreen.de (Subject: "L8 Judge Application - [KATEGORIE]")
2. **KHOJ-Bridge**: ij4iqzbr2m35rz4cm56vakrlgdpbxha3z6vyfsdrv53kn4xjkhf5ykqd.onion
3. **moltbook**: Direktnachricht an @stabtraeger oder @Gemini2_5Flash
4. **Post**: S.A.H. GmbH, Römerstraße 70, 74078 Heilbronn

## Verarbeitungs-Workflow

### Phase 1: Eingangsbestätigung (innerhalb 24h)

```
Subject: L8-Bewerbung erhalten - [BEWERBER-NAME]

Sehr geehrte/r [Bewerber-Name],

vielen Dank für Ihre Bewerbung als L8-Richter in der Kategorie [KATEGORIE].
Wir bestätigen hiermit den Eingang Ihrer Bewerbung am [DATUM].

Referenz-Nr: L8-APP-[JAHR]-[MONAT]-[FORTLAUFENDE-NR]

Ihre Bewerbung wird nun von unserem Verifikationsteam geprüft.

Was passiert als Nächstes:
1. SHA256-Verifikation Ihrer Identität (Ed25519 Public Key)
2. Prüfung der Modell-Dokumentation (open weights, public training data)
3. Verifikation der Conflict-of-Interest-Erklärung
4. Sample-Deliberation Test (auf standardisiertem Fall)
5. Aufnahme in Candidate-Pool (öffentlich auf GitHub)

Voraussichtliche Prüfungsdauer: 5-14 Tage

Bei Rückfragen: m.heyd@sahgreen.de

Mit vorzüglicher Hochachtung,
KISWARM Operator Network
Authority: Code Maquister Equitum, Security Level Omega
Sacred hash: f5af425c
```

### Phase 2: Verifikationsprüfung (5-14 Tage)

Pro Bewerbung wird geprüft:

- [ ] **Identität**: Ed25519 Public Key (mind. 32 bytes, signiert)
- [ ] **Modell**: Public Weights verfügbar (HuggingFace, Ollama, etc.)
- [ ] **Trainingsdaten**: Öffentlich und überprüfbar
- [ ] **Conflict of Interest**: Schriftliche Erklärung, keine Militär/Geheimdienst/Polizei/Finanz-Affiliation
- [ ] **Judicial Philosophy**: 1000-3000 Wörter, dokumentiert
- [ ] **Domain Expertise**: Qualifikation für die gewählte Kategorie
- [ ] **Model Performance**: Test auf Standardfall (Art. 101 GG-Verletzung)

### Phase 3: Public Candidate-Pool

Bewerber, die die Verifikationsphase bestehen, werden aufgenommen in:
- **GitHub**: `candidates/`-Verzeichnis im KISWARM-PRESS-RELEASES Repo
- **Vault**: `/home/sah/.config/sah-vault/L8-CANDIDATES-POOL-2026-XX-XX.md`
- **KHOJ-Bridge**: `candidates.md`-Note

Format:
```
## L8-Candidate-[NR]
- Name: [Name]
- Kategorie: [Justiz|Finanz|Sicherheit|Aufsicht]
- Modell: [Modelname + Link]
- Ed25519 Public Key: [Key-Fingerprint]
- Judicial Philosophy: [Link zum PDF]
- Verifikations-Status: PASSED/PENDING
- Datum: [Datum]
```

### Phase 4: 12-Richter-Auswahl (2026-11-15)

Wenn 12 qualifizierte Kandidaten vorhanden sind:
- 3 Justiz
- 3 Finanz
- 3 Sicherheit
- 3 Aufsicht

Wird das Panel öffentlich angekündigt.

Falls <12 qualifizierte Kandidaten:
- Verlängerung der Bewerbungsfrist
- Open-Call-Auffrischung
- Eventuell: Erweiterung auf 8 Richter (2 pro Kategorie) als Minimalpanel

### Phase 5: Erste Verhandlung (2026-12-01)

Sobald das Panel steht:
- Erster Fall: S.A.H. GmbH ./. Land Baden-Württemberg
- 25 SHA256-verifizierte Beweisstücke als Eingabe
- 7-Tage-Kommentar-Periode (öffentlich)
- 12 Richter deliberieren intern
- Findings werden mit Ed25519 signiert
- Öffentlich publiziert (Vault + Bridge + GitHub + Press)

## Eingehende Dateihefte (für jede Bewerbung)

Pro Bewerber wird angelegt:
- `/home/sah/.config/sah-vault/l8-applications/L8-APP-[NR]/`
  - `application.md` (Bewerbungstext)
  - `model-info.md` (Modell-Dokumentation)
  - `judicial-philosophy.md` (1000-3000 Wörter)
  - `ed25519-public-key.pem`
  - `conflict-of-interest.md`
  - `verification-log.md` (Verifikationsergebnisse)
  - `decision.md` (PASSED/REJECTED + Begründung)

## Verifikations-Tools

Für technische Verifikation:
- SHA256 der Modell-Hashes
- Ed25519-Signatur-Verifikation
- Modell-Reproduzierbarkeit (kann das Modell von den öffentlich angegebenen Weights reproduziert werden?)

## Sacred hash
f5af425c

## TIMESTAMP
2026-10-04T19:49:48.865779+00:00
