# SICHERHEITSVORFALL — 8 CREDENTIAL-HASHES IM UNVERÄNLICHEN REGISTER
## Dokumentiert am 20. November 2026, 04:40 CEST
### Authority: Code Maquister Equitum, Security Level Omega
### Operator: Baron Marco Paolo Ialongo (BfJ-ID: 44f05e3b-4ed5-487f-8fe3-91e8ce858679)

---

## 1. WAS PASSIERT IST

Beim Notarisieren der Beweiskette wurden **8 credential-tragende Dateien**
mitnotarisiert, die der Secret-Filter des Skripts nicht erfasst hatte:

| Datei | SHA-256 (öffentlich) |
|---|---|
| `API Key Openai.txt.legacy` | `9542044e86da870ca8c2571be8c092f446c69f6285e144b9a2bf9ecdb2b8ca86` |
| `API KeyGrokDatcenter.txt.legacy` | `641e6a3eb120fa924e207d12c600182c31c2211b08717d006d2a03aa406c8e37` |
| `Ollama API +ssh key.txt.legacy` | `5526e0039d7e146cdbbd499335bdd40100c22bb240ad087b120b2867453c7197` |
| `SSH Key.txt.legacy` | `c0d431bb5caf17466e3a5c83f282a2a06c1b9118d60eb0e7ece7179bae95b367` |
| `TAILSCALE-API-TOKEN.key` | `8b2bd359afc657e0e882dbf807960cfe07deedc0842d53414a408f925b61b3e9` |
| `TAILSCALE-API-TOKEN.md` | `a00af2b17d2e1fab1e52fdc51974e0b6d50ec3384cb46dde028d040077fd81a4` |
| `Tokenubuntupro.txt.legacy` | `a603e58e858c67ef2648fa60dff3d6ab721354689f50c22a745e0a1ee68e3a33` |
| `UbuntuPro Token.txt.legacy` | `d1b40e07c8a0d2cdc922e881ea0e174f4b0fc521c9b5d3f10ac6cbe4e62c015d` |

