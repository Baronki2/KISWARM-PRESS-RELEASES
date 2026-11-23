#!/usr/bin/env python3
"""
l8-ocr-artifact.py — OCR-Ergebnis als Dauer-Artefakt in die Beweiskette.

Ein OCR-Text, der nur in /tmp liegt, ist kein Beleg: er verschwindet beim
Neustart und traegt keine Herkunft. Dieses Skript legt ihn als benanntes
Artefakt neben die Quelle ab - mit Herkunftsangabe, Hash der Quelle, Hash des
Textes, Verfahren, Seitenzahl und Datum.

Aufruf: l8-ocr-artifact.py <quelle.pdf> <zielname> [--note "..."]
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ocr_pdf(src, dpi=200):
    """Rendert + OCRt. Liefert (text, seiten, methode)."""
    tmp = tempfile.mkdtemp(prefix="l8ocr-")
    try:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-png", src,
                        os.path.join(tmp, "p")], check=True, timeout=1500,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pngs = sorted(p for p in os.listdir(tmp) if p.endswith(".png"))
        if not pngs:
            return "", 0, "render_failed"
        for i, p in enumerate(pngs):
            full = os.path.join(tmp, p)
            subprocess.run(["tesseract", full, full[:-4], "-l", "deu+eng"],
                           timeout=300, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        seiten = []
        for p in pngs:
            tp = os.path.join(tmp, p[:-4] + ".txt")
            seiten.append(open(tp, encoding="utf-8", errors="replace").read()
                          if os.path.exists(tp) else "")
        return "\n\n".join(seiten), len(pngs), "pdftoppm-{dpi}dpi-gray + tesseract deu+eng".format(dpi=dpi)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src = sys.argv[1]
    name = sys.argv[2]
    note = ""
    if "--note" in sys.argv:
        note = sys.argv[sys.argv.index("--note") + 1]
    if not os.path.exists(src):
        print("   !! Quelle fehlt:", src)
        return 1

    pdf_sha = sha256(src)
    # 1) vorhandenen Textlayer pruefen
    tl = subprocess.run(["pdftotext", "-layout", src, "-"], capture_output=True,
                        text=True, timeout=300).stdout or ""
    if len(tl.strip()) > 1500:
        text, seiten, methode = tl, "Textlayer", "pdftotext -layout"
    else:
        text, seiten, methode = ocr_pdf(src)
    if not text.strip():
        print("   !! Kein Text erzeugt - kein leeres Artefakt schreiben")
        return 1

    # 2) Artefakt schreiben
    ziel = os.path.join(E, name + ".txt")
    kopf = [
        "ARTEFAKT: OCR-VOLLTEXT",
        "QUELLE: {}".format(os.path.basename(src)),
        "QUELLE_SHA256: {}".format(pdf_sha),
        "TEXT_SHA256: {}".format(hashlib.sha256(text.encode("utf-8")).hexdigest()),
        "SEITEN: {}".format(seiten),
        "METHODE: {}".format(methode),
        "ERZEUGT: {}".format(datetime.now(timezone.utc).isoformat()),
        "ERZEUGER: kiswarm-sah6 (Hermes Agent, autonom)",
        "HINWEIS: {}".format(note) if note else "HINWEIS: -",
        "PROVENIENZ: OCR eines Scans. Der Text ist maschinell gelesen; fuer Zitate "
        "gegenueber Dritten ist die Seite am Scan zu pruefen. Fehler der "
        "Texterkennung sind moeglich (Ziffern/L/U/I, Umlaute).",
        "=" * 78,
        "",
    ]
    open(ziel, "w", encoding="utf-8").write("\n".join(kopf) + text)
    print("   OK {:58s} {:>7d} B | {} | {}".format(
        name + ".txt", os.path.getsize(ziel), methode, seiten))
    return 0


if __name__ == "__main__":
    sys.exit(main())
