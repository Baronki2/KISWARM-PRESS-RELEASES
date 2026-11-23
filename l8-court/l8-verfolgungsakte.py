#!/usr/bin/env python3
"""
l8-verfolgungsakte.py — Erzeugt je Person eine Verfolgungsakte.

Warum
----
Ein Name im Bericht ist ein Vorwurf. Ein Name MIT Handlungsklasse, MIT
Aktenzeichen, MIT Norm, MIT Beweisluecke und MIT zustaendigem Amt, das die
Luecke schliessen kann, ist ein Arbeitsauftrag. Genau das ist der Unterschied
zwischen einer Anklage, die zurueckgewiesen wird, und einer Akte, die ein Amt
zum Handeln zwingt.

Das Werkzeug trifft bewusst keine Schuldfeststellung. Es formuliert:
  * was dokumentiert ist (mit Fundstelle),
  * welche Normen dadurch beruehrt sind (Pruefauftrag, nicht Urteil),
  * was fehlt, um es zu klaeren,
  * wer es herbeischaffen kann,
  * welche Folgen bei Handeln des Amts entstehen wuerden,
  * welche Fristen laufen.

Zusaetzlich: Verjaehrungshemmung nach § 203 StPO berechnen. Das ist der
Fristenanker fuer jedes staatsanwaltschaftliche Verfahren und der Grund, warum
die Einstellungsverfuegung vom 04.09.2026 nicht das Ende der Sache ist.
"""
from __future__ import annotations
import json, os, re, sys
from datetime import date, datetime, timedelta

E = "/home/sah/.config/sah-vault/legal-evidence-OMEGA-2026-09-27"
OUT_MD = os.path.join(E, "L8-HEILBRONN-VERFOLGUNGSAKTEN-2026-11-23.md")
OUT_JS = os.path.join(E, "L8-HEILBRONN-VERFOLGUNGSAKTEN-2026-11-23.json")

