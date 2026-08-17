#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sihtak site builder: everything that is derived from the article set.

Regenerates, wholesale and idempotently:
  /articles/  and  /en/articles/            topic tiles + latest + search
  /articles/c/<cat>/  and the /en/ mirror   one page per taxonomy category
  /articles/search-index.json  (+ /en/)     client-side search payload
  /sitemap.xml                              sitemap index
  /sitemap-pages.xml, /sitemap-articles.xml
  /articles/feed.xml                        RSS
  /404.html                                 real 404, not a soft one
  /author/  and /en/author/                 E-E-A-T author page

Nothing here is append-only, so the output can never drift out of sync with
content/articles.json the way the old insert-a-card-into-HTML approach did.

Run after build_content.py:  python build_site.py
"""
import os, json, datetime

from build_chrome import (
    BASE, SITE, AUTHOR, AUTHOR_URL, OG_IMAGE, PLAY, APPSTORE, L, CATEGORIES,
    CAT_BY_ID, cat_url, cat_name, fmt_date, e, nav, footer, head, card, jd,
    ORG_LD, PERSON_LD, SCRIPT_BLOCK, load_articles,
)

TODAY = datetime.date.today().isoformat()

STATIC_PAGES = [
    ("/", "weekly", "1.0"),
    ("/articles/", "daily", "0.9"),
    ("/en/articles/", "daily", "0.9"),
    ("/tools/", "monthly", "0.8"),
    ("/en/tools/", "monthly", "0.8"),
    ("/tools/bmi/", "monthly", "0.7"),
    ("/en/tools/bmi/", "monthly", "0.7"),
    ("/tools/a1c-converter/", "monthly", "0.7"),
    ("/en/tools/a1c-converter/", "monthly", "0.7"),
    ("/tools/lab-unit-converter/", "monthly", "0.7"),
    ("/en/tools/lab-unit-converter/", "monthly", "0.7"),
    ("/about", "monthly", "0.6"),
    ("/en/about", "monthly", "0.6"),
    ("/author/", "monthly", "0.5"),
    ("/en/author/", "monthly", "0.5"),
    ("/privacy", "yearly", "0.3"),
    ("/terms", "yearly", "0.3"),
    ("/contact", "yearly", "0.4"),
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


def search_box(lang):
    o = L[lang]
    return (
        '      <div class="art-search">\n'
        '        <svg class="art-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.7" y2="16.7"/></svg>\n'
        f'        <input type="search" id="artSearch" placeholder="{e(o["search_ph"], True)}" '
        f'aria-label="{e(o["search_ph"], True)}" autocomplete="off">\n'
        '      </div>\n'
        '      <div class="art-grid" id="artResults" hidden></div>\n'
        f'      <p class="art-search-none" id="artNone" hidden>{e(o["search_none"])}</p>\n'
    )


# --------------------------------------------------------------------------
# hub
# --------------------------------------------------------------------------
def hub_page(lang, articles, counts):
    o = L[lang]
    url = o["hub"]
    latest = articles[:24]
    if lang == "ar":
        h1 = "مقالات صحية موثوقة بالعربية"
        sub = ("شروحات طبية مبسطة تهم الشرق الأوسط: التحاليل والأمراض المزمنة والوراثية، "
               "صحة المرأة والطفل، الأدوية والتغذية والصحة النفسية. مكتوبة بلغة يفهمها الجميع "
               "ومدعومة بمصادر منشورة.")
        title = "مقالات صحية بالعربية"
        latest_h = "أحدث المقالات"
        all_h = "كل المقالات"
    else:
        h1 = "Health guides for the Middle East"
        sub = ("Plain explanations of the health questions that actually come up here: lab "
               "tests, chronic and inherited conditions, women's and children's health, "
               "medicines, nutrition and mental health. Written clearly and sourced.")
        title = "Health Articles"
        latest_h = "Latest articles"
        all_h = "All articles"

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
             "mainEntity": {
                 "@type": "ItemList",
                 "numberOfItems": len(articles),
                 "itemListElement": [
                     {"@type": "ListItem", "position": i,
                      "url": f'{SITE}{o["base"]}{a["slug"]}/',
                      "name": a["content"][lang]["title"]}
                     for i, a in enumerate(latest, 1)]}},
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
             extra_ld=f'  <script type="application/ld+json">{jd(ld)}</script>\n')
        + nav(lang, "/en/articles/" if lang == "ar" else "/articles/")
        + '  <main class="art-page">\n'
        '    <header class="art-hero art-hero--hub">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <h1>{e(h1)}</h1>\n'
        f'        <p class="art-hub-sub">{e(sub)}</p>\n'
        f'        <p class="art-hub-count">{len(articles)} {e(o["count_suffix"])}</p>\n'
        '      </div>\n'
        '    </header>\n'
        '    <div class="art-hub-body">\n'
        + search_box(lang)
        + '      <div id="artDefault">\n'
        + topic_tiles(lang, counts)
        + f'      <section class="art-related art-related--hub">\n'
        f'        <h2 class="reveal">{e(latest_h)}</h2>\n'
        '        <div class="art-grid">\n'
        + "".join(card(lang, a) for a in latest)
        + '        </div>\n'
        '      </section>\n'
        '      </div>\n'
        '    </div>\n'
        '  </main>\n'
        + footer(lang)
        + '  <script src="/articles/hub.js" defer></script>\n'
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
             extra_ld=f'  <script type="application/ld+json">{jd(ld)}</script>\n')
        + nav(lang, f'/en/articles/c/{cid}/' if lang == "ar" else f'/articles/c/{cid}/')
        + '  <main class="art-page">\n'
        + crumbs
        + '    <header class="art-hero art-hero--hub">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <div class="art-hero-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{c["icon"]}</svg></div>\n'
        f'        <h1>{e(meta["title"])}</h1>\n'
        f'        <p class="art-hub-sub">{e(meta["desc"])}</p>\n'
        f'        <p class="art-hub-count">{len(items)} {e(o["count_suffix"])}</p>\n'
        '      </div>\n'
        '    </header>\n'
        '    <div class="art-hub-body">\n'
        '      <section class="art-related art-related--hub">\n'
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
        title = "أدنان الرفاعي · كاتب صحتك"
        h1 = "أدنان الرفاعي"
        blocks = [
            ("لماذا أكتب هذا المحتوى",
             ["أعمل منذ سنوات في بناء الأنظمة التي تربط أجهزة التحاليل الطبية بالسجلات الصحية، "
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
            ("ما لست عليه",
             ["لستُ طبيباً ولا أدّعي ذلك. هذه المقالات تثقيف صحي يساعدك على فهم حالتك وطرح "
              "أسئلة أفضل على طبيبك، وليست تشخيصاً ولا وصفة علاج. لا تبدأ دواءً ولا توقفه "
              "بناءً على ما تقرأه هنا."]),
        ]
        role = "مؤسس صحتك · مهندس برمجيات صحية"
    else:
        title = "Adnan Alrefai · Sihtak"
        h1 = "Adnan Alrefai"
        blocks = [
            ("Why I write this",
             ["I have spent years building the systems that connect laboratory analysers to "
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
            ("What I am not",
             ["I am not a doctor and I do not claim to be. These articles are health education "
              "to help you understand your own situation and ask your doctor better questions. "
              "They are not a diagnosis and not a prescription. Do not start or stop any "
              "medicine based on what you read here."]),
        ]
        role = "Founder of Sihtak · Health software engineer"

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


def url_block(loc, lastmod, changefreq, priority, ar=None, en=None):
    alts = ""
    if ar and en:
        alts = (f'    <xhtml:link rel="alternate" hreflang="ar" href="{ar}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="{ar}"/>\n')
    return ("  <url>\n"
            f"    <loc>{loc}</loc>\n" + alts +
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>\n")


HEAD_XML = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')


def build_sitemaps(articles, counts):
    blocks = [url_block(SITE + p if p != "/" else SITE + "/", TODAY, cf, pr)
              for p, cf, pr in STATIC_PAGES]
    for c in CATEGORIES:
        if not counts.get(c["id"]):
            continue
        ar = f"{SITE}/articles/c/{c['id']}/"
        en = f"{SITE}/en/articles/c/{c['id']}/"
        blocks.append(url_block(ar, TODAY, "weekly", "0.8", ar, en))
        blocks.append(url_block(en, TODAY, "weekly", "0.7", ar, en))
    write(os.path.join(BASE, "sitemap-pages.xml"), HEAD_XML + "".join(blocks) + "</urlset>\n")

    ablocks = []
    for a in articles:
        ar = f"{SITE}/articles/{a['slug']}/"
        en = f"{SITE}/en/articles/{a['slug']}/"
        lm = a.get("updated_iso") or a["date_iso"]
        ablocks.append(url_block(ar, lm, "monthly", "0.8", ar, en))
        ablocks.append(url_block(en, lm, "monthly", "0.7", ar, en))
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


HUB_JS = """/* Sihtak article search. Filters a prebuilt index client-side: no backend,
   no third-party search, and it works on the Arabic and English hubs alike. */
