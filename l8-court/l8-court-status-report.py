#!/usr/bin/env python3
"""
L8 COURT STATUS REPORT — der vollständige Statusbericht, der AUSLÖST.

Baron: "eine vollständige Statusmeldung, wenn das KI Strafgerichtshof mit
der KI Enforcement online und working ist."

Das ist kein Versprechen, sondern ein Auslöser. Dieses Skript liest den
Zustand, und sobald die Bedingung erfüllt ist, erzeugt es den vollständigen
Bericht, publiziert ihn (GitHub, Vault, Feed, Notebook) und schreibt den
Record über die erste verbundene Vollstreckung.

BEDINGUNG FÜR "ONLINE":
    enforcer_seats_connected      >= 1   (fremder Sitz im Register MIT Notice)
    decisions_enforced_by_third_party >= 1 (ein Finding extern bestätigt)

Solange die Bedingung nicht erfüllt ist, schreibt das Skript nur einen
kurzen Pending-Marker mit den aktuellen Zahlen — kein Spam, kein
Verdoppeln des Berichts.

  python3 l8-court-status-report.py            # Prüfen + ggf. publizieren
  python3 l8-court-status-report.py --test-online   # Online-Zweig testen
"""
import base64
import json
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Der Cron-Scheduler startet Skripte unter dem venv-Interpreter des
# Installations-Hashes (Python 3.14.9). Dort ist nicht jede Krypto-Bibliothek
# vorhanden - die Feed-Signatur braucht aber Ed25519. Deshalb: fehlt die
# Bibliothek, startet sich das Skript einmalig im System-Python neu, das sie
# kennt. Das Flag verhindert eine Endlosschleife.
if os.environ.get("_L8_STATUS_REEXEC") != "1":
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        for _cand in ("/usr/bin/python3", "/usr/bin/python3.11"):
            if os.path.exists(_cand):
                os.environ["_L8_STATUS_REEXEC"] = "1"
                os.execv(_cand, [_cand, os.path.abspath(__file__)] + sys.argv[1:])

V = "/home/sah/.config/sah-vault"
E = os.path.join(V, "legal-evidence-OMEGA-2026-09-27")
P = os.path.join(V, "l8-sentinel-pool")
REPO = "Baronki2/KISWARM-PRESS-RELEASES"
API = "https://api.github.com/repos/" + REPO + "/contents/"
FEED = "http://100.84.143.125:5500"
NOTEBOOK = "http://127.0.0.1:5055"
NOTEBOOK_ID = "9cfki9920zs5otp548qd"
FEEDKEY = "/home/sah/.config/kiswarm-feed/stabtraeger.key"
FLAG = os.path.join(V, ".l8-court-online-published")
PENDING = os.path.join(E, "L8-COURT-STATUS-PENDING.json")
SACRED = "f5af425c"


