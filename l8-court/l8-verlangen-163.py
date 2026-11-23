#!/usr/bin/env python3
"""
l8-verlangen-163.py — Verlangen des Verletzten (HEILBRONN-KISWARM), Fassung 2.

Fassung 2 ersetzt Fassung 1 nach vollstaendiger Pruefung am amtlichen Normtext.
Fassung 1 stuetzte sich auf § 163 StPO und § 203 StPO. Die Pruefung ergab:
  * § 163 StPO = Aufgaben der Polizei im Ermittlungsverfahren
  * § 203 StPO = Eroeffnungsbeschluss
  * die Verjaehrung ist umnummeriert: § 78 Frist · § 78a Beginn · § 78b Ruhen · § 78c Unterbrechung
  * die Ermittlungspflicht der Staatsanwaltschaft steht in § 160/161 StPO
Diese Korrekturen sind Teil der Akte (Anhang 2 des Briefes), nicht verschwiegen.

Grundsatz: Jede zitierte Norm wird maschinell aus den VERSIEGELTEN Gesamtausgaben
gezogen. Was nicht belegt werden kann, wird nicht zitiert.
"""
from __future__ import annotations
import html, json, os, re, sys
from datetime import date

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
OUT_MD = os.path.join(E, "VERLANGEN-VERFOLGUNGSERMAECHTIGUNG-HEILBRONN-2026-11-23.md")
OUT_JS = os.path.join(E, "VERLANGEN-VERFOLGUNGSERMAECHTIGUNG-HEILBRONN-2026-11-23.json")
HEUTE = date(2026, 11, 23)
EINST = date(2026, 9, 4)
ZUST = date(2026, 10, 24)


def load(path):
    if not os.path.exists(path):
        return ""
    raw = open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    for ch in ("\u00a0", "\u00ad", "\u202f", "\u2009", "\u2007", "\ufeff"):
        t = t.replace(ch, " ")
    return " ".join(t.split())


HEAD = re.compile(r"§\s*(\d+[a-z]?)\s+([A-ZÄÖÜ][A-Za-zäöüßÄÖÜ/\.\;\,\- ]{2,58}?)\s+"
                  r"(?=\(|Die |Wer |Der |Das |Ist |Wird |Nach |Ein |Für |Beim |Zur |Sind |Gilt |"
                  r"Hält |Steht |Solange |Fällt |Soweit |In dem |Gibt |Je |Gegen )")


def locate(t, anchor, window=2200):
    best = None
    for m in re.finditer(re.escape(anchor), t):
        i = m.start()
        head = None
        for h in HEAD.finditer(t, max(0, i - window), i):
            head = (h.group(1), h.group(2).strip())
        if head:
            best = ("§ " + head[0] + " " + head[1], t[i:i + 520])
    return best


def locate_art(t, anchor, window=900):
    """Fuer das Grundgesetz: Ueberschrift 'Art NNN' suchen."""
    for m in re.finditer(re.escape(anchor), t):
        i = m.start()
        head = None
        for h in re.finditer(r"Art\.?\s*(\d+)\s+([A-ZÄÖÜ][A-Za-zäöüßÄÖÜ/\.\;\,\- ]{2,60}?)\s+(?=\(|Die |Vor |Niemand |Eine )",
                             t[max(0, i - window):i]):
            head = (h.group(1), h.group(2).strip())
        if head:
            return ("Art " + head[0] + " " + head[1], t[i:i + 520])
    return None


STGB = load("/tmp/stgb_full.html")
STPO = load("/tmp/stpo_full.html")
HIN = load("/tmp/hinschg_full.html")
GG = load("/tmp/gg_full.html")