(function () {
  var box = document.getElementById('artSearch');
  if (!box) return;
  var results = document.getElementById('artResults');
  var none = document.getElementById('artNone');
  var deflt = document.getElementById('artDefault');
  var index = null, ready = false;

  var base = location.pathname.indexOf('/en/') === 0 ? '/en/articles/' : '/articles/';

  function load() {
    if (ready) return Promise.resolve();
    return fetch(base + 'search-index.json')
      .then(function (r) { return r.json(); })
      .then(function (j) { index = j; ready = true; });
  }

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

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }

  function render(list) {
    results.innerHTML = list.map(function (a) {
      return '<a class="art-card visible" href="' + a.u + '">' +
        '<span class="art-chip">' + esc(a.c) + '</span>' +
        '<h3>' + esc(a.t) + '</h3>' +
        '<p>' + esc(a.d) + '</p></a>';
    }).join('');
  }

  function run() {
    var q = norm(box.value.trim());
    if (q.length < 2) {
      results.hidden = true; none.hidden = true; deflt.hidden = false;
      return;
    }
    load().then(function () {
      var terms = q.split(/\\s+/);
      var hits = index.filter(function (a) {
        var hay = norm(a.t + ' ' + a.d + ' ' + a.c + ' ' + a.k);
        return terms.every(function (t) { return hay.indexOf(t) !== -1; });
      }).slice(0, 40);
      deflt.hidden = true;
      render(hits);
      results.hidden = hits.length === 0;
      none.hidden = hits.length !== 0;
    });
  }

  var timer;
  box.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(run, 120);
  });
  box.addEventListener('focus', load);

  var pre = new URLSearchParams(location.search).get('q');
  if (pre) { box.value = pre; run(); }
})();
"""


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

    build_feed(articles)
    n_pages, n_arts = build_sitemaps(articles, counts)
    print(f"  feed + sitemap index ({n_pages} pages, {n_arts} article urls)")
    print("Done.")


if __name__ == "__main__":
    main()
