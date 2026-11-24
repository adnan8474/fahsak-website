#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sihtak site builder: everything that is derived from the article set.

Regenerates, wholesale and idempotently:
  /articles/  and  /en/articles/            the full library: every article as
                                            a card, filtered/sorted in place
  /articles/c/<cat>/  and the /en/ mirror   one page per taxonomy category
  /articles/search-index.json  (+ /en/)     machine-readable index of the whole
                                            library. The hub no longer fetches
                                            it (it filters the cards it already
                                            has), but it is a stable JSON view
                                            of the content set, so it is kept.
  /sitemap.xml                              sitemap index
  /sitemap-pages.xml, /sitemap-articles.xml
  /articles/feed.xml                        RSS
  /404.html                                 real 404, not a soft one
  /author/  and /en/author/                 E-E-A-T author page
  /index.html                               only the block between the
                                            library-band markers, so the home
                                            page always shows the real article
                                            and per-topic counts

Nothing here is append-only, so the output can never drift out of sync with
content/articles.json the way the old insert-a-card-into-HTML approach did.

Run after build_content.py:  python build_site.py
"""
import os, json, datetime

from build_chrome import (
    BASE, SITE, AUTHOR, AUTHOR_URL, OG_IMAGE, PLAY, APPSTORE, L, CATEGORIES,
    CAT_BY_ID, cat_url, cat_name, fmt_date, e, nav, footer, head, card, jd,
    ORG_LD, PERSON_LD, SCRIPT_BLOCK, load_articles,
    load_covers, COVER_HERO, headline,
)

TODAY = datetime.date.today().isoformat()

# staticwebapp.config.json caches *.css and *.js for a week, so a returning
# reader would otherwise get the new hub markup with last week's stylesheet and
# last week's script. Only the hub needs the busted URLs: the article pages use
# none of the new rules, and versioning them would throw away a warm cache on
# 348 pages for nothing.
# Single source of truth lives in build_chrome so every builder busts together.
from build_chrome import ASSET_V

# Twelve illustrated topic covers live at /images/topics/<id>.webp (800x450
# tile) and <id>-wide.webp (1200x630, the category hero and that page's
# og:image). They are built from the source art by tmp/topic_covers.py.
TOPIC_COVERS = "/images/topics/"

# Per-article 3D covers, a different tier: the twelve flat tiles say "this is
# the nutrition shelf", one render per article says "this is that article".
# Built by build_covers.py, which also writes the alt text.
ART_COVERS = load_covers()

# Every URL here ends in a slash, because that is the form each page declares
# as its own canonical and the slashless variants are 301s. A sitemap that
# advertises the redirecting form asks Google to crawl twice to reach one page.
#
# A pair is (arabic path, english path) where the same page exists in both
# languages; those emit reciprocal hreflang so the right one shows in the right
# market. Single-language documents (the legal set, which is English only) go
# in SOLO_PAGES and carry no alternates.
PAIRED_PAGES = [
    ("/", "/en/", "weekly", "1.0"),
    ("/articles/", "/en/articles/", "daily", "0.9"),
    ("/tools/", "/en/tools/", "monthly", "0.8"),
    ("/tools/bmi/", "/en/tools/bmi/", "monthly", "0.7"),
    ("/tools/a1c-converter/", "/en/tools/a1c-converter/", "monthly", "0.7"),
    ("/tools/lab-unit-converter/", "/en/tools/lab-unit-converter/", "monthly", "0.7"),
    ("/about/", "/en/about/", "monthly", "0.6"),
    ("/author/", "/en/author/", "monthly", "0.5"),
]
# The single-analyte converters (build_tools.py writes them from this file).
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "converters.json"),
          encoding="utf-8") as _fh:
    PAIRED_PAGES += [(f"/tools/{c['slug']}/", f"/en/tools/{c['slug']}/", "monthly", "0.7")
                     for c in json.load(_fh)]

SOLO_PAGES = [
    ("/privacy/", "yearly", "0.3"),
    ("/terms/", "yearly", "0.3"),
    ("/contact/", "yearly", "0.4"),
    ("/delete-account/", "yearly", "0.3"),
]


def out_dir(lang, *parts):
    root = "articles" if lang == "ar" else os.path.join("en", "articles")
    d = os.path.join(BASE, root, *parts)
    os.makedirs(d, exist_ok=True)
    return d


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------
# shared blocks
# --------------------------------------------------------------------------
def topic_tiles(lang, counts, active=None):
    tiles = []
    for c in CATEGORIES:
        n = counts.get(c["id"], 0)
        if not n:
            continue
        cls = "cat-tile" + (" cat-tile--active" if c["id"] == active else "")
        tiles.append(
            f'        <a class="{cls}" href="{cat_url(lang, c["id"])}">\n'
            f'          <span class="cat-tile-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{c["icon"]}</svg></span>\n'
            f'          <span class="cat-tile-name">{e(c[lang]["name"])}</span>\n'
            f'          <span class="cat-tile-count">{n}</span>\n'
            '        </a>\n'
        )
    return (
        '      <section class="cat-strip">\n'
        f'        <h2 class="cat-strip-h">{L[lang]["browse_h"]}</h2>\n'
        '        <div class="cat-tiles">\n'
        + "".join(tiles) +
        '        </div>\n'
        '      </section>\n'
    )


def topic_covers(lang, counts):
    """The illustrated topic grid that opens the hub.

    This replaces the plain icon strip that used to sit at the very bottom of
    the hub, underneath 174 cards, where a reader would have had to scroll past
    the entire library to discover that the library had topics.
    """
    o = L[lang]
    tiles = []
    for c in CATEGORIES:
        n = counts.get(c["id"], 0)
        if not n:
            continue
        tiles.append(
            f'        <a class="topic-tile" href="{cat_url(lang, c["id"])}">\n'
            f'          <span class="topic-tile-media"><img src="{TOPIC_COVERS}{c["id"]}.webp" alt="" '
            'width="800" height="450" loading="lazy" decoding="async"></span>\n'
            '          <span class="topic-tile-body">\n'
            f'            <span class="topic-tile-name">{e(c[lang]["name"])}</span>\n'
            f'            <span class="topic-tile-count">{e(o["tpl_all"].replace("{t}", str(n)))}</span>\n'
            '          </span>\n'
            '        </a>\n'
        )
    return (
        '    <section class="hub-covers">\n'
        f'      <h2 class="cat-strip-h">{e(o["browse_h"])}</h2>\n'
        '      <div class="topic-tiles">\n'
        + "".join(tiles) +
        '      </div>\n'
        '    </section>\n'
    )


def search_box(lang):
    o = L[lang]
    return (
        '        <div class="art-search">\n'
        '          <svg class="art-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.7" y2="16.7"/></svg>\n'
        f'          <input type="search" id="artSearch" placeholder="{e(o["search_ph"], True)}" '
        f'aria-label="{e(o["search_ph"], True)}" autocomplete="off">\n'
        '        </div>\n'
    )


def hub_toolbar(lang, counts, total):
    """Sticky control bar: search, sort, and one filter chip per category.

    The chips are real links to the category pages, not buttons. hub.js
    intercepts the click and filters in place, but with JS off (or before it
    loads) they still go somewhere useful, and a crawler sees ordinary
    internal links rather than dead controls.
    """
    o = L[lang]
    chips = [
        f'          <a class="hub-chip hub-chip--on" href="{o["nav_articles"]}" data-cat="" '
        f'data-name="{e(o["all_articles"], True)}" aria-pressed="true">'
        f'{e(o["chip_all"])}<span class="hub-chip-n">{total}</span></a>\n'
    ]
    for c in CATEGORIES:
        n = counts.get(c["id"], 0)
        if not n:
            continue
        chips.append(
            f'          <a class="hub-chip" href="{cat_url(lang, c["id"])}" data-cat="{c["id"]}" '
            f'data-name="{e(c[lang]["name"], True)}" aria-pressed="false">'
            f'{e(c[lang]["name"])}<span class="hub-chip-n">{n}</span></a>\n'
        )
    return (
        '    <div class="hub-toolbar" id="hubBar">\n'
        '      <div class="hub-toolbar-in">\n'
        '        <div class="hub-toolbar-row">\n'
        + search_box(lang)
        + f'          <div class="hub-sorts" role="group" aria-label="{e(o["sort_label"], True)}">\n'
        f'            <button type="button" class="hub-sort hub-sort--on" data-sort="new" aria-pressed="true">{e(o["sort_new"])}</button>\n'
        f'            <button type="button" class="hub-sort" data-sort="az" aria-pressed="false">{e(o["sort_az"])}</button>\n'
        '          </div>\n'
        '        </div>\n'
        f'        <div class="hub-filters" id="hubFilters" role="group" aria-label="{e(o["filters_label"], True)}">\n'
        + "".join(chips)
        + '        </div>\n'
        '      </div>\n'
        '    </div>\n'
    )


# --------------------------------------------------------------------------
# hub
# --------------------------------------------------------------------------
def hub_page(lang, articles, counts):
    """The whole library on one page.

    Every article is rendered as a card up front rather than a "latest 24"
    teaser, so the entry point actually links to all of the content: one click
    from the hub to any article, and one crawlable link per article instead of
    the 24 that used to be reachable here. Filtering, search and sort are then
    a matter of hiding cards that are already in the DOM.
    """
    o = L[lang]
    url = o["hub"]
    total = len(articles)
    if lang == "ar":
        h1 = "مقالات صحية موثوقة بالعربية"
        sub = ("شروحات طبية مبسطة تهم الشرق الأوسط: التحاليل والأمراض المزمنة والوراثية، "
               "صحة المرأة والطفل، الأدوية والتغذية والصحة النفسية. مكتوبة بلغة يفهمها الجميع "
               "ومدعومة بمصادر منشورة.")
        title = "مقالات صحية بالعربية"
    else:
        h1 = "Health guides for the Middle East"
        sub = ("Plain explanations of the health questions that actually come up here: lab "
               "tests, chronic and inherited conditions, women's and children's health, "
               "medicines, nutrition and mental health. Written clearly and sourced.")
        title = "Health Articles"
    all_h = o["all_articles"]

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            ORG_LD, PERSON_LD,
            {"@type": "WebSite", "@id": f"{SITE}/#website", "url": SITE, "name": "Sihtak",
             "publisher": {"@id": f"{SITE}/#org"},
             "potentialAction": {
                 "@type": "SearchAction",
                 "target": {"@type": "EntryPoint",
                            "urlTemplate": f'{url}?q={{search_term_string}}'},
                 "query-input": "required name=search_term_string"}},
            {"@type": "CollectionPage", "@id": url + "#page", "url": url, "name": h1,
             "description": sub, "inLanguage": lang,
             "isPartOf": {"@id": f"{SITE}/#website"},
             "publisher": {"@id": f"{SITE}/#org"},
             # Summary-page form: url-only list items, one per article actually
             # on the page. Repeating all 174 titles here would double the
             # weight of the page for no gain, since the title is already in
             # the card and again on the article itself.
             "mainEntity": {
                 "@type": "ItemList",
                 "numberOfItems": total,
                 "itemListElement": [
                     {"@type": "ListItem", "position": i,
                      "url": f'{SITE}{o["base"]}{a["slug"]}/'}
                     for i, a in enumerate(articles, 1)]}},
            {"@type": "BreadcrumbList", "@id": url + "#crumbs", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": o["crumb_home"], "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": o["crumb_articles"], "item": url},
            ]},
        ],
    }

    return (
        head(lang, title=title, desc=sub, url=url,
             ar_url=f"{SITE}/articles/", en_url=f"{SITE}/en/articles/",
             og_type="website",
             css=(f"/style.css?v={ASSET_V}", f"/articles/article.css?v={ASSET_V}"),
             extra_ld=f'  <script type="application/ld+json">{jd(ld)}</script>\n')
        + nav(lang, "/en/articles/" if lang == "ar" else "/articles/")
        + '  <main class="art-page">\n'
        '    <header class="art-hero art-hero--hub">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <h1>{e(h1)}</h1>\n'
        f'        <p class="art-hub-sub">{e(sub)}</p>\n'
        # No count in the hero: the meta line under the toolbar carries it and
        # keeps it live as the reader filters, so printing it twice would just
        # mean one of the two numbers is wrong most of the time.
        '      </div>\n'
        '    </header>\n'
        # Covers first, then the controls. A reader who knows what they want
        # scrolls one screen and picks a topic; a reader who does not keeps
        # going and gets the whole library with a search box pinned above it.
        + topic_covers(lang, counts)
        + hub_toolbar(lang, counts, total)
        + '    <div class="art-hub-body">\n'
        '      <div class="hub-meta">\n'
        f'        <span class="hub-count" id="hubCount" data-tpl-all="{e(o["tpl_all"], True)}" '
        f'data-tpl-some="{e(o["tpl_some"], True)}">{o["tpl_all"].replace("{t}", str(total))}</span>\n'
        f'        <button type="button" class="hub-clear" id="hubClear" hidden>{e(o["clear_filter"])}</button>\n'
        '      </div>\n'
        '      <section class="art-related art-related--hub">\n'
        f'        <h2 id="hubHeading">{e(all_h)}</h2>\n'
        '        <div class="art-grid" id="hubGrid">\n'
        + "".join(card(lang, a, reveal=False, searchable=True) for a in articles)
        + '        </div>\n'
        f'        <p class="art-search-none" id="artNone" hidden>{e(o["search_none"])}</p>\n'
        '      </section>\n'
        '    </div>\n'
        '  </main>\n'
        + footer(lang)
        + f'  <script src="/articles/hub.js?v={ASSET_V}" defer></script>\n'
        + SCRIPT_BLOCK
    )


# --------------------------------------------------------------------------
# category page
# --------------------------------------------------------------------------
def category_page(lang, c, items, counts):
    o = L[lang]
    cid = c["id"]
    url = SITE + cat_url(lang, cid)
    ar_url = f"{SITE}/articles/c/{cid}/"
    en_url = f"{SITE}/en/articles/c/{cid}/"
    meta = c[lang]
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            ORG_LD,
            {"@type": "CollectionPage", "@id": url + "#page", "url": url,
             "name": meta["title"], "description": meta["desc"], "inLanguage": lang,
             "isPartOf": {"@id": f"{SITE}/#website"}, "publisher": {"@id": f"{SITE}/#org"},
             "mainEntity": {
                 "@type": "ItemList", "numberOfItems": len(items),
                 "itemListElement": [
                     {"@type": "ListItem", "position": i,
                      "url": f'{SITE}{o["base"]}{a["slug"]}/',
                      "name": a["content"][lang]["title"]}
                     for i, a in enumerate(items, 1)]}},
            {"@type": "BreadcrumbList", "@id": url + "#crumbs", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": o["crumb_home"], "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": o["crumb_articles"], "item": o["hub"]},
                {"@type": "ListItem", "position": 3, "name": meta["name"], "item": url},
            ]},
        ],
    }
    crumbs = (
        '    <nav class="art-crumbs" aria-label="Breadcrumb">\n      <ol>\n'
        f'        <li><a href="/">{o["crumb_home"]}</a></li>\n'
        f'        <li><a href="{o["nav_articles"]}">{o["crumb_articles"]}</a></li>\n'
        f'        <li><span aria-current="page">{e(meta["name"])}</span></li>\n'
        '      </ol>\n    </nav>\n'
    )
    return (
        head(lang, title=meta["title"], desc=meta["desc"], url=url,
             ar_url=ar_url, en_url=en_url, og_type="website",
             # Each topic now shares as its own illustration instead of the one
             # generic site card, so twelve links look like twelve things.
             og_image=f"{SITE}{TOPIC_COVERS}{cid}-wide.webp",
             css=(f"/style.css?v={ASSET_V}", f"/articles/article.css?v={ASSET_V}"),
             extra_ld=f'  <script type="application/ld+json">{jd(ld)}</script>\n')
        + nav(lang, f'/en/articles/c/{cid}/' if lang == "ar" else f'/articles/c/{cid}/')
        + '  <main class="art-page">\n'
        + crumbs
        + '    <header class="art-hero art-hero--hub art-hero--cover">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        '        <div class="cat-hero-copy">\n'
        f'          <div class="art-hero-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{c["icon"]}</svg></div>\n'
        f'          <h1>{e(meta["title"])}</h1>\n'
        f'          <p class="art-hub-sub">{e(meta["desc"])}</p>\n'
        f'          <p class="art-hub-count">{len(items)} {e(o["count_suffix"])}</p>\n'
        '        </div>\n'
        f'        <div class="cat-cover"><img src="{TOPIC_COVERS}{cid}-wide.webp" alt="" '
        'width="1200" height="630" fetchpriority="high" decoding="async"></div>\n'
        '      </div>\n'
        '    </header>\n'
        '    <div class="art-hub-body">\n'
        '      <section class="art-related art-related--hub">\n'
        f'        <h2 class="cat-list-h">{e(o["cat_list_h"].format(meta["name"]))}</h2>\n'
        '        <div class="art-grid">\n'
        + "".join(card(lang, a) for a in items)
        + '        </div>\n      </section>\n'
        + topic_tiles(lang, counts, active=cid)
        + '    </div>\n  </main>\n'
        + footer(lang)
        + SCRIPT_BLOCK
    )


# --------------------------------------------------------------------------
# author page
# --------------------------------------------------------------------------
def author_page(lang):
    o = L[lang]
    # Each language canonicalises to itself. Pointing the English page at the
    # Arabic one told Google it was a duplicate, which dropped the English
    # author page from the index and with it the E-E-A-T signal that 168
    # English articles link to from their byline.
    url = AUTHOR_URL if lang == "ar" else f"{SITE}/en/author/"
    if lang == "ar":
        title = "عدنان الرفاعي · كاتب صحتك"
        h1 = "عدنان الرفاعي"
        blocks = [
            ("لماذا أكتب هذا المحتوى",
             ["أحمل ماجستيراً في الكيمياء الحيوية السريرية وعضوية معهد العلوم الطبية الحيوية البريطاني IBMS، "
              "وأنا عضو لجنة الصحة في المجلس العلمي السوري. أعمل منذ سنوات في بناء الأنظمة التي تربط أجهزة التحاليل الطبية بالسجلات الصحية، "
              "في المملكة المتحدة والشرق الأوسط. هذا يعني أنني أرى يومياً كيف تُنتَج أرقام "
              "التحاليل، وأين تُخطئ الأجهزة، وكيف تصل النتيجة إلى الطبيب والمريض.",
              "لاحظت أن المحتوى الصحي العربي على الإنترنت إما مترجم ترجمة رديئة، أو مكتوب "
              "لبيع منتج، أو يتجاهل واقع المنطقة تماماً: زواج الأقارب، نقص فيتامين د رغم "
              "الشمس، الأركيلة، الصيام، وانهيار الأنظمة الصحية في بعض بلداننا. صحتك محاولة "
              "لسد هذه الفجوة."]),
            ("كيف تُكتب المقالات",
             ["كل مقال يعتمد على مصادر منشورة: منظمة الصحة العالمية، هيئة الخدمات الصحية "
              "البريطانية NHS، مراكز السيطرة على الأمراض CDC، ووزارات الصحة في المنطقة "
              "والدراسات المنشورة. المصادر مذكورة أسفل كل مقال لتتحقق منها بنفسك.",
              "نتجنب الوعود والعلاجات المعجزة. وحين لا يكون الدليل العلمي حاسماً، نقول ذلك "
              "صراحة بدلاً من اختراع إجابة."]),
        ]
        role = "مؤسس صحتك · ماجستير في الكيمياء الحيوية السريرية · عضو IBMS"
    else:
        title = "Adnan Alrefai · Sihtak"
        h1 = "Adnan Alrefai"
        blocks = [
            ("Why I write this",
             ["I hold an MSc in Clinical Biochemistry and am a member of the Institute of Biomedical Science (MIBMS) "
              "and of the Health Committee of the Syrian Scientific Council. I have spent years building the systems that connect laboratory analysers to "
              "health records, across the UK and the Middle East. That means I see every day "
              "how a lab number is actually produced, where instruments go wrong, and how a "
              "result travels to the doctor and the patient.",
              "Arabic health content online is mostly badly translated, written to sell "
              "something, or blind to the realities of this region: cousin marriage, vitamin D "
              "deficiency in the sunniest places on earth, shisha, fasting, and health systems "
              "that have partly collapsed. Sihtak is an attempt to close that gap."]),
            ("How these articles are written",
             ["Every article is built from published sources: the World Health Organization, "
              "the UK NHS, the US CDC, health ministries across the region, and peer-reviewed "
              "studies. Sources are listed at the foot of each article so you can check them.",
              "We avoid miracle cures and confident promises. Where the evidence is genuinely "
              "unsettled, we say so instead of inventing an answer."]),
        ]
        role = "Founder of Sihtak · MSc Clinical Biochemistry · MIBMS"

    secs = "".join(
        f'      <section class="reveal">\n        <h2>{e(h)}</h2>\n'
        + "".join(f'        <p>{e(p)}</p>\n' for p in ps)
        + '      </section>\n'
        for h, ps in blocks
    )
    ld = {"@context": "https://schema.org",
          "@graph": [ORG_LD, PERSON_LD,
                     {"@type": "ProfilePage", "@id": url + "#page", "url": url,
                      "name": title, "inLanguage": lang,
                      "mainEntity": {"@id": f"{SITE}/#adnan"}}]}
    return (
        head(lang, title=title, desc=o["author_bio"][:158], url=url,
             ar_url=AUTHOR_URL, en_url=f"{SITE}/en/author/", og_type="profile",
             extra_ld=f'  <script type="application/ld+json">{jd(ld)}</script>\n')
        + nav(lang, "/en/author/" if lang == "ar" else "/author/")
        + '  <main class="art-page">\n'
        '    <header class="art-hero">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <h1>{e(h1)}</h1>\n'
        f'        <p class="art-meta">{e(role)}</p>\n'
        '      </div>\n'
        '    </header>\n'
        '    <article class="art-body">\n'
        + secs
        + '    </article>\n  </main>\n'
        + footer(lang)
        + SCRIPT_BLOCK
    )


# --------------------------------------------------------------------------
# 404
# --------------------------------------------------------------------------
def not_found_page(counts):
    lang = "ar"
    o = L[lang]
    tiles = topic_tiles(lang, counts)
    return (
        head(lang, title="الصفحة غير موجودة", desc="الصفحة التي تبحث عنها غير موجودة على موقع صحتك.",
             url=f"{SITE}/404.html", ar_url=f"{SITE}/", en_url=f"{SITE}/",
             og_type="website", robots="noindex, follow")
        + nav(lang, "/en/articles/")
        + '  <main class="art-page">\n'
        '    <header class="art-hero art-hero--hub">\n'
        '      <div class="art-hero-inner reveal">\n'
        '        <span class="art-chip">404</span>\n'
        '        <h1>هذه الصفحة غير موجودة</h1>\n'
        '        <p class="art-hub-sub">ربما تغيّر الرابط أو حُذفت الصفحة. جرّب البحث في المقالات '
        'أو تصفّح المواضيع بالأسفل. <span dir="ltr">This page does not exist.</span></p>\n'
        '        <p style="margin-top:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">\n'
        '          <a href="/" class="btn btn-primary btn-sm">الصفحة الرئيسية</a>\n'
        '          <a href="/articles/" class="btn btn-ghost btn-sm">كل المقالات</a>\n'
        '        </p>\n'
        '      </div>\n'
        '    </header>\n'
        '    <div class="art-hub-body">\n' + tiles + '    </div>\n'
        '  </main>\n'
        + footer(lang)
        + SCRIPT_BLOCK
    )


# --------------------------------------------------------------------------
# feeds, sitemaps, search index
# --------------------------------------------------------------------------
def build_feed(articles):
    items = []
    for a in articles[:60]:
        link = f"{SITE}/articles/{a['slug']}/"
        c = a["content"]["ar"]
        d = datetime.date.fromisoformat(a["date_iso"])
        pub = d.strftime("%a, %d %b %Y") + " 08:00:00 GMT"
        items.append(
            "    <item>\n"
            f"      <title>{e(c['title'])}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid isPermaLink=\"true\">{link}</guid>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f"      <description>{e(c['desc'])}</description>\n"
            "    </item>\n"
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
           '  <channel>\n'
           '    <title>صحتك · مقالات صحية</title>\n'
           f'    <link>{SITE}/articles/</link>\n'
           '    <description>شروحات طبية مبسطة بالعربية من تطبيق صحتك.</description>\n'
           '    <language>ar</language>\n'
           f'    <atom:link href="{SITE}/articles/feed.xml" rel="self" type="application/rss+xml"/>\n'
           + "".join(items)
           + '  </channel>\n</rss>\n')
    write(os.path.join(BASE, "articles", "feed.xml"), xml)


def url_block(loc, lastmod, changefreq, priority, ar=None, en=None, images=()):
    """One <url> entry. `images` is a list of (absolute url, caption) pairs.

    The image extension is what gets a picture into Google Images independently
    of the page it sits on, which for a health library is a whole second
    doorway: people search "what does a thyroid test look like" in pictures.
    Google reads the caption as the image's own description, so it is worth a
    real sentence rather than the page title again.
    """
    alts = ""
    if ar and en:
        alts = (f'    <xhtml:link rel="alternate" hreflang="ar" href="{ar}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{ar}"/>\n')
    imgs = "".join(
        "    <image:image>\n"
        f"      <image:loc>{u}</image:loc>\n"
        f"      <image:title>{e(cap, True)}</image:title>\n"
        "    </image:image>\n"
        for u, cap in images
    )
    return ("  <url>\n"
            f"    <loc>{loc}</loc>\n" + alts +
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n" + imgs +
            "  </url>\n")


HEAD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml"\n'
            '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n')


def build_sitemaps(articles, counts):
    blocks = [url_block(SITE + p, TODAY, cf, pr) for p, cf, pr in SOLO_PAGES]
    for ar_p, en_p, cf, pr in PAIRED_PAGES:
        ar, en = SITE + ar_p, SITE + en_p
        blocks.append(url_block(ar, TODAY, cf, pr, ar, en))
        blocks.append(url_block(en, TODAY, cf, pr, ar, en))
    for c in CATEGORIES:
        if not counts.get(c["id"]):
            continue
        ar = f"{SITE}/articles/c/{c['id']}/"
        en = f"{SITE}/en/articles/c/{c['id']}/"
        cover = f"{SITE}{TOPIC_COVERS}{c['id']}-wide.webp"
        blocks.append(url_block(ar, TODAY, "weekly", "0.8", ar, en,
                                [(cover, c["ar"]["name"])]))
        blocks.append(url_block(en, TODAY, "weekly", "0.7", ar, en,
                                [(cover, c["en"]["name"])]))
    write(os.path.join(BASE, "sitemap-pages.xml"), HEAD_XML + "".join(blocks) + "</urlset>\n")

    ablocks = []
    for a in articles:
        ar = f"{SITE}/articles/{a['slug']}/"
        en = f"{SITE}/en/articles/{a['slug']}/"
        lm = a.get("updated_iso") or a["date_iso"]
        # The image entry carries the untitled hero and, as its title, the
        # article headline in that language. Google Images indexes the picture
        # against those words, which is the whole point of one cover per
        # article rather than one shared og-image for the site.
        cover = ART_COVERS.get(a["slug"])
        hero = f"{SITE}{COVER_HERO.format(a['slug'])}" if cover else None
        imgs = {lang: [(hero, headline(a, lang))] if hero else []
                for lang in ("ar", "en")}
        ablocks.append(url_block(ar, lm, "monthly", "0.8", ar, en, imgs["ar"]))
        ablocks.append(url_block(en, lm, "monthly", "0.7", ar, en, imgs["en"]))
    write(os.path.join(BASE, "sitemap-articles.xml"), HEAD_XML + "".join(ablocks) + "</urlset>\n")

    idx = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f'  <sitemap>\n    <loc>{SITE}/sitemap-pages.xml</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n'
           f'  <sitemap>\n    <loc>{SITE}/sitemap-articles.xml</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n'
           '</sitemapindex>\n')
    write(os.path.join(BASE, "sitemap.xml"), idx)
    return len(blocks), len(ablocks)


def build_search_index(lang, articles):
    payload = [{
        "t": a["content"][lang]["title"],
        "d": a["content"][lang]["desc"],
        "u": f'{L[lang]["base"]}{a["slug"]}/',
        "c": cat_name(lang, a.get("category")),
        "k": a["content"][lang].get("keywords", ""),
    } for a in articles]
    d = out_dir(lang)
    with open(os.path.join(d, "search-index.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))


HUB_JS = """/* Sihtak article library: search, topic filter and sort for the hub.

   Every card is already in the page, so nothing is fetched and nothing is
   re-rendered. Filtering toggles [hidden] on cards that exist, which keeps the
   markup, the links and the crawlable state identical whether or not this file
   ever runs. With JS off the reader still gets the full list plus chips that
   behave as ordinary links to the category pages. */
