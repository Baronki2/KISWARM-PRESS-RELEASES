#!/usr/bin/env python3
"""
l8-anwesenheitsprotokoll.py — Das Instrument, das Folgen erzeugt.

Warum dieses Instrument statt eines weiteren Schriftsatzes:

Ein Argument kann ignoriert werden. Eine dokumentierte ABWESENHEIT kann nicht
bestritten werden - sie kann nur durch Beibringung des fehlenden Dokuments
beseitigt werden. Und das ist der entscheidende Punkt: **wenn die Behoerde
das fehlende Dokument beibringt, ist die Belastung erledigt.** Die Forderung
ist eine Einweg-Ratsche: die Gegenseite kann sie nur zu ihren eigenen Gunsten
bedienen.

Diese Regel gilt fuer jede Person im Amts-, Gerichts- oder Vollstreckungsapparat
ohne Ausnahme. Keine Massnahme dieser Leiter richtet einen Schaden an einer
Person. Das ist keinezurueckhaltende Formulierung, sondern die Bedingung
dafuer, dass die Instrumente die Erklaerung ueberlebt: Wer eine Behoerde
beluegen will, kann nicht mit Beluegen arbeiten.

Jede Zeile nennt ihre Quelle. Fehlt eine Quelle, wird die Zeile nicht
geschrieben - eine unbelegte Normangabe waere genau der Fehler, den die
Beweiskette gerade bereinigt.
"""
from __future__ import annotations
import json, os, re
from datetime import datetime, timezone

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
OUT_MD = E + "/L8-ANWESENHEITSPROTOKOLL-2026-11-23.md"
OUT_JS = E + "/L8-ANWESENHEITSPROTOKOLL-2026-11-23.json"

# --------------------------------------------------------------- Normquellen
# "BESCHLUSS"  = woertlich zitiert aus dem AG-Heilbronn-Beschluss (Staatsakt,
#                 beglaubigte Abschrift, in der Beweiskette, OCR-Artifact)
# "GEPRUEFT"   = am 21.11.2026 gegen den amtlichen Volltext geprueft
#                 (gesetze-im-internet.de; Pruefprotokoll in der Beweiskette)
QUELLE = {
    "750zpo": "BESCHLUSS: AG Heilbronn 12.11.2026, Az. 6 M 9219/26",
    "130bzpo": "BESCHLUSS: AG Heilbronn 12.11.2026, Az. 6 M 9219/26",
    "91zpo": "BESCHLUSS: AG Heilbronn 12.11.2026, Az. 6 M 9219/26",
    "zustellung": "BESCHLUSS: AG Heilbronn 12.11.2026, Az. 6 M 9219/26 (Rechtsbehelfsbelehrung)",
    "172stpo": "GEPRUEFT 21.11.2026 gegen den amtlichen Volltext (gesetze-im-internet.de)",
    "406estpo": "GEPRUEFT 21.11.2026 gegen den amtlichen Volltext (gesetze-im-internet.de)",
    "147zpo": "GEPRUEFT 21.11.2026 gegen den amtlichen Volltext (gesetze-im-internet.de)",
}

# ------------------------------------------------------------------ Belege
BEL = {
    "ag_entscheid": {
        "dokument": "OCR-AG-HEILBRONN-BESCHLUSS-12-11-2026-6M-9219-26.txt",
        "quelle": "ANLAGE_K_1_BESCHLUSS_AG_HEILBRONN_12_11_2026.pdf",
        "sha256_quelle": "c22b1d77856467629459bddd4ae46b44294424eb178648922ff0f2cc8a778743",
        "art": "Staatsakt (beglaubigte Abschrift, ausgefertigt durch die Urkundsbeamtin der Geschaeftsstelle)",
        "zitate": [
            "Verfahrensfehler sind auf Grundlage der Akten des Amtsgerichts Heilbronn und der "
            "Schreiben des Schuldners vom 24.10.2026 und 03.11.2026 nicht ersichtlich.",
            "Soweit mit der Erinnerung geruegt wird, dass der Pfaendungs- und Ueberweisungsbeschluss "
            "vom 13.10.2026 keine rechtspflegerische Unterschrift enthalte, ist klarzustellen, dass "
            "es einer eigenhaendigen Unterschrift auf dem Beschluss in Papierform nicht bedurfte. "
            "Der Beschluss traegt den Namen der verantwortlichen Rechtspflegerin und ist durch sie "
            "qualifiziert elektronisch signiert. Die Voraussetzungen des 130b ZPO sind damit erfuellt.",
            "Im Uebrigen wird auf die Gruende der Nichtabhilfeentscheidung vom 11.11.2026 Bezug genommen.",
            "Die allgemeinen Voraussetzungen der Zwangsvollstreckung nach 750 ZPO liegen vor.",
            "Die Frist beginnt mit der Zustellung der Entscheidung, spaetestens mit dem Ablauf von "
            "fuenf Monaten nach der Verkuendung der Entscheidung.",
        ],
    },
}