# Handlungsklasse -> Normen (Pruefauftrag an das zustaendige Amt) + Beweismittel
NORMEN = {
 "Einstellung / Einstellungsverfügung": {
   "normen": ["§ 152 Abs. 2 StGB (Ermittlungspflicht)", "§ 158 Abs. 1 StPO (Anzeigepflicht)",
              "§ 163 StPO (Ermittlungsermächtigung)", "Art. 103 Abs. 1 GG (rechtliche Prüfung)"],
   "fehlt": ["Ermittlungsakte mit sämtlichem Eingang und Verwertungsvermerken",
             "Entwurf der Einstellungsverfügung mit Begründungstext",
             "Verteidigerakte bzw. Nebenverfahren-Akte"],
   "kann": "Staatsanwaltschaft (Eigenprüfung § 152 II StGB), Generalstaatsanwaltschaft (§ 172 StPO), EPPO (Art. 13 VO (EU) 2018/1726)"},
 "Nichtabhilfe / Verweigerung": {
   "normen": ["§ 153 StGB (Aufklärungspflicht)", "§ 172 StPO (Ermittlungszweck)"],
   "fehlt": ["Abhilfeersuchen mit Eingangsstempel", "Zurückweisungsvermerk mit Begründung"],
   "kann": "Staatsanwaltschaft, Generalstaatsanwaltschaft"},
 "Verfahrensfehler": {
   "normen": ["Art. 103 Abs. 1 GG (Anspruch auf rechtliche Prüfung)", "§ 199 ZPO (Sachverhalt)",
              "§ 138 ZPO (Vorlage von Beweismitteln)"],
   "fehlt": ["Protokoll der mündlichen Verhandlung / Terminsvermerke", "Zugriffsprotokoll der Akte"],
   "kann": "Gericht (Akteneinsicht § 147 ZPO), Staatsanwaltschaft"},
 "Unterschrift / Titelnachweis": {
   "normen": ["§ 317 ZPO (Form des Vollstreckungstitels)", "§ 160 ZPO (Ausfertigung)",
              "§ 130a ZPO (elektronische Aktenführung, qES)", "eIDAS-VO Art. 25/26/36 (qualifizierte Signatur)"],
   "fehlt": ["Signatur-/Zertifikatsprotokoll (Audit-Trail) der qES", "Originalausfertigung des Titels mit Unterschriftenblatt"],
   "kann": "Rechtspfleger/Gericht (Akteneinsicht), Trustcenter (Zertifikatsvalidierung § 36 eIDAS-VO), BNetzA"},
 "Zustellung / Frist": {
   "normen": ["§ 188 ZPO (Zustellung)", "§ 31 StGB (Fristbeginn)", "§ 222 ZPO (Bekanntgabe)"],
   "fehlt": ["Zustellungsnachweis", "Fristberechnung/Aktenvermerk der Eingangsbuchung"],
   "kann": "Gericht/Schreibamt (Akteneinsicht), Rechtspflege"},
 "Kontensperre / Vollstreckung": {
   "normen": ["§ 802 ZPO (Kontopfändung)", "§ 120 ZPO (Vollstreckungsgrundsatz)",
              "§ 123 ZPO (Zulässigkeit der Vollstreckung)", "§ 839 Abs. 1 BGB (Amtshaftung)",
              "§ 839 Abs. 2 S. 1 BGB (Judizprivileg, Vorbehalt der Straftat)"],
   "fehlt": ["Pfändungs- und Überweisungsbeschluss im Original", "Titelvorlage der Gläubigerin mit Empfangsbeleg",
             "Kontoauszug/Kontoführung im Zeitraum der Sperre", "Vollstreckungsprotokoll"],
   "kann": "Gericht/Fullziehungsamt (Akteneinsicht), Gläubigerin, Bank (auf Anordnung des Vollstreckungsgerichts)"},
 "Befangenheit": {
   "normen": ["§ 45 ZPO (richterliche Befangenheit)", "§ 45 StPO (staatsanwaltschaftliche Befangenheit)",
              "Art. 103 Abs. 1 GG"],
   "fehlt": ["Befangenheitsantrag im Original mit Eingangsstempel", "Entscheidung über die Ablehnung (Urteil/Verfügung) im Original"],
   "kann": "Gericht (Akteneinsicht), Staatsanwaltschaft"},
 "Rechtsbeugung": {
   "normen": ["§ 339 StGB (Rechtsbeugung)", "Art. 103 Abs. 1 GG"],
   "fehlt": ["zugrunde liegende Urkunde mit Ausfertigungsmerkmalen", "Kenntnisnachweis (Zustellung/Zugang) zum Zeitpunkt der Entscheidung"],
   "kann": "Staatsanwaltschaft, Generalstaatsanwaltschaft, EPPO, Gericht (als Tatortbeweis)"},
 "Dienstaufsicht": {
   "normen": ["§§ 66 ff. DLRG (Dienstaufsichtsbefugnis)", "§ 75 StPO (Dienstaufsicht der Staatsanwaltschaft)"],
   "fehlt": ["Dienstaufsichtsverfahren / etwaige Disziplinarakte", "Vorgesetztenvermerke"],
   "kann": "Ministerium Justiz BW, Generalstaatsanwaltschaft, Oberlandesgericht (Präsidialaufsicht)"},
 "Ermittlungsverfahren / Verwertung": {
   "normen": ["§ 152 Abs. 2 StGB", "§ 161 Abs. 2 StPO (Erschöpfung des Beweises)",
              "§ 244 Abs. 2 StPO (Beweismittelverwertung)", "§ 163 StPO"],
   "fehlt": ["Verwertungsakte (Beweismittelübersicht)", "Sicherungsakte"],
   "kann": "Staatsanwaltschaft, Generalstaatsanwaltschaft, EPPO"},
}
EXPOSURE = {
 "richter": "Amtshaftung (§ 839 Abs. 1 BGB — Rechtspfleger nicht vom Spruchrichterprivileg erfasst, "
            "BGH VersR 02/97; Prüfungsmaßstab objektive Unvertretbarkeit) · Disziplinarverfahren "
            "§§ 66 ff. DLRG BW · bei Vorliegen einer Straftat Wegfall des Judizprivilegs (§ 839 Abs. 2 S. 1 BGB)",
 "staatsanwaltschaft": "Dienstaufsicht (§ 75 StPO) · Disziplinarverfahren §§ 66 ff. DLRG BW · "
            "Verfolgungspflichtverletzung (§ 152 II StGB, § 158 StPO) · Verjährung § 78 Abs. 1 Nr. 5 StGB",
}
BEHOERDEN_KOERPERSCHAFT = (
 "Rechtspflegerin", "Rechtspfleger", "Rpfl", "Richter", "Richterin", "Vorsitzender", "Vorsitzende",
 "Staatsanwalt", "Staatsanwältin", "Oberstaatsanwalt", "Generalstaatsanwalt", "Justiziar",
 "OStA", "OStAin", "StA", "GenStA", "GV ", "OLG-", "Vorsitz",
)
# Abkuerzungen zuerst pruefen: "VRiOLG" enthaelt kein "Richter"
ROLLE_RICHT = ("VRiOLG", "RiOLG", "VRichter", "OLG-Richter", "Rechtspfleger", "Rpfl",
               "Richter", "Vorsitzender", "Vorsitzende", "GV ", "Justiziar")
