---
name: web-intel-triage
description: Use when the case file needs INDEPENDENT public records about a named party. Acquires and classifies public sources under the active scope, refuses private data, and separates leads from evidence.
---

# Web-Intel-Triage — unabhängige Beschaffung für den Sentinel Case Officer

## Wozu

Die versiegelte Beweiskette enthält nur, was **wir** selbst erzeugt haben.
Eigene Dokumente können eigene Vorwürfe **nicht** bestätigen — das ist
zirkulär. Für Behauptungen, die außerhalb der Kette liegen (vom Betreiber
benannte Personen, Sachverhalte, institutionelle Fragen), braucht es
**unabhängige** Quellen.

Dieses Werkzeug beschafft diese Quellen. Es behauptet nichts.

## Aufruf

```bash
python3 /app/data/sentinel/tools/sentinel_web_intel.py \
  --case-id HEILBRONN-KISWARM \
  --target "<exaktes Label oder Alias aus dem Scope>" \
  --query "<Suchbegriffe>" \
  --kind general|institutional|person|event|money \
  --limit 5
```

Direktabruf einer konkreten öffentlichen Seite (dann wird der **Seiteninhalt**
mit echtem SHA-256 versiegelt):

```bash
python3 /app/data/sentinel/tools/sentinel_web_intel.py \
  --case-id HEILBRONN-KISWARM --target "<Label>" --url "https://..."
```

Hilfen: `--list-targets`, `--sources`, `--only <adapter>`.

## Quellen

| Adapter | Ebene |
|---|---|
| `wikidata` | strukturiertes öffentliches Register |
| `wikipedia` | Sekundärquelle |
| `landtag_bw`, `bundestag`, `justiz_bw` | amtlich/primär |
| `openlibrary` | bibliografisch (primär) |
| `duckduckgo_html`, `duckduckgo_lite` | **nur Lead** |
| `duckduckgo_instant` | Sekundärquelle |

## Die drei Regeln, die im Code erzwungen werden

**1. Default deny.** Ein Ziel, das nicht im aktiven Scope steht, wird
verweigert — auch dann, wenn es noch so plausibel erscheint. Keine Wildcards,
keine Schlussfolgerung, keine Bequemlichkeit.

**2. Lead ≠ Beleg.** Ein Suchtreffer wird als `search_lead` protokolliert:
URL + Titel, **ohne** Artefakt-Hash. Erst `--url` holt den Inhalt und
versiegelt ihn mit dem echten Seiten-Hash. Ein Hash über einen Titel würde
wie ein Hash über die Seite aussehen — das ist der ganze Unterschied zwischen
einem Beleg und dem Anschein eines Belegs.

**3. Zirkularitätsschutz.** Ein Artefakt, das eines **eigenen** publizierten
Dokuments ist, wird als `operator_circular` markiert und darf keine eigenen
Vorwürfe stützen.

## Was das Werkzeug nicht kann und nicht wird

* **Keine privaten Kanäle.** Kein Adapter für private Kommunikation, keine
  Entschlüsselung, kein Abhören, kein Zugriff auf Geräte. Die Abfrage-Policy
  verweigert solche Anfragen (auch in Umlaut-Schreibweise).
* **Keine Privatsphäre-Verletzung.** Anfragen nach Adresse, Telefonnummer,
  privatem Postfach, Familienangehörigen, Gesundheits- oder Kontodaten werden
  verweigert. Persönliche Social-Profile werden verworfen, auch wenn die
  Suchmaschine sie liefert.
* **Keine Schlussfolgerungen.** Das Werkzeug liefert Fakten mit Provenienz.
  Ein Finding braucht mehrere unabhängige Quellen — das entscheidet der
  Case Officer, nicht das Werkzeug.

## Workflow für den Officer

1. `case-scope-gate` → `set_constraints`
2. Recherche je Ziel: `--query` (Leads + Fakten)
3. Leads prüfen: die vielversprechenden URLs mit `--url` nachziehen
4. Jedes Ergebnis mit `record_fact` erfassen: Quelle, Ebene, Unabhängigkeit,
   SHA-256, Abrufzeit
5. `report_finding` **nur** bei mehreren unabhängigen, stützenden Quellen
6. In den Bericht: was geprüft wurde — und was nicht

## Formulierungsregel

Das Werkzeug liefert **Beobachtungen**, keine Bewertungen. Formuliere
als Observation, was protokolliert ist; Schlussfolgerungen bleiben beim
menschlichen Prüfer. Kein Finding ohne Unabhängigkeitskennzeichnung.