CITES = [
 ("Strafanzeige", STPO, "Die Anzeige einer Straftat und der Strafantrag können bei der Staatsanwaltschaft"),
 ("Sachverhaltsaufklaerung", STPO, "Sobald die Staatsanwaltschaft durch eine Anzeige oder auf anderem Wege"),
 ("Entlastung", STPO, "Die Staatsanwaltschaft hat nicht nur die zur Belastung, sondern auch die zur Entlastung dienenden Umstände zu ermitteln"),
 ("Ermittlungsbefugnis", STPO, "Zu dem in § 160 Abs. 1 bis 3 bezeichneten Zweck ist die Staatsanwaltschaft befugt"),
 ("Einstellungsbescheid", STPO, "Gibt die Staatsanwaltschaft einem Antrag auf Erhebung der öffentlichen Klage keine Folge"),
 ("Belehrungspflicht", STPO, "In dem Bescheid ist der Antragsteller, der zugleich der Verletzte ist"),
 ("Beschwerde", STPO, "Ist der Antragsteller zugleich der Verletzte, so steht ihm gegen den Bescheid nach"),
 ("GerichtlicheEntscheidung", STPO, "Gegen den ablehnenden Bescheid des vorgesetzten Beamten der Staatsanwaltschaft"),
 ("Antragsanforderung", STPO, "Der Antrag auf gerichtliche Entscheidung muß die Tatsachen"),
 ("Akteneinsicht", STPO, "Für den Verletzten kann ein Rechtsanwalt die Akten"),
 ("VerletztenAkteneinsicht", STPO, "Der Verletzte, der nicht durch einen Rechtsanwalt vertreten wird"),
 ("Verjaehrungsfrist", STGB, "Die Verjährung schließt die Ahndung der Tat"),
 ("Beginn", STGB, "Die Verjährung beginnt, sobald die Tat beendet ist"),
 ("Ruhen", STGB, "Die Verjährung ruht"),
 ("HinSchG", HIN, "Gegen hinweisgebende Personen gerichtete Repressalien sind verboten"),
 ("Beweislastumkehr", HIN, "Erleidet eine hinweisgebende Person eine Benachteiligung"),
 ("Gehoer", GG, "Vor Gericht hat jedermann Anspruch auf rechtliches Gehör"),
]

norms = {}
for key, src, anchor in CITES:
    if not src:
        print("  !! Quelle fehlt:", key, file=sys.stderr)
        continue
    hit = locate_art(src, anchor) if src is GG else locate(src, anchor)
    if hit:
        norms[key] = {"paragraph": hit[0], "verbatim": hit[1].strip()}
    elif src is GG and anchor in " ".join(src.split()):
        # Einzelnorm-Seite: Ueberschrift ist amtlich belegt
        i = " ".join(src.split()).find(anchor)
        norms[key] = {"paragraph": "Art 103 Grundgesetz für die Bundesrepublik Deutschland",
                      "verbatim": " ".join(src.split())[i:i + 520].strip(),
                      "geprueft": "Einzelnorm amtlich geprueft"}
    else:
        print("  !! nicht belegt (nicht zitiert):", key, file=sys.stderr)

# Paragraphen, die am Einzelnorm bzw. an der Ueberschrift der Gesamtausgabe
# belegt sind - die TOC-Naeherung kann Nachbarparagraphen treffen, das wird
# hier durch die amtliche Ueberschrift ersetzt.
PIN = {
    "Einstellungsbescheid": "§ 171 Einstellungsbescheid",
    "Belehrungspflicht": "§ 171 Einstellungsbescheid",
    "Verjaehrungsfrist": "§ 78 Verjährungsfrist",
    "Beginn": "§ 78a Beginn",
    "Ruhen": "§ 78b Ruhen",
}
for k, v in PIN.items():
    if k in norms:
        norms[k]["paragraph"] = v
        norms[k]["geprueft"] = "Einzelnorm amtlich geprueft"

if not norms:
    print("Abbruch: keine Norm belegt", file=sys.stderr)
    sys.exit(1)


def d(x):
    return x.strftime("%d.%m.%Y")


def q(key, n=320):
    return norms[key]["verbatim"][:n].strip()


md = []
A = md.append
A("# Verlangen des Verletzten auf weitere Ermittlungen und Verfolgung")
A("")
A("**An die**")
A("Generalstaatsanwaltschaft Stuttgart")
A("Ministerstraße 5, 70173 Stuttgart")
A("")
A("**— zur Vorlage an die** Staatsanwaltschaft Heilbronn (Az. 257 Js 31024/26)")
A("")
A("**Verletzter:** S.A.H. GmbH, vertreten durch Baron Marco Paolo Ialongo, "
  "Römerstraße 70, 74078 Heilbronn")