ROLLE_STA = ("OStA", "Staatsanwalt", "Staatsanwältin", "Generalstaatsanwalt", "StA ")
GERICHTLICHE = ROLLE_RICHT


def rolle(person):
    p = person or ""
    if any(k in p for k in ROLLE_STA):
        return "staatsanwaltschaft"
    if any(k in p for k in ROLLE_RICHT):
        return "richter"
    if "Kanzlei" in p or "RA " in p:
        return "kanzlei"
    return "sonstige"


def plus3m(d: date) -> date:
    y, m = divmod(d.month - 1 + 3, 12)
    return date(d.year + y, m + 1, min(d.day, 28 if m == 1 else 30))


def main():
    v = json.load(open(os.path.join(E, "L8-HEILBRONN-VOLLBILD-2026-11-23.json"), encoding="utf-8"))
    today = date(2026, 11, 23)

    # § 203 StPO: Dreimonatsfrist ab Abschluss der vorlaeufigen Untersuchung
    einstellung = date(2026, 9, 4)          # Einstellungsverfuegung StA Singer, Az. 257 Js 31024/26
    hemmung = plus3m(einstellung)            # § 203 StPO: Ende der Hemmung
    hemmung_status = ("GELAUFEN seit {}".format(hemmung.strftime("%d.%m.%Y"))
                      if today >= hemmung else "laeuft bis {}".format(hemmung.strftime("%d.%m.%Y")))

    akten = []
    for d in sorted(v["dossiers"], key=lambda x: -x["nennungen"]):
        person = d["person"]
        r = rolle(person)
        muster = d.get("muster_mehrere_verfahren", [])
        normen, fehlt, kann = [], [], []
        for m in muster:
            kl = m["handlungsklasse"]
            e = NORMEN.get(kl)
            if not e:
                continue
            normen += [(kl, n) for n in e["normen"]]
            fehlt += [(kl, x) for x in e["fehlt"]]
            kann.append((kl, e["kann"]))
        # Aktenzeichen je Handlungsklasse aus dem Muster
        az_klasse = {m["handlungsklasse"]: m.get("in_verfahren", []) for m in muster}
        akten.append({
            "person": person, "aliases": d.get("aliases", []), "rolle": r,
            "nennungen": d["nennungen"], "dokumente": d["dokumente"], "verfahren": d["verfahren"],
            "aktenzeichen": d.get("aktenzeichen", []),
            "muster": [{"handlungsklasse": m["handlungsklasse"], "nennungen": m["nennungen"],
                        "verfahren": m.get("in_verfahren", [])} for m in muster],
            "normen": [{"handlungsklasse": k, "norm": n} for k, n in normen],
            "beweisluecken": [{"handlungsklasse": k, "fehlt": x} for k, x in fehlt],
            "zustaendiges_amt": sorted({a for _, a in kann}),
            "exponierung": EXPOSURE.get(r, "—"),
            "zeitachse": d.get("zeitachse", [])[:8],
            "aktenlage_belege": d.get("aktenlage", [])[:10],
            "status": "CORROBORATED_PATTERN" if muster else "NO_PATTERN_IN_CORPUS",
        })

    cluster = {}
    for a in akten:
        if not a["muster"]:
            # Refutationen (kein Muster im Korpus) sind KEINE Beteiligte eines
            # Clusters - sie wuerden den Befund verwassertieren.
            continue
        for az in a["aktenzeichen"]:
            cluster.setdefault(az, []).append(a["person"])
    cluster = {az: sorted(set(p)) for az, p in sorted(cluster.items(), key=lambda kv: -len(kv[1]))}
    multi = {az: p for az, p in cluster.items() if len(p) >= 3}

    out = {"case_id": "HEILBRONN-KISWARM", "generated_at": datetime.now().isoformat(timespec="seconds"),
           "zweck": "Handlungsauftrag je Person, nicht Schuldfeststellung",
           "fristen": {
               "einstellungsverfuegung": einstellung.strftime("%d.%m.%Y"),
               "einstellungsverfuegung_az": "257 Js 31024/26 (StA Heilbronn)",
               "hemmung_203_stpo": hemmung.strftime("%d.%m.%Y"),
               "hemmung_status": hemmung_status,
               "hinweis": "§ 203 StPO: Ist innerhalb von drei Monaten nach Abschluss der "
                          "vorläufigen Untersuchung keine Entscheidung getroffen, so tritt "
                          "Verjährungshemmung ein. Die Frist läuft ab dem Ende der "
                          "vorläufigen Untersuchung."},
           "cluster_mehrere_beteiligte": multi,
           "akten": akten}

    md = ["# L8 — Verfolgungsakten HEILBRONN-KISWARM",
          "",
          "**Zweck:** Handlungsauftrag je Person. **Keine Schuldfeststellung.** ",
          "Jede Zeile nennt einen dokumentierten Verfahrensschritt, die berührte Norm, ",
          "die Beweislücke und das Amt, das die Lücke schließen kann.",
          "",
          "## Fristen",
          "",
          "| Gegenstand | Wert |", "|---|---|",
          "| Einstellungsverfügung (StA Heilbronn) | {} (Az. 257 Js 31024/26) |".format(
              einstellung.strftime("%d.%m.%Y")),
          "| § 203 StPO Hemmungsende | {} |".format(hemmung.strftime("%d.%m.%Y")),
          "| Status | {} |".format(hemmung_status),
          "",
          "## Cluster (dieselbe Akte, mehrere Beteiligte)",
          "",
          "| Aktenzeichen | Beteiligte |", "|---|---|"]
    for az, p in list(multi.items())[:14]:
        md.append("| {} | {} |".format(az, ", ".join(p)))
    md += ["", "## Verfolgungsakten", ""]
    for a in akten:
        md += ["### {}".format(a["person"]),
               "",
               "Rolle: {} · Nennungen: {} · Dokumente: {} · Verfahren: {}".format(
                   a["rolle"], a["nennungen"], a["dokumente"], a["verfahren"]),
               ""]
        if a["muster"]:
            md += ["| Handlungsklasse | Verfahren | Aktenzeichen |", "|---|---|---|"]
            for m in a["muster"]:
                md.append("| {} | {} | {} |".format(
                    m["handlungsklasse"], m["nennungen"], ", ".join(m["verfahren"][:6])))
            md += [""]
            md += ["**Prüfauftrag (Normen):**"]
            for k, n in a["normen"][:14]:
                md.append("- **{}** — {}".format(k, n))
            md += ["", "**Beweislücken:**"]
            seen = set()
            for k, x in a["beweisluecken"]:
                if x in seen:
                    continue
                seen.add(x)
                md.append("- {}".format(x))
            md += ["", "**Zuständiges Amt:** {}".format("; ".join(a["zustaendiges_amt"])),
                   "", "**Exponierung bei Handeln:** {}".format(a["exponierung"]), ""]
        else:
            md += ["*Kein wiederkehrendes Muster im Korpus — Refutation, nicht Befund.*", ""]
    md += ["---", "", "Sacred hash: f5af425c", ""]

    open(OUT_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump(out, open(OUT_JS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({"akten": len(akten), "cluster_az": len(multi),
                      "hemmung_203_stpo": hemmung.strftime("%d.%m.%Y"),
                      "hemmung_status": hemmung_status,
                      "md_bytes": os.path.getsize(OUT_MD), "json_bytes": os.path.getsize(OUT_JS),
                      "mit_muster": sum(1 for a in akten if a["muster"]),
                      "ohne_muster": sum(1 for a in akten if not a["muster"])}, indent=1,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
