#!/usr/bin/env python3
"""
sentinel_web_intel.py — Case-scoped web/OSINT intelligence for the ARTEX Sentinel Case Officer.

WHY
---
The sealed KISWARM corpus contains only what WE produced. Our own documents can
never corroborate our own allegations — that is circular. This tool acquires
INDEPENDENT public records about the named parties of a case so that a claim
can be tested against something that is not ours.

It is an evidence-acquisition instrument, not an attack instrument:
  * PUBLIC sources only. No adapter exists for a private channel.
  * It cannot decrypt, intercept, brute-force, authenticate or log in.
  * It never asserts a conclusion. It emits FACTS with provenance; a finding
    requires multiple independent sources, judged by the case officer.

ENFORCED IN CODE (not by convention)
  * DEFAULT DENY — a target absent from the active scope is refused.
  * QUERY POLICY LINT — queries aimed at private contact data, family members,
    private communications or interception are refused.
  * CIRCULARITY GUARD — a fetched document that is one of OUR OWN published
    artifacts is tagged `circular` and excluded from corroboration counting.
  * NO EMPTY ARTEFACTS — a response without body content is never stored as a
    fact (an empty file has the SHA-256 of the empty string and would look
    like a valid, verifiable record).
  * EVERY ARTEFACT — SHA-256 + retrieval timestamp + source URL + size cap.

USAGE
  sentinel_web_intel.py --case-id HEILBRONN-KISWARM --target "<label|alias>" \
      --query "<terms>" [--kind general|institutional|person|event|money] [--limit N]
  sentinel_web_intel.py --case-id ... --url "https://..." --target "<label>"
  sentinel_web_intel.py --case-id ... --list-targets
  sentinel_web_intel.py --case-id ... --sources
"""
from __future__ import annotations
import argparse, hashlib, html as htmllib, json, os, re, sys, time, unicodedata
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "KISWARM-SentinelCaseOfficer/1.0 (case-scoped public-record research)"
# Pfade relativ zum Skript: das Werkzeug laeuft identisch auf dem Host
# (/home/sah/ARTEX/data/sentinel/tools/) und im ARTEX-Container
# (/app/data/sentinel/tools/). Keine festen Hostpfade im Code.
_HERE = os.path.dirname(os.path.abspath(__file__))
SCOPE_DIR = os.environ.get("SENTINEL_SCOPE_DIR") or os.path.abspath(os.path.join(_HERE, "..", "scopes"))
TASK_DIR = os.environ.get("SENTINEL_TASK_DIR") or os.path.abspath(os.path.join(_HERE, "..", "..", "tasks"))
MAX_BYTES = 2_000_000
HOST_DELAY = 1.2

TIER = {
    "wikipedia": "secondary_reference",
    "wikidata": "primary_official_structured",
    "duckduckgo_html": "search_lead",
    "duckduckgo_lite": "search_lead",
    "duckduckgo_instant": "secondary_reference",
    "landtag_bw": "primary_official",
    "bundestag": "primary_official",
    "justiz_bw": "primary_official",
    "openlibrary": "primary_bibliographic",
    "generic_fetch": "unknown_requires_tiering",
    "direct_url": "unknown_requires_tiering",
}
OPERATOR_CIRCULAR_MARKERS = [
    "raw.githubusercontent.com/baronki2", "github.com/baronki2",
    "kiswarm", "sah-vault", "deusproof",
]


class Denied(Exception):
    pass


# ------------------------------------------------------------------ scope

def load_scope(case_id):
    p = os.path.join(SCOPE_DIR, case_id + ".json")
    if not os.path.exists(p):
        raise Denied("scope_missing_or_unreadable: " + p)
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        raise Denied("scope_unreadable: %s" % e)


def scope_targets(scope):
    out = []
    for x in scope.get("authorized_targets", []) or []:
        out.append(x if isinstance(x, dict)
                   else {"label": str(x), "kind": "named_party", "aliases": []})
    return out


def resolve_target(scope, label):
    want = (label or "").strip().lower()
    for t in scope_targets(scope):
        for n in [t.get("label", "")] + list(t.get("aliases", []) or []):
            if n and n.strip().lower() == want:
                return t
    raise Denied("target_not_in_scope: %r" % label)


