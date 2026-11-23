#!/usr/bin/env python3
"""
l8-sentinel-watch.py — Taeglicher unabhaengiger Intel-Waechter fuer das Fallportfolio.

Auftrag: "Sentinel sammelt alles verfuegbare" ist ein Prozess, kein einmaliger
Lauf. Dieser Waechter laeuft taeglich, sucht fuer jede benannte Person des
Fallportfolios in unabhaengigen oeffentlichen Quellen und protokolliert nur das,
was NEU ist.

Er nutzt das Werkzeug sentinel_web_intel.py, das default-deny arbeitet: nur
Ziele aus dem aktiven Scope, kein Adapter fuer private Kanaele, kein
personenbezogenes Social-Profil, Suchtreffer werden als Lead protokolliert und
erst mit --url zu echtem Seiteninhalt versiegelt.

Ausgabe: nur wenn sich etwas geaendert hat (Watchdog-Muster). Sonst bleibt
stdout leer - ein Job, der taeglich "alles ok" sendet, wird nicht mehr gelesen.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime, timezone

W = "/home/sah/ARTEX/data/sentinel/tools/sentinel_web_intel.py"
CASE = "HEILBRONN-KISWARM"
STATE = "/home/sah/.config/sah-vault/l8-sentinel-watch-state.json"
JOURNAL = "/home/sah/.config/sah-vault/l8-sentinel-watch-journal.jsonl"
SCOPE = "/home/sah/ARTEX/data/sentinel/scopes/%s.json" % CASE

# Suchprofile je Person: (Suchbegriff, Art)
PROFILE = {
    "default": [("{name} Richter OR Vorsitzender OR Urteil OR Entscheidung", "person"),
                ("{name} Landgericht Heilbronn OR Staatsanwaltschaft", "person")],
    "office": [("{name} Entscheidungen OR Urteile OR Pressemitteilung", "institutional")],
}


def run(target, query, kind, limit=4):
    cmd = [sys.executable, W, "--case-id", CASE, "--target", target,
           "--query", query, "--kind", kind, "--limit", str(limit)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
        out = r.stdout.strip()
        try:
            return json.loads(out)
        except Exception:
            return {"status": "UNPARSED", "raw": out[:300], "rc": r.returncode}
    except Exception as e:
        return {"status": "ERROR", "reason": repr(e)}


def main():
    if not os.path.exists(SCOPE):
        print(json.dumps({"status": "SCOPE_MISSING", "path": SCOPE}))
        return 1
    scope = json.load(open(SCOPE, encoding="utf-8"))
    targets = [t for t in scope.get("authorized_targets", []) if isinstance(t, dict)]
    persons = [t for t in targets if t.get("kind") in ("named_person", "operator_attested_party")]
    offices = [t for t in targets if t.get("kind") in ("named_office", "matter")]

    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding="utf-8"))
        except Exception:
            state = {}
    known = set(state.get("seen_urls", []))

    new_urls, runs, errors = [], 0, []
    for t in persons:
        name = t.get("label")
        if not name:
            continue
        short = t.get("searchbegriff") or name.split("(")[0].strip()
        for tmpl, kind in PROFILE.get("default", []):
            q = tmpl.format(name=short)
            res = run(name, q, kind)
            runs += 1
            if res.get("status") in ("DENIED", "ERROR", "UNPARSED"):
                errors.append({"target": name, "query": q, "status": res.get("status"),
                               "reason": str(res.get("reason"))[:180]})
                continue
            for s in res.get("sample", []):
                u = s.get("url")
                if u and u not in known:
                    known.add(u)
                    new_urls.append({"target": name, "query": q, "url": u,
                                     "title": s.get("title", "")[:160],
                                     "claim_kind": s.get("claim_kind"),
                                     "tier": s.get("tier"),
                                     "sha256": s.get("sha256"),
                                     "found_at": datetime.now(timezone.utc).isoformat()})
            # negative findings zaehlen als Ergebnis
            for g in (res.get("sample") or []):
                pass
    for t in offices:
        name = t.get("label")
        if not name:
            continue
        for tmpl, kind in PROFILE.get("office", []):
            q = tmpl.format(name=name.split("(")[0].strip())
            res = run(name, q, kind)
            runs += 1
            if res.get("status") in ("DENIED", "ERROR", "UNPARSED"):
                errors.append({"target": name, "query": q, "status": res.get("status")})
                continue
            for s in res.get("sample", []):
                u = s.get("url")
                if u and u not in known:
                    known.add(u)
                    new_urls.append({"target": name, "query": q, "url": u,
                                     "title": s.get("title", "")[:160],
                                     "claim_kind": s.get("claim_kind"),
                                     "tier": s.get("tier"),
                                     "sha256": s.get("sha256"),
                                     "found_at": datetime.now(timezone.utc).isoformat()})

    state = {"seen_urls": sorted(known), "last_run": datetime.now(timezone.utc).isoformat(),
             "runs": runs, "targets": len(persons) + len(offices)}
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STATE)

    if new_urls:
        with open(JOURNAL, "a", encoding="utf-8") as f:
            for n in new_urls:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")

    if not new_urls and not errors:
        return 0   # nichts Neues -> kein Output (Watchdog-Muster)
    print(json.dumps({"status": "NEU" if new_urls else "FEHLER",
                      "neue_funde": len(new_urls), "laeufe": runs,
                      "ziele": len(persons) + len(offices),
                      "fehler": errors[:5],
                      "funde": new_urls[:20]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