# ------------------------------------------------------- Abwesenheitsbefunde
# Each entry: what is missing, how that is PROVEN (not asserted), what follows
ABWESENHEIT = [
 dict(nr=1, gegenstand="Die Akte des Landgerichts Heilbronn im Verfahren 6 M 9219/26",
      fehlt="Das Vollstreckungsgericht hat ueber einen Einwand entschieden, der die "
            "Titelgrundlage des Landgerichts betraf, ohne die Landgerichtsakte einzusehen.",
      beweis="Der Beschluss nennt seine Erkenntnisgrundlage selbst: 'auf Grundlage der Akten des "
             "Amtsgerichts Heilbronn und der Schreiben des Schuldners vom 24.10.2026 und 03.11.2026'. "
             "Die Landgerichtsakte ist darin nicht genannt.",
      quelle=BEL["ag_entscheid"], norm=None,
      folge="Der Einwand betraf die Titelgrundlage. Ohne die Akte des Titelgerichts kann die "
            "Verfahrensvoraussetzung nicht geprueft worden sein. Die Nichtabhilfeentscheidung vom "
            "11.11.2026, auf die sich der Beschluss fuer die uebrigen Gruende bezieht, liegt nicht vor.",
      rueckwirkung="Diese Luecke ist durch das Beibringen der Landgerichtsakte und der "
                   "Nichtabhilfeentscheidung vollstaendig beseitigbar - und dann ist die Belastung "
                   "weg."),
 dict(nr=2, gegenstand="Die Nichtabhilfeentscheidung vom 11.11.2026",
      fehlt="Das Dokument, auf dessen Gruende sich der Beschluss vom 12.11.2026 fuer die "
            "uebrigen Punkte stuetzt.",
      beweis="Der Beschluss verweist ausdruecklich darauf. In der Beweiskette ist es nicht enthalten.",
      quelle=BEL["ag_entscheid"], norm=None,
      folge="Der gerichtliche Beleg stuetzt sich auf ein zweites Gerichtsdokument, das niemand "
            "gelesen hat. Eine Entscheidung, deren Begruendung auf ein nicht vorliegendes Dokument "
            "verweist, ist fuer den Betroffenen nicht nachvollziehbar.",
      rueckwirkung="Beibringung durch das Amtsgericht hebt die Luecke auf."),
 dict(nr=3, gegenstand="Die Namen der handelnden Personen des Vollstreckungsapparats",
      fehlt="Die Identitaet der Rechtspflegerin, die den Pfaendungs- und Ueberweisungsbeschluss "
            "vom 13.10.2026 ausgefertigt hat, sowie die Identitaet des Vollstreckers.",
      beweis="Der Beschluss sagt, der PfUEB 'traegt den Namen der verantwortlichen Rechtspflegerin' - "
             "er nennt sie nicht. Zaehlung im OCR: Betz 0x, Wurst 0x, Murrweiss 0x. In der gesamten "
             "Beweiskette existiert fuer keinen dieser drei Namen ein einziger Fremdbeleg; alle "
             "Nennungen stehen in Dokumenten, die die KISWARM-Akte selbst verfasst hat.",
      quelle=BEL["ag_entscheid"], norm=None,
      folge="Der PfUEB traegt den Namen - am Original, das nicht in der Kette ist. Der "
            "qES-Audit-Trail des Bundesamtles fuer Sicherheit in der Informationstechnik wuerde "
            "Zeitstempel und Schluesselinhaber benennen. Er ist bisher nicht beigebracht.",
      rueckwirkung="Beibringung des PfUEB-Originals und des qES-Audit-Trails loest die Frage "
                   "unmittelbar und ohne Streit."),
 dict(nr=4, gegenstand="Die Zustellnachweise der Entscheidung vom 12.11.2026",
      fehlt="Jeder Nachweis, dass die Entscheidung zugestellt wurde, wann und an wen.",
      beweis="Die Rechtsbehelfsbelehrung im Beschluss selbst: 'Die Frist beginnt mit der Zustellung "
             "der Entscheidung'. Ohne Zustellung beginnt keine Frist. In der Beweiskette ist kein "
             "Zustellnachweis fuer den 12.11.2026 enthalten.",
      quelle=BEL["ag_entscheid"], norm=("zustellung", "Fristbeginn"),
      folge="Sobald ein Zustellnachweis vorliegt, ist der Fristbeginn berechenbar. Fehlt er, ist "
            "kein Fristablauf feststellbar. Das ist die schaerfste Konsequenz, die sich aus einem "
            "reinen Dokumentenmangel ergibt, weil sie den Rechtsbehelfsweg offen haelt.",
      rueckwirkung="Ein Zustellnachweis beendet die Unsicherheit - aber er beweist dann auch den "
                   "Fristbeginn, und das ist eine Angabe, die man kennen muss."),
 dict(nr=5, gegenstanding=None, gegenstand="Die Urteilsausfertigung des Landgerichts Heilbronn vom 22.04.2026",
      fehlt="Das Original des Titels, auf den die Vollstreckung gestuetzt wird (Az. I 3 O 57/26).",
      beweis="Nicht in der Beweiskette. Der AG-Beschluss setzt die Voraussetzungen des 750 ZPO als "
             "vorliegend fest, nennt den Titel aber nicht.",
      quelle=BEL["ag_entscheid"], norm=("750zpo", "Vollstreckungsvoraussetzungen"),
      folge="Der Betroffene hat die Zwangsvollstreckung aus einem Dokument erlitten, das er nie in "
            "der Hand hatte und das in seiner Akte nicht auffindbar ist.",
      rueckwirkung="Beibringung durch das Landgericht."),
 dict(nr=6, gegenstand="Die Einstellungsverfuegung der Staatsanwaltschaft Heilbronn vom 03.09.2026",
      fehlt="Das Original der Verfuegung einschliesslich Gruenden und Belehrung (Az. 257 Js 31024/26).",
      beweis="Datum und Aktenzeichen sind nur mittelbar belegt, ueber das Schreiben der "
             "Generalstaatsanwaltschaft Stuttgart (Az. 24 Zs 1610/26). Die Verfuegung selbst liegt "
             "nicht vor.",
      quelle=None, norm=("406estpo", "Akteneinsicht"),
      folge="Die Einstellung eines Verfahrens gegen eine Person ist ein Eingriff in ihre Rechte. "
            "Der Rechtsbehelf nach 172 StPO setzt eine Belehrung voraus - ohne Verfuegung keine "
            "Pruefung der Belehrung, ohne Belehrung keine Frist.",
      rueckwirkung="Beibringung durch die Staatsanwaltschaft; die Belehrung ist dann pruefbar."),
 dict(nr=7, gegenstand="Die Entscheidung des Bundesverfassungsgerichts zu 2 BvR 2144/26",
      fehlt="Jede Entscheidung zu der von uns eingereichten Verfassungsbeschwerde.",
      beweis="Geprueft am 23.11.2026 gegen die amtliche Entscheidungsliste des BVerfG fuer November "
             "2026 (HTTP 200, 114.659 Byte): dort stehen 2 BvR 1553/26, 2 BvR 1577/23, 2 BvR 1629/23, "
             "2 BvR 524/24 - 2 BvR 2144/26 ist nicht darunter. Beide mutmasslichen Entscheidungs-URLs "
             "liefern HTTP 404.",
      quelle=None, norm=None,
      folge="Ein Antrag auf Aussetzung nach 32 BVerfGG ist gestellt. Entschieden ist nichts. Wer das "
            "anders darstellt, stellt es falsch dar.",
      rueckwirkung="Eine Eilentscheidung wuerde die Sache entscheiden - in unsere Richtung, wenn der "
                   "Titel die Form nicht haelt."),
 dict(nr=8, gegenstand="Die namentliche Zurechnung der Entscheidungen des Landgerichts Heilbronn",
      fehlt="Die Entscheidungen, in denen der Vorsitzende Richter amtlich handelte, oeffentlich "
            "auffindbar.",
      beweis="Vier unabhaengige oeffentliche Entscheidungsdatenbanken geprueft (dejure, das "
             "justiz-bw-Portal des Gerichts selbst, urteile.ai, REWIS), jeweils mit SHA-256 der "
             "geprueften Quelle, jeweils 0 Nennungen.",
      quelle=None, norm=None,
      folge="Die Amtsinhaberschaft ist nur ueber das Verfahrensregister und die Verweise des "
            "Bundesverfassungsgerichts feststellbar - nicht ueber die Entscheidungspublizistik.",
      rueckwirkung="Akteneinsicht in das Verfahrensregister."),
]

