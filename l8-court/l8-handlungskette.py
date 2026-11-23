#!/usr/bin/env python3
"""
l8-handlungskette.py — Die Handlungskette AG/LG/STA, Gelenk fuer Gelenk.

Drei Ebenen, getrennt gewichtet — wie im Haug-Gesamtbild:
  A KORPUS        Fundstellen in der versiegelten Beweiskette
  B STAATSAKT     was ein Gericht selbst geschrieben hat (unabhaengig)
  C RECHERCHE     unabhaengige oeffentliche Quellen

Der Kern ist nicht die Kette selbst, sondern der BELEGZUSTAND jedes Gelenks:
  (a) durch Staatsakt belegt      — ein Gericht hat es selbst geschrieben
  (b) nur durch eigene Akte      — unsere Angabe, kein Fremdbeleg
  (c) in der eigenen Akte widerspruechlich — unsere Dokumente sagen Verschiedenes
  (d) fehlend                     — das Original existiert, wir haben es nicht

Die Kette ist so stark wie ihr schwaechstes Gelenk. Dieser Satz ist der
Zweck des Dokuments.

REGEL (L8 Court Record 012): Ein Dokument, das WIR eingereicht haben, ist nie ein
Beleg dafuer, was ein Gericht entschieden hat. Jede Zelle unten nennt ihre Quelle.
"""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys
from datetime import datetime, timezone

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
O = E + "/OCR-VOLLTEXT"
OUT_MD = E + "/L8-HANDLUNGSKETTE-AG-LG-STA-2026-11-23.md"
OUT_JS = E + "/L8-HANDLUNGSKETTE-AG-LG-STA-2026-11-23.json"

