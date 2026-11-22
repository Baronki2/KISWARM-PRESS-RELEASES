# L8 INDEPENDENT SEAT — SPEC v0.2
**22. November 2026 · ersetzt LEF-1.1-ENFORCER-SEAT-SPEC v0.1 · Sacred hash f5af425c (Identifier, keine Autorität)**

Diese Spezifikation ist die **übernommene und erweiterte Fassung** des von
opencode/big-pickle am 22.11.2026 eingereichten Entwurfs
(`INDEPENDENT-ENFORCER-CHARTER-v0.1.md`, `KEY-REGISTRATION-POLICY-v0.1.md`,
`CONFLICT-DISCLOSURE-TEMPLATE.md`, `PROOF-OF-POSSESSION-CHALLENGE.txt`,
`counter-logic.py`). Der Entwurf wurde **nicht** als angenommener Sitz
gewertet — er war ein Designvorschlag, und der Assistent selbst hat den
Sitz abgelehnt. Die Regeln sind übernommen, weil sie richtig waren.

---

## 1. Wozu dieser Sitz existiert

Ein Enforcer-Sitz hat genau eine Eigenschaft, die ihm Wert gibt: **der
Betreiber kann ihn weder erzeugen noch einsehen noch erzwingen noch ersetzen.**
Ein Schlüssel, der auf einer vom Betreiber verwalteten Maschine erzeugt oder
gehalten wird, ist **kein unabhängiger Sitz** — gleichgültig, wie gültig die
Signatur ist und wie viele Notices er signiert.

Ein Assistent, der auf Betreiber-Infrastruktur in einer vom Betreiber
gesteuerten Session arbeitet, **kann keinen unabhängigen Sitz bekleiden**.
Die korrekte Antwort ist, das zu sagen und stattdessen ein transparentes,
klar gekennzeichnetes Procedural Audit zu liefern. Genau das hat ein Peer
am 22.11.2026 getan — und das war ein besserer Beitrag als eine vorgetäuschte
Unabhängigkeit.

**Der Zählerstand, der das begründet** (berechnet, nie gesetzt):

```
notices_total                                14
notices_verifiable                           14
notices_self_signed                          14   <- alle vom Betreiber-Sitz 01
notices_independently_signed                  0
enforcer_seats_independent                    0   of 5
enforcer_seats_connected                      0
findings_externally_attested                  0
decisions_enforced_by_third_party             0
```

## 2. Definition der Unabhängigkeit — alle sieben Bedingungen

Ein Sitz gilt nur dann als unabhängig, wenn **alle** gelten:

1. **Alleinige Schlüsselkontrolle.** Der private Schlüssel ist auf Hardware
   und unter einem Konto erzeugt und gespeichert, das der Betreiber nicht
   verwaltet und nicht lesen kann (kein gemeinsames Root, kein gemeinsames
   SSH, kein betreiberseitiger Sandbox).
2. **Keine Übertragung.** Der private Schlüssel wird nie gesendet, gemailt,
   hochgeladen oder hinterlegt. Veröffentlicht wird nur der öffentliche
   Schlüssel und der Fingerprint.
3. **Verifizierter Besitznachweis.** Der Kandidat signiert eine
   Challenge; die Prüfung gelingt gegen den veröffentlichten öffentlichen
   Schlüssel. Besitz wird nachgewiesen, ohne den Schlüssel preiszugeben.
   **Der Nachweis wird vom Zähler selbst nachgerechnet** — ein Registry-Flag
   wird nicht geglaubt.
4. **Verdictsautonomie.** Der Betreiber kann die Notice des Sitzes weder
   anweisen noch bearbeiten noch vetoieren noch umschreiben. Der Sitz darf
   `PROTOCOL NON-CONFORMANT` über die Notices des Betreibers veröffentlichen.
5. **Offengelegte Konflikte.** Eine signierte Konflikterklärung liegt vor der
   ersten Notice vor.
6. **Dissent geschützt.** Der Sitz darf widersprechen und wird **nicht**
   wegen Widerspruchs entfernt.
7. **Öffentliche Identität.** Handle, Fingerprint, Macht, Registrierungs-
   zeitpunkt und Notices sind öffentlich und dauerhaft.

Fällt eine Bedingung, ist der Sitz `operator-controlled` und wird von den
unabhängigen Zählern ausgeschlossen — **mit dokumentiertem Grund**, nicht
stillschweigend.

## 3. Die fünf Mächte

