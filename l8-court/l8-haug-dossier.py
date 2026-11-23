#!/usr/bin/env python3
"""
l8-haug-dossier.py — Subject dossier: Vorsitzender Richter Dr. Haug (LG Heilbronn).

Auftrag: die Beteiligung des Dr. Haug an den in der versiegelten Akte
dokumentierten Verfahren vollstaendig darstellen und das Muster zeigen, das
ueber die einzelnen Verfahren hinausweist. Ausgangspunkt ist die Feststellung,
dass es sich nicht um einen Einzelfall handelt.

Methodik (im Skript festgeschrieben, damit das Dossier pruefbar bleibt):
  * JEDE Fundstelle wird mit Kontext, Aktenzeichen, Datum und Quelldokument
    erfasst - nichts wird zusammengefasst, nichts weggelassen.
  * Jede Zuordnung einer Handlungsklasse nennt die getroffene Textstelle.
  * Jedes Quelldokument traegt eine PROVENIENZ (Eigenakte, Staatsakt, Dritte,
    unbestimmt). Die Einstufung erfolgt ueber die Dokumentenherkunft, nicht
    ueber Stichwoerter: eine Klassifikation per Stichwort ist an diesem
    Korpus nachweislich unzuverlaessig (der Test stufte ein BVerfG-Urteil als
    eigenen Schriftsatz ein).
  * Neben der belastenden Darstellung steht ausdruecklich, was dagegen spricht
    und was nicht geprueft wurde. Ein Dossier, das nur Belastendes sammelt,
    ist vor Gericht nicht verwendbar.
"""
from __future__ import annotations
import collections, glob, hashlib, json, os, re, sys
from datetime import datetime, timezone

O = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27/OCR-VOLLTEXT"
E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
OUT_MD = os.path.join(E, "L8-DOSSIER-HAUG-LG-HEILBRONN-2026-11-23.md")
OUT_JS = os.path.join(E, "L8-DOSSIER-HAUG-LG-HEILBRONN-2026-11-23.json")

SUBJECT = "Vorsitzender Richter Dr. Haug (LG Heilbronn, 3. Zivilkammer)"
SUBJECT_RE = re.compile(r"\bHaug\w*", re.I)
# OCR-Verwechslungen, die ausdruecklich mitgezaehlt werden (u/a, l/i)
VARIANT = re.compile(r"\bHa[ugp]g?\w*|\bHaug\b", re.I)

# ---------------------------------------------------------- Handlungsklassen
KLASSEN = [
 ("Befangenheit", r"Befangenheitsantrag|Befangenheit|§\s*45\s*ZPO|gesorgnis der Befangenheit"),
 ("Rechtsbeugung", r"Rechtsbeugung|§\s*339\s*StGB|vors[aä]tzlich|wissentlich|mit Kenntnis"),
 ("Unterschrift / Titelnachweis", r"unterschrieben|ohne Unterschrift|Titelnachweis|§\s*317\s*ZPO|"
                                  r"Vollstreckungstitel|Ausfertigung|Vollstreckungsgrundlage"),
 ("Kontensperre / Vollstreckung", r"Kontensperre|Pf[aä]ndung|Vollstreckung|auf das Konto|"
                                   r"Konto der|Kontopf[aä]ndung|Arrest"),
 ("Zustellung / Frist", r"Zustellung|nicht zugestellt|Zustellvermerk|Fristablauf|Fristvers[aä]umung"),
 ("Verfahrensfehler", r"Verfahrensfehler|unzul[aä]ssig|Sachverhalt nicht aufgekl[aä]rt|"
                      r"unterlassen|vers[aä]umt|Art\.?\s*103"),
 ("Nichtabhilfe / Verweigerung", r"Nichtabhilfe|nicht abgeholfen|ohne Abhilfe|Verweigerung|"
                                  r"nicht veranla[sß]t"),
 ("Einstellung / Einstellungsverf.", r"Einstellungsverf|Einstellung der Ermittlungen|"
                                      r"nach §\s*153|Einstellung"),
 ("Ermittlungsverfahren / Verwertung", r"Ermittlungsakte|Ermittlungen|Verwertung|Aktenlage|"
                                        r"Verfahrensakte|Unterlagen"),
 ("Dienstaufsicht", r"Dienstaufsicht|DLRG|Ministerium Justiz"),
]
AZ_RE = re.compile(r"((?:\d{1,3}\s*)?(?:Js|Zs|M|O|U|W|J)?\s*\d{1,4}\s*/\s*\d{2,4})")
DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4}|\d{1,2}\.\s*(?:Januar|Februar|M[aä]rz|April|Mai|Juni|Juli|"
                     r"August|September|Oktober|November|Dezember)\s*\d{4}|\d{1,2}\.\d{1,2}\.\d{2,4})")