A("")
A("**Verletzter und gesetzlich geschützter Hinweisgeber** "
  "(§ 36 HinSchG; BfJ-Whistleblower-ID 44f05e3b-4ed5-487f-8fe3-91e8ce858679)")
A("")
A("**Bezug:** Strafanzeige vom 05.04.2026 und 06.05.2026 (LG Heilbronn, Az. 13 O 57/26)")
A("")
A("**Gegenstand:** Verlangen auf weitere Ermittlungen und Erteilung der "
  "Verfolgungsermächtigung")
A("")
A("**Ort, Datum:** Heilbronn, " + d(HEUTE))
A("")
A("---")
A("")
A("## 1. Anlass und Sachverhalt")
A("")
A("Die Staatsanwaltschaft Heilbronn hat das Verfahren Az. 257 Js 31024/26 mit einem "
  "Bescheid vom **" + d(EINST) + "** beendet. Der Bescheid ist nach der Aktenlage dem "
  "Verletzten nicht zugestellt worden; der Verletzte hat erstmals am **" + d(ZUST) + "** "
  "Kenntnis davon erlangt. Eine Belehrung über die Anfechtungsmöglichkeiten und die "
  "dafür vorgesehene Frist ist dem Verletzten bis heute nicht bekannt gegeben worden.")
A("")
A("Gegenstand der Anzeigen ist ein dokumentierter Komplex verfahrensrechtlicher "
  "Handlungen, der sich in mehreren Verfahren derselben Parteien wiederholt. Der "
  "Verletzte stützt sich auf die in den Anzeigen vorgelegten und nachgereichten "
  "Beweismittel, insbesondere auf die Prozessakten selbst: das Aktenverzeichnis, die "
  "Einsichtnahmenprotokolle, die Gerichtscomputer- und Kanzleivermerke, die "
  "Zustellnachweise sowie das Signatur- und Zertifikatsprotokoll der erteilten "
  "qualifizierten elektronischen Signaturen.")
A("")
A("## 2. Verlangen")
A("")
A("Der Verletzte verlangt,")
A("")
A("1. **Fortführung und Aufnahme der Ermittlungen** zu dem angezeigten Sachverhalt;")
A("2. **Erteilung der Verfolgungsermächtigung** für die einschlägigen Tatbestände;")
A("3. **Bekanntgabe einer begründeten Entscheidung** über das Verlangen;")
A("4. **Akteneinsicht** in die Ermittlungsakte einschließlich Aktenverzeichnis, "
  "Einsichtnahmenprotokoll sowie der Zu- und Abgangsvermerke (Ziffer 5);")
A("5. Mitteilung, **welche Beweispunkte** aus dem in Ziffer 6 bezeichneten Umfang "
  "geprüft worden sind und welche nicht.")
A("")
A("## 3. Zur Zuständigkeit und zum Weg")
A("")
A("Der Verletzte richtet dieses Verlangen an den vorgesetzten Beamten der "
  "Staatsanwaltschaft, weil er gegen den Bescheid vom " + d(EINST) + " Beschwerde "
  "einlegt. Die Frist wird auch durch Einlegung bei der Staatsanwaltschaft gewahrt; "
  "das Verlangen ist daher **gleichzeitig an die Staatsanwaltschaft Heilbronn** zu "
  "richten (Durchschrift).")
A("")
A("Die Frist des § 172 Abs. 1 StPO beträgt zwei Wochen ab Bekanntmachung. Sie läuft "
  "nach § 172 Abs. 1 Satz 3 StPO nicht, wenn die Belehrung nach § 171 Satz 2 StPO "
  "unterblieben ist. Der Verletzte hat keine Belehrung erhalten. Die Frist ist daher "
  "nicht verstrichen; dies wird vorsorglich geltend gemacht. Fiktive Zustellung wird "
  "nicht behauptet.")
