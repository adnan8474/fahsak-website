#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sihtak article page builder.

Reads content/articles.json and writes, for every article:
  /articles/<slug>/index.html        Arabic
  /en/articles/<slug>/index.html     English

Hubs, category pages, sitemaps and the feed are NOT written here. They are
regenerated wholesale from data by build_site.py, which must run after this.

Run:  python build_content.py && python build_site.py
"""
import os, json, datetime

from build_chrome import (
    BASE, SITE, AUTHOR, AUTHOR_URL, OG_IMAGE, PLAY, APPSTORE, L, CAT_BY_ID,
    cat_url, cat_name, fmt_date, e, nav, footer, head, card, jd,
    ORG_LD, PERSON_LD, SCRIPT_BLOCK, load_articles,
    load_covers, COVER_HERO, COVER_SHARE,
)
import build_visuals
from build_links import Linker, related_for

DATA = os.path.join(BASE, "content", "articles.json")
COVERS = load_covers()


# --------------------------------------------------------------------------
# From reading to doing: a one-line app pitch matched to the article's topic,
# and a link to the free tool that converts the numbers the article discusses.
# Every claim here is a feature the app ships (see the homepage).
# --------------------------------------------------------------------------
APP_LINE = {
    "lab-tests": ("صوّر ورقة تحاليلك، ويكتب لك صحتك كل نتيجة بالعربية مع حالتها وشرح مبسط لها.",
                  "Photograph your lab report and Sihtak writes out every result with its status and a plain explanation."),
    "medicines": ("صحتك يذكّرك بكل جرعة في وقتها، وينبّهك قبل أن ينفد دواؤك.",
                  "Sihtak reminds you of every dose on time and warns you before your medicine runs out."),
    "chronic-conditions": ("سجّل أدويتك وقراءات ضغطك وسكرك في مكان واحد، ويخبرك صحتك حين يبتعد رقمك عن معدلك.",
                           "Keep your medicines and your blood pressure and glucose readings in one place, and Sihtak tells you when a number drifts from your normal."),
    "child-health": ("أضف ملفاً صحياً لكل فرد في عائلتك، وتابع أدويته وتحاليله من هاتفك.",
                     "Add a health profile for each person in your family and follow their medicines and results from your phone."),
    "womens-health": ("أضيفي ملفاً صحياً لكل فرد في عائلتك، وتابعي الأدوية والتحاليل من هاتفك.",
                      "Add a health profile for each person in your family and follow their medicines and results from your phone."),
}
APP_LINE_DEFAULT = ("اسأل المساعد الصحي في صحتك عن أي سؤال، كتابةً أو بصوتك، بالعربية أو الإنجليزية.",
                    "Ask Sihtak's health assistant anything, by text or voice, in Arabic or English.")


def app_strip(lang, a):
    ar_t, en_t = APP_LINE.get(a.get("category"), APP_LINE_DEFAULT)
    lead = "تطبيق صحتك مجاني" if lang == "ar" else "Sihtak is a free app"
    return ('      <aside class="art-app reveal">\n'
            '        <img src="/images/app-icon-112.webp" alt="" width="40" height="40" loading="lazy">\n'
            f'        <p><b>{lead}.</b> {e(ar_t if lang == "ar" else en_t)}</p>\n'
            '        <div class="art-app-btns">'
            f'<a href="{PLAY}" target="_blank" rel="noopener" data-cta="article-strip-play">Google Play</a>'
            f'<a href="{APPSTORE}" target="_blank" rel="noopener" data-cta="article-strip-ios">App Store</a></div>\n'
            '      </aside>\n')


def _tool_map():
    """article slug -> [(tool slug, ar title, en title)]"""
    with open(os.path.join(BASE, "content", "tools.json"), encoding="utf-8") as fh:
        tools = json.load(fh)
    with open(os.path.join(BASE, "content", "converters.json"), encoding="utf-8") as fh:
        convs = json.load(fh)
    t = {x["slug"]: (x["ar"]["h1"], x["en"]["h1"]) for x in tools + convs}
    m = {}
    for c in convs:
        for s in c.get("related", []):
            m.setdefault(s, []).append(c["slug"])
    extra = {
        "a1c-converter": ["hba1c-test-explained", "type-2-diabetes-complete-guide", "prediabetes-reversing-it",
                          "diabetes-in-syria", "gestational-diabetes-guide", "diabetic-foot-care",
                          "diabetic-retinopathy-eyes", "sugar-in-arabic-sweets"],
        "bmi": ["obesity-in-the-gulf", "weight-loss-that-works", "weight-loss-herbs-danger",
                "mediterranean-diet-arab-version", "fatty-liver-disease"],
        "glucose-mmol-to-mg": ["diabetes-in-syria", "gestational-diabetes-guide"],
        "creatinine-umol-to-mg": ["painkillers-and-your-kidneys"],
    }
    for tool, slugs in extra.items():
        for s in slugs:
            m.setdefault(s, [])
            if tool not in m[s]:
                m[s].append(tool)
    return {s: [(x, *t[x]) for x in v if x in t] for s, v in m.items()}, t


TOOL_MAP, TOOL_TITLES = _tool_map()


def tool_box(lang, a):
    tools = TOOL_MAP.get(a["slug"])
    if not tools and a.get("category") == "lab-tests":
        tools = [("lab-unit-converter", *TOOL_TITLES["lab-unit-converter"])]
    if not tools:
        return ""
    base = "/tools/" if lang == "ar" else "/en/tools/"
    h = "أداة مجانية لهذا التحليل" if lang == "ar" else "A free tool for this"
    links = "".join(f'<li><a href="{base}{s}/">{e(ar if lang == "ar" else en)}</a></li>'
                    for s, ar, en in tools[:3])
    return (f'      <aside class="art-tool reveal">\n        <p class="art-tool-h">{h}</p>\n'
            f'        <ul>{links}</ul>\n      </aside>\n')


# --------------------------------------------------------------------------
# normalisation: authors supply the minimum, the builder derives the rest
# --------------------------------------------------------------------------
def normalise(a):
    a.setdefault("date_iso", datetime.date.today().isoformat())
    a["date_ar"] = a.get("date_ar") or fmt_date(a["date_iso"], "ar")
    a["date_en"] = a.get("date_en") or fmt_date(a["date_iso"], "en")
    cat = CAT_BY_ID.get(a.get("category"))
    if cat and not a.get("icon"):
        a["icon"] = cat["icon"]
    if not a.get("read_min"):
        words = 0
        c = a["content"]["en"]
        for s in c["sections"]:
            words += sum(len(p.split()) for p in s.get("paras", []))
            words += sum(len(x.split()) for x in s.get("list", []) or [])
        a["read_min"] = max(3, round(words / 210))
    return a


# --------------------------------------------------------------------------
# page fragments
# --------------------------------------------------------------------------
def breadcrumbs(lang, a):
    o = L[lang]
    c = a["content"][lang]
    cid = a.get("category")
    mid = ""
    if cid:
        mid = (f'        <li><a href="{cat_url(lang, cid)}">{e(cat_name(lang, cid))}</a></li>\n')
    return (
        '    <nav class="art-crumbs" aria-label="Breadcrumb">\n'
        '      <ol>\n'
        f'        <li><a href="/">{o["crumb_home"]}</a></li>\n'
        f'        <li><a href="{o["nav_articles"]}">{o["crumb_articles"]}</a></li>\n'
        + mid +
        f'        <li><span aria-current="page">{e(c["h1"])}</span></li>\n'
        '      </ol>\n'
        '    </nav>\n'
    )


def cover_hero(a, lang):
    """The article's own 3D cover, as a lead_image dict, if one exists.

    Alt text describes the artwork rather than repeating the h1 sitting two
    inches above it: a screen reader would otherwise announce the headline
    twice, and Google Images matches on what the picture shows.
    """
    cover = COVERS.get(a["slug"])
    if not cover:
        return None
    return {"src": COVER_HERO.format(a["slug"]), "alt": cover.get(f"alt_{lang}", "")}


def lead_image(a, lang):
    img = a.get("lead_image") or cover_hero(a, lang)
    if not img:
        return ""
    credit = ""
    if img.get("credit"):
        label = e(img["credit"])
        if img.get("credit_url"):
            label = (f'<a href="{e(img["credit_url"], True)}" target="_blank" '
                     f'rel="noopener nofollow">{label}</a>')
        credit = f'      <p class="viz-credit">{label}</p>\n'
    return (
        '    <div class="art-lead reveal">\n'
        f'      <img src="{e(img["src"], True)}" alt="{e(img.get("alt", ""), True)}" '
        'width="1200" height="675" fetchpriority="high" decoding="async">\n'
        + credit +
        '    </div>\n'
    )


def toc(lang, a):
    secs = a["content"][lang]["sections"]
    if len(secs) < 4:
        return ""
    items = "".join(
        f'          <li><a href="#s{i}">{e(s["h2"])}</a></li>\n'
        for i, s in enumerate(secs, 1)
    )
    return (
        f'      <details class="art-toc reveal" open>\n'
        f'        <summary>{L[lang]["toc_h"]}</summary>\n'
        f'        <ol>\n{items}        </ol>\n'
        '      </details>\n'
    )


def author_box(lang):
    o = L[lang]
    return (
        '      <aside class="art-author reveal">\n'
        '        <div class="art-author-avatar" aria-hidden="true">AA</div>\n'
        '        <div class="art-author-body">\n'
        f'          <h3><a href="{"/author/" if lang == "ar" else "/en/author/"}">{AUTHOR}</a></h3>\n'
        f'          <p class="art-author-role">{o["author_role"]}</p>\n'
        f'          <p class="art-author-bio">{o["author_bio"]}</p>\n'
        '        </div>\n'
        '      </aside>\n'
    )


def body_html(lang, a, articles=()):
    c = a["content"][lang]
    o = L[lang]
    out = []
    link = Linker(lang, a["slug"], [x["slug"] for x in articles])

    lis = "".join(f'          <li>{e(t)}</li>\n' for t in c["takeaways"])
    out.append(f'      <aside class="art-takeaways reveal">\n        <h2>{o["takeaways_h"]}</h2>\n'
               f'        <ul>\n{lis}        </ul>\n      </aside>\n')
    out.append(app_strip(lang, a))

    out.append(toc(lang, a))

    for i, s in enumerate(c["sections"], 1):
        out.append('      <section class="reveal">\n')
        out.append(f'        <h2 id="s{i}">{e(s["h2"])}</h2>\n')
        for p in s.get("paras", []):
            out.append(f'        <p>{link.para(p)}</p>\n')
        if s.get("list"):
            items = "".join(f'          <li>{e(li)}</li>\n' for li in s["list"])
            out.append(f'        <ul class="art-list">\n{items}        </ul>\n')
        out.append(build_visuals.render_all(lang, s))
        out.append('      </section>\n')
        if i == 2:
            out.append(tool_box(lang, a))

    out.append(f'      <section class="art-tie reveal">\n        <p>{e(c["tie"])}</p>\n      </section>\n')

    out.append(
        '      <aside class="art-cta reveal">\n'
        '        <img src="/images/app-icon-112.webp" alt="Sihtak app icon" width="56" height="56">\n'
        '        <div class="art-cta-text">\n'
        f'          <h3>{o["cta_h"]}</h3>\n'
        f'          <p>{o["cta_p"]}</p>\n'
        '        </div>\n'
        '        <div class="art-cta-btns">\n'
        f'          <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">{o["cta_b1"]}</a>\n'
        f'          <a href="{APPSTORE}" class="btn btn-ghost btn-sm" target="_blank" rel="noopener">{o["cta_b2"]}</a>\n'
        '        </div>\n'
        '      </aside>\n'
    )

    faqs = "".join(
        '        <details class="art-faq-item">\n'
        f'          <summary>{e(f["q"])}</summary>\n'
        f'          <p>{e(f["a"])}</p>\n'
        '        </details>\n'
        for f in c["faqs"]
    )
    out.append(f'      <section class="art-faq reveal">\n        <h2>{o["faq_h"]}</h2>\n{faqs}      </section>\n')

    src = a.get("sources") or []
    if src:
        # A thesis or a print journal often has no stable URL we can trust. The
        # citation is still worth showing, so it renders as plain text rather
        # than being dropped or given a guessed link.
        def _cite(s):
            label = e(s["label"])
            if not s.get("url"):
                return f'          <li>{label}</li>\n'
            return (f'          <li><a href="{e(s["url"], True)}" target="_blank" '
                    f'rel="noopener nofollow">{label}</a></li>\n')

        items = "".join(_cite(s) for s in src)
        out.append(f'      <section class="reveal">\n        <h2>{o["sources_h"]}</h2>\n'
                   f'        <ul class="art-list">\n{items}        </ul>\n      </section>\n')

    out.append(f'      <p class="art-disclaimer">{o["disclaimer"]}</p>\n')
    out.append(author_box(lang))
    return "".join(out)


# --------------------------------------------------------------------------
# structured data
# --------------------------------------------------------------------------
def ldjson(lang, a):
    c = a["content"][lang]
    url = f'{SITE}{L[lang]["base"]}{a["slug"]}/'
    cid = a.get("category")
    # Schema.org gets the untitled 16:9 hero, not the share card. This image
    # is what Discover and rich results may reuse at their own crop, and text
    # burnt into a picture cannot reflow when they do.
    lead = a.get("lead_image") or cover_hero(a, lang)
    img, dims = OG_IMAGE, (1200, 630)
    if lead and lead.get("src"):
        img, dims = SITE + lead["src"], (1200, 675)

    page = {
        "@type": "MedicalWebPage",
        "@id": url + "#page",
        "url": url,
        "name": c["h1"],
        "headline": c["h1"],
        "description": c["desc"],
        "inLanguage": lang,
        "datePublished": a["date_iso"],
        "dateModified": a.get("updated_iso") or a["date_iso"],
        "lastReviewed": a.get("updated_iso") or a["date_iso"],
        "image": {"@type": "ImageObject", "url": img, "width": dims[0], "height": dims[1]},
        "author": {"@id": f"{SITE}/#adnan"},
        "publisher": {"@id": f"{SITE}/#org"},
        "isPartOf": {"@id": f"{SITE}/#website"},
        "audience": {"@type": "Patient"},
        "isAccessibleForFree": True,
    }
    if cid:
        page["about"] = {"@type": "Thing", "name": cat_name(lang, cid)}
    if a.get("sources"):
        page["citation"] = [
            {k: v for k, v in
             (("@type", "CreativeWork"), ("name", s["label"]), ("url", s.get("url")))
             if v}
            for s in a["sources"]
        ]

    faq = {
        "@type": "FAQPage",
        "@id": url + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in c["faqs"]
        ],
    }

    crumbs = [
        {"@type": "ListItem", "position": 1, "name": L[lang]["crumb_home"], "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": L[lang]["crumb_articles"], "item": L[lang]["hub"]},
    ]
    if cid:
        crumbs.append({"@type": "ListItem", "position": 3, "name": cat_name(lang, cid),
                       "item": SITE + cat_url(lang, cid)})
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": c["h1"], "item": url})

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            ORG_LD,
            PERSON_LD,
            {"@type": "WebSite", "@id": f"{SITE}/#website", "url": SITE,
             "name": "Sihtak", "publisher": {"@id": f"{SITE}/#org"}},
            page, faq,
            {"@type": "BreadcrumbList", "@id": url + "#crumbs", "itemListElement": crumbs},
        ],
    }
    return f'  <script type="application/ld+json">{jd(graph)}</script>\n'


# --------------------------------------------------------------------------
def related(lang, a, articles):
    """Nearest by vocabulary, same category weighted up (build_links.related_for).
    Topical clusters beat a global rotation for the reader and for how Google
    reads the internal link graph, and the old first-four-in-file-order pick
    left most of a large category with no inbound related links at all."""
    cid = a.get("category")
    same = [x for x in articles if x["slug"] != a["slug"] and x.get("category") == cid]
    picked = related_for(a, articles)
    heading = L[lang]["related_h"]
    if cid and len(same) >= 3:
        heading = f'{L[lang]["more_in_h"]} {cat_name(lang, cid)}'
    return (
        '    <section class="art-related">\n'
        f'      <h2 class="reveal">{heading}</h2>\n'
        '      <div class="art-grid">\n'
        + "".join(card(lang, x) for x in picked) +
        '      </div>\n'
        '    </section>\n'
        '  </main>\n'
    )


def page(lang, a, articles):
    c = a["content"][lang]
    o = L[lang]
    slug = a["slug"]
    url = f'{SITE}{o["base"]}{slug}/'
    ar_url = f'{SITE}/articles/{slug}/'
    en_url = f'{SITE}/en/articles/{slug}/'
    other_href = f'/en/articles/{slug}/' if lang == "ar" else f'/articles/{slug}/'
    cid = a.get("category")
    chip = cat_name(lang, cid) or a.get(f"chip_{lang}", "")
    date_txt = a["date_ar"] if lang == "ar" else a["date_en"]
    byline = (f'{o["byline"]} <bdi><strong>{AUTHOR}</strong></bdi> · {date_txt} · '
              f'{a["read_min"]} {o["read_suffix"]}')
    # og:image is the titled share card, in this page's language: a link
    # pasted into WhatsApp or LinkedIn shows a picture and a headline where
    # the site's own words would otherwise be a caption nobody reads.
    cover = COVERS.get(slug)
    og_img = SITE + COVER_SHARE.format(slug, lang) if cover else (
        SITE + a["lead_image"]["src"] if a.get("lead_image", {}).get("src") else None)
    og_alt = (cover or {}).get(f"alt_{lang}", "")

    chip_html = (f'<a class="art-chip" href="{cat_url(lang, cid)}">{e(chip)}</a>'
                 if cid else f'<span class="art-chip">{e(chip)}</span>')

    hero = (
        '  <main class="art-page">\n'
        + breadcrumbs(lang, a) +
        '    <header class="art-hero">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <div class="art-hero-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{a.get("icon", "")}</svg></div>\n'
        f'        {chip_html}\n'
        f'        <h1>{e(c["h1"])}</h1>\n'
        f'        <p class="art-meta">{byline}</p>\n'
        '      </div>\n'
        '    </header>\n'
        + lead_image(a, lang) +
        '    <article class="art-body">\n'
    )

    return (
        head(lang, title=c["title"], desc=c["desc"], url=url, ar_url=ar_url, en_url=en_url,
             keywords=c.get("keywords", ""), og_type="article", og_image=og_img,
             og_image_alt=og_alt, extra_ld=ldjson(lang, a))
        + nav(lang, other_href)
        + hero
        + body_html(lang, a, articles)
        + "    </article>\n"
        + related(lang, a, articles)
        + footer(lang)
        + SCRIPT_BLOCK
    )


def main():
    with open(DATA, encoding="utf-8") as fh:
        raw = json.load(fh)
    for a in raw:
        normalise(a)
    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump(raw, fh, ensure_ascii=False, indent=1)

    everything = load_articles()
    print(f"Building {len(raw)} article(s); {len(everything)} total in the index")
    for a in raw:
        for lang in ("ar", "en"):
            d = os.path.join(BASE, "articles" if lang == "ar" else os.path.join("en", "articles"),
                             a["slug"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(page(lang, a, everything))
    print("  pages written for both languages")
    print("Now run: python build_site.py")


if __name__ == "__main__":
    main()