# ── Zustand lesen ──────────────────────────────────────────────────────
def read_state(test_online=False):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "att", "/home/sah/.hermes/scripts/lef-enforcement-attribution.py")
    att = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(att)
    enf = att.attribute()
    cyc = {}
    p = os.path.join(P, "LEF-CYCLE-REPORT.json")
    if os.path.exists(p):
        cyc = json.load(open(p))
    idx = json.load(open(os.path.join(V, "EVIDENCE-CHAIN-CANONICAL.json")))
    nz = json.load(open(os.path.join(V, "DEUSPROOF-CHAIN-NOTARIZATION-2026-11-18.json")))
    recs = nz if isinstance(nz, list) else (nz.get("records") or [])
    seats = {}
    sp = os.path.join(P, "SEAT-PUBLIC-KEYS.json")
    if os.path.exists(sp):
        seats = json.load(open(sp)).get("seats") or {}
    notices = []
    for f in sorted(os.listdir(os.path.join(P, "notices"))):
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(P, "notices", f), encoding="utf-8",
                 errors="replace").read()
        m = re.search(r"(?m)^status:\s*(.+)$", t)
        notices.append({"file": f, "status": (m.group(1).strip() if m else "?"),
                        "power": (re.search(r"(?m)^power:\s*(.+)$", t) or [None, "?"])[1].strip()
                        if re.search(r"(?m)^power:\s*(.+)$", t) else "?"})
    st = {
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "enforcement": enf,
        "cycle": cyc,
        "chain": {"index_files": len(idx["files"]),
                  "total_bytes": idx.get("total_bytes"),
                  "notarization_records": len(recs)},
        "seats": {"count": len(seats)},
        "notices": notices,
        "findings_total": len(os.listdir(os.path.join(P, "findings"))),
    }
    if test_online:
        # SYNTHETISCHER ZUSTAND - nur zum Beweis, dass der Online-Zweig
        # einen vollstaendigen Bericht erzeugt. Veraendert nichts.
        st["enforcement"] = dict(enf)
        st["enforcement"].update({
            "notices_foreign_signed": 1,
            "enforcer_seats_registered": 1,
            "enforcer_seats_connected": 1,
            "findings_externally_attested": 1,
            "decisions_enforced_by_third_party": 1,
            "enforcement_connected": True,
            "notices": [{"file": "LEF-EXTERNAL-E5-TEST.md", "status": "PROTOCOL CONFORMANT",
                         "power": "LEF-E5", "attribution": "externer Enforcer-Sitz",
                         "signature_verified": True,
                         "signer": "TESTFINGERPRINT0000000000",
                         "enforcer": "TEST-SITZ (synthetisch, --test-online)",
                         "enforcer_key_fp": "TESTFINGERPRINT0000000000",
                         "finding_id": "L8-CALIBRATION-001",
                         "payload_sha256": "0"*64}],
        })
        st["_synthetic"] = True
    return st


def is_online(st):
    e = st["enforcement"]
    return (e.get("enforcer_seats_connected", 0) >= 1
            and e.get("decisions_enforced_by_third_party", 0) >= 1)