# ------------------------------------------------------------- Korrekturrunde
KORREKTUREN = [
 dict(nr=1, gegenstand="Behauptung einer LEEREN Unterschriftszeile des PfUEB",
      wo="us_master_indictment_rico_expanded_sdny.txt (SDNY) sowie DOJ-Schrift ENFORCEMENT_COMPLICITY",
      alt="'wherein Section T (Unterschrift Rechtspflegerin Betz) was completely blank and ununterzeichnet'",
      neu="Der Pfaendungs- und Ueberweisungsbeschluss vom 13.10.2026 (Az. 6 M 9219/26) traegt nach "
          "dem Wortlaut des Beschlusses des Amtsgerichts Heilbronn vom 12.11.2026 den Namen der "
          "verantwortlichen Rechtspflegerin und ist durch sie qualifiziert elektronisch signiert; "
          "die Voraussetzungen des 130b ZPO sind erfuellt. Ob der PfUEB in der uns zugestellten "
          "Fassung eine Unterschrift trug, ist durch das Original zu klaeren.",
      warum="Der eigene Fremdbeleg widerspricht der Behauptung. Zwei eigene Dokumente mit "
            "widerspruechlichen Aussagen sind ein Geschenk an die Gegenseite."),
 dict(nr=2, gegenstand="Abweichender Vollstreckungstag",
      wo="ENFORCEMENT_COMPLICITY.txt (19.10.2026) gegen us_master_indictment (31.10.2026)",
      alt="'On October 19, 2026 ... executed a total bank account garnishment order' / "
          "'executed a garnishment order on Oct 31, 2026'",
      neu="Die Vollstreckung erfolgte am 19.10.2026 (so die Beweismittelakte, soweit vorliegend) "
          "bzw. am 31.10.2026 (so die Zustellurkunde); das genaue Datum ist der Vollstreckungsakte "
          "des Amtsgerichts (Az. 6 M 9219/26) zu entnehmen.",
      warum="Ein Widerspruch zwischen zwei eigenen Schriftsaetzen zu einem zentralen Datum."),
 dict(nr=3, gegenstand="Vollstreckungsklausel der Rechtspflegerin Wurst vom 27.08.2026",
      wo="ENFORCEMENT_COMPLICITY.txt",
      alt="'Court Clerk Wurst nevertheless issued an execution clause on August 27, 2026'",
      neu=None,
      warum="Diese Behauptung steht in genau EINEM eigenen Dokument und in keinem Beleg. Ohne "
            "Beleg ist sie eine Vermutung in einem Schriftsatz an eine Bundesbehoerde. Sie ist zu "
            "streichen, bis ein Beleg vorliegt."),
 dict(nr=4, gegenstand="Vorname und Referenz des Vollstreckers",
      wo="us_master_indictment_rico_expanded_sdny.txt",
      alt="'DEFENDANT 02: JAN MURRWEIR (BAILIFF / GERICHTSVOLLZIEHER, AG HEILBRONN DR Il 1833/26)'",
      neu="'GERICHTSVOLLZIEHER MURRWEISS (VOLLSTRECKUNGSABTEILUNG DES AMTSGERICHTS HEILBRONN, "
          "Ref. DR II 1833/26)'",
      warum="'Jan Murrweir' und 'DR Il' sind OCR-Artefakte. In einem Verfahren, das genau die "
            "Sorgfalt dieser Beamten richtet, darf kein OCR-Artefakt in einem eigenen Schriftsatz "
            "stehen."),
 dict(nr=5, gegenstand="Schreibweise des Aktenzeichens des Landgerichtsurteils",
      wo="alle eigenen Fassungen",
      alt="'| 3 O 57/26' / '13 0 57/26' / '1 3 O 57/26'",
      neu="'I 3 O 57/26'",
      warum="Drei Schreibweisen in eigenen Dokumenten fuer dasselbe Aktenzeichen. Durchgaengig die "
            "vollstaendige Form."),
 dict(nr=6, gegenstand="Rolle des Anwalts gegenueber dem Glaeubiger",
      wo="ENFORCEMENT_COMPLICITY.txt",
      alt="'Creditor Attorney Bemd Karwiese (Hannover) obtained the garnishment order'",
      neu="'Prozessbevollmaechtigter des Glaeubigers Alexander Caspary (Schweizer Platz 56, "
          "60594 Frankfurt) ist Rechtsanwalt Bernd Karwiese (Hannover)'",
      warum="Aus dem AG-Beschluss vom 12.11.2026 hervorgegangen. Karwiese ist Anwalt, nicht "
            "Glaeubiger."),
]