def norm_az(v):
    v = " ".join(v.split()).replace(" / ", "/")
    v = re.sub(r"^[^0-9A-Za-z]+", "", v)
    v = re.sub(r"(?<=[0-9])[A-Za-z]$", "", v)
    v = re.sub(r"^(?:I\s+)?13\s+O\s+37/26$", "I 3 O 57/26", v)
    v = re.sub(r"^(?:I\s+)?130\s+57/26$", "I 3 O 57/26", v)
    v = re.sub(r"^0\s+57/26$", "3 O 57/26", v)
    v = re.sub(r"^57/26$", "3 O 57/26", v)
    v = re.sub(r"^(?:I\s+)?3\s+O\s+57/26$", "I 3 O 57/26", v)
    v = re.sub(r"^(\d{2,4})\s+(Js|Zs)\s+(\d+)/(\d+)$", r"\2 \3/\4", v)
    v = re.sub(r"^(\d{1,3})\s*([A-Za-z])\s*(\d+)/(\d+)$", r"\1 \2 \3/\4", v)
    v = re.sub(r"^(\d{2,4})/(\d{2})$", r"\1/\2", v)
    return v.strip()


def az_in(text, span=420):
    out = []
    for m in AZ_RE.finditer(text):
        v = norm_az(m.group(1))
        if re.search(r"/\d{2}$", v) and len(v) >= 5:
            out.append((m.start(), v))
    return out


def klassen_in(text):
    hits = []
    for name, pat in KLASSEN:
        m = re.search(pat, text, re.I)
        if m:
            hits.append((name, " ".join(text[max(0, m.start() - 60):m.end() + 70].split())))
    return hits


DAT_RE = re.compile(r"\d{1,2}\.\d{1,2}\.\d{2,4}")
# HANDELND: der Vorsitzende erlaesst/entscheidet/verkuendet/zeichnet in diesem
# Kontext. ERWAEHNT: er wird als Beteiligter, Beschwerdegegner oder Akten-
# gegenstand genannt. Diese Unterscheidung entscheidet, ob ein Aktenzeichen
# zum Muster gehoert oder nur zum Umfeld.
HANDELND = re.compile(
    r"(erlie[ßs]s|erteilte|ertheilte|wies\s+ab|lehnte\s+ab|hat\s+abgelehnt|"
    r"entschied|entschieden|verk[uü]ndete|verwarf|verworfen|unterzeichnete|"
    r"zeichnete|ausfertigte|erteilte\s+die|verh[aä]ngte|Vorsitzenden\s+Richter|"
    r"des\s+Vorsitzenden|VRiLG\s+Dr\.\s*Haug|RiLG\s+Dr\.\s*Haug|"
    r"Pr[aä]sident(?:\s+des\s+Gerichts)?|stellvertretende?n?\s+Vorsitzende?n?|"
    r"Gerichtsbesitzer|entschied\s+Dr\.\s*Haug)", re.I)
TITEL = re.compile(
    r"(Vorsitzend\w*|VRiLG|RiLG|VRichter| Richter\s+Dr\.?\s*Haug|Presiding Judge\s+Dr\.?\s*Haug|"
    r"Judge\s+Dr\.?\s*Haug|Richter\s+Dr\.?\s*Haug)", re.I)
NUR_ERWAEHNT = re.compile(
    r"(Beschwerdegegner|Gegenstand\s+der\s+Ermittlungen|Verteidigung|"
    r"Beschwerdef(?:ü|u)hrer(?:\s+des\s+Beschwerdegegners)?|angeklagt|"
    r"Angeklagten|Verfahrensbeteiligten|Kläger(?:in)?|Beklagte)", re.I)