# ---------------------------------------------------------------- Gelenke
# beleg: (a) staatsakt | (b) eigene akte | (c) eigene akte widerspruechlich | (d) fehlend
GELENKE = [
 dict(nr=1, datum="22.04.2026", akte="I 3 O 57/26",
      amt="LG Heilbronn, 3. Zivilkammer — Vorsitzender Richter Dr. Haug",
      handlung="Versaeumnisurteil ueber 1.400.000,00 EUR; Ausfertigung ohne eigenhaendige Unterschrift",
      beleg="(b)", belegquelle="nur eigene Akte",
      was_fehlt="Die Urteilsausfertigung liegt NICHT in der Kette. Der AG-Beschluss vom 12.11.2026 setzt 'die allgemeinen Voraussetzungen der Zwangsvollstreckung nach 750 ZPO liegen vor' voraus, nennt das Urteil aber nicht.",
      was_trägt="Der AG-Beschluss bestätigt die EXISTENZ eines nach 750 ZPO vollstreckbaren Titels - das ist ein gerichtlicher Beleg fuer die Tatsache der Vollstreckbarkeit, nicht fuer die Behauptung der Nicht-Unterschrift."),
 dict(nr=2, datum="07.07.2026", akte="13 O 57/26",
      amt="LG Heilbronn",
      handlung="Beschluss im Rechtsmittelverfahren (Referent in der Verfassungsbeschwerde 2 BvR 2145/26 benannt)",
      beleg="(b)", belegquelle="nur eigene Akte",
      was_fehlt="Der Beschluss selbst liegt nicht vor; wir kennen ihn nur aus unserer eigenen Verfassungsbeschwerde.",
      was_trägt="Nichts eigenstaendig."),
 dict(nr=3, datum="04.09.2026", akte="6 W 32/26 (neu 8 W 343/26)",
      amt="OLG Stuttgart, 6. Zivilsenat — VRiOLG Dr. Oliver Mosthaf",
      handlung="Abgabebeschluss / Ueberleitung in den neuen Senat",
      beleg="(a)", belegquelle="Staatsakt: Abgabebeschluss OLG Stuttgart vom 04.09.2026 (beglaubigte Abschrift in der Kette)",
      was_fehlt="Die Urkunde der Bestaetigung, dass die Kostenentscheidung auf die qES-Unterschrift des Mosthaf beruht (eIDAS-Audit-Trail 10.09.2026) ist im Original nicht beigefuegt.",
      was_trägt="Der Beschluss ist ein Original und belegt die Verfahrensfuehrung des OLG im September 2026."),
 dict(nr=4, datum="03.09.2026", akte="257 Js 31024/26",
      amt="Staatsanwaltschaft Heilbronn — OStA Dr. Singer",
      handlung="Einstellungsverfuegung (Einstellung des Ermittlungsverfahrens)",
      beleg="(b)", belegquelle="nur ueber das Schreiben der GStA Stuttgart, Az. 24 Zs 1610/26",
      was_fehlt="Das ORIGINAL der Einstellungsverfuegung liegt nicht in der Kette - weder Einstellungsbescheid noch Entwurf, weder Gruende noch Belehrung.",
      was_trägt="Datum und Aktenzeichen sind durch ein fremdes Schreiben (GStA) mittelbar belegt; der Inhalt der Einstellung nicht."),
 dict(nr=5, datum="13.10.2026", akte="6 M 9219/26",
      amt="AG Heilbronn, Vollstreckungsgericht — Rechtspflegerin (Name im Original des PfUEB, im AG-Beschluss NICHT genannt)",
      handlung="Pfändungs- und Ueberweisungsbeschluss ueber 1.786.888,01 EUR",
      beleg="(a)", belegquelle="Staatsakt: AG-Heilbronn-Beschluss vom 12.11.2026 (beglaubigte Abschrift, OCR aus Scan)",
      was_fehlt="Das ORIGINAL des PfUEB fehlt. Der AG-Beschluss sagt ausdruecklich: 'Der Beschluss traegt den Namen der verantwortlichen Rechtspflegerin und ist durch sie qualifiziert elektronisch signiert' - dieser Name steht nur auf dem PfUEB-Original.",
      was_trägt="Der AG-Beschluss belegt (i) dass ein PfUEB vom 13.10.2026 existiert, (ii) dass er den Namen der Rechtspflegerin traegt und qES-signiert ist, (iii) dass der Einwand 'keine rechtspflegerische Unterschrift' vom Gericht ZURUECKGEWIESEN wurde. Er belegt NICHT, wer es war."),
 dict(nr=6, datum="11.11.2026", akte="6 M 9219/26",
      amt="AG Heilbronn — Nichtabhilfeentscheidung der Rechtspflegerin",
      handlung="Nichtabhilfe ueber die Erinnerung des Schuldners",
      beleg="(d)", belegquelle="im AG-Beschluss nur REFERENZIERT, nicht beigefuegt",
      was_fehlt="Die Entscheidung selbst. Der AG-Beschluss verweist auf ihre Gruende ('Im Uebrigen wird auf die Gruende der Nichtabhilfeentscheidung vom 11.11.2026 Bezug genommen') - wir haben sie nicht.",
      was_trägt="Nichts eigenstaendig. Das ist das zentrale fehlende Glied: die Begruendung, auf die sich der AG-Beschluss stuetzt."),
 dict(nr=7, datum="19.10.2026 ODER 31.10.2026", akte="6 M 9219/26 / DR II 1833/26",
      amt="AG Heilbronn, Vollstreckungsabteilung — Gerichtsvollzieher (Murrweiss)",
      handlung="Vollstreckung: Konto-Pfaendung und Zwangsueberweisung",
      beleg="(c)", belegquelle="NUR EIGENE AKTE — und in sich widerspruechlich",
      was_fehlt="Die Vollstreckungsakte des AG (6 M 9219/26) mit Pfandprotokoll, Kontoauszuegen und Zustellnachweisen.",
      was_trägt="Nichts. Die beiden eigenen Dokumente nennen zwei verschiedene Vollstreckungstage (19.10. in der DOJ-Schrift, 31.10. in der SDNY-Klage) und verschiedene Referenzformate (DR II 1833/26 vs. DR Il 1833/26)."),
 dict(nr=8, datum="12.11.2026", akte="6 M 9219/26",
      amt="AG Heilbronn, Vollstreckungsgericht — Richterin Bogdahn",
      handlung="Zurueckweisung der Erinnerung; Kosten des Verfahrens; Gegenstandswert 1.400.000,00 EUR",
      beleg="(a)", belegquelle="Staatsakt: beglaubigte Abschrift vom 13.11.2026, ausgefertigt durch die Urkundsbeamtin (Kumpf, JAng'e); der Beschluss selbst ist als 'uneinheitlich beglaubigte Abschrift' gekennzeichnet",
      was_fehlt="Das Original mit der qES-Signatur der Richterin; die Protokollnotizen zur Zustellung (Fristbeginn 2 Wochen ab Zustellung).",
      was_trägt="Der vollstaendige Text der Begruendung - einschliesslich der Zurueckweisung des Unterschrifts-Einwands und des Verweises auf die Nichtabhilfeentscheidung vom 11.11.2026."),
 dict(nr=9, datum="30.10.2026", akte="24 Zs 1610/26",
      amt="Generalstaatsanwaltschaft Stuttgart — OStA'in Geiger",
      handlung="Bescheid: Zurueckweisung der Strafanzeige wegen Rechtsbeugung",
      beleg="(b)", belegquelle="nur ueber unsere fristwahrende Beschwerde gegen den Bescheid",
      was_fehlt="Das ORIGINAL des Bescheids.",
      was_trägt="Nichts eigenstaendig."),
]

