#!/usr/bin/env python3
"""
l8-doc-splitter.py — Mischdokumente an der Grenze zwischen Fremdbeleg und eigener Akte trennen.

Ein Anlagendokument kann zwei Textarten in einer Datei enthalten: den Wortlaut
des Gerichts und unsere eigene Bewertung. Wird die Datei als "Staatsakt"
gefuehrt, erscheint unsere Behauptung als waere sie die Feststellung des
Gerichts. Das ist Record 012 eine Ebene tiefer.

Dieses Skript setzt eine sichtbare Grenze in den Text und kennzeichnet den
Kopf als Mischdokument. Die Originaldatei wird NICHT veraendert - es entsteht
eine getrennte, gekennzeichnete Fassung.
"""
from __future__ import annotations
import hashlib, os, re, sys
from datetime import datetime, timezone

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"

# Markierungen, an denen ein Anlagenband vom Gerichtstext in unsere Bewertung wechselt
GERICHT_MARKER = [
    "TENOR UND INHALT DES ABGABEBESCHLUSSES",
    "BESCHLUSS",
    "Gründe:",
    "Rechtsbehelfsbelehrung:",
]
EIGEN_MARKER = [
    "VERFASSUNGSRECHTLICHER BEWEISWERT",
    "BEWEISWERT",
    "SYSTEMATISCHER ZIRKELSCHLUSS",
    "HUTCHENSPIEL",
]


def split_text(t):
    """Findet die Grenze zwischen Gerichtstext und eigener Bewertung."""
    # Der EIGENE-Text beginnt beim fruehesten Eigen-Marker, der nach einem
    # Gerichts-Marker liegt. Alles davor ist Gerichtstext (inkl. Deckblatt).
    e_pos, e_name = None, None
    for m in EIGEN_MARKER:
        p = t.find(m)
        if p >= 0 and (e_pos is None or p < e_pos):
            e_pos, e_name = p, m
    if e_pos is None:
        return None, None, None
    # Wo endet der Gerichtstext? Der letzte Gerichts-Marker VOR der Eigen-Position.
    g_pos = None
    for m in GERICHT_MARKER:
        p = t.rfind(m, 0, e_pos)
        if p > (g_pos or 0):
            g_pos = p
    return g_pos, e_pos, e_name


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    hinweis = sys.argv[3] if len(sys.argv) > 3 else ""
    t = open(src, encoding="utf-8").read()
    g_pos, e_pos, e_name = split_text(t)
    if e_pos is None:
        print("   !! Keine Eigen-Marker gefunden - nichts getrennt")
        return 1

    gericht = t[:g_pos] if g_pos else ""
    rest = t[g_pos:] if g_pos else t
    eigen = rest[e_pos - (g_pos or 0):]
    zwischen = rest[:e_pos - (g_pos or 0)] if g_pos else t[:e_pos]

    kopf = t.split("=" * 78)[0] + "\n" if "=" * 78 in t else ""
    # Kopf um die Mischdokument-Kennzeichnung erweitern
    extra = [
        "MISCHDOKUMENT: JA - dieses Anlagenband enthaelt zwei Textarten.",
        "  SICHERUNGSGRENZE A = Wortlaut des Gerichts, uebernommen, nicht veraendert.",
        "  SICHERUNGSGRENZE B = Kommentar der KISWARM-Akte. Das ist KEINE Feststellung",
        "                       des Gerichts und darf nicht als solche zitiert werden.",
        "TRENNSTELLE: {}".format(e_name),
        "HINWEIS: {}".format(hinweis),
    ]
    # In den bestehenden Kopf einfuegen
    teile = kopf.split("\n")
    neu = []
    for z in teile:
        neu.append(z)
        if z.startswith("PROVENIENZ:"):
            neu.extend(extra)
    if not any(z.startswith("MISCHDOKUMENT") for z in neu):
        neu.extend(extra)
    neukopf = "\n".join(neu)

    out = (neukopf + "\n" + "=" * 78 + "\n\n"
           + "<<<SICHERUNGSGRENZE A - GERICHTS-TEXT>>>\n" + gericht.strip() + "\n\n"
           + (zwischen.strip() + "\n\n" if zwischen.strip() else "")
           + "<<<SICHERUNGSGRENZE B - EIGENE BEWERTUNG>>>\n" + eigen.strip() + "\n")
    open(dst, "w", encoding="utf-8").write(out)
    print("   OK {:58s} {:>7d} B | Gerichtstext {:>5d} Z | eigene Bewertung {:>5d} Z".format(
        os.path.basename(dst), os.path.getsize(dst), len(gericht.strip()),
        len(eigen.strip())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
