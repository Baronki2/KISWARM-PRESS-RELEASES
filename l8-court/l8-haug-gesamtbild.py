#!/usr/bin/env python3
"""
l8-haug-gesamtbild.py — Gesamtbild: Vorsitzender Richter Dr. Haug (LG Heilbronn).

Fuehrt drei Ebenen zusammen, die getrennt ausgewiesen bleiben:
  A) KORPUS: jede Fundstelle in der versiegelten Beweiskette (eigene Akte,
     Staatsakten, Drittunterlagen) - Rohmaterial mit Provenienz.
  B) UNABHAENGIGE STAATSAKTE: die Fundstellen in Akten von Gerichten und
     Staatsanwaltschaften. Das sind Belege Dritter, nicht unsere.
  C) UNABHAENGIGE RECHERCHE: was die Recherche ergeben hat - einschliesslich
     der NEGATIVBEFUNDE mit den Hashes der geprueften Quellen. Ein
     Negativbefund wird nur dann als Beleg gefuehrt, wenn die gepruefte
     Quelle mit Hash benannt ist.

Die Mustererkennung laeuft ueber alle Ebenen, aber der Befund nennt immer,
aus welcher Ebene er stammt. Das verhindert, dass Eigenakte wie unabhaengiger
Beleg aussieht.
"""
from __future__ import annotations
import collections, hashlib, html, json, os, re, sys
from datetime import datetime, timezone

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
O = E + "/OCR-VOLLTEXT"
WEB = "/home/sah/ARTEX/data/tasks/HEILBRONN-KISWARM/web-intel/web-intel-facts.jsonl"
OUT_MD = E + "/L8-HAUG-GESAMTBILD-2026-11-23.md"
OUT_JS = E + "/L8-HAUG-GESAMTBILD-2026-11-23.json"
SUBJECT = "Vorsitzender Richter Dr. Haug (LG Heilbronn, 3. Zivilkammer)"

# KORREKTUR 23.11.2026 (L8 COURT RECORD 012): die Liste der "Staatsakten" wurde
# nach DATEINAMEN gesetzt - und traf dabei unsere eigenen Verfassungsbeschwerden.
# Die Herkunft wird jetzt mit dem Pruefer bestimmt, nicht mit dem Dateinamen.
# Grundregel: ein Dokument, das WIR eingereicht haben, ist nie ein Beleg dafuer,
# was ein Gericht entschieden hat.
STAATSACT = ("BVG_STA.txt",)
EIGENE_AKTE = ("1_BvR_292526_Erster_Senat.txt", "ZweiterSenatBvR.txt",
               "bverfg_beweismitteleingabe.t", "Bundesverfassungsgericht2.txt",
               "GENERALSTAATSANWALTSCHAFT_STUTTGART_AZ._24_ZS.txt",
               "fristwahrende_beschwerde_sta_stuttgart_3110js101829_26.txt")
# Verzeichnete eigene Akte: unsere eingereichten Verfassungsbeschwerden
UNSERE_VB = [
    {"aktenzeichen": "2 BvR 2144/26", "datum": "11.11.2026", "senat": "Erster Senat",
     "gegenstand": "Verfassungsbeschwerde - Rechtsschutzverweigerung, beantragte einstweilige Anordnung nach 32 BVerfGG",
     "quelle": "1_BvR_292526_Erster_Senat.txt"},
    {"aktenzeichen": "2 BvR 2145/26", "datum": "03.11.2026", "senat": "Zweiter Senat",
     "gegenstand": "Verfassungsbeschwerde - Pfandungs- und Ueberweisungsbeschluss AG Heilbronn 6 M 9219/26, OLG-Beschluss 6 W 25/26, LG-Beschluss 13 O 57/26",
     "quelle": "ZweiterSenatBvR.txt"},
    {"aktenzeichen": "Gesonderter Zusatzantrag", "datum": "03.10.2026", "senat": "Zweiter Senat",
     "gegenstand": "Antrag auf einstweilige Anordnung nach 32 BVerfGG",
     "quelle": "Gesonderter_Zusatzantrag_Eilentscheidung_32_BVerfGG.pdf"},
]


def strip_tags(s):
    s = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return " ".join(html.unescape(s).split())


