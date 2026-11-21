#!/usr/bin/env python3
"""
OCR-SCAN DER BEWEISKETTE — Suche nach dem PfÜB / dem Beschluss vom 12.11.2026
===========================================================================
54 der 161 PDFs in der evidence chain haben keinen Textlayer: sie sind Scans.
`pdftotext` sieht dort nichts, also wurde der Beschluss bislang nie gefunden —
nicht weil er fehlt, sondern weil niemand ihn gelesen hat.

Dieses Skript OCRt die Scans (tesseract deu+eng) und sucht nach den Signaturen
des Beschlusses:
  - "6 M 9219"
  - "12.11.2026"
  - "Pfändungs- und Überweisungsbeschluss"
  - "Richterin am Amtsgericht"
  - "gez." / "Ausfertigung" / "beglaubigt"

Es läuft parallel über mehrere Worker und schreibt die Treffer als JSON.
"""
import glob
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

EVIDENCE = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
WORK = "/home/sah/.hermes/cache/scratch/ocr"
OUT = "/home/sah/.hermes/cache/scratch/ocr_beschluss_hits.json"
STATE = "/home/sah/.hermes/cache/scratch/ocr_scans_state.json"

PATTERN = re.compile(
    r"6\s*M\s*9219"
    r"|12\.\s*11\.\s*2026"
    r"|13\.\s*11\.\s*2026"
    r"|Pf.{0,4}ndungs-\s*und\s*.{0,4}berweisungsbeschluss"
    r"|Richterin\s+am\s+Amtsgericht"
    r"|Aufrechterhaltung\s+der\s+Zwangsvollstreckung",
    re.I,
)


def ocr_pdf(path):
    """OCR the first N pages of one PDF. Returns (path, [(page, text)]).

    The temp prefix must be unique per file AND per worker. Truncating the
    basename to 40 characters made two different documents (and the two copies
    of the same document, one with a _1 suffix) share a temp prefix, so the
    parallel workers overwrote each other's rendered pages and tesseract
    read a half-written file.
    """
    stem = os.path.basename(path)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", stem)[:60]
    tmp = os.path.join(WORK, "w{0}_{1}".format(os.getpid(), safe))
    try:
        os.makedirs(WORK, exist_ok=True)
        subprocess.run(
            ["pdftoppm", "-r", "150", "-gray", "-f", "1", "-l", "6", "-png", path, tmp],
            capture_output=True, timeout=300)
        hits = []
        for img in sorted(glob.glob(tmp + "*.png")):
            r = subprocess.run(["tesseract", img, "stdout", "-l", "deu+eng"],
                               capture_output=True, text=True, timeout=300)
            t = r.stdout or ""
            if PATTERN.search(t):
                hits.append((os.path.basename(img), t))
            try:
                os.remove(img)
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass
        return path, hits
    except Exception as e:
        return path, [("ERROR", str(e)[:120])]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        pdfs = sorted(glob.glob(os.path.join(EVIDENCE, "*.pdf")))
    else:
        pdfs = json.load(open(STATE))

    # only those without a text layer
    todo = []
    for p in pdfs:
        try:
            r = subprocess.run(["pdftotext", "-layout", p, "-"],
                               capture_output=True, text=True, timeout=120)
            if not (r.stdout or "").strip():
                todo.append(p)
        except Exception:
            pass

    print("SCANS OHNE TEXTLAYER: {0}".format(len(todo)), flush=True)
    hits = {}
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(ocr_pdf, p): p for p in todo}
        done = 0
        for f in as_completed(futs):
            p, h = f.result()
            done += 1
            if h:
                real = [x for x in h if x[0] != "ERROR"]
                if real:
                    hits[p] = h
                    print("TREFFER {0} ({1} Seiten)".format(
                        os.path.basename(p)[:60], len(real)), flush=True)
                else:
                    print("  (OCR-Fehler) {0}: {1}".format(
                        os.path.basename(p)[:40], h[0][1][:60]), flush=True)
            if done % 5 == 0:
                print("  ... {0}/{1}".format(done, len(todo)), flush=True)
                with open(OUT, "w") as fh:
                    json.dump(hits, fh, ensure_ascii=False)

    with open(OUT, "w") as fh:
        json.dump(hits, fh, ensure_ascii=False)
    print("FERTIG. Treffer-Dateien: {0}".format(len(hits)), flush=True)
    print("  -> {0}".format(OUT), flush=True)


if __name__ == "__main__":
    main()