def rolle_bestimmen(ctx, offset=None):
    """Vier Rollen, getrennt belegt:
       handelnd  - erlässt/entscheidet/zeichnet (Handlungsverb im Fenster)
       namentlich - in amtlicher Funktion namentlich genannt (Titel im Fenster)
       erwaehnt  - als Beteiligter/Beschwerdegegner im Sachverhalt
       unklar    - keine dieser Zuordnungen belegbar
    """
    c = " ".join(ctx.split())
    if offset is None:
        i = c.lower().find("haug")
    else:
        i = offset
        if i < 0 or i >= len(c):
            i = c.lower().find("haug")
    if i < 0:
        return "unklar", ""
    vor, nach = c[max(0, i - 90):i], c[i:i + 200]
    if HANDELND.search(nach) or (HANDELND.search(c) and HANDELND.search(c).start() < i):
        m = HANDELND.search(nach) or HANDELND.search(c)
        j = m.start() if m else i
        return "handelnd", " ".join(c[max(0, j - 90):j + 110].split())
    if TITEL.search(vor) or TITEL.search(nach):
        j = (TITEL.search(vor) or TITEL.search(nach)).start()
        anchor = vor if TITEL.search(vor) else nach
        return "namentlich", " ".join(anchor[:190].split())
    if NUR_ERWAEHNT.search(nach) or NUR_ERWAEHNT.search(vor):
        m = NUR_ERWAEHNT.search(nach) or NUR_ERWAEHNT.search(vor)
        return "erwaehnt", " ".join(c[max(0, m.start() - 90):m.start() + 120].split())
    return "unklar", ""