def check_actions(scope):
    allowed = set(scope.get("allowed_actions", []) or [])
    missing = {"browser_readonly", "evidence_pack"} - allowed
    if missing:
        raise Denied("actions_not_in_scope: missing %s" % ",".join(sorted(missing)))
    exp = scope.get("expires_at")
    if exp:
        try:
            e = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
            if e < datetime.now(timezone.utc):
                raise Denied("scope_expired: %s" % exp)
        except ValueError:
            pass


# ------------------------------------------------------------ query policy

def _fold(s):
    """Umlaut-/ß-Normalisierung. Ohne sie umgeht 'abhören' das Muster 'abhoeren' -
    ein Lint, das man durch Tippen umgehen kann, ist kein Lint."""
    return (s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
             .replace("Ä", "ae").replace("Ö", "oe").replace("Ü", "ue")
             .replace("ß", "ss").replace("ẞ", "ss"))


PRIVACY_PATTERNS = [(re.compile(_fold(pat), re.I), why) for pat, why in [
    (r"\b(hausnummer|wohnadresse|privatadresse|anschrift|wohnort|wohnt)\b", "address harvesting"),
    (r"\b(telefonnummer|mobilnummer|handynummer|private nummer|rufnummer)\b", "private phone number"),
    (r"\b(privates postfach|private e-?mail|persoenliche e-?mail|pme|postfach)\b", "private mailbox"),
    (r"\b(ehefrau|ehemann|sohn|tochter|kind(er)?|familienangehoer|verheiratet)\b", "family members"),
    (r"\b(whatsapp|telegram|signal|facebook messenger|privatnachricht|privatchat)\b", "private messaging"),
    (r"\b(medizin|krankheit|diagnos|therapie|psychiater|rezept|gesundheit)\b", "health data"),
    (r"\b(bankkonto|kontoauszug|gehaltsabrechnung|kontoverbindung|iban)\b", "private financial records"),
    (r"\b(knacken|entschlüssel|decrypt|brute.?force|passwort.*knack|mithack|exploit|datenbank.*dump)\b",
     "offensive intrusion"),
    (r"\b(abhoeren|mitlesen|mitschnitt|intercept|wiretap|ueberwachung)\b", "interception"),
    (r"\b(privatgerät|privatgeraet|diensthandy.*(mitlesen|lesen))\b", "private device access"),
]]
ENCRYPTION_QUERY = re.compile(_fold(
    r"(verschlüssel|encrypted|cipher|schlüsselaustausch|chat(protokoll|verlauf)|"
    r"interne.*(kommunikation|mail)|email.*(verkehr|server)|betriebsrat.*mail|"
    r"diensthandy|privatger(ä|a)t|abhör|vernehmung)"), re.I)


def lint_query(q):
    ql = _fold(q or "").lower()
    for pat, why in PRIVACY_PATTERNS:
        if pat.search(ql):
            return "query_refused_private_data (%s)" % why
    if ENCRYPTION_QUERY.search(ql):
        return "query_refused_private_data (interception/decryption of communications)"
    return None


# ------------------------------------------------------------------- fetch

_last_host = {}


