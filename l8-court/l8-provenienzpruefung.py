#!/usr/bin/env python3
"""Provenienzpruefung: ist ein Dokument aus dem Korpus ein Staatsakt oder unser eigenes?"""
import re, os, json

O = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/OCR-VOLLTEXT"
LIST = ["1_BvR_292526_Erster_Senat.txt", "ZweiterSenatBvR.txt", "bverfg_beweismitteleingabe.t",
        "GENERALSTAATSANWALTSCHAFT_STUTTGART_AZ._24_ZS.txt", "BVG_STA.txt",
        "fristwahrende_beschwerde_sta_stuttgart_3110js101829_26.txt", "Bundesverfassungsgericht2.txt"]

OWN = [("S.A.H. GmbH", r"S\.A\.H\.\s*GmbH"), ("Beschwerdefuehrer", r"Beschwerdef[uü]hrer"),
       ("Ill-Marker", r"\bIll\."), ("eee-EEE-Marker", r"e+e+\s*E+E+"),
       ("Antrag/Begehren", r"\b(Begehren|Antrag|Wir bitten|Wir beantragen)\b"),
       ("Unsere Ueberschrift", r"(SYSTEMATISCHER ZIRKELSCHLUSS|VERFASSUNGSRECHTLICHE W[ÜU]RDIGUNG)"),
       ("Verweis auf Uns", r"\bunser(er|e)?\s+(Schriftsatz|Antrag|Gesuch)")]
FOREIGN = [("Tenor", r"\bTenor\b"), ("Verkuendet", r"Verk[uü]ndet"),
           ("Justizstatistik", r"Justizstatistik"),
           ("Der Senat hat entschieden", r"Der\s+Senat\s+hat\s+entschieden"),
           ("Beschluss vom ...", r"Beschluss\s+vom\s+\d{2}\.\d{2}\.\d{4}"),
           ("Staatsanwaltschaft-Briefkopf", r"(Staatsanwaltschaft|Generalstaatsanwaltschaft)"),
           ("Vollstreckungsabteilung", r"Vollstreckungsabteilung"),
           ("Aktenzeichen 24 Zs", r"24\s*Zs\s*1610/26")]

print("{:50s} {:>6s} {:>6s}  {}".format("Dokument", "eigen", "fremd", "Klassifikation"))
print("-" * 112)
res = {}
for fn in LIST:
    p = os.path.join(O, fn)
    if not os.path.exists(p):
        continue
    t = " ".join(open(p, encoding="utf-8", errors="replace").read().split())
    o = sum(len(re.findall(rx, t, re.I)) for _, rx in OWN)
    f = sum(len(re.findall(rx, t, re.I)) for _, rx in FOREIGN)
    kl = "EIGENES DOKUMENT" if o >= 3 else ("STAATSAKT" if f >= 3 else "GEMISCH/UNKLAR")
    res[fn] = {"own": o, "foreign": f, "class": kl, "len": len(t),
               "own_hits": [k for k, rx in OWN if re.search(rx, t, re.I)],
               "foreign_hits": [k for k, rx in FOREIGN if re.search(rx, t, re.I)]}
    print("{:50s} {:>6d} {:>6d}  {}".format(fn[:50], o, f, kl))

print("\n=== GENERALSTAATSANWALTSCHAFT_STUTTGART_AZ._24_ZS.txt — Anfang ===")
t = " ".join(open(os.path.join(O, "GENERALSTAATSANWALTSCHAFT_STUTTGART_AZ._24_ZS.txt"),
                  encoding="utf-8", errors="replace").read().split())
print(" ", t[:900])
for fn in ("BVG_STA.txt", "ZweiterSenatBvR.txt", "fristwahrende_beschwerde_sta_stuttgart_3110js101829_26.txt"):
    p = os.path.join(O, fn)
    if os.path.exists(p):
        print("\n=== {} — Anfang ===".format(fn))
        print(" ", " ".join(open(p, encoding="utf-8", errors="replace").read().split())[:700])
json.dump(res, open("/home/sah/.config/sah-vault/l8-provenienzpruefung-2026-11-23.json", "w"),
          indent=1, ensure_ascii=False)
print("\nGeschrieben: l8-provenienzpruefung-2026-11-23.json")
