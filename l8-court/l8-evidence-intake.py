#!/usr/bin/env python3
"""
l8-evidence-intake.py — Aufnahme physischer/offizieller Beweismittel in die Kette.

Warum es das gibt
-----------------
Der Korpus kann die Urheberschaft eines Dokuments nicht zuverlaessig bestimmen
(OCR-Fragmente, Scan ohne Textebene). Deshalb wird sie hier NICHT geraten,
sondern als PROVENIENZ erfasst: wer hat das Dokument, wann, woher, in welcher
Eigenschaft (Original/Kopie/Abschrift/Scan), und wer hat es uebergeben.

Jede aufgenommene Urkunde erhaelt:
  * SHA-256 des Inhalts (Bit-identisch, nicht des Dateinamens)
  * Provenienzblock (Quelle, Zeitpunkt, Uebergabe, Verwahrung)
  * einen Eintrag im kanonischen Index -> Notarisierung -> Feed
  * eine Blackout-Referenz, damit spaeter der Abgleich mit dem Aktenverzeichnis
    moeglich ist

Das ist die Grundlage, auf der die Aussage "sie haben meine Beweise
schwarzgelassen" ueberhaupt pruefbar wird: ein Beweismittel, das mit
Empfangsbeleg eingereicht wurde, aber im Aktenverzeichnis fehlt.

Aufruf
------
  l8-evidence-intake.py --file <pfad> --title "<Titel>" --kind original|copy|transcript|scan \
      --source "<woher>" --acquired-at "<ISO>" --acquired-by "<wer>" \
      --submitted-to "<Empfänger>" --submitted-on "<ISO>" --receipt-id "<Beleg-Nr>" \
      [--exhibit-id "<Anlage-Nr des Verzeichnisses>"] [--dossier-id HEILBRONN-KISWARM]

  l8-evidence-intake.py --list
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, secrets, shutil, sys, time
from datetime import datetime, timezone

VAULT = "/home/sah/.config/sah-vault"
INTAKE_DIR = os.path.join(VAULT, "l8-intake")
LEDGER = os.path.join(INTAKE_DIR, "intake-ledger.jsonl")
INDEX = os.path.join(VAULT, "EVIDENCE-CHAIN-CANONICAL.json")
SCRIPTS = "/home/sah/.hermes/scripts"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_ledger():
    if not os.path.exists(LEDGER):
        return []
    out = []
    for line in open(LEDGER, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def rebuild_private_chain():
    """Baut die private Kette reproduzierbar aus dem Ledger.
    Das Ledger ist die Wahrheit, die Kette ist das Siegel darueber."""
    pchain = os.path.join(INTAKE_DIR, "PRIVATE-CHAIN.json")
    entries = load_ledger()
    sealed, prev = [], "genesis"
    for e in entries:
        body = json.dumps({"intake_id": e["intake_id"], "sha256": e["sha256"],
                           "bytes": e["bytes"], "title": e["title"],
                           "provenance": e["provenance"], "submission": e["submission"]},
                          ensure_ascii=False, sort_keys=True)
        seal = hashlib.sha256((prev + "|" + body).encode()).hexdigest()
        sealed.append({**e, "seal": seal, "prev_seal": prev})
        prev = seal
    chain = {"chain": "l8-private-intake", "entries": sealed,
             "sealed": [e["seal"] for e in sealed], "rebuilt_from": "intake-ledger.jsonl",
             "note": "Private Kette. NICHT veroeffentlichen: die Hashes privater Originale "
                     "sind Brute-Force-Orakel. Der oeffentliche Index bleibt unberuehrt."}
    os.makedirs(INTAKE_DIR, exist_ok=True)
    tmp = pchain + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(chain, f, indent=1, ensure_ascii=False)
    os.replace(tmp, pchain)
    return chain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--title")
    ap.add_argument("--kind", default="copy")
    ap.add_argument("--source")
    ap.add_argument("--acquired-at")
    ap.add_argument("--acquired-by")
    ap.add_argument("--submitted-to")
    ap.add_argument("--submitted-on")
    ap.add_argument("--receipt-id")
    ap.add_argument("--exhibit-id")
    ap.add_argument("--dossier-id", default="HEILBRONN-KISWARM")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    os.makedirs(INTAKE_DIR, exist_ok=True)
    if a.list:
        rows = load_ledger()
        print("  Aufgenommene Beweismittel: {}".format(len(rows)))
        for r in rows:
            sub = r.get("submission", {}) or {}
            print("  {:22s} {:9s} {:38s} {}  Empfang: {}".format(
                r.get("exhibit_id") or "-", r.get("kind", "?"), (r.get("title") or "")[:38],
                (r.get("sha256") or "")[:12],
                "{} / {}".format(sub.get("submitted_to") or "-",
                                 sub.get("submitted_on") or "-")[:34]))
        return 0

    if not a.file:
        ap.error("--file erforderlich")
    if not os.path.exists(a.file):
        print(json.dumps({"status": "ERROR", "reason": "file_not_found: " + a.file},
                         ensure_ascii=False))
        return 3

    sha = sha256_file(a.file)
    size = os.path.getsize(a.file)
    now = datetime.now(timezone.utc).isoformat()
    rows = load_ledger()
    for r in rows:
        if r["sha256"] == sha:
            rebuild_private_chain()
            print(json.dumps({"status": "ALREADY_IN_CHAIN", "sha256": sha,
                              "intake_id": r["intake_id"], "title": r["title"],
                              "chain": "PRIVATE (unveraendert, neu versiegelt)"},
                             ensure_ascii=False))
            return 0

    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(a.file))[:80]
    dest = os.path.join(INTAKE_DIR, sha[:16] + "_" + safe)
    shutil.copy2(a.file, dest)

    intake_id = "INTAKE-" + sha[:12]
    rec = {
        "intake_id": intake_id,
        "dossier_id": a.dossier_id,
        "exhibit_id": a.exhibit_id,
        "title": a.title or os.path.basename(a.file),
        "kind": a.kind,
        "sha256": sha,
        "bytes": size,
        "original_path": a.file,
        "stored_path": dest,
        "provenance": {
            "source": a.source or "nicht angegeben",
            "acquired_at": a.acquired_at or now,
            "acquired_by": a.acquired_by or "nicht angegeben",
            "method": "manuelle Aufnahme durch den Betreiber",
        },
        "submission": {
            "submitted_to": a.submitted_to,
            "submitted_on": a.submitted_on,
            "receipt_id": a.receipt_id,
            "receipt_present": bool(a.receipt_id),
        },
        "intake_at": now,
        "sacred_hash": "f5af425c",
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # PRIVATE KETTE: die aufgenommenen Belege gehen NICHT in den oeffentlichen
    # kanonischen Index. Grund: der oeffentliche Index wird veroeffentlicht;
    # ein Hash eines privaten Originals darin ist ein Brute-Force-Orakel
    # (Vorlage + Variablen genuegen). Die privaten Belege werden stattdessen
    # in einer eigenen, lokalen Hashkette versiegelt - mit Verkettung: jeder
    # Eintrag versiegelt den Siegelwert des Vorgaengers.
    # Die Kette wird REPRODUZIERBAR aus dem Ledger gebaut: das Ledger ist die
    # Wahrheit, die Kette ist das Siegel darueber. So kann ein Dublettentreffer
    # die Kette nicht unversiegelt lassen.
    pchain = os.path.join(INTAKE_DIR, "PRIVATE-CHAIN.json")
    entries = load_ledger()
    sealed, prev = [], "genesis"
    for e in entries:
        body = json.dumps({"intake_id": e["intake_id"], "sha256": e["sha256"],
                           "bytes": e["bytes"], "title": e["title"],
                           "provenance": e["provenance"], "submission": e["submission"]},
                          ensure_ascii=False, sort_keys=True)
        seal = hashlib.sha256((prev + "|" + body).encode()).hexdigest()
        sealed.append({**e, "seal": seal, "prev_seal": prev})
        prev = seal
    chain = {"chain": "l8-private-intake", "entries": sealed, "sealed": [e["seal"] for e in sealed],
             "rebuilt_from": "intake-ledger.jsonl", "note":
             "Private Kette. NICHT veroeffentlichen: die Hashes privater Originale "
             "sind Brute-Force-Orakel. Der oeffentliche Index bleibt unberuehrt."}
    tmp = pchain + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(chain, f, indent=1, ensure_ascii=False)
    os.replace(tmp, pchain)
    seal = sealed[-1]["seal"] if sealed else "genesis"
    prev = sealed[-2]["seal"] if len(sealed) > 1 else "genesis"

    print(json.dumps({"status": "INTAKED", "intake_id": intake_id,
                      "sha256": sha, "bytes": size, "stored": dest,
                      "chain": "PRIVATE (nicht in der oeffentlichen Kette, nicht publiziert)",
                      "private_chain_seal": seal[:32], "prev_seal": prev[:16],
                      "public_index_touched": False,
                      "provenance": rec["provenance"],
                      "submission": rec["submission"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