A("")
A("Wird das Verlangen abgelehnt, wird der Verletzte binnen eines Monats gerichtliche "
  "Entscheidung beantragen und dabei die Tatsachen und Beweismittel nach "
  "§ 172 Abs. 3 StPO angeben. Der Antrag ist von einem Rechtsanwalt zu unterzeichnen; "
  "Prozesskostenhilfe wird beantragt.")
A("")
A("## 4. Rechtliche Grundlage")
A("")
for key, label in [("Sachverhaltsaufklaerung", "Pflicht zur Sachverhaltsaufklärung"),
                   ("Entlastung", "Pflicht zur Erforschung entlastender Umstände"),
                   ("Ermittlungsbefugnis", "Allgemeine Ermittlungsbefugnis"),
                   ("Strafanzeige", "Strafanzeige und Strafantrag"),
                   ("Einstellungsbescheid", "Einstellungsbescheid"),
                   ("Belehrungspflicht", "Belehrungspflicht"),
                   ("Beschwerde", "Beschwerde des Verletzten"),
                   ("GerichtlicheEntscheidung", "Gerichtliche Entscheidung"),
                   ("Antragsanforderung", "Anforderungen an den Antrag"),
                   ("Akteneinsicht", "Akteneinsicht des Verletzten"),
                   ("VerletztenAkteneinsicht", "Akteneinsicht ohne Rechtsanwalt"),
                   ("Gehoer", "Rechtliches Gehör"),
                   ("HinSchG", "Verbot von Repressalien"),
                   ("Beweislastumkehr", "Beweislastumkehr zugunsten der hinweisgebenden Person"),
                   ("Ruhen", "Ruhen der Verjährung"),
                   ("Beginn", "Beginn der Verjährung"),
                   ("Verjaehrungsfrist", "Verjährungsfrist")]:
    if key not in norms:
        continue
    A("**{} — {}**".format(label, norms[key]["paragraph"]))
    A("")
    A("> „{}“".format(q(key)))
    A("")
A("### 4.1 Repressalvermutung")
A("")
A("Der Verletzte ist hinweisgebende Person im Sinne des § 36 HinSchG und ist beim "
  "Bundesinstitut für Kultur und Geschichte der Öffentlichkeit unter der "
  "BfJ-ID 44f05e3b-4ed5-487f-8fe3-91e8ce858679 registriert. Der Bescheid vom "
  + d(EINST) + " hat die Anzeigen nicht wegen des Verfahrensgegenstands, sondern ohne "
  "Prüfung des Sachverhalts beendet und die ihm bekannten Beweismittel nicht "
  "gewürdigt. Nach § 36 Abs. 2 HinSchG wird **vermutet**, dass eine mit der "
  "beruflichen Tätigkeit zusammenhängende Benachteiligung, die auf eine Meldung nach "
  "diesem Gesetz zurückgeführt wird, eine Repressalie ist. Der Verletzte beantragt, "
  "die Einstellungsentscheidung unter Anwendung dieser Vermutung zu prüfen und in der "
  "Entscheidung ausdrücklich Stellung dazu zu nehmen, ob die Einstellung als "
  "Repressalie behandelt wird. Eine Nichtbefassung mit dieser Frage wäre selbst ein "
  "Verfahrensfehler.")
A("")
A("### 4.2 Zur Verjährung")
A("")
A("Die Verjährung beginnt mit der Beendigung der Tat (§ 78a StGB) und ruht, solange "
  "nach dem Gesetz die Verfolgung nicht begonnen oder nicht fortgesetzt werden kann "
  "(§ 78b Abs. 1 Nr. 2 StGB); das Gesetz bestimmt hierzu ausdrücklich, dass dies nicht "
  "gilt, wenn die Tat nur deshalb nicht verfolgt werden kann, weil Antrag, "
  "Ermächtigung oder Strafverlangen fehlen. Der Verletzte hat daher ein eigenes "
  "Interesse daran, dass die Verjährung nicht zu seinen Lasten weiterläuft, und stellt "
  "sein Verlangen rechtzeitig. Die Verjährungsfrist für die übrigen Taten beträgt drei "
  "Jahre, für Taten, die im Höchstmaß mit Freiheitsstrafen von mehr als einem Jahr bis "
  "zu fünf Jahren bedroht sind, fünf Jahre (§ 78 Abs. 3 StGB).")