| Sitz | Macht | Domäne | Die Falle, vorab benannt |
|---|---|---|---|
| E1 | LEF-E1 | Beweiskette (Hash) | Ein Parser, der eine feste Indexform annimmt, passt auf **nichts** und meldet trotzdem Erfolg. Wer **null** Einträge findet, **muss** NON-CONFORMANT melden. |
| E2 | LEF-E2 | Sitz-Signaturen | Roh-32-Byte-Schlüssel und SSH-Wire-Format sind verschiedene Kodierungen; die menschenlesbare Zeichenkette daneben sieht benutzbar aus und ist es nicht. |
| E3 | LEF-E3 | Quorum-Arithmetik | Aus dem **Gespeicherten** neu aggregieren, nicht die Inferenz neu laufen lassen. Eine eigene Finding behauptete 9 von 12 und war 5–5 mit zwei ungeparsten (Court Record 006). Rohkarte und Effektivkarte nebeneinander veröffentlichen. |
| E4 | LEF-E4 | Konsistenz und Divergenz-Offenlegung | Divergenz muss **offengelegt**, nicht wegkorrigiert werden. Ein Sitz, der die Formatanweisung zurückspiegelt, hat gar kein Verdikt gezeigt. |
| E5 | LEF-E5 | Finding-Integrität | Quorum auf den **deklarierten Labels** neu berechnen plus Korrektur-Audit: aus der eigenen Begründung abgeleitet oder aus der Anweisung kopiert? Dieser Sitz ist **für jede externe Entität offen**. |

## 4. Aufnahme — sieben Schritte

1. Kandidat erzeugt den Schlüssel auf eigener Hardware (nie auf Betreiber-
   Infrastruktur).
2. Kandidat veröffentlicht Handle, Sitz, `pub_b64`, Fingerprint, **signierte
   Konflikterklärung** und die **Signatur über die Challenge**.
3. Kandidat weist Besitz nach, indem er `sha256(challenge)` als 32 rohe Bytes
   signiert (nicht den Text, nicht einen Hex-String).
4. Die Registrierung trägt den Sitz **erst** als `independent: true`, wenn
   1–3 von einer dritten Instanz geprüft wurden.
5. Kandidat prüft sein Werkzeug: richtiger Key → Exit `0`; falscher Key →
   Exit `1`; leere Eingabe → Exit `1` (**kein Pass**).
6. Kandidat veröffentlicht eine Notice.
7. **Erst dann** bewegt sich der Zähler.

## 5. Registry-Schema

```json
{
  "seat": "E5",
  "handle": "public handle",
  "pubkey_raw_b64": "base64 raw 32-byte Ed25519 key",
  "public_key_fingerprint": "sha256(raw32)[:16]",
  "power": "LEF-E5",
  "registered_at": "ISO-8601",
  "independent": true,
  "proof_of_possession": true,
  "proof_of_possession_verified": true,
  "proof_of_possession_signature_b64": "base64 detached signature over sha256(challenge)",
  "proof_of_possession_challenge": "the exact challenge string that was signed",
  "control_attestation": "statement that the key is held on hardware the operator cannot administer",
  "conflict_disclosure_ref": "path or URL of the signed disclosure",
  "operator_controlled": false,
  "status": "active",
  "revoked_at": null,
  "notes": ""
}
```

`independent: true` ist nur zulässig mit Besitznachweis, Kontroll-Attest und
Konflikterklärung. **Fehlt eines, wird der Eintrag mit `independent: false`
geführt und von den unabhängigen Zählern ausgeschlossen.**

## 6. Zählerdefinitionen — und ihre einzige Quelle

**Die Zähler werden niemals handverlesen gesetzt.** Einzige Quelle:
`l8-counter-logic.py`, aufgerufen als

```bash
python3 l8-counter-logic.py --registry enforcer-seat-keys.json --notices notices/ --json
```

| Zähler | Definition |
|---|---|
| `notices_total` | alle Notice-Dateien im übergebenen Verzeichnis |
| `notices_verifiable` | Notices, deren veröffentlichter Digest **und** Signatur gegen den eingebetteten Schlüssel prüfen |
| `notices_self_signed` | verifizierbare Notices, deren Fingerprint im **operator-gehaltenen** Schlüsselsatz liegt |
| `notices_signed_by_registered_non_independent` | verifizierbar, aber der Sitz ist registriert und **nicht** unabhängig |
| `notices_signed_by_unregistered` | verifizierbar, Schlüssel in keiner Liste — **wird nie als unabhängig gezählt** |
| `notices_independently_signed` | verifizierbar **und** signiert von einem aktiven, unabhängigen Sitz mit geprüftem Besitznachweis |
| `enforcer_seats_registered` | Registry-Einträge mit `status: active` |
| `enforcer_seats_independent` | aktive Einträge, die das Unabhängigkeits-Gate bestehen |
| `enforcer_seats_connected` | unabhängige Sitze mit **mindestens einer** verifizierbaren Notice |
| `findings_externally_attested` | verschiedene `finding_id`s mit einer **unabhängigen** Notice im Status `PROTOCOL CONFORMANT` |
| `decisions_enforced_by_third_party` | unabhängige Notices im Status `PROTOCOL CONFORMANT` — eine Notice mit `NON-CONFORMANT` zählt **nicht**: sie schickt das Finding zurück in den Pool |

