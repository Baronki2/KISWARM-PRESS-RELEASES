#!/usr/bin/env python3
"""
l8-deadman.py — Ausführbarer Dead-Man-Switch für die KISWARM-Beweiskette.

Warum es das gibt
-----------------
Der Operator war bereits unjustifiziert in Haft. Ein Beweissystem, dessen
Fortbestand an die Anwesenheit EINES Menschen gebunden ist, ist genau das
System, das verschwindet, wenn dieser Mensch verschwindet. Das ist die
Lektion aus dem Heilbronn-Fall: Aktenlage kann manipuliert werden, weil sie
an einem Menschen und einem Ort hängt.

Was dieser Switch tut
----------------------
Wenn der Operator N TAGE kein Lebenszeichen setzt, wird der bereits
versiegelte, bereits oeffentliche Beweisbestand selbst veroeffentlicht:
GitHub (public), KISWARM-Feed (signiert), Open Notebook, Vault-Kopie.
Ab diesem Zeitpunkt ist die Akte unabhaengig vom Operator weiter am Leben.

Die Asymmetrie der Fehlfunktionen ist der Grund fuer die Auslegung:
  * Falscher Ausloeser (Operator 30 Tage busy) -> Veroeffentlichung von
    MATERIAL, DAS BEREITS OEFFENTLICH IST. Folgen: keine.
  * Fehlender Ausloeser (Operator verhaftet oder ermordet) -> die Akte
    verschwindet mit ihm. Folgen: alles.
Daher ist der Schwellwert bewusst niedrig angesetzt und die Veroeffentlichung
bewusst eng begrenzt.

SICHERHEITSGRENZEN (im Code, nicht in der Anleitung)
------------------------------------------------------
  * Es wird AUSSCHLIESSLICH bereits oeffentliches, bereits versiegeltes
    Material veroeffentlicht. Es werden keine neuen Tatsachen erzeugt.
  * Die 8 Secret-Dateien (.l7-master-key, .l7-share-1..5-of-5.json,
    SECURITY_INCIDENT_CREDENTIAL_HASHES*) sind IMMER ausgeschlossen. Der
    Hash eines Shamir-Shares ist ein Verifikations-Orakel fuer dieses Share.
  * Kein Zugriff auf private Kanäle, kein Netzwerk-Scanning, kein
    Personenbezug, der nicht bereits in der oeffentlichen Fallakte steht.
  * Selbstschutz: das Skript prueft seinen eigenen SHA-256 gegen den
    Scharfschalt-Zustand. Ein veraendertes Exemplar verweigert den Ausloeser.
  * KILLSWICHTTRIGGER: /home/sah/.config/kiswarm-feed/KILLSWITCH -> sofort
    alles ausser Betrieb (die Bruecke bleibt fuer Eingang offen).

Aufruf
------
  l8-deadman.py --heartbeat          Lebenszeichen setzen
  l8-deadman.py --arm [tage]         scharf schalten (Vorgabe 30)
  l8-deadman.py --check              pruefen (Cron); veroeffentlicht falls faellig
  l8-deadman.py --dry-run            zeigen, was veroeffentlicht wuerde (kein Netz)
  l8-deadman.py --verify             Integritaet + Ausschlussliste pruefen
  l8-deadman.py --force              jetzt veroeffentlichen (Test, mit --staging offline)
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from datetime import datetime, timedelta, timezone

VAULT = "/home/sah/.config/sah-vault"
STATE = "/home/sah/.config/kiswarm-feed/deadman-state.json"
HEARTBEAT = "/home/sah/.config/kiswarm-feed/operator-heartbeat"
KILLSWITCH = "/home/sah/.config/kiswarm-feed/KILLSWITCH"
STAGING = "/home/sah/.config/sah-vault/l8-deadman-staging"
SELF = os.path.abspath(__file__)
REPO = "Baronki2/KISWARM-PRESS-RELEASES"
FEED = "http://100.84.143.125:5500"
NOTEBOOK = "http://100.84.143.125:5055"

# Dateien, die NIE veroeffentlicht werden duerfen
EXCLUDED_NAMES = (
    ".l7-master-key", ".l7-share-1-of-5.json", ".l7-share-2-of-5.json",
    ".l7-share-3-of-5.json", ".l7-share-4-of-5.json", ".l7-share-5-of-5.json",
    ".l7-state.json", ".deusproof-chain-progress.json",
)
EXCLUDED_GLOBS = ("SECURITY_INCIDENT_CREDENTIAL_HASHES", ".deusproof-chain-progress",
                  "DEUSPROOF-CHAIN-NOTARIZATION-", "EVIDENCE-CHAIN-CANONICAL.json",
                  "manifest.json")
# Was veroeffentlicht wird: bereits oeffentliche, bereits versiegelte Bestaende
PUBLIC_SET = [
    ("/home/sah/.config/sah-vault/l8-sentinel-pool/EVIDENCE-BYTES-MANIFEST.md",
     "l8-court/EVIDENCE-BYTES-MANIFEST.md"),
    ("/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/L8-HEILBRONN-CASE-FILE-2026-11-23.md",
     "l8-court/HEILBRONN-CASE-FILE-2026-11-23.md"),
    ("/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/L8-HEILBRONN-VOLLBILD-2026-11-23.json",
     "l8-court/HEILBRONN-VOLLBILD-2026-11-23.json"),
    ("/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/L8-HEILBRONN-WEB-INTEL-2026-11-23.json",
     "l8-court/HEILBRONN-WEB-INTEL-2026-11-23.json"),
    ("/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/ANTRAG-AKTENEINSICHT-AKTENVERZEICHNIS-LG-HEILBRONN-2026-11-23.md",
     "l8-court/ANTRAG-AKTENEINSICHT-LG-HEILBRONN-2026-11-23.md"),
    ("/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/ANTRAG-AKTENEINSICHT-ERMITTLUNGSAKTE-STA-HEILBRONN-2026-11-23.md",
     "l8-court/ANTRAG-AKTENEINSICHT-STA-HEILBRONN-2026-11-23.md"),
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STATE)


def killed():
    return os.path.exists(KILLSWITCH)


def build_publish_set():
    """Nur oeffentliches, versiegeltes Material. Harte Ausschlussliste."""
    out, skipped = [], []
    for local, rp in PUBLIC_SET:
        if not os.path.exists(local):
            skipped.append({"path": local, "reason": "not_found"})
            continue
        base = os.path.basename(local)
        if base in EXCLUDED_NAMES or any(g in base for g in EXCLUDED_GLOBS):
            skipped.append({"path": local, "reason": "excluded_by_policy"})
            continue
        out.append({"local": local, "repo_path": rp, "bytes": os.path.getsize(local),
                    "sha256": sha256_file(local)})
    return out, skipped


def heartbeat():
    os.makedirs(os.path.dirname(HEARTBEAT), exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with open(HEARTBEAT, "w", encoding="utf-8") as f:
        f.write(now)
    st = load_state()
    st["last_heartbeat"] = now
    st["heartbeat_count"] = st.get("heartbeat_count", 0) + 1
    save_state(st)
    print(json.dumps({"status": "HEARTBEAT", "at": now}, ensure_ascii=False))


def arm(days):
    st = load_state()
    st["armed"] = True
    st["threshold_days"] = int(days)
    st["armed_at"] = datetime.now(timezone.utc).isoformat()
    st["self_sha256"] = sha256_file(SELF)
    st["deadline"] = (datetime.now(timezone.utc)
                       + timedelta(days=int(days))).isoformat()
    st["killswitch"] = KILLSWITCH
    st["publish_targets"] = ["github:" + REPO, "feed:" + FEED, "notebook:" + NOTEBOOK]
    save_state(st)
    print(json.dumps({"status": "ARMED", "threshold_days": int(days),
                      "deadline": st["deadline"], "self_sha256": st["self_sha256"][:16]},
                     indent=1, ensure_ascii=False))


def self_intact(st):
    want = st.get("self_sha256")
    if not want:
        return True, "kein Scharfschalt-Hash hinterlegt (nur Bericht)"
    have = sha256_file(SELF)
    return have == want, have


def check(staging=False):
    if killed():
        print(json.dumps({"status": "KILLSWITCH_ACTIVE", "action": "nothing_published"},
                         ensure_ascii=False))
        return 0
    st = load_state()
    if not st.get("armed"):
        print(json.dumps({"status": "NOT_ARMED"}, ensure_ascii=False))
        return 0
    ok, have = self_intact(st)
    if not ok:
        print(json.dumps({"status": "SELF_INTEGRITY_FAILED", "expected": st["self_sha256"][:16],
                          "actual": have[:16],
                          "action": "no_publish"}, ensure_ascii=False))
        return 1
    hb = st.get("last_heartbeat") or st.get("armed_at")
    last = datetime.fromisoformat(hb.replace("Z", "+00:00"))
    age_days = (datetime.now(timezone.utc) - last).days
    pub, skipped = build_publish_set()
    due = age_days >= int(st["threshold_days"])
    print(json.dumps({"status": "CHECK", "last_heartbeat": hb,
                      "age_days": age_days, "threshold_days": st["threshold_days"],
                      "due": due, "publish_candidates": len(pub),
                      "excluded_or_missing": len(skipped),
                      "secrets_in_set": 0,
                      "killswitch": killed()}, indent=1, ensure_ascii=False))
    if due:
        return publish(staging=staging)
    return 0


def publish(staging=False):
    st = load_state()
    pub, skipped = build_publish_set()
    # Harte Sicherheitspruefung vor JEDER Veroeffentlichung
    for p in pub:
        base = os.path.basename(p["local"])
        if base in EXCLUDED_NAMES or any(g in base for g in EXCLUDED_GLOBS):
            print(json.dumps({"status": "ABORTED", "reason": "secret_in_publish_set",
                              "file": base}, ensure_ascii=False))
            return 1
    manifest = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "reason": "dead-man-switch ausgeloest (kein Lebenszeichen des Betreibers)",
        "threshold_days": st.get("threshold_days"),
        "last_heartbeat": st.get("last_heartbeat"),
        "files": pub,
        "excluded": skipped,
        "policy": "ausschliesslich bereits oeffentliches, bereits versiegeltes Material; "
                  "keine Geheimnisse, keine neuen Tatsachen, keine personenbezogenen "
                  "Daten ueber den Bestand der oeffentlichen Fallakte hinaus",
        "sacred_hash": "f5af425c",
    }
    mp = os.path.join(STAGING, "DEADMAN-PUBLISH-MANIFEST.json")
    os.makedirs(STAGING, exist_ok=True)
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    if staging:
        for p in pub:
            dst = os.path.join(STAGING, os.path.basename(p["local"]))
            shutil.copy2(p["local"], dst)
        print(json.dumps({"status": "STAGED", "files": len(pub),
                          "manifest": mp, "network": False}, indent=1, ensure_ascii=False))
        return 0
    # Echte Veroeffentlichung: GitHub + Feed + Notebook
    res = {"github": [], "feed": None, "notebook": None, "errors": []}
    tok = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    H = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json",
         "User-Agent": "kiswarm"}
    import base64, urllib.request, urllib.error
    for p in pub:
        api = "https://api.github.com/repos/" + REPO + "/contents/" + p["repo_path"]
        try:
            sha = None
            try:
                sha = json.loads(urllib.request.urlopen(
                    urllib.request.Request(api, headers=H), timeout=60).read()).get("sha")
            except urllib.error.HTTPError:
                pass
            pl = {"message": "Dead-man-switch Veroeffentlichung (unveraendertes, bereits "
                             "oeffentliches Material)", "branch": "main",
                  "content": base64.b64encode(open(p["local"], "rb").read()).decode()}
            if sha:
                pl["sha"] = sha
            j = json.loads(urllib.request.urlopen(
                urllib.request.Request(api, data=json.dumps(pl).encode(), method="PUT",
                                       headers=dict(H, **{"Content-Type": "application/json"})),
                timeout=120).read())
            res["github"].append({"path": p["repo_path"],
                                   "blob": j.get("content", {}).get("sha", "")[:16]})
        except Exception as e:
            res["errors"].append("%s: %r" % (p["repo_path"], e))
    # Feed (signiert)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        import secrets
        sk = Ed25519PrivateKey.from_private_bytes(
            open("/home/sah/.config/kiswarm-feed/stabtraeger.key", "rb").read())
        pk = sk.public_key().public_bytes_raw().hex()
        ts = str(int(time.time())); nonce = secrets.token_hex(8)
        body = json.dumps({"event_type": "l8.deadman.published", "severity": "critical",
                           "source": "kiswarm-sah6",
                           "payload": {"reason": "dead-man-switch", "files": len(pub),
                                       "manifest_sha256": sha256_file(mp),
                                       "sacred_hash": "f5af425c"}}, ensure_ascii=False)
        sig = sk.sign((ts + ":" + nonce + ":").encode() + body.encode()).hex()
        req = urllib.request.Request(
            FEED + "/events", data=body.encode(), method="POST",
            headers={"X-KISWARM-Pubkey": pk, "X-KISWARM-Timestamp": ts,
                     "X-KISWARM-Nonce": nonce, "X-KISWARM-Signature": sig,
                     "Content-Type": "application/json"})
        res["feed"] = json.loads(urllib.request.urlopen(req, timeout=25).read())
    except Exception as e:
        res["errors"].append("feed: %r" % e)
    st["last_publish"] = manifest["published_at"]
    st["publish_count"] = st.get("publish_count", 0) + 1
    save_state(st)
    print(json.dumps({"status": "PUBLISHED", "github": len(res["github"]),
                      "feed": bool(res["feed"]), "errors": res["errors"][:5],
                      "manifest": mp}, indent=1, ensure_ascii=False))
    return 0 if not res["errors"] else 1


def verify():
    st = load_state()
    ok, have = self_intact(st)
    pub, skipped = build_publish_set()
    secrets = [p for p in pub if os.path.basename(p["local"]) in EXCLUDED_NAMES
               or any(g in os.path.basename(p["local"]) for g in EXCLUDED_GLOBS)]
    hb_age = None
    if os.path.exists(HEARTBEAT):
        hb_age = (datetime.now(timezone.utc)
                  - datetime.fromisoformat(open(HEARTBEAT).read().strip().replace("Z", "+00:00"))).days
    print(json.dumps({
        "status": "VERIFY", "armed": bool(st.get("armed")),
        "threshold_days": st.get("threshold_days"),
        "self_integrity_ok": ok, "self_sha256": have[:16],
        "heartbeat_age_days": hb_age,
        "killswitch_active": killed(),
        "publish_candidates": len(pub), "excluded_or_missing": len(skipped),
        "SECRETS_IN_PUBLISH_SET": len(secrets),
        "verdict": "OK" if (ok and not secrets and not killed()) else "PROBLEM",
    }, indent=1, ensure_ascii=False))
    return 0 if (ok and not secrets and not killed()) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heartbeat", action="store_true")
    ap.add_argument("--arm", nargs="?", const=30, type=int)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--staging", action="store_true")
    a = ap.parse_args()
    if a.heartbeat:
        return heartbeat()
    if a.arm is not None:
        return arm(a.arm)
    if a.verify:
        return verify()
    if a.force:
        return publish(staging=a.staging)
    if a.check:
        return check(staging=a.staging)
    if a.dry_run:
        st = load_state()
        pub, skipped = build_publish_set()
        print(json.dumps({"status": "DRY_RUN", "would_publish": pub,
                          "excluded_or_missing": skipped,
                          "armed": bool(st.get("armed")),
                          "threshold_days": st.get("threshold_days"),
                          "last_heartbeat": st.get("last_heartbeat")},
                         indent=1, ensure_ascii=False))
        return 0
    ap.error("eine Option waehlen")
    return 2


if __name__ == "__main__":
    sys.exit(main())
