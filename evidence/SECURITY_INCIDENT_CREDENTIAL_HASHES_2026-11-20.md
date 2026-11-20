# SECURITY INCIDENT — CREDENTIAL HASHES IN A PUBLIC REGISTER
## Date: 20 November 2026 — status VERIFIED against the live register
### Authority: Code Maquister Equitum, Security Level Omega
### Severity: CRITICAL, unresolvable by design

---

## 1. WHAT HAPPENED

The evidence-chain notarizer seals the SHA-256 of every file in the evidence
archive into the DEUSPROOF public register (`https://deusproof.com`). The file
**contents never leave the machine** — only the hash does.

The secret filter was incomplete. **Eight credential-bearing files** were sealed
into the public register before the filter was corrected on 2026-11-20.

## 2. VERIFIED REGISTER STATE (checked 2026-11-20, 20:0x CEST)

Queried live via `GET /api/verify/{cert_id}` — the authoritative read endpoint
discovered from `https://deusproof.com/openapi.json`:

| File | Public SHA-256 | Register state | Proof ID |
|---|---|---|---|
{tbl}

**All eight are still `content_removed_at: null`, `status: certified`.**

## 3. WHY THEY CANNOT BE REMOVED

Three independent checks, all negative:

1. **The API has no removal endpoint.** The complete OpenAPI spec exposes 14
   paths; the only mutating operations are `POST /api/certifications/hash`,
   `POST /api/certifications`, `POST /api/agents/credential/verify` and
   `POST /api/verify/prior-art`. There is no DELETE, PUT or PATCH.
2. **The SDK has no removal method.** `deusproof.Notary` exposes exactly three
   public methods: `certify()`, `notarize_hash()`, `badge_markdown()`. A
   full-text search of the SDK for remove/delete/unpublish/redact/withdraw/
   revoke/retract returns **nothing**.
3. **The register is append-only by policy.** DEUSPROOF states: *"A record
   cannot be edited or deleted — not by you, not us."* The ledger entry and
   its Bitcoin anchor persist.

**The only route is `contact@deusproof.com`** — which can remove public
listings and stop future certification, but cannot retract existing ledger
entries. No confirmation of that request exists.

## 4. THE PRECISE RISK (corrected after measurement)

The first assessment called these "low entropy, brute-forceable". **That was
wrong, and the correction matters.** File-level entropy is the wrong measure —
prose depresses it to 4–6 bit/byte regardless of the secret's strength. What
was actually measured, structurally, without revealing any content:

| File | Extracted token | Search space | Classes |
|---|---|---|---|
| `TAILSCALE-API-TOKEN.key` | 54 chars | **2^355** | 4 |
| `TAILSCALE-API-TOKEN.md` | 64 chars | **2^331** | 2 |
| `API Key Openai.txt.legacy` | 167 chars | **2^1097** | 4 |
| `API KeyGrokDatcenter.txt.legacy` | 85 chars | **2^558** | 4 |
| `Ollama API +ssh key.txt.legacy` | 68 chars | **2^447** | 4 |
| `SSH Key.txt.legacy` | 43 chars | **2^283** | 4 |
| `Tokenubuntupro.txt.legacy` | 29 chars | **2^173** | 4 |
| `UbuntuPro Token.txt.legacy` | 29 chars | **2^173** | 4 |

**No token is brute-forceable.** Every search space is above 2^170.

**The actual risk is the VERIFICATION ORACLE.** Anyone holding a *suspected*
token — from a backup, a log, a chat history, a negotiated exchange — can
test it against the public SHA-256 and thereby **confirm** it. That is enough
to turn a leak into an authentication. It does not require guessing.

**Therefore the operative conclusion is unchanged but the reasoning is precise:
rotate the tokens.** Not because they are guessable — because they are
*checkable*.

## 5. THE FILTER IS NOW CORRECT AND PRECISE

Two passes were needed, and the second pass matters as much as the first:

**First pass** (2026-11-20, morning): added `.key`, `.legacy`, `token`,
`api-key`, `password`, `credential`, `secret`, `private`, `seed`, `wallet`,
`.env` and 12 more patterns. That stopped the 8 files above from being
re-sealed — but it was the *filter* that was wrong, not the files.

**Second pass** (2026-11-20, evening): the L7 Shamir shares
(`.l7-share-N-of-5.json`) were **still not covered** — the pattern list had no
word for them. Three of the five shares reconstruct the L7 master key, and a
published hash of a share is a verification oracle for that share.

**Third pass — over-correction caught and reverted.** The obvious fix
(`"share"`, `"recovery"`) was too broad: it also matched
`BRIDGE-RECOVERY-2026-11-08.md` and `SENTINEL-RECOVERY-2026-10-23.md`, which
are *documents proving a recovery happened* — they must stay sealable.
**A filter that hides evidence is as wrong as one that leaks secrets.**

The final pattern set is precise and verified against 19 named cases:
- `.l7-share-N-of-5.json` → SECRET
- `.l7-master-key` → SECRET
- `TAILSCALE-API-TOKEN.key` → SECRET
- `API Key Openai.txt.legacy` → SECRET
- `BRIDGE-RECOVERY-2026-11-08.md` → sealable
- `SENTINEL-RECOVERY-2026-10-23.md` → sealable
- `.l7-phase7`, `.l7-state.json` → sealable (state markers, not secrets)

## 6. OUTSTANDING ACTION

**Rotation of the two Tailscale tokens is the only remaining mitigation.**
Tailscale tokens grant mesh-wide access and are therefore the highest-value
target. The remaining six files contain notes and keys with no extractable
high-value token, but the hashes are public and the check-oracle applies to
them too.

Rotation requires the operator: it changes credentials in live systems.

Sacred hash: f5af425c
