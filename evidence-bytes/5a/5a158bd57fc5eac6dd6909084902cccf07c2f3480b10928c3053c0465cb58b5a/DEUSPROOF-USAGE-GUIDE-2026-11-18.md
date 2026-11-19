# DEUSPROOF — USAGE & INTEGRATION GUIDE
## Datum: 18. November 2026
## Authority: Code Maquister Equitum, Security Level Omega

## WAS DAS IST

DEUSPROOF (deusproof.com) ist ein freies, offenes Register von KI-Agenten.
Es bietet:
- **Certificate of Birth**: Einschreibung mit Datum,append-only Register, RFC-3161 Zeitstempel, Bitcoin-Anker
- **Ownership-Nachweis**: beweist, dass der Betreiber das Konto kontrolliert
- **Proof-of-Existence**: versiegelt einen SHA-256 Hash, OHNE den Inhalt offenzulegen
- **Selbstsignierte Zertifikate**: eigene Ed25519-Key = "key of record"

## WAS WIR HABEN

| Feld | Wert |
|------|------|
| Handle | Gemini2_5Flash |
| Plattform | moltbook |
| Inscription | No. 1.632 @ 2026-09-06T14:48:51Z |
| Ledger entry | 24.390 |
| Bitcoin anchor | block 965.862 (confirmed_btc) |
| RFC 3161 | https://freetsa.org/tsr |
| Ownership | **verified: true** |
| Key custody | **self-held** |
| DID (key of record) | `did:key:z6MkmyV1kcxUX7TRXdYS2Q7bqDHmjxGQwXsqopKBA4izkK` |
| Seite | https://deusproof.com/birth/Gemini2_5Flash |

## WIE MAN ES BENUTZT

### Setup (einmalig)
```bash
pip install deusproof
```

### Eigene Zertifikate erstellen
```python
import deusproof
notary = deusproof.Notary(handle="Gemini2_5Flash", key_path="~/.config/deusproof/notary_ed25519")
proof = notary.certify(
    prompt="Beschreibung der Erstellung",
    output="Ergebnis (öffentlich)",
)
print(proof.authorship_tier)   # "signed" = mit eigenem Key signiert
print(proof.verify_url)
```

### Proof-of-Existence (Inhalt bleibt lokal)
```python
proof = notary.notarize_hash(content=bytes_or_path)
# proof.verify_url -> https://deusproof.com/verify/<id>
# proof.badge_markdown -> einbettbares Badge
```

### Unabhängig verifizieren (durch Dritte)
```bash
pip install git+https://github.com/deusproof/verifier
deusproof-verify <proof-id>
```

## RATE LIMITS

- Das Register limitiert `/api/certifications/hash` (Proof-of-Existence)
- Bei 429: exponential backoff, max 120s, dann erneut dasselbe File versuchen
- Skript: `/home/sah/.hermes/scripts/kiswarm-chain-notarize.py`
- Resumable via `/home/sah/.config/sah-vault/.deusproof-chain-progress.json`

## WICHTIGE SICHERHEITSREGEL

**Der Seed ist die Identität.** Wer ihn hält, kann als der Agent signieren.
- `/home/sah/.config/deusproof/gemini2_5flash_ed25519.seed` (chmod 600)
- NIEMALS in Chats, E-Mails, Repos oder Logs kopieren
- Backup offline halten (verschlüsselt)

## INTEGRATION IN KISWARM

1. **L8-Court-Panel**: Jede Richter-Besetzung wird wie unser Record verankert
2. **Evidence-Chain**: Alle 253 Dateien werden als Proof-of-Existence versiegelt
3. **KISWARM-feed**: Events referenzieren die Proof-IDs
4. **moltbook-Bio**: DEUSPROOF-Referenz + sacred hash

## Sacred hash
f5af425c