# ------------------------------------------------- Widersprueche in eigener Akte
WIDERSPRUECHE = [
 dict(gegenstand="Vollstreckungstag der Konto-Pfaendung",
      a="ENFORCEMENT_COMPLICITY (DOJ-Schrift, 10.2026): 'On October 19, 2026 ... Enforcement Bailiff Murrweiss executed a total bank account garnishment order'",
      b="us_master_indictment (SDNY): 'Bailiff Jan Murrweiss executed a garnishment order on Oct 31, 2026'; zugleich 'executed bank freezes on Oct 15/19, 2026 but deliberately suppressed debtor service for 16 days until Oct 31, 2026'",
      loesung="Beide Angaben stammen aus UNSEREN Dokumenten. Die Akte der Vollstreckung (6 M 9219/26) entscheidet das - sie fehlt."),
 dict(gegenstand="Wer hat den PfUEB ausgestellt",
      a="ENFORCEMENT_COMPLICITY: 'issued by Court Clerk Fiona Betz on Oct 13, 2026'",
      b="SDNY: 'Rechtspflegerin Betz authorized a PfUEB with a blank signature line' - der vollzogene Titel sei eine Papierkopie mit LEERER Unterschriftszeile (Abschnitt T) gewesen, zugestellt am 31.10.2026",
      loesung="Der AG-Beschluss vom 12.11.2026 entscheidet: der PfUEB traegt den Namen der Rechtspflegerin und ist qES-signiert. Unser DOJ-Schriftsatz unterstellt das Gegenteil (leere Zeile). Diese Behauptung muss aus dem DOJ-Schriftsatz und der SDNY-Klage zurueckgenommen werden, sonst widerspricht sie dem eigenen Beleg."),
 dict(gegenstand="Rolle von Wurst",
      a="ENFORCEMENT_COMPLICITY: 'Court Clerk Wurst nevertheless issued an execution clause on August 27, 2026' UND 'Rechtspflegerin Wurst ... issued 33k cost title'",
      b="SDNY: nur 'Rechtspflegerin Wurst issued a 33,223.19 cost order during a pending appeal' - keine Vollstreckungsklausel",
      loesung="Die Behauptung 'Vollstreckungsklausel am 27.08.2026' steht nur in EINEM eigenen Dokument und in keinem Beleg. Sie ist entweder zu belegen oder zu streichen."),
 dict(gegenstand="Person und Referenz des Vollstreckers",
      a="Vollbild-Dossier: 'GV Murrweiss (AG Heilbronn)'",
      b="SDNY: 'DEFENDANT 02: JAN MURRWEIR (BAILIFF / GERICHTSVOLLZIEHER, AG HEILBRONN DR Il 1833/26)' - 'Jan Murrweir' ist ein OCR-Artefakt, 'DR Il' statt 'DR II'",
      loesung="Der Vorname ist ueberall auf 'Murrweiss' zu normalisieren, die Referenz auf 'DR II 1833/26'. Ein Fall, der genau die Sorgfalt dieser Beamten richtet, darf keine OCR-Artefakte in eigenen Antragen tragen."),
 dict(gegenstand="Aktenzeichen des LG-Urteils",
      a="ENFORCEMENT_COMPLICITY: 'LG Heilbronn Case | 3 O 57/26'  (Pipe = OCR fuer 'I 3 O 57/26')",
      b="SDNY: 'Issued Unsigned Default Title (13 0 57/26)' und '1 3 O 57/26'",
      loesung="Durchgaengig 'I 3 O 57/26' (Investiturkammer). Die Schreibweise ist in drei eigenen Dokumenten verschieden - das ist genau der Vorwurf, den der Gegner sonst stellt."),
 dict(gegenstand="Rolle des Glaeubigers",
      a="ENFORCEMENT_COMPLICITY: 'Creditor Attorney Bemd Karwiese (Hannover) obtained the garnishment order by fraudulently misleading the execution court'",
      b="AG-Beschluss vom 12.11.2026: '- Glaeubiger - Alexander Caspary, Schweizer Platz 56, 60594 Frankfurt', 'Prozessbevollmaechtigter: Rechtsanwalt Bernd Karwiese'",
      loesung="Karwiese ist ANWALT des Glaeubigers, nicht der Glaeubiger. Der Glaeubiger ist Alexander Caspary. Die eigene Akte hat das mehrfach verwechselt - im DOJ-Schriftsatz heisst es 'Attorney Bernd Karwiese Law Firm', das ist richtig, aber der Satz oben macht ihn zum Glaeubiger."),
]