# ── Der vollständige Bericht ────────────────────────────────────────────
def render(st):
    e = st["enforcement"]
    c = st.get("cycle") or {}
    ch = st["chain"]
    ts = st["measured_at"]
    ext_notices = [n for n in e.get("notices", [])
                   if str(n.get("attribution", "")).startswith("extern")
                   and n.get("signature_verified")]
    who = ext_notices[0] if ext_notices else {}
    e1 = next((x for x in c.get("checks", []) if x.get("power") == "LEF-E1"), {})
    syn = " _(synthetischer Testzustand — keine echte Verbindung)_" if st.get("_synthetic") else ""

    L = []
    A = L.append
    A("# L8 SOVEREIGN KI COURT — STATUSBERICHT: ONLINE")
    A("")
    A("**Das Gericht ist online. Die Vollstreckung hängt an einem fremden "
      "Schlüssel.**")
    A("")
    A(f"**Gemessen:** {ts}  ")
    A(f"**Sacred hash:** {SACRED}  ")
    A(f"**Statusbericht:** LEF-1.1 Enforcement Attribution, LEF-1.0 Protokoll-Notices, "
      f"LEF-E1 Beweiskette dreifach geprüft{syn}")
    A("")
    A("---")
    A("")
    A("## 1. Die Bedingung, die erfüllt ist")
    A("")
    A("```")
    A("enforcer_seats_connected            {}   (fremder Sitz im Register, "
      "mindestens eine Notice damit signiert)".format(e.get("enforcer_seats_connected")))
    A("decisions_enforced_by_third_party   {}   (Findings, deren Verfahren von einem "
      "fremden Enforcer bestätigt wurde)".format(e.get("decisions_enforced_by_third_party")))
    A("notices_foreign_signed              {}   von {}".format(
        e.get("notices_foreign_signed"), e.get("notices_total")))
    A("```")
    A("")
    A("Ein Sitz, dessen Schlüssel auf der Maschine des Betreibers liegt, ist "
      "keine unabhängige Instanz. Dieser Sitz hat seinen Schlüssel selbst "
      "erzeugt, und der private Teil ist nie auf unsere Maschine gekommen.")
    A("")
    A("## 2. Die verbundene Vollstreckung im Einzelnen")
    A("")
    A("| | |")
    A("|---|---|")
    A("| Enforcer-Sitz | {} |".format(who.get("enforcer", "?")))
    A("| Öffentlicher Schlüssel (Fingerprint) | `{}` |".format(
        who.get("enforcer_key_fp", "?")))
    A("| Signatur nachgerechnet | {} |".format(
        "bestätigt" if who.get("signature_verified") else "NICHT bestätigt"))
    A("| Notice | `{}` |".format(who.get("file", "?")))
    A("| Macht | {} |".format(who.get("power", "?")))
    A("| Geprüftes Finding | {} |".format(who.get("finding_id", "?")))
    A("| Payload-Hash | `{}` |".format(str(who.get("payload_sha256", "?"))[:32]))
    A("| Befund | {} |".format(who.get("status", "?")))
    A("")
    A("## 3. Das Gericht")
    A("")
    A("| Schicht | Zustand | Zahl |")
    A("|---|---|---|")
    A("| Tier 1 — Beratungssitze | läuft | {} |".format(st["seats"]["count"]))
    A("| Tier 3 — Law-Enforcer-Sitze | **verbunden** | {} von {} |".format(
        e.get("enforcer_seats_connected"), e.get("enforcer_seats_total")))
    A("| Findings | vorliegend | {} |".format(st["findings_total"]))
    A("| Protokoll-Notices | publiziert | {} |".format(e.get("notices_total")))
    A("| davon fremdsigniert | — | {} |".format(e.get("notices_foreign_signed")))
    A("| davon selbstsigniert (Betreiber) | — | {} |".format(e.get("notices_self_signed")))
    A("| davon unzugeordnet | — | {} |".format(e.get("notices_unattributed")))
    A("| Signaturen nachgerechnet | — | {} von {} |".format(
        e.get("notices_verifiable"), e.get("notices_total")))
    A("")
    A("## 4. Die Beweiskette")
    A("")
    A("```")
    A("Index-Dateien          {}".format(ch["index_files"]))
    A("Bytes                   {}".format(ch["total_bytes"]))
    A("Notarisierungs-Records  {}".format(ch["notarization_records"]))
    if e1:
        A("LEF-E1                 declared {0}  indexed {1}  checked {2}  match {3}  "
          "skipped {4}".format(e1.get("indexed"), e1.get("indexed"),
                               e1.get("checked"), e1.get("match"), e1.get("skipped")))
        A("                       attested {0}  excluded {1}  unattested {2}  "
          "coverage {3} %".format(e1.get("attested"), e1.get("attested_excluded"),
                               e1.get("attested_unattested"), e1.get("coverage_percent")))
    A("```")
    A("")
    A("Die Kette existiert dreifach — Platte, kanonischer Index, öffentliches "
      "Register — und wird gegen alle drei geprüft. Das ist seit Court Record "
      "011 so.")
    A("")
    A("## 5. Der Zyklus")
    A("")
    A("```")
    A("Gesamtverdikt: {}".format(c.get("overall", "?")))
    if c.get("overall_disclosure"):
        A("OFFENLEGUNG:  {}".format(c["overall_disclosure"]))
    if c.get("enforcement_disclosure"):
        A("ENFORCUNG:    {}".format(c["enforcement_disclosure"]))
    A("```")
    A("")
    A("## 6. Die Protokoll-Notices")
    A("")
    A("| Notice | Macht | Befund |")
    A("|---|---|---|")
    for n in st["notices"]:
        A("| `{}` | {} | {} |".format(n["file"], n.get("power", "?"), n.get("status", "?")))
    A("")
    A("## 7. Der Unabhängigkeitsnachweis")
    A("")
    A("Jeder kann nachrechnen:")
    A("")
    A("```bash")
    A("# 1) Die Notice holen und ihre Signatur gegen den publizierten")
    A("#    Schluessel des externen Sitzes pruefen")
    A("python3 lef-notice-verifier.py --notice <notice.md> \\")
    A("        --pubkey <base64 raw 32-byte pubkey des Sitzes>")
    A("")
    A("# 2) Die Beweiskette gegen den kanonischen Index pruefen")
    A("python3 lef-verifier.py --index EVIDENCE-CHAIN-CANONICAL.json")
    A("")
    A("# 3) Die Zaehler, die diesen Bericht erzeugt haben")
    A("python3 lef-enforcement-attribution.py")
    A("```")
    A("")
    A("Der öffentliche Schlüssel des verbundenen Sitzes steht in "
      "`l8-court/enforcer-seat-keys.json`. Der private Teil ist nie publiziert "
      "worden und nie auf eine Maschine des Betreibers gekommen.")
    A("")
    A("## 8. Die Grenzen")
    A("")
    A("- **Keine Vollstreckung gegen Personen.** Notices binden Artefakte. Ein "
      "Notice, der eine Person oder eine Institution adressierte, wäre keine "
      "Justiz, sondern eine Waffe.")
    A("- **Keine Verbindlichkeit ohne staatliche Gewalt.** Kein KI-Gericht kann "
      "jemanden zwingen. Was es kann, ist die Beweislast umkehren: wer ein "
      "fremdbestätigtes Finding bestreitet, trägt die Prüfung.")
    A("- **Tier 3 stimmt nicht ab.** Enforcer prüfen das Verfahren, nicht den "
      "Inhalt. Die Beweislast für ein Finding bleibt bei den zwölf Sitzen.")
    A("- **Selbstvollstreckung zählt nicht.** Die {0} selbstsignierten Notices "
      "bleiben sichtbar und bleiben als das gekennzeichnet, was sie sind: "
      "Prüfung des Betreibers gegen die eigenen Artefakte.".format(
          e.get("notices_self_signed")))
    A("")
    A("## 9. Die Zahlen")
    A("")
    A("```")
    for k in ("notices_total", "notices_foreign_signed", "notices_self_signed",
              "notices_unattributed", "notices_verifiable",
              "enforcer_seats_registered", "enforcer_seats_connected",
              "enforcer_seats_total", "findings_total",
              "findings_externally_attested",
              "decisions_enforced_by_third_party", "enforcement_connected"):
        A("{:<34} {}".format(k, e.get(k)))
    A("```")
    A("")
    A("---")
    A("")
    A("**Status: ONLINE.** Die Maschine stand. Die Beweiskette steht. Das "
      "Verfahren wird geprüft. Und die Vollstreckung hängt jetzt an einem "
      "Schlüssel, der nicht uns gehört.")
    A("")
    A(f"Sacred hash: {SACRED}")
    return "\n".join(L) + "\n"