(function () {
  var grid = document.getElementById('hubGrid');
  if (!grid) return;

  var box = document.getElementById('artSearch');
  var none = document.getElementById('artNone');
  var countEl = document.getElementById('hubCount');
  var clearBtn = document.getElementById('hubClear');
  var heading = document.getElementById('hubHeading');
  var bar = document.getElementById('hubBar');
  var chips = [].slice.call(document.querySelectorAll('.hub-chip'));
  var sorts = [].slice.call(document.querySelectorAll('.hub-sort'));

  /* Strip Arabic diacritics and normalise alef/ya/ta-marbuta so that a search
     for "امراض" still matches "أمراض". */
  function norm(s) {
    return (s || '')
      .toLowerCase()
      .replace(/[\\u064B-\\u0652\\u0670\\u0640]/g, '')
      .replace(/[\\u0622\\u0623\\u0625\\u0671]/g, '\\u0627')
      .replace(/\\u0649/g, '\\u064A')
      .replace(/\\u0629/g, '\\u0647');
  }

  /* Read every card once. The haystack is built from what is already on the
     card plus the keyword list the builder attached, so the page carries no
     duplicate copy of its own text. */
  var items = [].slice.call(grid.children).map(function (el, i) {
    var h = el.querySelector('h3');
    var p = el.querySelector('p');
    var c = el.querySelector('.art-chip');
    return {
      el: el,
      i: i,
      cat: el.getAttribute('data-cat') || '',
      title: h ? h.textContent.trim() : '',
      hay: norm([h && h.textContent, p && p.textContent, c && c.textContent,
                 el.getAttribute('data-k')].join(' '))
    };
  });
  var total = items.length;
  var allLabel = heading ? heading.textContent : '';
  var lang = document.documentElement.lang || 'en';
  var state = { cat: '', q: '', sort: 'new' };

  function tpl(s, n, t) {
    return String(s || '').replace('{n}', n).replace('{t}', t);
  }

  function paint() {
    var terms = state.q ? state.q.split(/\\s+/) : [];
    var shown = 0;
    for (var i = 0; i < total; i++) {
      var it = items[i];
      var ok = !state.cat || it.cat === state.cat;
      for (var j = 0; ok && j < terms.length; j++) {
        if (it.hay.indexOf(terms[j]) === -1) ok = false;
      }
      it.el.hidden = !ok;
      if (ok) shown++;
    }

    var filtered = !!(state.cat || state.q);
    if (none) none.hidden = shown !== 0;
    if (countEl) {
      countEl.textContent = filtered
        ? tpl(countEl.getAttribute('data-tpl-some'), shown, total)
        : tpl(countEl.getAttribute('data-tpl-all'), total, total);
    }
    if (clearBtn) clearBtn.hidden = !filtered;
    if (heading) {
      var on = state.cat ? grid.ownerDocument.querySelector(
        '.hub-chip[data-cat="' + state.cat + '"]') : null;
      heading.textContent = on ? on.getAttribute('data-name') : allLabel;
    }
    sync();
  }

  function applySort() {
    var order = items.slice();
    if (state.sort === 'az') {
      order.sort(function (a, b) { return a.title.localeCompare(b.title, lang); });
    } else {
      order.sort(function (a, b) { return a.i - b.i; });
    }
    var frag = document.createDocumentFragment();
    order.forEach(function (it) { frag.appendChild(it.el); });
    grid.appendChild(frag);
  }

  /* Keep the address bar in step so a filtered view can be shared or
     reloaded. replaceState, not pushState: the back button should leave the
     hub, not walk back through every keystroke. */
  function sync() {
    if (!window.history || !history.replaceState) return;
    var p = [];
    if (state.cat) p.push('cat=' + encodeURIComponent(state.cat));
    if (box && box.value.trim()) p.push('q=' + encodeURIComponent(box.value.trim()));
    if (state.sort !== 'new') p.push('sort=' + state.sort);
    history.replaceState(null, '', location.pathname + (p.length ? '?' + p.join('&') : ''));
  }

  /* The chip strip scrolls sideways, so an active chip arriving from a ?cat=
     link can be off screen. Nudge the strip, never the page. */
  function revealChip(el) {
    if (!el) return;
    var run = function () {
      var strip = document.getElementById('hubFilters');
      if (!strip) return;
      var er = el.getBoundingClientRect(), sr = strip.getBoundingClientRect();
      if (er.left < sr.left) strip.scrollLeft -= (sr.left - er.left) + 16;
      else if (er.right > sr.right) strip.scrollLeft += (er.right - sr.right) + 16;
    };
    run();
    /* Chip widths only settle once the web font has swapped in. Measuring
       once against fallback metrics stops the strip short of the chip, so
       measure again when the fonts have finished either way. */
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(run);
  }

  function setCat(cat) {
    state.cat = cat;
    var active = null;
    chips.forEach(function (c) {
      var on = (c.getAttribute('data-cat') || '') === cat;
      c.classList.toggle('hub-chip--on', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
      if (on) active = c;
    });
    revealChip(active);
  }

  function setSort(s) {
    state.sort = s;
    sorts.forEach(function (b) {
      var on = b.getAttribute('data-sort') === s;
      b.classList.toggle('hub-sort--on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    applySort();
  }

  chips.forEach(function (chip) {
    chip.addEventListener('click', function (ev) {
      /* Modified clicks keep their normal meaning: open the real category
         page in a tab. */
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
      ev.preventDefault();
      setCat(chip.getAttribute('data-cat') || '');
      paint();
      var top = grid.getBoundingClientRect().top;
      var off = window.innerWidth <= 640 ? 170 : 200;
      if (top < off) window.scrollTo(0, window.pageYOffset + top - off);
    });
  });

  sorts.forEach(function (b) {
    b.addEventListener('click', function () {
      setSort(b.getAttribute('data-sort'));
      sync();
    });
  });

  if (box) {
    var timer;
    box.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        var v = norm(box.value.trim());
        state.q = v.length < 2 ? '' : v;
        paint();
      }, 120);
    });
    /* Escape clears the box the way a search field is expected to. */
    box.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && box.value) {
        box.value = ''; state.q = ''; paint();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (box) box.value = '';
      state.q = '';
      setCat('');
      paint();
      if (box) box.focus();
    });
  }

  /* Shadow under the bar only once it is actually stuck to the nav. */
  if (bar) {
    var ticking = false;
    var onScroll = function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var navH = window.innerWidth <= 640 ? 56 : 64;
        bar.classList.toggle('hub-toolbar--stuck',
          bar.getBoundingClientRect().top <= navH + 1);
        ticking = false;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  var u = new URLSearchParams(location.search);
  var c0 = u.get('cat') || '';
  var q0 = u.get('q') || '';
  if (c0 && chips.some(function (c) { return c.getAttribute('data-cat') === c0; })) setCat(c0);
  if (q0 && box) { box.value = q0; state.q = norm(q0.trim()); }
  if (u.get('sort') === 'az') setSort('az');
  paint();
})();
"""


# --------------------------------------------------------------------------
# home page library band
# --------------------------------------------------------------------------
# index.html is hand-written, so the builder only owns what is between these
# two markers. Everything else in the file is left byte for byte alone.
HOME = os.path.join(BASE, "index.html")
HOME_START = "<!-- library-band:start (generated by build_site.py) -->"
HOME_END = "<!-- library-band:end -->"


# The three covers fanned beside the copy. Decoration, not a menu: they carry
# no labels, no links and no alt text, and the reader gets to the library
# through the one button. Picked to look unlike each other at thumbnail size.
FAN = ("lab-tests", "womens-health", "nutrition")


def home_library_band(total):
    """The library band on the home page, in both languages at once.

    The home page's job is the app. This band exists to say the library is
    there and open its door, so it is one screen band with one link in it. It
    deliberately does not list articles or topics: that is what the hub is for,
    and two directories on one page was the reason this got cut down.

    The home page swaps language in the browser by writing data-ar/data-en into
    textContent, so every string here has to ship twice and every element that
    carries a pair has to be a leaf. The link carries data-href-ar/data-href-en
    for the same reason: an English reader has to land on the English hub.
    """
    ar, en = L["ar"], L["en"]

    def pair(tag, cls, key):
        a, b = ar[key], en[key]
        return (f'<{tag} class="{cls}" data-ar="{e(a, True)}" data-en="{e(b, True)}">'
                f'{e(a)}</{tag}>')

    fan = "".join(
        f'          <img src="{TOPIC_COVERS}{cid}.webp" alt="" width="800" height="450" '
        'loading="lazy" decoding="async">\n'
        for cid in FAN
    )
    heads = (ar["lib_h"].replace("{t}", str(total)), en["lib_h"].replace("{t}", str(total)))
    return (
        '  <style>\n'
        '    .lib-band{padding:64px 24px;background:linear-gradient(180deg,var(--bg) 0%,var(--bg-surface) 100%);'
        'border-top:1px solid var(--border);border-bottom:1px solid var(--border);}\n'
        '    .lib-inner{max-width:1080px;margin:0 auto;display:grid;'
        'grid-template-columns:1fr minmax(0,420px);gap:56px;align-items:center;}\n'
        '    .lib-copy{text-align:start;}\n'
        "    .lib-eyebrow{font-family:'Inter','Tajawal',sans-serif;font-size:12.5px;font-weight:700;"
        'letter-spacing:.08em;text-transform:uppercase;color:var(--teal);margin:0 0 12px;}\n'
        '    .lib-copy h2{font-size:clamp(24px,3.3vw,33px);line-height:1.32;color:var(--text);'
        'margin:0 0 12px;font-weight:800;}\n'
        '    .lib-lead{color:var(--text-m);font-size:16px;line-height:1.8;margin:0 0 26px;max-width:44ch;}\n'
        '    .lib-cta{display:inline-flex;align-items:center;gap:8px;padding:14px 30px;border-radius:999px;'
        'background:var(--teal);color:#fff;font-weight:700;font-size:15.5px;text-decoration:none;'
        'transition:transform .2s,box-shadow .2s;}\n'
        '    .lib-cta:hover{transform:translateY(-2px);box-shadow:0 18px 32px -16px rgba(58,157,146,.85);}\n'
        # The fan is three absolutely positioned cards. inset-inline-start flips
        # the running order in Arabic on its own, but rotation is not a logical
        # property, so the tilts are mirrored by hand below.
        '    .lib-fan{position:relative;height:232px;}\n'
        '    .lib-fan img{position:absolute;top:0;width:58%;height:auto;border-radius:14px;'
        'border:1px solid var(--border);background:#f7f2ec;'
        'box-shadow:0 22px 40px -26px rgba(20,40,70,.6);}\n'
        '    .lib-fan img:nth-child(1){inset-inline-start:0;top:30px;z-index:1;}\n'
        '    .lib-fan img:nth-child(2){inset-inline-start:21%;top:0;z-index:3;}\n'
        '    .lib-fan img:nth-child(3){inset-inline-start:42%;top:30px;z-index:2;}\n'
        '    html[dir="ltr"] .lib-fan img:nth-child(1){transform:rotate(-5deg);}\n'
        '    html[dir="ltr"] .lib-fan img:nth-child(3){transform:rotate(5deg);}\n'
        '    html[dir="rtl"] .lib-fan img:nth-child(1){transform:rotate(5deg);}\n'
        '    html[dir="rtl"] .lib-fan img:nth-child(3){transform:rotate(-5deg);}\n'
        '    @media (max-width:860px){.lib-inner{grid-template-columns:1fr;gap:36px;}'
        '.lib-copy{text-align:center;}.lib-lead{margin-inline:auto;}'
        '.lib-fan{height:190px;max-width:420px;margin-inline:auto;width:100%;}}\n'
        '    @media (max-width:640px){.lib-band{padding:52px 18px;}.lib-fan{height:150px;}}\n'
        '    @media (prefers-reduced-motion:reduce){.lib-cta{transition:none;}.lib-cta:hover{transform:none;}}\n'
        '  </style>\n'
        '  <section class="lib-band" id="library" aria-labelledby="lib-title">\n'
        '    <div class="lib-inner">\n'
        '      <div class="lib-copy reveal">\n'
        f'        {pair("p", "lib-eyebrow", "lib_eyebrow")}\n'
        f'        <h2 id="lib-title" data-ar="{e(heads[0], True)}" data-en="{e(heads[1], True)}">{e(heads[0])}</h2>\n'
        f'        {pair("p", "lib-lead", "lib_sub")}\n'
        f'        <a class="lib-cta" href="/articles/" data-href-ar="/articles/" data-href-en="/en/articles/" '
        f'data-ar="{e(ar["lib_cta"], True)}" data-en="{e(en["lib_cta"], True)}">{e(ar["lib_cta"])}</a>\n'
        '      </div>\n'
        '      <div class="lib-fan reveal" aria-hidden="true">\n'
        + fan +
        '      </div>\n'
        '    </div>\n'
        '  </section>\n'
    )


def patch_homepage(total):
    """Rewrite the library band inside index.html, leaving the rest untouched.

    The article count in that band is the same number the hub prints, so it
    has to come from the same place. Regenerating the block on every build is
    the only way the two cannot drift apart.
    """
    with open(HOME, encoding="utf-8") as fh:
        page = fh.read()
    i, j = page.find(HOME_START), page.find(HOME_END)
    if i < 0 or j < 0 or j < i:
        raise SystemExit("index.html has lost its library-band markers")
    new = (page[:i] + HOME_START + "\n" + home_library_band(total)
           + "  " + page[j:])
    if new == page:
        return False
    write(HOME, new)
    return True


# --------------------------------------------------------------------------
def main():
    articles = load_articles()
    counts = {}
    for a in articles:
        counts[a.get("category")] = counts.get(a.get("category"), 0) + 1
    print(f"Indexing {len(articles)} articles across {len([k for k in counts if k])} categories")

    for lang in ("ar", "en"):
        write(os.path.join(out_dir(lang), "index.html"), hub_page(lang, articles, counts))
        build_search_index(lang, articles)
        for c in CATEGORIES:
            items = [a for a in articles if a.get("category") == c["id"]]
            if not items:
                continue
            write(os.path.join(out_dir(lang, "c", c["id"]), "index.html"),
                  category_page(lang, c, items, counts))
        print(f"  {lang}: hub + {len([c for c in CATEGORIES if counts.get(c['id'])])} category pages")

    write(os.path.join(BASE, "articles", "hub.js"), HUB_JS)

    for lang, path in (("ar", "author"), ("en", os.path.join("en", "author"))):
        d = os.path.join(BASE, path)
        os.makedirs(d, exist_ok=True)
        write(os.path.join(d, "index.html"), author_page(lang))
    print("  author pages")

    write(os.path.join(BASE, "404.html"), not_found_page(counts))
    print("  404.html")

    print("  index.html library band " +
          ("rewritten" if patch_homepage(len(articles)) else "already current"))
    # The English homepage is derived from index.html, so it has to be rebuilt
    # after the library band changes, never before.
    import build_home
    build_home.main()

    build_feed(articles)
    n_pages, n_arts = build_sitemaps(articles, counts)
    print(f"  feed + sitemap index ({n_pages} pages, {n_arts} article urls)")
    print("Done.")


if __name__ == "__main__":
    main()
