#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal links inside article bodies, and a better pick for "related articles".

Until this existed every paragraph was plain escaped text, so 174 articles that
mention each other's subjects constantly did not link to each other once. The
only internal links were the four "related" cards, and those were the first
four articles of the category in file order, which meant that in a category of
21 every page linked to the same four and the other seventeen got nothing.

content/links.json maps each slug to the phrases that should link to it:

    {"vitamin-d-blood-test": {"ar": ["تحليل فيتامين د"], "en": ["vitamin D test"]}}

Rules the linker keeps, because over-linking reads as spam to people and to
Google alike:
  - body paragraphs only, never headings, takeaways, visuals or FAQs
  - at most one link per paragraph and MAX_PER_PAGE per page
  - each target linked once per page, never to the page itself
  - longest phrase wins where two overlap, earliest position otherwise

Arabic matching allows the attached prefixes a word really takes in running
text (و ف ب ك ل, and لل in place of ال), and refuses a match that runs into
another Arabic letter, so "السكر" does not light up inside "السكري". The prefix
sits inside the link so the letters stay joined.
"""
import json
import os
import re
import zlib

from build_chrome import BASE, L, e

LINKS = os.path.join(BASE, "content", "links.json")
MAX_PER_PAGE = 6

AR = "ء-غف-يٱ-ۓ"   # Arabic letters, no tatweel or digits
LAT = "A-Za-z0-9"


def _load():
    if not os.path.exists(LINKS):
        return {}
    with open(LINKS, encoding="utf-8") as fh:
        return json.load(fh)


def _alt(term, lang):
    t = term.strip()
    if not t:
        return None
    if re.match(f"^[{LAT}]", t):          # Latin, also inside Arabic text: TSH, HbA1c, H. pylori
        return rf"(?<![{LAT}]){re.escape(t)}(?:s|es)?(?![{LAT}])" if lang == "en" else \
               rf"(?<![{LAT}]){re.escape(t)}(?![{LAT}])"
    if t.startswith("ال"):
        core = re.escape(t[2:])
        return rf"(?<![{AR}])(?:[وف]?(?:[بك]?ال|لل)){core}(?![{AR}])"
    return rf"(?<![{AR}])(?:[وف]?[بكل]?){re.escape(t)}(?![{AR}])"


class _Index:
    """One compiled alternation per language, longest phrase first."""

    def __init__(self, links, valid):
        self.rx, self.slug_of = {}, {}
        for lang in ("ar", "en"):
            pairs = []
            for slug, terms in links.items():
                if slug not in valid:
                    continue
                for t in terms.get(lang, []):
                    if _alt(t, lang):
                        pairs.append((t, slug))
            pairs.sort(key=lambda p: -len(p[0]))
            parts, names = [], {}
            for i, (t, slug) in enumerate(pairs):
                names[f"g{i}"] = slug
                parts.append(f"(?P<g{i}>{_alt(t, lang)})")
            self.slug_of[lang] = names
            self.rx[lang] = re.compile("|".join(parts), re.I if lang == "en" else 0) if parts else None


_INDEX = None


def _index(valid):
    global _INDEX
    if _INDEX is None:
        _INDEX = _Index(_load(), valid)
    return _INDEX


class Linker:
    """Per page and per language. Call para() on each body paragraph in order."""

    def __init__(self, lang, slug, valid_slugs):
        self.lang, self.slug = lang, slug
        self.idx = _index(set(valid_slugs))
        self.used = {slug}
        self.count = 0
        self.base = L[lang]["base"]

    def para(self, text):
        rx = self.idx.rx[self.lang]
        if rx is None or self.count >= MAX_PER_PAGE:
            return e(text)
        names = self.idx.slug_of[self.lang]
        for m in rx.finditer(text):
            target = names[m.lastgroup]
            if target in self.used:
                continue
            self.used.add(target)
            self.count += 1
            s, t = m.span()
            return (e(text[:s]) + f'<a class="art-ilink" href="{self.base}{target}/">'
                    + e(text[s:t]) + "</a>" + e(text[t:]))
        return e(text)


# --------------------------------------------------------------------------
# related articles
# --------------------------------------------------------------------------
_STOP = set("""a an and are as at be by can do does for from how in is it its of on or
that the this to what when where which who why with you your yours guide explained
complete test tests symptoms symptom treatment treatments causes cause signs sign
meaning means normal level levels result results what's vs versus about after before
should need needs know""".split())


def _tokens(a):
    c = a.get("content", {}).get("en", {})
    text = " ".join([a.get("slug", "").replace("-", " "), c.get("title", ""), c.get("keywords", "")])
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in _STOP}


def related_for(a, articles, n=4):
    """Nearest articles by shared vocabulary, same category weighted up.

    The tie-break is a hash of the pair, not file order, so equally close
    articles are spread across pages instead of the same few winning every
    time. Deterministic, so a rebuild does not churn every page's links.
    """
    me = _tokens(a)
    cid = a.get("category")
    scored = []
    for x in articles:
        if x["slug"] == a["slug"]:
            continue
        other = _tokens(x)
        overlap = len(me & other) / (len(me | other) or 1)
        score = overlap + (0.25 if x.get("category") == cid else 0)
        jitter = zlib.crc32(f'{a["slug"]}|{x["slug"]}'.encode()) / 2**32 * 0.05
        scored.append((score + jitter, x))
    scored.sort(key=lambda p: -p[0])
    return [x for _, x in scored[:n]]