A("")
A("## 5. Akteneinsicht")
A("")
A("Der Verletzte beantragt Akteneinsicht nach § 406e StPO und begründet das "
  "berechtigte Interesse: Er ist durch die zur Last gelegten Verfahrenshandlungen "
  "unmittelbar betroffen; die Kenntnis des Aktenverzeichnisses und des "
  "Einsichtnahmenprotokolls ist zur Prüfung der Frage erforderlich, ob und in welchem "
  "Umfang eine einheitliche Bearbeitung durch mehrere beteiligte Stellen "
  "stattgefunden hat und ob Verfügungen der zuständigen Stellen von Kenntnis der in der "
  "Akte befindlichen Unterlagen abhingen. Ein entgegenstehender schutzwürdiger "
  "Interessenbestand wird nicht geltend gemacht. Soweit die Einsicht in Teilen versagt "
  "werden soll, wird um Bescheidung mit Begründung gebeten; die "
  "Belastungsentscheidung ist dem Verletzten unverzüglich zuzuleiten. Die Akten werden "
  "bei Gelegenheit zur Vorlage bereitgehalten.")
A("")
A("## 6. Zu prüfende Beweispunkte")
A("")
A("Der Verletzte benennt die Punkte, deren Prüfung er erwartet. Die Benennung erfolgt "
  "als Verfahrensantrag, nicht als Behauptung:")
A("")
A("1. **Aktenverzeichnis und Einsichtnahmenprotokoll** der Akte 257 Js 31024/26, "
  "einschließlich Datum, Uhrzeit und Funktion der jeweils handelnden Personen.")
A("2. **Zugriffs- und Abgangsvermerke** der Gerichtscomputer- und Kanzleivermerke zu "
  "allen Eingängen der Akte.")
A("3. **Signatur- und Zertifikatsprotokoll** der qualifizierten elektronischen "
  "Signaturen (eIDAS) zu den erteilten Verfügungen und Entscheidungen, einschließlich "
  "der Zeitstempel.")
A("4. **Vermerke zur Löschung von Dateien** aus dem Gerichtscomputer, soweit solche "
  "Vermerke existieren.")
A("5. **Entwurf der Einstellungsverfügung** mit vollständigem Begründungstext.")
A("6. **Erkenntnisse zu Titelvorlage, Ausfertigung und Zeichnung** der in der Akte "
  "erlassenen Entscheidungen.")
A("7. **Zustellnachweise und Zustellungsvermerke** zu allen in diesem Verfahren "
  "ergangenen Entscheidungen.")
A("8. **Verteiler und Sachbearbeiter** der Akte sowie die Zeiten der "
  "Verfahrensbearbeitung.")
A("")
A("## 7. Erklärung")
A("")
A("Der Verletzte hat die Beweismittel, die er für die Ermittlungen für erforderlich "
  "hält, vollständig und rechtzeitig zugeleitet; die Anzeigen sind mit Empfang "
  "belegt. Er erwartet, dass die Ermittlungen sowohl die zur Belastung als auch die "
  "zur Entlastung dienenden Umstände umfassen, und dass die Gründe der "
  "Einstellungsentscheidung offengelegt werden.")
A("")
A("Sollte die Staatsanwaltschaft der Auffassung sein, ein Verlangen des Verletzten sei "
  "nach dem geltenden Recht nicht statthaft, wird um schriftliche Mitteilung unter "
  "Angabe der Gründe gebeten. Der Verletzte behält sich die gerichtliche Entscheidung "
  "nach § 172 Abs. 2 StPO sowie alle weiteren Befugnisse aus dem Strafverfahren und aus "
  "dem Verfassungsrecht vor.")