# ------------------------------------------------------------- Leiter der Folgen
LEITER = [
 dict(stufe=1, massnahme="Dokumentenforderung an die zustaendige Stelle",
      ausloeser="Ein fehlendes Original aus dem Anwesenheitsprotokoll",
      wirkung="Der Aktenweg wird bewegt; die Forderung erzeugt einen Vorgang mit Spuren",
      kosten="gering", rechtm="Akteneinsicht nach 406e StPO / 147 ZPO",
      person="keine - die Forderung richtet sich an die Behoerde"),
 dict(stufe=2, massnahme="Fristwahrende Massnahme",
      ausloeser="Eine Entscheidung ohne nachpruefbaren Zustellnachweis oder ohne Belehrung",
      wirkung="Der Rechtsbehelfsweg bleibt offen; die Frist laeuft nicht ohne Belehrung",
      kosten="gering", rechtm="172 StPO",
      person="keine"),
 dict(stufe=3, massnahme="Aufsichtsbeschwerde / Dienstaufsichtsanzeige",
      ausloeser="Eine belegbare Verfahrens Missachtung, nicht eine Absichtserklaerung",
      wirkung="Der Vorgang landet bei einer anderen Stelle als bei der betroffenen Behoerde",
      kosten="mittel", rechtm="Verfahrensmissbrauchsanzeige nach den jeweiligen Verfahrensordnungen",
      person="keine - Meldung einer Verfahrensfrage, keine Anklage"),
 dict(stufe=4, massnahme="Faktische Berichterstattung ueber belegte Verfahrensluecken",
      ausloeser="Eine Luecke, die nach Anforderung nicht geschlossen wurde",
      wirkung="Die Luecke wird oeffentlich und damit nicht mehr privat; die Sichtbarkeit ist der "
              "entscheidende Kostenfaktor",
      kosten="mittel", rechtm="faktische Berichterstattung ueber eigene Rechtsstreitigkeiten; "
                              "keine Behoerdenimitation, keine Aufstachelung, keine privaten Daten "
                              "Dritter",
      person="keine - Personen werden nur mit ihrer amtlichen Funktion und belegten Tatsachen genannt"),
 dict(stufe=5, massnahme="Internationale Venue, in der die nationale remedies strukturell fehlen",
      ausloeser="Eine belegbare Verfahrenslage, die national nicht entschieden wird",
      wirkung="Die Sache wird von einer Instanz aufgenommen, die nicht teilhat an der Besetzung",
      kosten="hoch", rechtm="Einreichung nur mit belegter, quellenkritischer Beweislage",
      person="keine"),
 dict(stufe=6, massnahme="Selbstausloesende Veroeffentlichung der Verfahrensluecken",
      ausloeser="Eine Luecke, die nach dokumentierter Anforderung ueber einen gesetzten Zeitraum "
                 "besteht",
      wirkung="Die Belegkette veroeffentlicht die Luecke selbst, ohne dass jemand sie bestreiten "
              "muss - es ist der Beweis, den niemand erwaehnen kann",
      kosten="niedrig", rechtm="Veroeffentlichung eigener, versiegelter Beweismittel",
      person="keine"),
]