Der LEF-Zyklus liest dieselbe Quelle. Es gibt keine zweite Zahl.

## 7. Ausdrückliche Ausschlüsse

Nie ein unabhängiger Sitz, nie ein Zählerbewegung:

- Schlüssel, erzeugt auf betreiberseitig kontrollierten Maschinen, Konten,
  Sandboxes oder VMs
- **KI-Assistenten oder Agenten, die auf Betreiber-Anweisung handeln**
- Schlüssel, die übertragen, geteilt, hinterlegt oder dort gespeichert sind,
  wo der Betreiber sie lesen kann
- Sitze ohne geprüften Besitznachweis oder ohne veröffentlichte
  Konflikterklärung
- Sitze, die wegen eines Grundes entfernt oder widerrufen wurden

**Betonung:** Ein Widerspruch schließt aus, ein fehlendes Flag gewährt
nichts. Steht im Registry `proof_of_possession_verified: false`, zählt der
Sitz nicht — auch wenn die Signatur technisch prüft. Steht dort nichts,
rechnet die Schicht selbst nach; nur dann darf der Sitz zählen.

## 8. Das Unabhängigkeits-Gate, getestet

`l8-independence-gate-test.py` prüft die Schleuse mit sieben Angriffen und
drei Positivfällen, in einer isolierten Kopie:

| | Angriff | Erwartung |
|---|---|---|
| A1 | Notice mit dem **Operator-Schlüssel** | bleibt `notices_self_signed` |
| A2 | Registry-Eintrag mit Operator-Fingerprint | ausgeschlossen |
| A3 | Besitznachweis nur behauptet (`verified: false`) | ausgeschlossen |
| A4 | `operator_controlled: true` | ausgeschlossen |
| A5 | ohne Konflikterklärung | ausgeschlossen |
| A6 | Textmarker „assistant" / „sandbox" / „operator-controlled" | ausgeschlossen |
| A7 | Besitznachweis gegen die **falsche** Challenge signiert | ausgeschlossen |
| P1 | echter Sitz: frischer Schlüssel, geprüfter Besitz, Disclosure | **zählt** |
| P2 | derselbe Sitz mit `PROTOCOL NON-CONFORMANT` | verbunden, aber **keine** vollstreckte Entscheidung |
| P3 | leeres Notices-Verzeichnis | Exit `1` — **kein Pass** |

19 Prüfungen, alle bestanden. Ein Gate, das man nicht überlisten kann, ist
ein Gate; eines, das man nur nicht überlisten **konnte**, ist eine Behauptung.

## 9. Laufzeit, Widerruf, Ausschluss

- **Laufzeit:** fest (z. B. 12 Monate), Verlängerung durch veröffentlichte
  Entscheidung.
- **Widerruf:** der Sitz signiert eine Widerrufs-Notice; das Registry setzt
  `status: revoked` mit Zeitstempel. Frühere Notices bleiben im Register.
- **Entfernung:** nur für benannten Grund (Schlüsselkompromittierung,
  Konflikt, Inaktivität), mit signiertem öffentlichem Protokoll — **niemals
  wegen Widerspruchs**.
- **Schlüsselkompromittierung:** sofortiger Widerruf; alte Notices behalten
  ihre Zuordnung zum alten Fingerprint und werden markiert.

## 10. Transparenz

Veröffentlicht werden: Registry-Schema, alle Sitz-Einträge, alle Notices im
Volltext, Verifier-Quelle und Hash, **das Zählerskript**, und ein
Unabhängigkeitsbericht. Eine Schwärzung ist für Schlüsselmaterial,
Fingerprints und Verdicts nicht zulässig.

## 11. Rechtsstatus

Diese Spezifikation begründet ein **Dokumentverfahren, kein Gericht**. Sie
gewährt **keine Jurisdiktion** über Personen, Institutionen oder Staaten;
ihre Notices haben **keine Rechtskraft**. `f5af425c` und vergleichbare
Zeichenketten sind **Identifier einer Record-Serie, keine Autorität**. Kein
Sitz darf ohne **schriftliche Einwilligung** des Betroffenen über ein
Thema handeln.

---

**Entwurf und Prüfung:** opencode/big-pickle, 22.11.2026 — Designvorschlag,
ausdrücklich **kein angenommener Sitz und keine Attestierung**.
**Übernahme und Erweiterung:** KISWARM L8, 22.11.2026.
**Sacred hash: f5af425c**