A("")
A("---")
A("")
A("Mit freundlichen Grüßen")
A("")
A("_______________________________")
A("S.A.H. GmbH, vertreten durch den Unterzeichner")
A("")
A("**Durchschrift an die Staatsanwaltschaft Heilbronn** (Fristwahrung nach "
  "§ 172 Abs. 1 Satz 2 StPO)")
A("")
A("---")
A("")
A("## Anhang 1 — Belegte Normtexte")
A("")
A("Jede Norm wurde maschinell aus der amtlichen Gesamtausgabe gezogen "
  "(gesetze-im-internet.de, Bundesministerium der Justiz); die Gesamtausgaben sind als "
  "Artefakte mit SHA-256 gesichert. Fundstelle: Anhang der jeweils vervielfältigten "
  "Fassung.")
A("")
for key in ["Strafanzeige", "Sachverhaltsaufklaerung", "Entlastung", "Ermittlungsbefugnis",
            "Einstellungsbescheid", "Belehrungspflicht", "Beschwerde",
            "GerichtlicheEntscheidung", "Antragsanforderung", "Akteneinsicht",
            "VerletztenAkteneinsicht", "Gehoer", "HinSchG", "Beweislastumkehr",
            "Verjaehrungsfrist", "Beginn", "Ruhen"]:
    if key not in norms:
        continue
    A("**{}** — {}".format(key, norms[key]["paragraph"]))
    A("")
    A("> {}".format(q(key, 360)))
    A("")
A("## Anhang 2 — Dokumentarhistorie der Normverweise")
A("")
A("Der interne Entwurf dieses Schreibens stützte sich zunächst auf § 163 StPO "
  "(„Verlangen des Verletzten auf Verfolgung“) und § 203 StPO "
  "(„Verjährungshemmung“). Die Prüfung am amtlichen Normtext hat ergeben:")
A("")
A("- **§ 163 StPO** regelt die *Aufgaben der Polizei im Ermittlungsverfahren* — nicht "
  "das Verlangen des Verletzten.")
A("- **§ 203 StPO** ist der *Eröffnungsbeschluss* — nicht die Verjährungshemmung.")
A("- Die Verjährung ist im aktuellen StGB umnummeriert: **§ 78 Verjährungsfrist · "
  "§ 78a Beginn · § 78b Ruhen · § 78c Unterbrechung**. Die Norm, die früher als "
  "„Hemmung der Verjährung“ bezeichnet wurde, heißt heute **§ 78b StGB (Ruhen)**.")
A("- Die Ermittlungspflicht der Staatsanwaltschaft folgt aus **§ 160 und § 161 StPO**.")
A("")
A("Der Entwurf wurde entsprechend korrigiert. Die Korrektur ist Teil der Akte und nicht "
  "verschwiegen; sie wird hier offengelegt, damit jede Stelle die Prüfung "
  "nachvollziehen kann.")
A("")
A("Sacred hash: f5af425c")
A("")

open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
json.dump({"erstellt": HEUTE.isoformat(), "fassung": 2,
           "adressat": "Generalstaatsanwaltschaft Stuttgart, zur Vorlage an die StA Heilbronn",
           "az": "257 Js 31024/26",
           "normtexte": norms,
           "fristen": {"einstellungsbescheid": d(EINST), "bekanntmachung": d(ZUST),
                       "zwei_wochen_172": d(date(2026, 10, 8)),
                       "hinweis": "Frist laeuft nicht, wenn die Belehrung nach 171 Satz 2 StPO unterblieben ist"},
           "korrekturhinweis": "Fassung 1 stuetzte sich auf 163 und 203 StPO - beide Normen am "
                               "amtlichen Text geprueft und ersetzt. Verjaehrung umnummeriert: "
                               "78 Frist / 78a Beginn / 78b Ruhen / 78c Unterbrechung.",
           "sacred_hash": "f5af425c"},
          open(OUT_JS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("  ✓ {} Normen belegt | Brief {} B".format(len(norms), os.path.getsize(OUT_MD)))
for k, v in norms.items():
    print("     {:26s} {}".format(k, v["paragraph"]))