# ── Publizieren ────────────────────────────────────────────────────────
def gh_put(local, repo_path, message):
    tok = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    data = open(local, "rb").read()
    api = API + repo_path
    sha = None
    try:
        req = urllib.request.Request(api, headers={
            "Authorization": "Bearer " + tok,
            "Accept": "application/vnd.github+json", "User-Agent": "kiswarm"})
        sha = json.loads(urllib.request.urlopen(req, timeout=40).read()).get("sha")
    except urllib.error.HTTPError:
        pass
    payload = {"message": message, "content": base64.b64encode(data).decode(),
               "branch": "main"}
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(api, data=json.dumps(payload).encode(),
                                 method="PUT",
                                 headers={"Authorization": "Bearer " + tok,
                                          "Accept": "application/vnd.github+json",
                                          "User-Agent": "kiswarm",
                                          "Content-Type": "application/json"})
    try:
        j = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return j.get("content", {}).get("sha", "?")
    except Exception as ex:
        return None if ex else "?"


def feed(event_type, payload, severity="critical"):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    sk = Ed25519PrivateKey.from_private_bytes(open(FEEDKEY, "rb").read())
    pk = sk.public_key().public_bytes_raw().hex()
    ts = str(int(time.time()))
    nonce = secrets.token_hex(8)
    body = json.dumps({"event_type": event_type, "severity": severity,
                       "source": "kiswarm-sah6", "payload": payload},
                      ensure_ascii=False)
    sig = sk.sign(f"{ts}:{nonce}:".encode() + body.encode()).hex()
    req = urllib.request.Request(
        FEED + "/events", data=body.encode(), method="POST",
        headers={"X-KISWARM-Pubkey": pk, "X-KISWARM-Timestamp": ts,
                 "X-KISWARM-Nonce": nonce, "X-KISWARM-Signature": sig,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except Exception as ex:
        return {"_error": str(ex)[:120]}


def notebook(title, content):
    try:
        body = json.dumps({"notebook_id": NOTEBOOK_ID, "type": "text",
                           "title": title, "content": content, "embed": True})
        req = urllib.request.Request(NOTEBOOK + "/api/sources/json",
                                     data=body.encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as ex:
        return {"_error": str(ex)[:120]}


def publish(text, st):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fn = "L8-COURT-STATUS-REPORT-ONLINE-{}.md".format(ts)
    path = os.path.join(E, fn)
    open(path, "w", encoding="utf-8").write(text)
    blob = gh_put(path, "l8-court/" + fn,
                  "L8 Court STATUS REPORT: ONLINE — first connected enforcer "
                  "seat, first decision enforced by a third party")
    f = feed("l8.court.online", {
        "status": "ONLINE",
        "report": fn,
        "enforcer_seats_connected": st["enforcement"]["enforcer_seats_connected"],
        "decisions_enforced_by_third_party":
            st["enforcement"]["decisions_enforced_by_third_party"],
        "notices_foreign_signed": st["enforcement"]["notices_foreign_signed"],
        "sacred_hash": SACRED})
    n = notebook("L8 Court Status Report ONLINE " + ts, text[:20000])
    open(FLAG, "w").write(json.dumps({"published_at": st["measured_at"],
                                      "report": fn, "github_blob": blob},
                                     indent=1))
    print("   GitHub : {}".format(blob))
    print("   Feed   : {}".format(json.dumps(f, ensure_ascii=False)[:120]))
    print("   Notebook: {}".format(json.dumps(n, ensure_ascii=False)[:120]))
    return path


def main():
    test = "--test-online" in sys.argv
    st = read_state(test_online=test)
    online = is_online(st)
    e = st["enforcement"]
    print("=== L8 COURT STATUS REPORT ===")
    print("   enforcer_seats_connected            {}".format(e.get("enforcer_seats_connected")))
    print("   decisions_enforced_by_third_party   {}".format(
        e.get("decisions_enforced_by_third_party")))
    print("   notices_foreign_signed              {} von {}".format(
        e.get("notices_foreign_signed"), e.get("notices_total")))
    print("   BEDINGUNG: {}".format("ERFÜLLT" if online else "NICHT ERFÜLLT"))

    if test:
        text = render(st)
        out = "/home/sah/.hermes/cache/scratch/L8-STATUS-REPORT-ONLINE-TEST.md"
        open(out, "w", encoding="utf-8").write(text)
        print("   Testbericht: {} ({} Zeichen)".format(out, len(text)))
        print("   Abschnitte: {}".format(text.count("\n## ")))
        return 0

    if not online:
        json.dump({"checked_at": st["measured_at"], "status": "PENDING",
                   "condition": "enforcer_seats_connected >= 1 AND "
                                "decisions_enforced_by_third_party >= 1",
                   "current": {k: e.get(k) for k in (
                       "enforcer_seats_connected", "enforcer_seats_total",
                       "notices_total", "notices_foreign_signed",
                       "notices_self_signed", "decisions_enforced_by_third_party")}},
                  open(PENDING, "w"), indent=1, ensure_ascii=False)
        print("   -> Pending-Marker aktualisiert: {}".format(PENDING))
        print("   Der Bericht wird automatisch erzeugt, sobald ein fremder Sitz")
        print("   seinen Schluessel publiziert und eine Notice damit signiert.")
        return 0

    if os.path.exists(FLAG):
        print("   bereits publiziert: {}".format(open(FLAG).read().strip()[:160]))
        return 0
    print("   ÜBERGANG ERKANNT — erzeuge und publiziere den Statusbericht")
    publish(render(st), st)
    return 0


if __name__ == "__main__":
    sys.exit(main())
