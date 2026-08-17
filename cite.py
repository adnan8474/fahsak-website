"""Find and verify real citations against PubMed.

Language models recall plausible-looking PubMed IDs that belong to entirely
unrelated papers. On a health site published under a named byline that is worse
than having no citation at all, so writers must LOOK UP every study here rather
than recall it, and every batch is audited before it is merged.

    python cite.py search "vitamin d deficiency saudi arabia prevalence"
    python cite.py search "brucellosis raw milk" --n 8
    python cite.py verify 29706967
    python cite.py audit content/batches/some-slug.json

`search` returns real PMIDs with their real titles, journals and years. Cite
only what it gives you back, copying the values exactly.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "sihtak-citation-check/1.0 (health content verification)"}
PMID_RE = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)")

# Words that carry no matching signal, so a title overlap check is not fooled
# by two unrelated papers both containing "the study of patients".
STOP = {
    "the", "of", "and", "in", "a", "an", "for", "to", "on", "with", "by", "at",
    "from", "as", "is", "are", "study", "studies", "patients", "clinical",
    "review", "analysis", "among", "its", "their", "role", "effect", "effects",
}


def _get(url, tries=5):
    # NCBI allows about 3 requests a second per address and answers 429 above
    # that. Many writers run in parallel against one connection, so back off
    # generously rather than failing an article over someone else's timing.
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as exc:  # noqa: BLE001 - network flakiness is expected
            last = exc
            time.sleep(2.0 * (i + 1))
    raise last


def summaries(pmids):
    """Real title, journal and year for each PMID, or None if it does not exist."""
    pmids = [str(p) for p in pmids]
    if not pmids:
        return {}
    out = {}
    for i in range(0, len(pmids), 150):
        chunk = pmids[i:i + 150]
        d = _get(f"{EUTILS}/esummary.fcgi?db=pubmed&retmode=json"
                 f"&id={','.join(chunk)}")["result"]
        for p in chunk:
            r = d.get(p)
            if not r or "error" in r:
                out[p] = None
            else:
                out[p] = {
                    "pmid": p,
                    "title": r.get("title", "").rstrip("."),
                    "journal": r.get("fulljournalname") or r.get("source", ""),
                    "year": (r.get("pubdate") or "")[:4],
                    "authors": [a["name"] for a in r.get("authors", [])][:3],
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{p}/",
                }
    return out


def search(term, n=6):
    d = _get(f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&retmax={n}"
             f"&sort=relevance&term={urllib.parse.quote(term)}")
    ids = d["esearchresult"].get("idlist", [])
    got = summaries(ids)
    return [got[i] for i in ids if got.get(i)]


def _tokens(s):
    return {w for w in re.findall(r"[a-z]+", s.lower()) if len(w) > 3 and w not in STOP}


def title_matches(claim, real):
    """Does the cited label plausibly describe the paper at that PMID?

    Deliberately loose, and scored against the SHORTER of the two token sets.
    Labels are routinely a trimmed form of the real title, and journals publish
    titles with long subtitles after a colon, so scoring against the real title
    alone fails a correct citation whose label simply stopped at the colon.
    """
    rt, ct = _tokens(real), _tokens(claim)
    if not rt:
        return True
    hit = len(rt & ct)
    n = min(len(rt), len(ct))
    # Too few distinctive words to score either way, so fall back to the real
    # title and let a human read the pair in the report.
    return hit / len(rt) >= 0.4 if n < 3 else hit / n >= 0.5


def dead(url):
    """Is this link definitely broken? None means we could not tell.

    Publishers routinely block automated clients, so a 403 or a 405 says nothing
    about whether the page exists and must not fail a real citation. Only a 404
    or a name that does not resolve is treated as proof of a bad link.
    """
    try:
        req = urllib.request.Request(url, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read(1)
            return False
    except urllib.error.HTTPError as exc:
        return True if exc.code in (404, 410) else None
    except Exception:
        return None


def audit(paths, links=False):
    """Check every source in these article files. Returns (problems, warnings)."""
    claims = []
    for path in paths:
        data = json.load(open(path, encoding="utf-8"))
        for a in (data if isinstance(data, list) else [data]):
            for s in a.get("sources", []):
                claims.append((a.get("slug", path), s.get("label", ""), s.get("url", "")))

    pmids, others = {}, {}
    for slug, label, url in claims:
        if not url:
            continue
        m = PMID_RE.search(url)
        if m:
            pmids.setdefault(m.group(1), []).append((slug, label))
        else:
            others.setdefault(url, []).append((slug, label))

    real = summaries(list(pmids)) if pmids else {}
    problems = []
    for pmid, uses in pmids.items():
        r = real.get(pmid)
        for slug, label in uses:
            if r is None:
                problems.append((slug, "PMID DOES NOT EXIST", pmid, label, ""))
            elif not title_matches(label, r["title"]):
                problems.append((slug, "PMID IS A DIFFERENT PAPER", pmid, label, r["title"]))

    if links:
        for url, uses in others.items():
            if dead(url):
                for slug, label in uses:
                    problems.append((slug, "LINK IS 404", url, label, ""))
    return problems, len(claims), len(pmids), len(others)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "search":
        term = argv[2]
        n = int(argv[argv.index("--n") + 1]) if "--n" in argv else 6
        hits = search(term, n)
        if not hits:
            print("no results, try broader keywords")
            return 0
        for h in hits:
            who = ", ".join(h["authors"]) + (" et al" if len(h["authors"]) == 3 else "")
            print(f"\nPMID {h['pmid']}  ({h['year']})")
            print(f"  title   : {h['title']}")
            print(f"  journal : {h['journal']}")
            print(f"  authors : {who}")
            print(f"  url     : {h['url']}")
            print(f"  label   : {who}: {h['title']}, {h['journal']}, {h['year']}")
        return 0

    if cmd == "verify":
        got = summaries(argv[2:])
        for pmid, r in got.items():
            print(f"{pmid}: " + (f"{r['title']} ({r['journal']}, {r['year']})"
                                 if r else "DOES NOT EXIST"))
        return 0

    if cmd == "audit":
        args = [a for a in argv[2:] if a != "--links"]
        problems, n_src, n_pmid, n_other = audit(args, links="--links" in argv)
        for slug, kind, ref, label, real in problems:
            print(f"  FAIL [{slug}] {kind} {ref}")
            print(f"       cited as : {label}")
            if real:
                print(f"       actually : {real}")
        print(f"\n{n_src} sources, {n_pmid} PubMed links, {n_other} other links, "
              f"{len(problems)} bad")
        return 1 if problems else 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