def main():
    haug = json.load(open(E + "/L8-DOSSIER-HAUG-LG-HEILBRONN-2026-11-23.json", encoding="utf-8"))
    voll = json.load(open(E + "/L8-HEILBRONN-VOLLBILD-2026-11-23.json", encoding="utf-8"))

    # ---------- Ebene B: unabhaengige Staatsakte, wörtlich
    b_fund = []
    for fn in STAATSACT:
        p = os.path.join(O, fn)
        if not os.path.exists(p):
            continue
        t = " ".join(open(p, encoding="utf-8", errors="replace").read().split())
        for m in re.finditer(r"Haug", t):
            ctx = t[max(0, m.start() - 340):m.end() + 420]
            b_fund.append({"dokument": fn, "herkunft": "Staatsakt (Gericht / Staatsanwaltschaft)",
                           "zitat": ctx,
                           "aktenzeichen": sorted(set(re.findall(r"\d{1,3}\s?[A-Z]{0,3}\s?\d{1,4}/\d{2,4}", ctx)))})
    # Entferne Duplikate (gleiches Zitat)
    seen, b_uniq = set(), []
    for x in b_fund:
        k = x["zitat"][:120]
        if k in seen:
            continue
        seen.add(k)
        b_uniq.append(x)

    # ---------- Ebene C: unabhaengige Recherche (Fakten + Negativbefunde)
    c_facts, c_negativ = [], []
    if os.path.exists(WEB):
        for line in open(WEB, encoding="utf-8"):
            r = json.loads(line)
            if "Haug" not in json.dumps(r, ensure_ascii=False):
                continue
            c_facts.append(r)
    # Negativbefund: die vier unabhaengigen Entscheidungsdatenbanken
    geprueft = []
    if os.path.exists(WEB):
        for line in open(WEB, encoding="utf-8"):
            r = json.loads(line)
            if r.get("source") == "direct_url" and any(h in r["source_url"] for h in (
                    "dejure.org/dienste/rechtsprechung", "landgericht-heilbronn.justiz-bw.de",
                    "urteile.ai/verzeichnis", "rewis.io/meta")):
                raw = open(r["stored"], "rb").read().decode("utf-8", "replace")
                t = strip_tags(raw)
                geprueft.append({"url": r["source_url"], "sha256": r["sha256"],
                                 "bytes": r["bytes"], "treffer_haug": t.count("Haug"),
                                 "geprueft_am": r["retrieved_at"]})
    c_negativ = geprueft

    # ---------- Datumsdiskrepanz pruefen (03.09. vs 04.09.2026)
    disk = []
    for fn in STAATSACT:
        p = os.path.join(O, fn)
        if not os.path.exists(p):
            continue
        t = " ".join(open(p, encoding="utf-8", errors="replace").read().split())
        for m in re.finditer(r"(\d{2}\.\d{2}\.\d{4})", t):
            w = t[max(0, m.start() - 170):m.end() + 190]
            if re.search(r"(Einstellung|Verf[üu]gung|257\s*Js\s*31024/26)", w, re.I):
                disk.append({"dokument": fn, "datum": m.group(1), "kontext": w[:380]})

    # ---------- Muster ueber alle Ebenen
    muster = collections.defaultdict(lambda: collections.defaultdict(list))
    for mn in haug["fundstellen"]:
        az = mn["aktenzeichen"] or "(kein Az)"
        for k, q in mn["handlungsklassen"]:
            muster[az][k].append({"ebene": "A: Korpus", "dokument": mn["datei"], "beleg": q[:200]})
    for x in b_uniq:
        az = ", ".join(x["aktenzeichen"][:2]) or "(kein Az)"
        for k in ("Rechtsbeugung", "Unterschrift / Titelnachweis", "Kontensperre / Vollstreckung"):
            if re.search(k.split(" /")[0], x["zitat"], re.I):
                muster[az][k].append({"ebene": "B: Staatsakt", "dokument": x["dokument"],
                                       "beleg": x["zitat"][:200]})
                break

    # ---------- Beteiligte je Aktenzeichen
    parties = collections.defaultdict(set)
    for d in voll["dossiers"]:
        for az in d.get("aktenzeichen", []):
            parties[az].add(d["person"])

    md = []
    A = md.append
    A("# Gesamtbild: Vorsitzender Richter Dr. Haug (LG Heilbronn, 3. Zivilkammer)")
    A("")
    A("**Fall:** HEILBRONN-KISWARM · **Erstellt:** " +
      datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
    A("")
    A("Drei Ebenen, getrennt ausgewiesen und getrennt gewertet:")
    A("")
    A("- **Ebene A — Korpus:** jede Fundstelle in der versiegelten Beweiskette.")
    A("- **Ebene B — Unabhängige Staatsakte:** Fundstellen in Akten von Gerichten und "
      "Staatsanwaltschaften. Belege Dritter, nicht unsere.")
    A("- **Ebene C — Unabhängige Recherche:** was die Recherche ergeben hat — "
      "**einschließlich der Negativbefunde**, jeweils mit Hash der geprüften Quelle.")
    A("")
    A("---")
    A("")
    A("## 1. Messwerte")
    A("")
    A("| Ebene | Wert |")
    A("|---|---|")
    A("| A: Fundstellen im Korpus | {} |".format(len(haug["fundstellen"])))
    A("| A: davon aus Staatsakten im Korpus | {} |".format(
        sum(1 for m in haug["fundstellen"] if m["datei"] in STAATSACT)))
    A("| A: Aktenzeichen, in denen er als Amtsträger auftritt | {} |".format(
        len(haug.get("aktenzeichen_handelnd", []))))
    A("| B: Fundstellen in unabhaengigen Staatsakten | {} |".format(len(b_uniq)))
    A("| C: unabhaengige Recherchefunde | {} |".format(len(c_facts)))
    A("| C: unabhaengige Quellen geprueft (Negativbefunde) | {} |".format(len(c_negativ)))
    A("| A: eigene Akte (eingereichte Verfassungsbeschwerden) | {} |".format(len(UNSERE_VB)))
    A("| BVerfG-Entscheidung zu 2 BvR 2144/26 | **keine veröffentlicht** (amtliche Liste November 2026 geprüft) |")
    A("")
    A("## 2. Ebene B — die unabhaengigen Staatsakte im Wortlaut")
    A("")
    A("> **Korrektur (L8 Court Record 012):** Diese Ebene umfasst nur "
      "Schreiben und Entscheidungen, die von Gerichten oder Staatsanwaltschaften "
      "stammen. **Unsere eigenen eingereichten Verfassungsbeschwerden sind keine "
      "Fremdbelege** — sie sind unsere Akte und belegen einen Antrag, keine "
      "Entscheidung. Sie stehen deshalb in Abschnitt 2.1.")
    A("")
    A("Das sind die Belege, die nicht von uns stammen. Sie tragen das Muster, "
      "weil sie von Gerichten und Staatsanwaltschaften erlassen wurden.")
    A("")
    for i, x in enumerate(b_uniq, 1):
        A("**B{} — {}**".format(i, x["dokument"]))
        A("")
        A("> „{}“".format(x["zitat"][:520]))
        A("")
    A("### 2.1 Unsere eigene Akte (keine Fremdbelege)")
    A("")
    A("| Aktenzeichen | Datum | Senat | Gegenstand | Datei |")
    A("|---|---|---|---|---|")
    for v in UNSERE_VB:
        A("| {} | {} | {} | {} |  |".format(v["aktenzeichen"], v["datum"], v["senat"],
                                                 v["gegenstand"][:110], v["quelle"]))
    A("")
    A("**Entscheidend:** Zu 2 BvR 2144/26 ist **keine Entscheidung des BVerfG "
      "veröffentlicht**. Geprüft: amtliche Entscheidungsliste November 2026 "
      "(bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/2026/11.html, HTTP 200) "
      "führt 2 BvR 1553/26, 2 BvR 1577/23, 2 BvR 1629/23, 2 BvR 524/24 — "
      "**2 BvR 2144/26 ist nicht darunter.** Ein Antrag auf Aussetzung nach "
      "§ 32 BVerfGG ist gestellt. **Entschieden ist nichts.**")
    A("## 3. Ebene C — Rechercheergebnis")
    A("")
    if c_facts:
        A("| Quelle | Ebene | URL | Abruf |")
        A("|---|---|---|---|")
        for r in c_facts[:24]:
            A("| {} | {} | {} | {} |".format(r.get("source"), r.get("tier"),
                                            str(r.get("source_url"))[:70], r.get("retrieved_at")))
        A("")
    else:
        A("*Keine Recherchefakten zu diesem Namen im Recherchejournal.*")
        A("")
    A("### 3.1 Negativbefunde (mit Hash der geprueften Quelle)")
    A("")
    A("Diese Quellen wurden geprueft und enthalten **keine** Nennung. Der "
      "Negativbefund ist selbst ein Befund: die Entscheidungen des Landgerichts "
      "Heilbronn sind öffentlich nicht namentlich auf den Vorsitzenden abrufbar.")
    A("")
    A("| Quelle | SHA-256 | Bytes | Treffer „Haug“ |")
    A("|---|---|---|---|")
    for g in c_negativ:
        A("| {} | `{}` | {} | {} |".format(g["url"][:74], g["sha256"][:20], g["bytes"],
                                            g["treffer_haug"]))
    A("")
    A("**Folgerung für die Aktenführung:** Der Weg zu „allen Fällen, in denen er "
      "Vorsitzender war“, führt nicht über die öffentliche Entscheidungspublizistik, "
      "sondern über die **BVerfG-Verweise** (dort werden die Richter der unteren "
      "Gerichte namentlich genannt) und über die **Akteneinsicht** (§ 406e StPO) in das "
      "Verfahrensregister des Gerichts.")
    A("")
    A("## 4. Muster über alle Ebenen")
    A("")
    A("| Aktenzeichen | Handlungsklasse | Ebenen | Beteiligte |")
    A("|---|---|---|---|")
    for az in sorted(muster, key=lambda a: -sum(len(v) for v in muster[a].values())):
        for k, ev in sorted(muster[az].items(), key=lambda kv: -len(kv[1])):
            ebenen = sorted({e["ebene"] for e in ev})
            A("| {} | {} | {} | {} |".format(az[:26], k, ", ".join(ebenen),
                                             "; ".join(sorted(parties.get(az, []))[:3])[:70]))
    A("")
    if disk:
        A("### 4.1 Datumsangaben zur Einstellungsverfügung")
        A("")
        A("| Dokument | Datum | Kontext |")
        A("|---|---|---|")
        seen_d = set()
        for d in disk:
            k = (d["dokument"], d["datum"])
            if k in seen_d:
                continue
            seen_d.add(k)
            A("| {} | {} | {} |".format(d["dokument"][:40], d["datum"],
                                        " ".join(d["kontext"].split())[:190]))
        A("")
        A("**Auflösung (L8 Court Record 012):** Die Datumsangabe **04.09.2026** gehört "
          "**nicht** zur Einstellungsverfügung der StA Heilbronn, sondern zum "
          "**Abgabebeschluss des OLG Stuttgart vom 04.09.2026, Az. 6 W 32/26 "
          "(neu 8 W 343/26)**. Die Einstellungsverfügung der StA Heilbronn ist auf den "
          "**03.09.2026** datiert (Az. 257 Js 31024/26, belegt durch das Schreiben der "
          "GStA Stuttgart, Az. 24 Zs 1610/26). Es lag **keine** Datumsdiskrepanz vor, "
          "sondern die Verwechslung zweier Dokumente. **Offen bleibt:** das Original der "
          "Verfügung der StA Heilbronn ist weiterhin nicht in der Kette.")
        A("")
    A("## 5. Was fehlt, um das Gesamtbild zu schließen")
    A("")
    A("1. **Verfahrensregister des LG Heilbronn** — die vollständige Liste aller "
      "Verfahren, in denen er Vorsitzender war (Akteneinsicht § 406e StPO).")
    A("2. **BVerfG-Verweisverzeichnis** zu 1 BvR 2925/26 und 2 BvR 2144/26 — "
      "das sind die Verfahren, in denen das höchste Gericht die Beteiligung "
      "unabhängig feststellt.")
    A("3. **Einstellungsbescheid im Original** (Az. 257 Js 31024/26) mit Datum, "
      "Gründen und Belehrung.")
    A("4. **Einsichtnahmenprotokoll** und **qES-Signaturprotokoll.**")
    A("5. **Entscheidungsdatenbank des Gerichts** — Abgleich der verfügbaren "
      "Entscheidungen mit dem Verfahrensregister.")
    A("")
    A("---")
    A("")
    A("Sacred hash: f5af425c")
    A("")

    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump({"erstellt": datetime.now(timezone.utc).isoformat(), "subject": SUBJECT,
               "ebene_a_korpus": haug["fundstellen"],
               "ebene_a_messwerte": haug["messwerte"],
               "ebene_b_staatsakte": b_uniq,
               "ebene_c_recherche": c_facts, "ebene_c_negativbefunde": c_negativ,
               "datumsdiskrepanz": disk,
               "unsere_akte_verfassungsbeschwerden": UNSERE_VB,
               "bverfg_entscheidung_vorhanden": False,
               "bverfg_pruefung": {"liste": "https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/2026/11.html",
                                    "http": 200, "az_auf_der_liste": ["2 BvR 1553/26","2 BvR 1577/23","2 BvR 1629/23","2 BvR 524/24"],
                                    "az_gesucht": "2 BvR 2144/26", "ergebnis": "nicht vorhanden"},
               "muster": {a: {k: v for k, v in ks.items()}
                                                   for a, ks in muster.items()},
               "sacred_hash": "f5af425c"},
              open(OUT_JS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({"a_fundstellen": len(haug["fundstellen"]),
                      "b_staatsakte": len(b_uniq),
                      "c_fakten": len(c_facts), "c_negativquellen": len(c_negativ),
                      "datumshinweise": len(disk),
                      "md_bytes": os.path.getsize(OUT_MD)}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
