"""Audit every built page against the things search engines actually check.

This reads the generated site on disk rather than the builders, because the
question is never "what did we intend to emit" but "what is in the file". It
prints a defect table and exits non-zero if any BLOCKER is found, so it can be
run before a deploy.

    python seo_audit.py            # summary
    python seo_audit.py --detail   # every offending page

Severities:
  BLOCKER  actively costs rankings or breaks a rich result
  WARN     leaves value on the table
  NOTE     worth knowing, not necessarily wrong
"""
import html as htmllib
import json
import os
import re
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.sihtak.com"
SKIP_DIRS = {".git", "content", "deck", "node_modules", "__pycache__", "screenshots"}

# Google truncates around these; they are guidance, not hard limits.
TITLE_MIN, TITLE_MAX = 15, 65
DESC_MIN, DESC_MAX = 70, 165
THIN_WORDS = 600

findings = defaultdict(list)          # (severity, rule) -> [page, ...]


def add(sev, rule, page, extra=""):
    findings[(sev, rule)].append(page + (f"  {extra}" if extra else ""))


def _ignored():
    """Paths git will not ship, so paths this audit should not judge.

    A deploy is `git archive HEAD`, but this walks the working tree, and the
    two are not the same set: /fahsak-com/ and /fahsak-co-uk/ are separate
    sites that merely live in this folder and are gitignored. Auditing them
    produced findings about pages that never reach sihtak.com, which is worse
    than useless because it makes a clean run look dirty.
    """
    import subprocess
    dirs = [d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d))]
    if not dirs:
        return set()
    # Passed as argv rather than down --stdin on purpose: subprocess with
    # text=True writes the pipe in text mode, so on Windows every "\n" becomes
    # "\r\n" and git compares "fahsak-com\r" against its patterns and matches
    # nothing. It fails silently, as an empty ignore set, which looks exactly
    # like a repo with no ignored directories.
    try:
        out = subprocess.run(["git", "check-ignore", "--"] + dirs, cwd=BASE,
                             capture_output=True, text=True, timeout=20).stdout
        return {line.strip().strip("/") for line in out.splitlines() if line.strip()}
    except Exception:
        return set()


def pages():
    skip = SKIP_DIRS | _ignored()
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            # google<token>.html is Search Console's ownership file: a bare token, not a page
            if f.endswith(".html") and not re.fullmatch(r"google[0-9a-f]{16}\.html", f):
                p = os.path.join(root, f)
                yield p, "/" + os.path.relpath(p, BASE).replace(os.sep, "/")


# Email templates that happen to live in the repo as .html. They are not web
# pages and should not be judged as such, nor shipped.
NOT_A_PAGE = re.compile(r"^/email-signature")

# The builder-owned tree: Arabic at the root, English mirrored under /en/.
# Everything else (legal, utility, rebrand stubs) is a standalone document.
BILINGUAL = re.compile(r"^(/en)?/(articles/|tools/|about/|author/|$)")


def is_bilingual(u):
    return bool(BILINGUAL.match(u))


def url_of(rel):
    return rel[: -len("index.html")] if rel.endswith("index.html") else rel


def text_of(html):
    body = re.sub(r"(?is)<(script|style|template)\b.*?</\1>", " ", html)
    body = re.sub(r"(?s)<!--.*?-->", " ", body)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def attr(tag, name):
    m = re.search(rf'{name}="([^"]*)"', tag)
    return m.group(1) if m else None