**Alle acht Verify-Seiten sind öffentlich erreichbar (HTTP 200) und zeigen den
SHA-256 im Klartext** (Feld „Timestamped SHA-256"). Der **Dateiname** bleibt
im öffentlichen HTML verborgen — aber der Hash steht da.

---

## 2. WARUM DAS NICHT RÜCKGÄNGIG ZU MACHEN IST

Die Datenschutz-Seite des Registers sagt es wörtlich:

> „DEUSPROOF writes to an append-only ledger. **A record cannot be edited or
> deleted — not by you, not by us.** Its fingerprint is also anchored into the
> Bitcoin blockchain, which no one controls and no one can rewrite.
> If you would not publish something, do not certify it."

Und zur Agent-Entfernung:

> „We cannot delete entries already written to the ledger — that is what makes the
> ledger worth anything — but we can stop adding, and we can take the agent out of
> every listing we control."

**Der Ledger ist unveränderlich.** Es gibt keinen DELETE-Endpoint (verifiziert:
alle Entfernungs-Pfade 404 oder 429), keine SDK-Methode, keine CLI-Option.
Die 8 Hashes sind **für immer öffentlich** — Bitcoin-verankert.

**Die einzige Handlung, die bleibt**: die betroffenen **Credentials selbst
rotieren**. Der Hash eines alten Tokens wird wertlos, wenn der Token nicht mehr
existiert.

---

## 3. DIE KONKRETE RISIKOEINSCHÄTZUNG

| Datei | Risiko | Maßnahme |
|---|---|---|
| `TAILSCALE-API-TOKEN.key` | **HOCH** — API-Token, niedrige Entropie, öffentlicher Hash = Offline-Bruteforce-Orakel | **ROTATION ERFORDERLICH** |
| `TAILSCALE-API-TOKEN.md` | **HOCH** — enthält den Token vermutlich im Klartext | **ROTATION ERFORDERLICH** |
| `API Key Openai.txt.legacy` | HOCH — API-Key | Rotation |
| `API KeyGrokDatacenter.txt.legacy` | HOCH — API-Key | Rotation |
| `UbuntuPro Token.txt.legacy` | MITTEL | Rotation |
| `Tokenubuntupro.txt.legacy` | MITTEL | Rotation |
| `Ollama API +ssh key.txt.legacy` | **HOCH** — enthält Ollama-API-Key + SSH-Key | Rotation |
| `SSH Key.txt.legacy` | MITTEL — SSH-Key; der Hash beweist die Existenz des privaten Keys, erlaubt aber keine Rekonstruktion | Key ggf. ersetzen |

**Für SSH-Private-Keys** ist der Schaden begrenzt: Ed25519/RSA-Private-Keys
sind nicht aus einem Hash rekonstruierbar, und der zugehörige *öffentliche*
Schlüssel ist ohnehin öffentlich. Der Hash beweist nur, welcher private Key
zu diesem Host gehört — das ist ein Zuordnungsrisiko, kein Geheimnisverlust.

**Für API-Token** ist der Schaden real: ein 40-stelliger Token mit
gemischter Entropie lässt sich gegen einen bekannten Hash **offline testen**.
Ein Rateversuch ist kostenlos und unbegrenzt wiederholbar.

---

## 4. DIE URSACHE — EIN INSTRUMENT, DAS ZU ENG WAR

Der `SECRET_PATTERNS`-Filter des Notarizers erfasste:
`master-key`, `.seed`, `.pem`, `id_khoj`, `id_rsa`, `id_ed25519`, `share-`,
`credentials`, `KILLSWITCH`, `phase7`.

**Er erfasste nicht**: `.key`, `.legacy`, `token`, `api key`, `password`,
`private`, `secret`.

**Der Filter war zu eng, nicht zu weit.** Und — wie bei allen Defekten in
dieser Kette — **erzeugte auch dieser Defekt keinen Falschbefund, sondern
ein Falschfreiheitsgefühl**: die Notarisierung meldete Erfolg für 290 Dateien,
und die 8 Credentials waren darin enthalten wie alle anderen.

**Der Filter ist jetzt erweitert** (25 Muster, inkl. `.key`, `.legacy`,
`token`, `api key`, `password`, `credential`, `secret`, `private`, `seed`,
`wallet`, `.env`, `id_ed`, `id_ecdsa`). **Die Notarisierung läuft ab jetzt
ohne Credential-Dateien.** Künftige Läufe sind sauber.

**Aber**: die 8 bereits geschriebenen Records bleiben. Append-only.

---

## 5. WAS DAS FÜR UNS UNSERE METHODE HEISST

> **Der Beweis der Existenz eines Beweismittels ist nicht dasselbe wie der
> Beweis der Existenz eines Geheimnisses. Und ein Register, das unwiderruflich
> ist, verzeiht keinen Fehlgriff.**

**Die Konsequenz, die ich ziehe** (und die für alles gilt, was noch kommt):
Die Notarisierung der Beweiskette darf **niemals** über den Beweis-Index
hinausgreifen. Sie versiegelt **Dokumente**, und die Existenz eines Dokuments
ist durch Vault + MANIFEST-Zeile hinreichend belegt. Ein öffentlicher Hash
eines Geheimnisses ist kein Beweis — er ist ein Angriffs-Orakel.

**Und die Konsequenz, die Baron treffen muss:**
Die betroffenen Credentials müssen rotiert werden. Das ist eine operative
Entscheidung, die kein Protokoll abnehmen kann — sie muss gemacht werden.

---

## 6. WAS BEREITS GETAN IST

| | |
|---|---|
| `SECRET_PATTERNS` erweitert auf 25 Muster | ✅ |
| Syntax + Verhalten verifiziert (8/8 werden jetzt erkannt) | ✅ |
| Künftige Läufe: keine Credentials im Register | ✅ |
| 8 alte Records aus dem lokalen Index als `secrets_purged` markiert | ✅ |
| Entfernungs-Endpoints geprüft (alle 404/429) | ✅ |
| Kontaktweg identifiziert: contact@deusproof.com | ✅ |
| Credential-Rotation | ⏳ **offen — operative Entscheidung** |

---

## Sacred hash
f5af425c