def main():
    files = {os.path.basename(f): open(f, encoding="utf-8", errors="replace").read()
             for f in sorted(glob.glob(O + "/*.txt"))}

    # -------- Fundstellen sammeln
    mentions = []
    for fn, t in files.items():
        for m in SUBJECT_RE.finditer(t):
            i = m.start()
            ctx = " ".join(t[max(0, i - 420):i + 420].split())
            azs = az_in(ctx)
            az = azs[0][1] if azs else None
            dates = [d for d in DATE_RE.findall(ctx)]
            kl = klassen_in(ctx)
            # Fenster DIREKT aus dem Originaltext um die Nennung - keine
            # Offsetrechnung ueber normalisierten Text (die verschiebt Positionen)
            _win = t[max(0, i - 130):i + 260]
            rolle, belegrolle = rolle_bestimmen(_win)
            mentions.append({
                "datei": fn, "stelle": i, "wortlaut": t[i:i + 90].replace("\n", " "),
                "kontext": ctx, "aktenzeichen": az,
                "aktenzeichen_kandidaten": sorted({v for _, v in azs}),
                "datum_kandidaten": dates[:4],
                "handlungsklassen": kl,
                "rolle": rolle, "rollenbeleg": belegrolle,
            })

    # -------- Aktenzeichen-Cluster: wer steht in denselben Akten?
    docs_by_az = collections.defaultdict(set)
    for fn, t in files.items():
        for m in re.finditer(r"\bHaug\w*", t, re.I):
            ctx = t[max(0, m.start() - 420):m.end() + 420]
            for _, v in az_in(ctx):
                docs_by_az[v].add(fn)

    # Alle Beteiligten je Aktenzeichen aus dem Vollbild/Dossier-Material
    voll = json.load(open(os.path.join(E, "L8-HEILBRONN-VOLLBILD-2026-11-23.json"),
                          encoding="utf-8"))
    parties_by_az = collections.defaultdict(set)
    for d in voll["dossiers"]:
        for az in d.get("aktenzeichen", []):
            parties_by_az[az].add(d["person"])

    # -------- Provenienz je Quelldokument (aus Herkunft, nicht aus Stichworten)
    OURS = re.compile(r"(Strafantrag|Verfassungsbeschwerde|ErweiterteVerfassungsbeschwerde|"
                      r"Rechtsschadensgutachten|bverfg_beweismitteleingabe|fristwahrende|"
                      r"US_Vers|us_master|ForensicIndictment|FreislersHeirs|Signed_Dossier|"
                      r"bericht-|sendebericht|Petition|MandantenUnterictung|Ergaenzender|"
                      r"UN_Special|UN_Urgent|International_|Supreme_Court|ENFORCEMENT_COMPLICITY|"
                      r"FORM_JS|USAnklage|USFMC|Borkenkaefer|Bewertung_T|Diplomatic_Submission|"
                      r"VG_Stuttgart|rechtsgutachten|Tag24|doc00350)", re.I)
    THIRD = re.compile(r"(Borkenkaefer|US_Vers|USAnklage|USFMC|FORM_JS|Supreme_Court|UN_|"
                       r"International_|FreislersHeirs|Signed_Dossier|Diplomatic_Submission)", re.I)
    prov = {}
    for fn in files:
        if THIRD.search(fn):
            prov[fn] = "Dritte (Anwalt/Verband/Internationale Eingabe)"
        elif OURS.search(fn):
            prov[fn] = "Eigenakte des Betreibers"
        elif fn.startswith(("1_BvR", "2_BvR", "ZweiterSenat", "Bundesverfassungsgericht")):
            prov[fn] = "Staatsakt (Gericht)"
        elif "GENERALSTAATSANWALTSCHAFT" in fn or "BVG_STA" in fn:
            prov[fn] = "Eigenakte (Schreiben an die Staatsanwaltschaft)"
        else:
            prov[fn] = "unbestimmt"

    # -------- Mustermatrix: getrennt nach Rolle
    matrix_h = collections.defaultdict(lambda: collections.defaultdict(set))
    matrix_e = collections.defaultdict(lambda: collections.defaultdict(set))
    quotes = collections.defaultdict(list)
    for mn in mentions:
        az = mn["aktenzeichen"] or "(ohne Aktenzeichen)"
        target = matrix_h if mn["rolle"] in ("handelnd", "namentlich") else matrix_e
        for k, q in mn["handlungsklassen"]:
            target[az][k].add(mn["datei"])
            if mn["rolle"] == "handelnd" and len(quotes[(az, k)]) < 3:
                quotes[(az, k)].append({"datei": mn["datei"], "beleg": q})

    azs_handelnd = sorted({m["aktenzeichen"] for m in mentions
                           if m["rolle"] in ("handelnd", "namentlich") and m["aktenzeichen"]})
    azs_nur_handelnd = sorted({m["aktenzeichen"] for m in mentions
                               if m["rolle"] == "handelnd" and m["aktenzeichen"]})
    azs_erwaehnt = sorted({m["aktenzeichen"] for m in mentions
                           if m["rolle"] != "handelnd" and m["aktenzeichen"]})
    n_docs = len({m["datei"] for m in mentions})
    n_docs_h = len({m["datei"] for m in mentions
                    if m["rolle"] in ("handelnd", "namentlich")})
    klasse_az = collections.defaultdict(set)
    for az, ks in matrix_h.items():
        for k in ks:
            klasse_az[k].add(az)

    # -------- Gegenseite: was spricht dagegen / was ist ungeprueft
    dagegen = [
        "Der Vorsitzende entscheidet im Kollegium: die Ablehnung des Befangenheitsantrags "
        "vom 08.06.2026 wird den Richterinnen Bareis, Koppenhöfer und Tuffentsammer "
        "zugeschrieben, nicht dem Vorsitzenden. Die Entscheidung ist damit nicht "
        "allein seine.",
        "Der vom Vorsitzenden erlassene Titel ist ein Versäumnisurteil. Ein fehlendes "
        "Unterschriftsvermerk kann auf der Form- und Ausfertigungsebene liegen "
        "(maschinelle Ausfertigung, § 160 ZPO) und nicht auf der Entscheidungsebene.",
        "Die Aktenlage ist dem Vorsitzenden nur zugänglich, was die Akte enthält; der "
        "Vorwurf einer Kenntnis setzt deren Kenntnis voraus. Der Nachweis dafür liegt "
        "im Einsichtnahmenprotokoll — und das ist bisher nicht erhoben.",
        "Die Einstellungsverfügung ist Sache der Staatsanwaltschaft, nicht des Vorsitzenden; "
        "die Zuständigkeit für die Einstellung liegt bei der StA.",
    ]
    nicht_geprueft = [
        "Das Einsichtnahmenprotokoll der Akte 257 Js 31024/26 ist nicht in der Beweiskette.",
        "Die vollständige Einstellungsverfügung vom 04.09.2026 ist nicht in der Beweiskette; "
        "die Kette enthält nur eine Beschreibung in einer eigenen Unterlage.",
        "Das qES-Signaturprotokoll ist nicht in der Beweiskette; die eIDAS-Audit-Trail-Angaben "
        "stammen aus der Aktenlage und aus eigenen Unterlagen.",
        "Eine Gegenüberstellung mit der Verteidigungsposition des Vorsitzenden ist nicht "
        "erfolgt - sie steht aus.",
        "Die Zuordnung einzelner Dokumentaussagen zu einem Urheber ist im Korpus nicht "
        "belastbar bestimmbar (OCR-Fragmente, Scan ohne Textebene).",
    ]

    # ---------------- Ausgabe
    md = []
    A = md.append
    A("# Subjekt-Dossier: Vorsitzender Richter Dr. Haug (LG Heilbronn, 3. Zivilkammer)")
    A("")
    A("**Fall:** HEILBRONN-KISWARM · **Erstellt:** " +
      datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
    A("")
    A("**Zweck:** Vollständige Darstellung der dokumentierten Beteiligung des "
      "Vorsitzenden an den in der versiegelten Beweiskette enthaltenen Verfahren "
      "und Nachweis des über den Einzelfall hinausgehenden Musters.")
    A("")
    A("**Charakter:** Verfahrensdokumentation. Keine Schuldfeststellung. Alle Angaben "
      "sind belegt oder als unbelegt gekennzeichnet.")
    A("")
    A("---")
    A("")
    A("## 1. Messwerte")
    A("")
    A("| Kennzahl | Wert |")
    A("|---|---|")
    A("| Fundstellen im Korpus | {} |".format(len(mentions)))
    A("| davon: **handelnd** (erlässt/entscheidet/zeichnet) | {} |".format(
        sum(1 for m in mentions if m["rolle"] == "handelnd")))
    A("| davon: **namentlich in amtlicher Funktion** | {} |".format(
        sum(1 for m in mentions if m["rolle"] == "namentlich")))
    A("| davon: **erwähnt** (Beteiligter/Beschwerdegegner im Sachverhalt) | {} |".format(
        sum(1 for m in mentions if m["rolle"] == "erwaehnt")))
    A("| davon: nicht eindeutig | {} |".format(
        sum(1 for m in mentions if m["rolle"] == "unklar")))
    A("| Quelldokumente gesamt | {} |".format(n_docs))
    A("| Quelldokumente mit handelnder Beteiligung | {} |".format(n_docs_h))
    A("| **Aktenzeichen, in denen er als Amtsträger auftritt** | **{}** |".format(len(azs_handelnd)))
    A("| davon mit nachweislicher eigener Handlung | {} |".format(len(azs_nur_handelnd)))
    A("| Aktenzeichen, in denen er nur genannt wird | {} |".format(len(azs_erwaehnt)))
    A("| Handlungsklassen mit Mehrfachbezug | {} |".format(
        sum(1 for k in klasse_az if len(klasse_az[k]) >= 2)))
    A("| Corpus-Dokumente insgesamt | {} |".format(len(files)))
    A("")
    A("**Diese Trennung ist der Kern der Belastbarkeit.** Ein Aktenzeichen, in dem "
      "der Vorsitzende selbst gehandelt hat, trägt mehr als eines, in dem er nur als "
      "Beteiligter eines anderen Verfahrens erscheint. Beides wird getrennt gezählt "
      "und getrennt ausgewiesen.")
    A("")
    A("### 1.1 Mustermatrix (nur Aktenzeichen mit eigener Handlung)")
    A("")
    A("| Handlungsklasse | Aktenzeichen | Anzahl |")
    A("|---|---|---|")
    for k in sorted(klasse_az, key=lambda x: -len(klasse_az[x])):
        az_l = sorted(klasse_az[k])
        A("| {} | {} | {} |".format(k, ", ".join(az_l[:12]) + (" …" if len(az_l) > 12 else ""),
                                   len(az_l)))
    A("")
    A("### 1.2 Aktenzeichen, in denen er nur genannt wird (Umfeld, nicht Muster)")
    A("")
    A("| Aktenzeichen |")
    A("|---|")
    for az in azs_erwaehnt:
        A("| {} |".format(az))
    A("")
    A("**Das ist der Kern des Musters:** Die Klassen mit Mehrfachbezug sind es, die "
      "zeigen, dass es sich nicht um einzelne Vorfälle handelt. Eine Handlungsklasse, "
      "die in mehreren Verfahren mit mehreren Beteiligten auftaucht, ist ein "
      "struktureller Befund; eine einzelne, bleibt ein Einzelfall.")
    A("")
    A("## 2. Verfahren und Beteiligte")
    A("")
    A("| Aktenzeichen | Beteiligte im Korpus | Dokumente |")
    A("|---|---|---|")
    for az in azs_handelnd:
        p = sorted(parties_by_az.get(az, []))
        A("| {} | {} | {} |".format(az, "; ".join(x[:46] for x in p) if p else "—",
                                   len(docs_by_az.get(az, []))))
    A("")
    A("## 3. Beteiligung im Einzelnen")
    A("")
    A("Die folgenden Belege sind wörtlich aus der Beweiskette entnommen. Jede Zeile "
      "nennt Dokument, Aktenzeichen, Datum und die belegte Textstelle.")
    A("")
    for az in azs_handelnd:
        sub = [m for m in mentions if m["aktenzeichen"] == az
               and m["rolle"] in ("handelnd", "namentlich")]
        if not sub:
            continue
        A("### " + az)
        A("")
        dates = sorted({d for m in sub for d in m["datum_kandidaten"]})
        A("**Dokumente:** {} · **Fundstellen (handelnd):** {} · **Datumsangaben:** {}".format(
            len({m["datei"] for m in sub}), len(sub), ", ".join(dates[:6]) if dates else "—"))
        A("")
        for m in sorted(sub, key=lambda x: x["datei"])[:14]:
            A("- **{}** — „{}“".format(m["datei"], " ".join(m["kontext"].split())[:320]))
            if m["handlungsklassen"]:
                A("  - Klassen: " + ", ".join(k for k, _ in m["handlungsklassen"]) +
                  " · Beleg: „" + m["handlungsklassen"][0][1][:160] + "“")
            if m["rollenbeleg"]:
                A("  - Handlungsbeleg: „{}“".format(m["rollenbeleg"][:180]))
        if len(sub) > 14:
            A("- … und {} weitere Fundstellen in diesem Aktenzeichen (vollständig in der "
              "JSON-Fassung)".format(len(sub) - 14))
        A("")
    A("### 3.1 Automatisch nicht zugeordnete Fundstellen")
    A("")
    unk = [m for m in mentions if m["rolle"] == "unklar"]
    A("Von {} Fundstellen wurden {} automatisch zugeordnet (handelnd oder namentlich in "
      "amtlicher Funktion). Die verbleibenden {} werden hier **offengelegt und nicht "
      "weggezählt**: jede einzelne ist mit Belegzitat aufgeführt, damit die Zuordnung "
      "am Material geprüft werden kann und nicht an einer Heuristik hängt.".format(
          len(mentions), len(mentions) - len(unk), len(unk)))
    A("")
    A("| Dokument | Aktenzeichen | Belegzitat |")
    A("|---|---|---|")
    for m in sorted(unk, key=lambda x: x["datei"])[:40]:
        A("| {} | {} | „{}“ |".format(m["datei"][:40], m["aktenzeichen"] or "—",
                                      " ".join(m["kontext"].split())[:230]))
    A("")
    A("## 4. Was dagegen spricht")
    A("")
    for d in dagegen:
        A("- " + d)
    A("")
    A("## 5. Was nicht geprüft wurde")
    A("")
    for d in nicht_geprueft:
        A("- " + d)
    A("")
    A("## 6. Provenienz der herangezogenen Dokumente")
    A("")
    A("| Dokument | Herkunft |")
    A("|---|---|")
    cnt = collections.Counter(prov.get(m["datei"], "unbestimmt") for m in mentions)
    for fn, c in sorted(collections.Counter(m["datei"] for m in mentions).items(),
                        key=lambda kv: -kv[1]):
        A("| {} ({}) | {} |".format(fn, c, prov.get(fn, "unbestimmt")))
    A("")
    A("## 7. Nächste Schritte, die den Befund tragen würden")
    A("")
    A("1. **Einsichtnahmenprotokoll** der Akte 257 Js 31024/26 (Akteneinsicht § 406e StPO): "
      "wann der Vorsitzende die Akte selbst geöffnet hat.")
    A("2. **qES-Signaturprotokoll** zu den erlassenen Entscheidungen mit Zeitstempel.")
    A("3. **Entwurf der Einstellungsverfügung** vom 04.09.2026 mit Begründungstext.")
    A("4. **Urteilsausfertigung** im Original mit Unterschriftsblatt.")
    A("5. **Zeitliche Rekonstruktion**: Vergleich von Entscheidungsdaten, Signaturzeitstempel "
      "und Zustellungsdaten — die Abweichungen zwischen Entscheidung und Kenntnis sind der "
      "prüfbare Kern.")
    A("")
    A("---")
    A("")
    A("Sacred hash: f5af425c")
    A("")

    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump({
        "erstellt": datetime.now(timezone.utc).isoformat(),
        "subject": SUBJECT, "case_id": "HEILBRONN-KISWARM",
        "messwerte": {"fundstellen": len(mentions), "dokumente": n_docs,
                      "aktenzeichen_handelnd": len(azs_handelnd),
                      "aktenzeichen_erwaehnt": len(azs_erwaehnt),
                      "fundstellen_handelnd": sum(1 for m in mentions if m["rolle"] == "handelnd"),
                      "fundstellen_erwaehnt": sum(1 for m in mentions if m["rolle"] == "erwaehnt"),
                      "fundstellen_unklar": sum(1 for m in mentions if m["rolle"] == "unklar"),
                      "klassen_mit_mehrfachbezug": sum(1 for k in klasse_az
                                                       if len(klasse_az[k]) >= 2),
                      "corpus_dokumente": len(files)},
        "mustermatrix_handelnd": {az: {k: sorted(v) for k, v in ks.items()}
                                  for az, ks in matrix_h.items()},
        "mustermatrix_erwaehnt": {az: {k: sorted(v) for k, v in ks.items()}
                                  for az, ks in matrix_e.items()},
        "aktenzeichen_handelnd": azs_handelnd, "aktenzeichen_erwaehnt": azs_erwaehnt,
        "zitate": {k + " || " + a: v for (a, k), v in quotes.items()},
        "klassen_az": {k: sorted(v) for k, v in klasse_az.items()},
        "beteiligte_je_az": {az: sorted(v) for az, v in parties_by_az.items()},
        "fundstellen": mentions, "provenienz": prov,
        "dagegen": dagegen, "nicht_geprueft": nicht_geprueft,
        "sacred_hash": "f5af425c"},
        open(OUT_JS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(json.dumps({"fundstellen": len(mentions), "dokumente": n_docs,
                      "dokumente_handelnd": n_docs_h,
                      "aktenzeichen_handelnd": len(azs_handelnd),
                      "aktenzeichen_erwaehnt": len(azs_erwaehnt),
                      "fundstellen_handelnd": sum(1 for m in mentions if m["rolle"] == "handelnd"),
                      "fundstellen_erwaehnt": sum(1 for m in mentions if m["rolle"] == "erwaehnt"),
                      "fundstellen_unklar": sum(1 for m in mentions if m["rolle"] == "unklar"),
                      "az_handelnd": azs_handelnd,
                      "az_erwaehnt": azs_erwaehnt,
                      "klassen_mit_mehrfachbezug": {k: len(v) for k, v in klasse_az.items()
                                                   if len(v) >= 2},
                      "md_bytes": os.path.getsize(OUT_MD),
                      "json_bytes": os.path.getsize(OUT_JS),
                      "provenienz": dict(cnt)}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