def main():
    detail = "--detail" in sys.argv
    titles, descs, h1s = defaultdict(list), defaultdict(list), defaultdict(list)
    og_images = defaultdict(list)
    seen, inbound, all_urls, noindex = {}, defaultdict(set), set(), set()
    surfaces = set()

    for path, rel in pages():
        u = url_of(rel)
        if NOT_A_PAGE.match(u):
            add("WARN", "not a web page but shipped in the site root", u,
                "email template, exclude from the deploy artifact")
            continue
        all_urls.add(u)
        seen[u] = open(path, encoding="utf-8").read()

    for u, html in sorted(seen.items()):
        head = html[: html.find("</head>") if "</head>" in html else len(html)]
        is_404 = u == "/404.html"

        # A "surface" is a page that can win a search result: indexable, and
        # speaking for itself rather than pointing its canonical at another
        # page. Everything else (the noindexed admin and invite pages, the
        # fahsak-* stubs that hand their equity to the home page) is plumbing.
        # Holding plumbing to the same standard as a landing page manufactures
        # work that changes nothing, so the metadata rules below are scoped to
        # surfaces and the plumbing is only checked for the things that would
        # leak: being crawled, being advertised, or pointing somewhere broken.
        c = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', head)
        noindexed = bool(re.search(
            r'<meta\s+name="robots"\s+content="[^"]*noindex', head))
        self_canon = not c or c.group(1).replace(SITE, "") in (u, u.rstrip("/"))
        surface = not noindexed and self_canon and not is_404
        if surface:
            surfaces.add(u)

        # ---- <html lang> / dir -------------------------------------------
        # Only the builder-owned tree is Arabic-first with an /en/ mirror. The
        # legal and utility pages at the root are genuinely English documents
        # and are right to say so, so they are only required to declare
        # something rather than to match a path convention.
        htag = re.search(r"<html[^>]*>", html)
        lang = attr(htag.group(0), "lang") if htag else None
        direction = attr(htag.group(0), "dir") if htag else None
        if not lang:
            add("BLOCKER", "no lang on <html>", u)
        elif is_bilingual(u):
            expect_lang = "en" if u.startswith("/en/") else "ar"
            expect_dir = "ltr" if expect_lang == "en" else "rtl"
            if lang != expect_lang:
                add("BLOCKER", "wrong <html lang>", u, f"got {lang!r} want {expect_lang!r}")
            if direction != expect_dir:
                add("WARN", "wrong <html dir>", u, f"got {direction!r}")

        # ---- title --------------------------------------------------------
        t = re.search(r"<title[^>]*>(.*?)</title>", head, re.S)
        # Measure what a person sees, not what the file stores: "&#x27;" is
        # one apostrophe to Google and six characters to a regex.
        title = htmllib.unescape(re.sub(r"\s+", " ", t.group(1)).strip()) if t else ""
        if not title:
            add("BLOCKER", "missing <title>", u)
        elif surface:
            titles[title].append(u)
            if len(title) > TITLE_MAX:
                add("WARN", f"title over {TITLE_MAX} chars", u, f"{len(title)}")
            if len(title) < TITLE_MIN:
                add("WARN", f"title under {TITLE_MIN} chars", u, f"{len(title)}")

        # ---- meta description --------------------------------------------
        d = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', head)
        desc = htmllib.unescape(d.group(1).strip()) if d else ""
        if not desc:
            if surface:
                add("BLOCKER", "missing meta description", u)
        elif surface:
            descs[desc].append(u)
            if len(desc) > DESC_MAX:
                add("WARN", f"description over {DESC_MAX} chars", u, f"{len(desc)}")
            elif len(desc) < DESC_MIN:
                add("WARN", f"description under {DESC_MIN} chars", u, f"{len(desc)}")

        # ---- canonical ----------------------------------------------------
        # A canonical pointing somewhere else is legitimate: the fahsak-* stubs
        # consolidate the old brand's link equity onto the home page. What is
        # never right is a canonical that differs from its own URL only by a
        # trailing slash, because that sends the crawler through a redirect.
        if not c:
            if not is_404 and not noindexed:
                add("BLOCKER", "missing canonical", u)
        else:
            got, want = c.group(1), SITE + u
            if got != want:
                if got.rstrip("/") == want.rstrip("/"):
                    sev = "NOTE" if noindexed else "BLOCKER"
                    add(sev, "canonical differs only by trailing slash", u, got)
                elif got.replace(SITE, "") in all_urls:
                    add("NOTE", "canonical points at another page (consolidation)",
                        u, got)
                else:
                    add("BLOCKER", "canonical points at a page that does not exist",
                        u, got)

        # ---- hreflang -----------------------------------------------------
        alts = dict(re.findall(
            r'<link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]+)"', head))
        if is_bilingual(u):
            # The home page is the one exception. It is Arabic, and its English
            # is a client-side toggle rather than a second URL, so there is no
            # honest "en" target to point at. Annotating one would be a lie to
            # the crawler. Build /en/ and this exception goes away.
            need_alts = ("ar", "x-default") if u == "/" else ("ar", "en", "x-default")
            for need in need_alts:
                if need not in alts:
                    add("WARN", f"missing hreflang {need}", u)
            for tag, href in alts.items():
                target = href.replace(SITE, "")
                if target not in all_urls:
                    add("BLOCKER", f"hreflang {tag} points at a missing page", u, href)

        # ---- robots -------------------------------------------------------
        # noindex is a decision, not a defect. It only becomes one when the
        # same page is being advertised in the sitemap.
        if noindexed and not is_404:
            add("NOTE", "noindex (intentional?)", u)
            noindex.add(u)

        # ---- viewport -----------------------------------------------------
        if not re.search(r'<meta\s+name="viewport"', head):
            add("BLOCKER", "missing viewport", u)

        # ---- open graph / twitter ----------------------------------------
        og = dict(re.findall(r'<meta\s+property="(og:[^"]+)"\s+content="([^"]*)"', head))
        for need in ("og:title", "og:description", "og:image", "og:url", "og:type"):
            if need not in og and surface:
                add("WARN", f"missing {need}", u)
        if "og:image" in og:
            img = og["og:image"]
            og_images[img].append(u)
            local = img.replace(SITE, "").lstrip("/").replace("/", os.sep)
            if img.startswith(SITE) and not os.path.exists(os.path.join(BASE, local)):
                add("BLOCKER", "og:image file does not exist", u, img)
        tw = dict(re.findall(r'<meta\s+name="(twitter:[^"]+)"\s+content="([^"]*)"', head))
        if "twitter:card" not in tw and surface:
            add("WARN", "missing twitter:card", u)

        # ---- headings -----------------------------------------------------
        hs = re.findall(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.S)
        h1 = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x[1])).strip()
              for x in hs if x[0] == "1"]
        if len(h1) == 0 and not is_404:
            add("BLOCKER", "no <h1>", u)
        elif len(h1) > 1:
            add("WARN", "more than one <h1>", u, f"{len(h1)}")
        if h1:
            h1s[h1[0]].append(u)
        levels = [int(x[0]) for x in hs]
        for a, b in zip(levels, levels[1:]):
            if b > a + 1:
                add("NOTE", "heading level skipped", u, f"h{a} -> h{b}")
                break

        # ---- images -------------------------------------------------------
        for tag in re.findall(r"<img\b[^>]*>", html):
            src = attr(tag, "src") or ""
            if attr(tag, "alt") is None:
                add("BLOCKER", "img without alt attribute", u, src)
            if (surface and "svg" not in src
                    and not (attr(tag, "width") and attr(tag, "height"))):
                add("WARN", "img without width/height (CLS risk)", u, src)

        # ---- structured data ----------------------------------------------
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if not blocks and surface:
            add("BLOCKER", "no JSON-LD", u)
        types = set()
        for b in blocks:
            try:
                data = json.loads(b)
            except Exception as ex:
                add("BLOCKER", "JSON-LD does not parse", u, str(ex)[:60])
                continue
            nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
            for n in nodes:
                if isinstance(n, dict) and "@type" in n:
                    types.add(n["@type"] if isinstance(n["@type"], str) else n["@type"][0])
        # /articles/<slug>/ and /en/articles/<slug>/, but not the hubs
        # themselves and not the /c/<id>/ category pages.
        is_article = bool(re.fullmatch(r"(/en)?/articles/[^/]+/", u))
        if is_article:
            for need in ("MedicalWebPage", "BreadcrumbList", "Person", "Organization"):
                if need not in types:
                    add("WARN", f"article missing {need} in JSON-LD", u)

        # ---- thin content ---------------------------------------------------
        words = len(text_of(html).split())
        if is_article and words < THIN_WORDS:
            add("WARN", f"thin content under {THIN_WORDS} words", u, f"{words}")

        # ---- internal links, for orphan detection ---------------------------
        for href in re.findall(r'href="(/[^"#?]*)"', html):
            inbound[href].add(u)

    # ---- cross-page uniqueness ---------------------------------------------
    for label, bag, sev in (("title", titles, "BLOCKER"),
                            ("meta description", descs, "BLOCKER"),
                            ("h1", h1s, "WARN")):
        for value, urls in bag.items():
            if len(urls) > 1:
                add(sev, f"duplicate {label} across pages",
                    f"{len(urls)} pages", f'"{value[:52]}"')

    # One picture standing in for hundreds of different pages is a wasted
    # social card and a wasted Google Images slot on every one of them.
    for img, urls in og_images.items():
        if len(urls) > 3:
            add("WARN", "many pages sharing one og:image",
                f"{len(urls)} pages", img.replace(SITE, ""))

    # ---- orphans -------------------------------------------------------------
    for u in sorted(surfaces):
        if u == "/":
            continue
        srcs = inbound.get(u, set()) - {u}
        if not srcs:
            add("WARN", "orphan page (no internal inbound link)", u)

    # ---- sitemap coverage ----------------------------------------------------
    smap = set()
    for name in ("sitemap-articles.xml", "sitemap-pages.xml"):
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            smap |= {m.replace(SITE, "")
                     for m in re.findall(r"<loc>([^<]+)</loc>", open(p, encoding="utf-8").read())}
    indexable = surfaces
    for u in sorted(indexable - smap):
        add("WARN", "page missing from sitemap", u)
    for u in sorted(smap - indexable):
        # A sitemap URL that only misses the trailing slash still costs a
        # redirect on every crawl, so name that case specifically.
        if u + "/" in indexable:
            add("BLOCKER", "sitemap URL missing its trailing slash", u)
        elif u in noindex:
            add("BLOCKER", "sitemap advertises a noindex page", u)
        else:
            add("BLOCKER", "sitemap lists a page that does not exist", u)
    has_img_sitemap = any(
        "image:image" in open(os.path.join(BASE, n), encoding="utf-8").read()
        for n in ("sitemap-articles.xml", "sitemap-pages.xml")
        if os.path.exists(os.path.join(BASE, n)))
    if not has_img_sitemap:
        add("WARN", "no image sitemap entries (Google Images discovery)", "site-wide")

    # ---- report ---------------------------------------------------------------
    order = {"BLOCKER": 0, "WARN": 1, "NOTE": 2}
    rows = sorted(findings.items(), key=lambda kv: (order[kv[0][0]], -len(kv[1])))
    blockers = 0
    out = sys.stdout.write
    out("\n%-8s %-58s %s\n" % ("SEVERITY", "RULE", "PAGES"))
    out("-" * 78 + "\n")
    for (sev, rule), hits in rows:
        if not hits:
            continue
        if sev == "BLOCKER":
            blockers += len(hits)
        out("%-8s %-58s %d\n" % (sev, rule[:58], len(hits)))
        if detail:
            for h in hits[:25]:
                out("           %s\n" % h.encode("ascii", "replace").decode("ascii"))
            if len(hits) > 25:
                out("           ... and %d more\n" % (len(hits) - 25))
    out("-" * 78 + "\n")
    out("%d pages audited, %d blocker-level findings\n\n" % (len(seen), blockers))
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