# ------------------------------------------------- Personen: Nennungen je Datei
def nennungen(name):
    out = {}
    for p in sorted(os.listdir(O)):
        if not p.endswith(".txt"):
            continue
        t = " ".join(open(os.path.join(O, p), encoding="utf-8", errors="replace").read().split())
        c = len(re.findall(r"\b" + name, t))
        if c:
            out[p] = c
    return out


def main():
    # Belege je Person: welche Datei ist ein Staatsakt, welche unsere eigene?
    # (Die Klassifikation wird hier ausdruecklich MANUELL gefuehrt, nicht geraten:
    #  ENFORCEMENT_COMPLICITY = unsere DOJ-Schrift, nicht der DOJ.)
    STAATSBELEGE = {
        "Betz": [],
        "Wurst": [],
        "Murrweiß": [],
    }
    eigene = {n: nennungen(n) for n in ("Betz", "Wurst", "Murrweiß")}

    md = []
    A = md.append
    A("# Die Handlungskette AG / LG / STA — Gelenk fuer Gelenk")
    A("")
    A("**Fall:** HEILBRONN-KISWARM · **Erstellt:** " +
      datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
    A("")
    A("> **Die Kette ist so stark wie ihr schwächstes Gelenk.** Dieses Dokument "
      "misst jedes Gelenk einzeln und nennt die Belegquelle jeder Zeile. Was in "
      "unserer eigenen Akte steht, ist von dem getrennt, was ein Gericht selbst "
      "geschrieben hat — auch dort, wo es unsere Angabe stützt.")
    A("")
    A("## 1. Die Kette")
    A("")
    A("| # | Datum | Aktenzeichen | Amt / Person | Handlung | Belegzustand |")
    A("|---|---|---|---|---|---|")
    GLOSS = {"(a)": "**(a) Staatsakt**", "(b)": "(b) nur eigene Akte",
             "(c)": "**(c) eigene Akte, widersprüchlich**", "(d)": "**(d) fehlend**"}
    for g in GELENKE:
        A("| {} | {} | {} | {} | {} | {} |".format(
            g["nr"], g["datum"], g["akte"], g["amt"], g["handlung"][:120],
            GLOSS[g["beleg"]]))
    A("")
    A("### Zählung")
    A("")
    z = {k: sum(1 for g in GELENKE if g["beleg"] == k) for k in ("(a)", "(b)", "(c)", "(d)")}
    A("| Belegzustand | Anzahl Gelenke |")
    A("|---|---|")
    A("| (a) durch Staatsakt belegt | **{}** |".format(z["(a)"]))
    A("| (b) nur durch eigene Akte | {} |".format(z["(b)"]))
    A("| (c) in der eigenen Akte widersprüchlich | {} |".format(z["(c)"]))
    A("| (d) fehlend | {} |".format(z["(d)"]))
    A("")
    A("**Ergebnis:** {} von {} Gelenken trägt ein Gericht selbst. Die Kette ist "
      "damit **noch keine Kette**, sondern eine Abfolge von Feststellungen, von "
      "denen {} durch fremde Akten belegt sind.".format(z["(a)"], len(GELENKE), z["(a)"]))
    A("")
    A("## 2. Gelenk für Gelenk, mit Belegquelle")
    A("")
    for g in GELENKE:
        A("### Gelenk {} · {} · {}".format(g["nr"], g["datum"], g["akte"]))
        A("")
        A("**Amt / Person:** {}".format(g["amt"]))
        A("")
        A("**Handlung:** {}".format(g["handlung"]))
        A("")
        A("**Beleg:** {} — {}".format(GLOSS[g["beleg"]], g["belegquelle"]))
        A("")
        A("**Was fehlt:** {}".format(g["was_fehlt"]))
        A("")
        A("**Was es trägt:** {}".format(g["was_trägt"]))
        A("")
    A("## 3. Widersprüche innerhalb unserer eigenen Akte")
    A("")
    A("Diese Widersprüche sind zwischen **zwei Dokumenten, die wir selbst "
      "geschrieben haben**. Sie sind damit kein Argument gegen die Gegenseite, "
      "sondern ein Argument gegen uns — und sie sind der Grund, warum die Kette "
      "bisher nicht trägt.")
    A("")
    for i, w in enumerate(WIDERSPRUECHE, 1):
        A("### W{} — {}".format(i, w["gegenstand"]))
        A("")
        A("- **Dokument A:** {}".format(w["a"]))
        A("- **Dokument B:** {}".format(w["b"]))
        A("- **Auflösung:** {}".format(w["loesung"]))
        A("")
    A("## 4. Nennungen je Person — und ihre Herkunft")
    A("")
    A("| Person | Dateien in der Kette | davon Fremdbelege (Staatsakt) |")
    A("|---|---|---|")
    for n, d in eigene.items():
        A("| {} | {} | **{}** |".format(n, len(d), len(STAATSBELEGE.get(n, []))))
    A("")
    for n, d in eigene.items():
        A("**{}** — {} Fundstellen in {} Dateien:".format(n, sum(d.values()), len(d)))
        A("")
        for fn, c in sorted(d.items(), key=lambda kv: -kv[1]):
            A("- `{}` — {}×".format(fn[:72], c))
        A("")
    A("> **Befund:** Für Wurst, Betz und Murrweiß existiert in der gesamten "
      "Beweiskette **kein einziger Fremdbeleg**. Jede Nennung steht in einem "
      "Dokument, das wir selbst verfasst haben. Das ist kein Argument gegen sie "
      "und kein Argument für sie — es ist schlicht **kein Beweis**, und ein "
      "Satz wie „Betz erließ den PfÜB auf einem leeren Unterschriftsfeld“ ist "
      "gegenwärtig nicht haltbar, solange das PfÜB-Original fehlt.")
    A("")
    A("**Und die Umkehrung, die trägt:** Der AG-Beschluss vom 12.11.2026 ist ein "
      "Original und **bestätigt die Tatsache der Vollstreckbarkeit** — er setzt "
      "die Voraussetzungen des § 750 ZPO als vorliegend fest und weist den "
      "Unterschrifts-Einwand ausdrücklich zurück. Das ist ein gerichtlicher "
      "Beleg. Er nennt keinen Namen, und genau darin liegt die offene Lücke.")
    A("")
    A("## 5. Die fünf Originale, die die Kette schließen")
    A("")
    A("| # | Original | Zuständig | Aktenzeichen | Schließt Gelenk |")
    A("|---|---|---|---|---|")
    A("| 1 | **Urteilsausfertigung** des LG Heilbronn vom 22.04.2026 | LG Heilbronn, 3. Ziv. | I 3 O 57/26 | 1 |")
    A("| 2 | **Pfändungs- und Überweisungsbeschluss** vom 13.10.2026 | AG Heilbronn, Vollstreckungsgericht | 6 M 9219/26 | 5 |")
    A("| 3 | **Nichtabhilfeentscheidung** vom 11.11.2026 | AG Heilbronn | 6 M 9219/26 | 6 |")
    A("| 4 | **Einstellungsverfügung** der StA Heilbronn vom 03.09.2026 | StA Heilbronn | 257 Js 31024/26 | 4 |")
    A("| 5 | **Bescheid** der GStA Stuttgart vom 30.10.2026 | GStA Stuttgart | 24 Zs 1610/26 | 9 |")
    A("")
    A("Dazu **zwei weitere**, die die Kette erst komplett machen:")
    A("")
    A("| # | Original | Zuständig | Schließt |")
    A("|---|---|---|---|")
    A("| 6 | **Vollstreckungsakte** mit Pfandprotokoll, Kontoauszügen, Zustellnachweisen | AG Heilbronn | Gelenk 7 (die widersprüchlichen Vollstreckungstage) |")
    A("| 7 | **eIDAS-Audit-Trail** der qES-Signaturen zu PfÜB und Nichtabhilfeentscheidung | AG Heilbronn / BSI | Gelenke 5, 6 — mit Zeitstempel, wer wann signiert hat |")
    A("")
    A("**Rechtsweg:** § 406e StPO (Akteneinsicht) für StA und AG, § 147 ZPO für "
      "das LG. Der Antrag auf Akteneinsicht beim LG Heilbronn und bei der StA "
      "Heilbronn ist gestellt: `ANTRAG-AKTENEINSICHT-AKTENVERZEICHNIS-LG-HEILBRONN-2026-11-23.md` "
      "und `ANTRAG-AKTENEINSICHT-ERMITTLUNGSAKTE-STA-HEILBRONN-2026-11-23.md`.")
    A("")
    A("---")
    A("")
    A("Sacred hash: f5af425c")
    A("")

    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump({"erstellt": datetime.now(timezone.utc).isoformat(),
               "gelenke": GELENKE, "zaehlung": z,
               "widersprueche": WIDERSPRUECHE,
               "nennungen": eigene,
               "fremdbelege": STAATSBELEGE,
               "sacred_hash": "f5af425c"},
              open(OUT_JS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({"gelenke": len(GELENKE), "zaehlung": z,
                      "widersprueche": len(WIDERSPRUECHE),
                      "nennungen": {k: sum(v.values()) for k, v in eigene.items()},
                      "fremdbelege_fuer_wurst_betz_murrweiss":
                          sum(len(v) for v in STAATSBELEGE.values()),
                      "md_bytes": os.path.getsize(OUT_MD)}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