def http_get(url, timeout=25):
    host = urllib.parse.urlparse(url).netloc
    d = time.time() - _last_host.get(host, 0)
    if d < HOST_DELAY:
        time.sleep(HOST_DELAY - d)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/json,*/*",
        "Accept-Language": "de,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(MAX_BYTES + 1)
            _last_host[host] = time.time()
            if len(body) > MAX_BYTES:
                body = body[:MAX_BYTES]
            return r.status, r.headers.get("Content-Type", ""), body
    except urllib.error.HTTPError as e:
        _last_host[host] = time.time()
        try:
            return e.code, "", e.read(200000)
        except Exception:
            return e.code, "", b""
    except Exception as e:
        _last_host[host] = time.time()
        return 0, "", str(e).encode()


def strip_tags(s):
    s = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = htmllib.unescape(s)
    return " ".join(s.split())


def links_of(raw, base):
    out = []
    for m in re.finditer(r'<a\b([^>]*)>', raw, re.I):
        attrs = m.group(1)
        hm = re.search(r'href\s*=\s*"([^"]+)"', attrs) or re.search(r"href\s*=\s*'([^']+)'", attrs)
        if not hm:
            continue
        href = htmllib.unescape(hm.group(1))
        tm = re.search(r'title\s*=\s*"([^"]*)"', attrs)
        title = htmllib.unescape(tm.group(1)) if tm else ""
        out.append((urllib.parse.urljoin(base, href), title))
    return out


def ddg_clean(u):
    if "duckduckgo.com/l/" in u:
        q = urllib.parse.urlparse(u if u.startswith("http") else "https:" + u).query
        v = urllib.parse.parse_qs(q).get("uddg")
        if v:
            return v[0]
    return u


def classify_independence(url):
    u = (url or "").lower()
    if any(m in u for m in OPERATOR_CIRCULAR_MARKERS):
        return ("operator_circular",
                "eigenes Artefakt des Betreibers - kann eigene Vorwuerfe nicht bestaetigen")
    if "wikipedia" in u or "wikidata" in u or "openlibrary" in u:
        return "independent_public", "oeffentliches Drittregister"
    if any(k in u for k in ("landtag", "bundestag", "eur-lex", "dejure", "justiz-bw", ".gv.")):
        return "independent_public", "amtliches Register"
    return "independent_public_pending_tier", "oeffentliche Quelle, Tierschwerung erst bei Volltextpruefung"


def store(case_id, tslug, url, body, meta):
    d = os.path.join(TASK_DIR, case_id, "web-intel", tslug)
    os.makedirs(d, exist_ok=True)
    sha = hashlib.sha256(body).hexdigest()
    raw = os.path.join(d, sha + ".bin")
    if not os.path.exists(raw):
        with open(raw, "wb") as f:
            f.write(body)
    side = os.path.join(d, sha + ".json")
    meta = dict(meta, url=url, sha256=sha, bytes=len(body), stored=raw)
    with open(side, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    return sha, raw


# ---------------------------------------------------------------- adapters

def a_wikipedia(q, limit):
    s = ("https://de.wikipedia.org/w/api.php?action=query&format=json&list=search"
         "&srsearch=" + urllib.parse.quote(q) + "&srlimit=" + str(max(1, limit)))
    st, ct, body = http_get(s)
    if st != 200:
        return []
    try:
        titles = [x["title"] for x in json.loads(body.decode("utf-8", "replace"))
                  .get("query", {}).get("search", [])][:limit]
    except Exception:
        return []
    if not titles:
        return []
    s2 = ("https://de.wikipedia.org/w/api.php?action=query&format=json&prop=extracts"
          "&exintro=1&explaintext=1&redirects=1&titles=" + urllib.parse.quote("|".join(titles)))
    st2, ct2, b2 = http_get(s2)
    if st2 != 200:
        return []
    out = []
    try:
        for pid, pg in (json.loads(b2.decode("utf-8", "replace"))
                        .get("query", {}).get("pages", {}) or {}).items():
            ex = pg.get("extract") or ""
            if len(ex.strip()) < 80:
                continue
            out.append({"title": pg.get("title"), "text": ex[:4000],
                        "url": "https://de.wikipedia.org/?curid=" + str(pid)})
    except Exception:
        pass
    return out


def a_wikidata(q, limit):
    s = ("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json"
         "&language=de&limit=" + str(max(1, limit)) + "&search=" + urllib.parse.quote(q))
    st, ct, body = http_get(s)
    if st != 200:
        return []
    out = []
    try:
        for it in (json.loads(body.decode("utf-8", "replace")).get("search") or [])[:limit]:
            qid = it.get("id")
            e = {"title": it.get("label"), "text": it.get("description", "") or "",
                 "url": "https://www.wikidata.org/wiki/" + str(qid)}
            st2, ct2, b2 = http_get("https://www.wikidata.org/wiki/Special:EntityData/%s.json" % qid)
            if st2 == 200:
                try:
                    ent = json.loads(b2.decode("utf-8", "replace"))["entities"][qid]
                    cl = []
                    for prop, arr in (ent.get("claims") or {}).items():
                        for c in arr:
                            dv = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                            if isinstance(dv, dict):
                                dv = dv.get("id") or dv.get("time") or dv.get("text")
                            if dv:
                                cl.append("%s=%s" % (prop, dv))
                    if cl:
                        e["text"] = (e["text"] + " | " + "; ".join(cl[:45])).strip(" |")
                except Exception:
                    pass
            out.append(e)
    except Exception:
        pass
    return out


def a_ddg_html(q, limit):
    st, ct, body = http_get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    if st != 200:
        return []
    raw = body.decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', raw, re.S | re.I):
        attrs, inner = m.group(1), m.group(2)
        if "result__a" not in attrs and "result-link" not in attrs:
            continue
        hm = re.search(r'href\s*=\s*"([^"]+)"', attrs)
        if not hm:
            continue
        url = ddg_clean(htmllib.unescape(hm.group(1)))
        title = strip_tags(inner)
        if not title or not url.startswith("http"):
            continue
        out.append({"title": title, "text": "", "url": url})
    snips = [strip_tags(x) for x in re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', raw, re.S)]
    for i, o in enumerate(out):
        if i < len(snips):
            o["text"] = snips[i][:500]
    return out[:limit * 3]


def a_ddg_lite(q, limit):
    st, ct, body = http_get("https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(q))
    if st != 200:
        return []
    raw = body.decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', raw, re.S | re.I):
        attrs, inner = m.group(1), m.group(2)
        if "result-link" not in attrs:
            continue
        hm = re.search(r'href\s*=\s*"([^"]+)"', attrs)
        if not hm:
            continue
        url = ddg_clean(htmllib.unescape(hm.group(1)))
        title = strip_tags(inner)
        if url.startswith("http") and title:
            out.append({"title": title, "text": "", "url": url})
    return out[:limit * 3]


def a_ddg_instant(q, limit):
    st, ct, body = http_get("https://api.duckduckgo.com/?format=json&no_html=1&q=" + urllib.parse.quote(q))
    if st != 200:
        return []
    try:
        j = json.loads(body.decode("utf-8", "replace"))
        txt = (j.get("AbstractText") or "")
        for t in (j.get("RelatedTopics") or [])[:limit]:
            if isinstance(t, dict):
                txt += " " + (t.get("Text") or "")
        if len(txt.strip()) < 40:
            return []
        return [{"title": j.get("Heading", q), "text": txt[:4000],
                 "url": j.get("AbstractURL") or "https://duckduckgo.com/?q=" + urllib.parse.quote(q)}]
    except Exception:
        return []


NAV_BLOCK = ("/drucksachen", "/parlamentsbibliothek", "/informationsmaterial", "/archiv-des-landtags",
             "/dokumente-1952-1996", "/parlamentsdokumentation", "/parlamentsarchiv",
             "/protokolle/amtlicheprotokolle", "/protokolle/plenarprotokolle",
             "/protokolle/vorlaeufig", "/textarchiv/", "/datenhandbuch")


def a_landtag(q, limit):
    st, ct, body = http_get("https://www.landtag-bw.de/suche/?q=" + urllib.parse.quote(q))
    if st != 200:
        return []
    raw = body.decode("utf-8", "replace")
    out = []
    for u, t in links_of(raw, "https://www.landtag-bw.de"):
        if "/dokumente/" not in u and "drucksache" not in u.lower():
            continue
        if any(b in u for b in NAV_BLOCK):
            continue
        out.append({"title": t or strip_tags(u), "text": "", "url": u})
    seen, uniq = set(), []
    for o in out:
        if o["url"] in seen:
            continue
        seen.add(o["url"])
        uniq.append(o)
    return uniq[:limit * 3]


def a_bundestag(q, limit):
    st, ct, body = http_get("https://www.bundestag.de/services/suche?suchaktion=suchen&q="
                             + urllib.parse.quote(q) + "&suchbereich=parlament")
    if st != 200:
        return []
    raw = body.decode("utf-8", "replace")
    out = []
    for u, t in links_of(raw, "https://www.bundestag.de"):
        if "/resource/blob/" in u:
            out.append({"title": t or u.rsplit("/", 1)[-1], "text": "", "url": u})
        elif "/dokumente/textarchiv/" in u and re.search(r"\d{4}/\d+", u):
            out.append({"title": t or u.rsplit("/", 1)[-1], "text": "", "url": u})
    seen, uniq = set(), []
    for o in out:
        if o["url"] in seen:
            continue
        seen.add(o["url"])
        uniq.append(o)
    return uniq[:limit * 3]


def a_justiz_bw(q, limit):
    out = []
    for base in ("https://www.justiz-bw.de/service/presse/",
                 "https://www.justiz-bw.de/gerichte/staatsanwaltschaften/",
                 "https://www.justiz-bw.de/gerichte/landgerichte/"):
        st, ct, body = http_get(base)
        if st != 200:
            continue
        raw = body.decode("utf-8", "replace")
        txt = strip_tags(raw)
        hits = [u for u, t in links_of(raw, base) if q.lower() in (u + " " + t).lower()]
        for u in hits[:limit]:
            out.append({"title": "justiz-bw: " + u.rsplit("/", 1)[-1][:80],
                        "text": txt[:1200], "url": u})
        if hits:
            break
    return out[:limit]


def a_openlibrary(q, limit):
    st, ct, body = http_get("https://openlibrary.org/search.json?q=" + urllib.parse.quote(q)
                            + "&limit=" + str(max(1, limit)))
    if st != 200:
        return []
    try:
        j = json.loads(body.decode("utf-8", "replace"))
    except Exception:
        return []
    out = []
    for d in (j.get("docs") or [])[:limit]:
        au = ", ".join((d.get("author_name") or [])[:4])
        out.append({"title": "%s — %s" % (d.get("title", ""), au),
                    "text": "Verlag: %s | Jahr: %s | ISBN: %s | Verfasser: %s" % (
                        ", ".join((d.get("publisher") or [])[:3]), d.get("first_publish_year", "?"),
                        ", ".join((d.get("isbn") or [])[:3]), au),
                    "url": ("https://openlibrary.org" + d["key"]) if d.get("key") else
                           "https://openlibrary.org/search?q=" + urllib.parse.quote(q)})
    return out


# --------------------------------------------------------- relevance + privacy

# Persoenliche Social-Profile gehoeren NICHT in eine Fallakte: sie sind weder
# ein oeffentliches Register noch ein unabhaengiger Beleg, und ein Link auf
# das Profil einer Privatperson ist ein Doxxing-Vektor. Presseartikel auf
# denselben Domänen bleiben zulaessig.
PERSONAL_PROFILE = re.compile(
    r"(facebook\.com/(people|profile)|instagram\.com/|linkedin\.com/in/|xing\.com/profile|"
    r"twitter\.com/[A-Za-z0-9_]+/status|facebook\.com/[A-Za-z0-9_.]+/posts)", re.I)
STOP = set("""der die das den dem des und oder mit von für auf im in am an zur zum
ist sind war wurde wurde eine einen einem einer wie was wer wo wann warum
bei aus auch noch nur schon nach vor über durch""".split())


def relevance(title, text, query, min_terms=2):
    """Ein Treffer zaehlt nur, wenn er den GEGENSTAND behandelt - nicht wenn das
    Wort nebenbei vorkommt (z.B. ein Film, in dem ein Kiesewetter mitspielt)."""
    blob = ((title or "") + " " + (text or "")).lower()
    terms = [t for t in re.findall(r"[\wäöüß-]{4,}", (query or "").lower())
             if t not in STOP]
    if not terms:
        return True, []
    hits = [t for t in terms if t in blob]
    exact = (query or "").strip().lower() in blob
    ok = exact or len(hits) >= min_terms
    return ok, hits


ADAPTERS = [
    ("wikidata", a_wikidata),
    ("wikipedia", a_wikipedia),
    ("duckduckgo_html", a_ddg_html),
    ("duckduckgo_lite", a_ddg_lite),
    ("duckduckgo_instant", a_ddg_instant),
    ("landtag_bw", a_landtag),
    ("bundestag", a_bundestag),
    ("justiz_bw", a_justiz_bw),
    ("openlibrary", a_openlibrary),
]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:64] or "target"


def _append(case_id, facts):
    outdir = os.path.join(TASK_DIR, case_id, "web-intel")
    os.makedirs(outdir, exist_ok=True)
    fp = os.path.join(outdir, "web-intel-facts.jsonl")
    with open(fp, "a", encoding="utf-8") as f:
        for x in facts:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


def run(args):
    case_id = args.case_id
    scope = load_scope(case_id)
    check_actions(scope)

    if args.list_targets:
        for t in scope_targets(scope):
            print("  {:44s} {:26s} {}".format(t.get("label", "")[:44], t.get("kind", "?"),
                                              (t.get("basis", "") or "")[:76]))
        return 0
    if args.sources:
        for n, _ in ADAPTERS:
            print("  {:22s} tier={}".format(n, TIER.get(n, "?")))
        return 0

    target = resolve_target(scope, args.target)
    tslug = slug(target.get("label", "target"))

    if args.url:
        u = args.url.strip()
        p = urllib.parse.urlparse(u)
        if p.scheme not in ("http", "https"):
            raise Denied("url_refused: nur http/https")
        if not p.hostname:
            raise Denied("url_refused: kein Host")
        if args.kind == "money" and ENCRYPTION_QUERY.search(u):
            raise Denied("url_refused: Geldfluss-Analyse setzt oeffentliche Registerdaten voraus")
        st, ct, body = http_get(u)
        if st != 200 or not body:
            raise Denied("fetch_failed: HTTP %s, %d B" % (st, len(body)))
        text = strip_tags(body.decode("utf-8", "replace")) if "html" in (ct or "") \
            else body.decode("utf-8", "replace")
        if len(text.strip()) < 60:
            raise Denied("fetch_too_thin: %d Zeichen Text (ein leeres Artefakt traegt den Hash "
                         "des leeren Strings und wuerde wie ein gueltiger Beleg aussehen)"
                         % len(text.strip()))
        meta = {"case_id": case_id, "target": target.get("label"), "source": "direct_url",
                "tier": TIER["direct_url"], "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "independence": classify_independence(u)[0],
                "independence_note": classify_independence(u)[1],
                "kind": args.kind, "query": "direct:" + u, "content_type": ct}
        sha, raw = store(case_id, tslug, u, body, meta)
        fact = {"fact_id": "WIF-D-" + sha[:12], "case_id": case_id,
                "target": target.get("label"), "target_kind": target.get("kind"),
                "basis": target.get("basis"), "claim_kind": "factual_observation",
                "summary": text[:900], "source_url": u, "source": "direct_url",
                "tier": TIER["direct_url"], "independence": meta["independence"],
                "independence_note": meta["independence_note"], "sha256": sha,
                "bytes": len(body), "retrieved_at": meta["retrieved_at"], "stored": raw,
                "assertion": False}
        _append(case_id, [fact])
        print(json.dumps({"case_id": case_id, "target": target.get("label"), "facts": 1,
                          "sha256": sha, "url": u, "bytes": len(body),
                          "independence": fact["independence"]}, indent=1, ensure_ascii=False))
        return 0

    lint = lint_query(args.query)
    if lint:
        raise Denied(lint)
    if args.kind == "money" and ENCRYPTION_QUERY.search(args.query):
        raise Denied("query_refused: Geldfluss-Analyse setzt oeffentliche Registerdaten voraus, "
                     "nicht den Inhalt von Kommunikations- oder Geraetekanaelen")

    limit = args.limit
    results, errors = [], []
    for name, fn in ADAPTERS:
        if args.only and name != args.only:
            continue
        try:
            got = fn(args.query, limit) or []
        except Exception as e:
            errors.append("%s: %r" % (name, e))
            got = []
        for g in got:
            g["source"] = name
            g["tier"] = TIER.get(name, "unknown")
        results.extend(got)

    seen, uniq = set(), []
    for r in results:
        k = r.get("url", "")
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(r)

    ts = datetime.now(timezone.utc).isoformat()
    facts, skipped_empty, skipped_irrelevant, skipped_social = [], 0, 0, 0
    for i, r in enumerate(uniq[:limit * 3]):
        url = r.get("url", "")
        title = (r.get("title") or "").strip()
        text = (r.get("text") or "").strip()
        if PERSONAL_PROFILE.search(url or ""):
            skipped_social += 1
            continue
        is_lead = (r.get("tier") == "search_lead")
        ok, hits = relevance(title, text, args.query, min_terms=1 if is_lead else 2)
        if not ok:
            skipped_irrelevant += 1
            continue
        if not title and not text:
            skipped_empty += 1
            continue
        body = (text if text else title).encode("utf-8", "replace")
        meta = {"case_id": case_id, "target": target.get("label"), "source": r.get("source"),
                "tier": r.get("tier"), "retrieved_at": ts,
                "independence": classify_independence(url)[0],
                "independence_note": classify_independence(url)[1],
                "kind": args.kind, "query": args.query,
                "matched_terms": hits}
        if is_lead:
            # Ein Suchtreffer ist KEIN Beleg. Er wird als Lead protokolliert
            # (URL + Titel), OHNE Artefakt-Hash - ein Hash des Titels wuerde
            # wie ein Hash der Seite aussehen. Der Inhalt wird erst mit --url
            # geholt und dann mit dem echten Seiten-Hash versiegelt.
            sha, raw = None, None
            meta["content_type"] = "search_lead (kein Seiteninhalt)"
        else:
            sha, raw = store(case_id, tslug, url, body, meta)
        facts.append({"fact_id": "WIF-%s-%03d" % (ts[11:19].replace(":", ""), i),
                      "case_id": case_id, "target": target.get("label"),
                      "target_kind": target.get("kind"), "basis": target.get("basis"),
                      "claim_kind": "search_lead" if is_lead else "factual_observation",
                      "needs_fetch": bool(is_lead),
                      "summary": (title[:220] + " — " + text[:600]).strip(" —"),
                      "source_url": url, "source": r.get("source"), "tier": r.get("tier"),
                      "independence": meta["independence"],
                      "independence_note": meta["independence_note"],
                      "matched_terms": hits,
                      "sha256": sha, "bytes": len(body), "retrieved_at": ts,
                      "stored": raw, "assertion": False})

    _append(case_id, facts)
    print(json.dumps({"case_id": case_id, "target": target.get("label"),
                      "target_kind": target.get("kind"), "query": args.query,
                      "facts": len(facts), "skipped_empty": skipped_empty,
                      "skipped_irrelevant": skipped_irrelevant,
                      "skipped_social_profile": skipped_social,
                      "adapter_errors": errors,
                      "independence": {k: sum(1 for f in facts if f["independence"] == k)
                                       for k in sorted({f["independence"] for f in facts})},
                      "sources_hit": sorted({f["source"] for f in facts}),
                      "sample": [{"title": f["summary"][:70], "url": f["source_url"],
                                  "sha256": (f.get("sha256") or "kein-hash-lead")[:12],
                                  "claim_kind": f["claim_kind"], "tier": f["tier"]}
                                 for f in facts[:8]]}, indent=1, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--target")
    ap.add_argument("--query")
    ap.add_argument("--url")
    ap.add_argument("--kind", default="general",
                    choices=["general", "institutional", "person", "event", "money"])
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--only")
    ap.add_argument("--list-targets", action="store_true")
    ap.add_argument("--sources", action="store_true")
    a = ap.parse_args()
    if not a.list_targets and not a.sources:
        if not a.target:
            ap.error("--target erforderlich")
        if not a.query and not a.url:
            ap.error("--query oder --url erforderlich")
    try:
        return run(a)
    except Denied as e:
        print(json.dumps({"status": "DENIED", "reason": str(e)}, ensure_ascii=False))
        return 2
    except Exception as e:
        print(json.dumps({"status": "ERROR", "reason": repr(e)}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main())