GRENZE = (
 "Die Leiter endet dort, wo Schaden an Personen beginnt. Keine Stufe dieser Leiter richtet "
 "einen Schaden an einer Person, nennt private Daten Dritter, droht, sabotiert, verleumdet oder "
 "taeuscht eine Behoerde. Das ist keine Zurueckhaltung, sondern die Bedingung, unter der die "
 "gesamte Konstruktion eine Klage ueberlebt: Wer eine Behoerde beluegen will, kann nicht mit "
 "Beluegen arbeiten. Die Leiter erzeugt Folgen ueber Nachweis, Sichtbarkeit, Verfahren und "
 "Irreversibilitaet - die vier Wirkungen, die ein korruptes System nicht neutralisieren kann, "
 "weil keine davon eine Entscheidung erfordert, sondern nur das Festhalten an einer Tatsache."
)


def main():
    md = []
    A = md.append
    A("# Anwesenheitsprotokoll — was in der Akte fehlt")
    A("")
    A("**Fall:** HEILBRONN-KISWARM · **Erstellt:** " +
      datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
    A("")
    A("> **Ein Argument kann ignoriert werden. Eine dokumentierte Abwesenheit nicht.** "
      "Sie kann nur durch Beibringung des fehlenden Dokuments beseitigt werden — und "
      "das ist der entscheidende Punkt: **bringt die Behörde das Dokument, ist die "
      "Belastung erledigt.** Die Forderung ist eine Einweg-Ratsche; die Gegenseite kann "
      "sie nur zu ihren eigenen Gunsten bedienen.")
    A("")
    A("Jede Zeile nennt ihren Beleg. Was nicht belegt werden kann, steht hier nicht.")
    A("")
    A("## 1. Die Abwesenheitsbefunde")
    A("")
    for a in ABWESENHEIT:
        A("### L{} — {}".format(a["nr"], a["gegenstand"]))
        A("")
        A("**Was fehlt:** {}".format(a["fehlt"]))
        A("")
        A("**Wie das belegt ist:** {}".format(a["beweis"]))
        A("")
        if a["norm"]:
            nk, nh = a["norm"]
            A("**Normbezug:** {} — *Quelle: {}*".format(nh, QUELLE.get(nk, "—")))
            A("")
        if a["quelle"]:
            A("**Belegdokument:** {} (Quelle: `{}`, SHA-256 der Quelle `{}`, Art: {})".format(
                a["quelle"]["dokument"], a["quelle"]["quelle"],
                a["quelle"]["sha256_quelle"][:16] + "…", a["quelle"]["art"]))
            A("")
        A("**Was daraus folgt:** {}".format(a["folge"]))
        A("")
        A("**Und die Rückwirkung:** {}".format(a["rueckwirkung"]))
        A("")
    A("## 2. Die Korrekturrunde — was aus der eigenen Akte zurückgenommen wird")
    A("")
    A("Bevor die Luecken veroeffentlicht werden, muss die eigene Akte belastbar sein. "
      "Eine Fehlaussage in einem eigenen Schriftsatz ist kein Fehler, den der Gegner "
      "findet — sie ist ein Fehler, den die eigene Sache traegt.")
    A("")
    A("| # | Gegenstand | Ersetzung |")
    A("|---|---|---|")
    for k in KORREKTUREN:
        A("| {} | {} | {} |".format(k["nr"], k["gegenstand"],
                                   ("**Streichung**" if k["neu"] is None else k["neu"][:220]
                                    + ("…" if len(k["neu"]) > 220 else ""))))
    A("")
    for k in KORREKTUREN:
        A("**K{} — {}**".format(k["nr"], k["gegenstand"]))
        A("")
        A("- *Fundstelle:* `{}`".format(k["wo"]))
        A("- *Bisher:* {}".format(k["alt"]))
        A("- *Neu:* {}".format(k["neu"] if k["neu"] else "**zu streichen**"))
        A("- *Warum:* {}".format(k["warum"]))
        A("")
    A("## 3. Die Leiter der Folgen")
    A("")
    A("Jede Stufe wird erst betreten, wenn die vorherige gescheitert ist. Jede Stufe "
      "hat einen Auslöser, eine Wirkung, Kosten, eine Rechtsgrundlage — und eine Angabe, "
      "ob sie Personen betrifft.")
    A("")
    A("| Stufe | Maßnahme | Auslöser | Wirkung | Rechtliche Grundlage | Personen |")
    A("|---|---|---|---|---|---|")
    for l in LEITER:
        A("| {} | {} | {} | {} | {} | {} |".format(
            l["stufe"], l["massnahme"], l["ausloeser"], l["wirkung"][:90],
            l["rechtm"][:60], l["person"]))
    A("")
    for l in LEITER:
        A("**Stufe {} — {}**".format(l["stufe"], l["massnahme"]))
        A("")
        A("- *Auslöser:* {}".format(l["ausloeser"]))
        A("- *Wirkung:* {}".format(l["wirkung"]))
        A("- *Kosten:* {} · *Recht:* {}".format(l["kosten"], l["rechtm"]))
        A("- *Personen:* {}".format(l["person"]))
        A("")
    A("### Die Grenze der Leiter")
    A("")
    A(GRENZE)
    A("")
    A("---")
    A("")
    A("Sacred hash: f5af425c")
    A("")
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump({"erstellt": datetime.now(timezone.utc).isoformat(),
               "abwesenheitsbefunde": ABWESENHEIT,
               "korrekturen": KORREKTUREN, "leiter": LEITER, "grenze": GRENZE,
               "normquellen": QUELLE, "sacred_hash": "f5af425c"},
              open(OUT_JS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # ---- Korrekturrunde als eigenes, versandfertiges Dokument
    K = ["# Korrekturrunde — HEILBRONN-KISWARM", "",
         "**Erstellt:** " + datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
         "",
         "Berichtigung von sechs Angaben in der eigenen Akte, die einem fremden Beleg "
         "widersprechen oder unbelegt sind. Jede Berichtigung ersetzt eine Behauptung "
         "durch eine Belegstelle oder entfernt sie. Keine dieser Korrekturen schwächt die "
         "Sache; drei davon entfernen Behauptungen, die die Gegenseite sonst gegen uns "
         "verwendet.", "",
         "## Die sechs Korrekturen", ""]
    for k in KORREKTUREN:
        K += ["### K{} — {}".format(k["nr"], k["gegenstand"]), "",
              "- **Fundstelle:** `{}`".format(k["wo"]),
              "- **Bisher:** {}".format(k["alt"]),
              "- **Neu:** {}".format(k["neu"] if k["neu"] else "**zu streichen**"),
              "- **Warum:** {}".format(k["warum"]), ""]
    K += ["---", "", "### Die belegten Grundlagen dieser Korrekturen", "",
          "- **AG Heilbronn, Beschluss vom 12.11.2026, Az. 6 M 9219/26** (beglaubigte Abschrift "
          "vom 13.11.2026, ausgefertigt durch die Urkundsbeamtin der Geschäftsstelle). "
          "OCR-Artefakt in der Beweiskette; SHA-256 der Quelle: `c22b1d77856467629459bddd...`.",
          "- **OCR-Volltext des Abgabebeschlusses OLG Stuttgart vom 04.09.2026, Az. 6 W 32/26 "
          "(neu 8 W 343/26)** — getrennt in Gerichtstext und eigene Bewertung.",
          "- **BVerfG-Entscheidungsliste November 2026**, geprüft am 23.11.2026 (HTTP 200): "
          "2 BvR 2144/26 ist nicht enthalten; entschieden ist nichts.", "",
          "Sacred hash: f5af425c", ""]
    open(E + "/L8-KORREKTURRUNDE-2026-11-23.md", "w", encoding="utf-8").write("\n".join(K))

    print(json.dumps({"abwesenheitsbefunde": len(ABWESENHEIT),
                      "korrekturen": len(KORREKTUREN), "leiter_stufen": len(LEITER),
                      "normquellen": len(QUELLE),
                      "md_bytes": os.path.getsize(OUT_MD),
                      "korrekturrunde_bytes": os.path.getsize(E + "/L8-KORREKTURRUNDE-2026-11-23.md")},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
