#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sihtak content engine.

Reads content/articles.json (a list of bilingual article objects) and:
  - writes /articles/<slug>/index.html         (Arabic page)
  - writes /en/articles/<slug>/index.html       (English page)
  - inserts new cards into /articles/index.html and /en/articles/index.html hubs
  - inserts <url> entries into sitemap.xml
  - inserts <item> entries into articles/feed.xml

Idempotent: re-running skips articles whose slug is already wired in.
No network, no deploy. Run:  python build_content.py
"""
import os, json, html, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "content", "articles.json")

AUTHOR = "Adnan Alrefai"
OG_IMAGE = "https://www.sihtak.com/og-image.png"
PLAY = "https://play.google.com/store/apps/details?id=com.sihhati.app"
APPSTORE = "https://apps.apple.com/us/app/sihtak-%D8%B5%D8%AD%D8%AA%D9%83/id6764330989"

# ---- per-language chrome ------------------------------------------------------
L = {
    "ar": {
        "htmltag": '<html lang="ar" dir="rtl" data-theme="light">',
        "site": "صحتك",
        "nav_articles": "/articles/", "nav_articles_label": "المقالات",
        "download": "حمّل الآن",
        "takeaways_h": "باختصار",
        "related_h": "مقالات ذات صلة",
        "faq_h": "أسئلة شائعة",
        "sources_h": "المصادر",
        "byline": "بقلم",
        "read_suffix": "دقائق قراءة",
        "disclaimer": "هذا المحتوى للتثقيف الصحي فقط ولا يغني عن استشارة الطبيب. إذا كانت لديك أعراض تقلقك فراجع طبيبك.",
        "cta_h": "جرّب صحتك مجاناً",
        "cta_p": "مساعد صحي ذكي يفهم تحاليلك وأدويتك ويتابع صحة عائلتك. مجاني بالكامل وبدون إعلانات.",
        "cta_b1": "حمّل من Google Play", "cta_b2": "حمّل من App Store",
        "base": "/articles/", "hub": "https://www.sihtak.com/articles/",
        "crumb_home": "الرئيسية", "crumb_articles": "المقالات",
        "oglocale": "ar_SA", "oglocale_alt": "en_US",
    },
    "en": {
        "htmltag": '<html lang="en" dir="ltr" data-theme="light">',
        "site": "Sihtak",
        "nav_articles": "/en/articles/", "nav_articles_label": "Articles",
        "download": "Download",
        "takeaways_h": "In short",
        "related_h": "Related articles",
        "faq_h": "Frequently asked questions",
        "sources_h": "Sources",
        "byline": "By",
        "read_suffix": "min read",
        "disclaimer": "This content is for health education only and is not a substitute for medical advice. If you have symptoms that worry you, see your doctor.",
        "cta_h": "Try Sihtak for free",
        "cta_p": "A smart health assistant that understands your labs and medications and looks after your family's health. Completely free, no ads.",
        "cta_b1": "Get it on Google Play", "cta_b2": "Download on the App Store",
        "base": "/en/articles/", "hub": "https://www.sihtak.com/en/articles/",
        "crumb_home": "Home", "crumb_articles": "Articles",
        "oglocale": "en_US", "oglocale_alt": "ar_SA",
    },
}

THEME_ICONS = (
    '<button class="theme-btn" onclick="toggleTheme()" aria-label="Toggle light/dark mode">'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon-sun"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon-moon" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    '</button>'
)

SCRIPT_BLOCK = """  <script>
    function applyTheme(theme) {
      var html = document.documentElement;
      if (theme === 'light') { html.setAttribute('data-theme', 'light'); }
      else { html.removeAttribute('data-theme'); }
      var sunIcon = document.querySelector('.theme-icon-sun');
      var moonIcon = document.querySelector('.theme-icon-moon');
      if (sunIcon && moonIcon) {
        sunIcon.style.display = theme === 'light' ? 'none' : 'block';
        moonIcon.style.display = theme === 'light' ? 'block' : 'none';
      }
      var metaTheme = document.getElementById('meta-theme-color');
      if (metaTheme) metaTheme.content = theme === 'light' ? '#ffffff' : '#030303';
      localStorage.setItem('sihtak-theme', theme);
    }
    function toggleTheme() {
      var current = document.documentElement.hasAttribute('data-theme') ? 'light' : 'dark';
      applyTheme(current === 'light' ? 'dark' : 'light');
    }
    applyTheme(localStorage.getItem('sihtak-theme') === 'dark' ? 'dark' : 'light');
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
    document.querySelectorAll('.reveal').forEach(function(el) { observer.observe(el); });
  </script>
</body>
</html>
"""

FOOTER = {
    "ar": """  <footer class="footer" role="contentinfo">
    <div class="footer-inner">
      <div class="footer-top">
        <div class="footer-brand-section">
          <div class="footer-logo-row">
            <img src="/icon.png" alt="" width="40" height="40">
            <span>صحتك</span>
          </div>
          <p class="footer-tag">مساعدك الصحي الذكي، مجاني وبدون إعلانات.</p>
          <a href="{play}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">حمّل الآن</a>
        </div>
        <div class="footer-col">
          <h4>التطبيق</h4>
          <ul class="footer-links">
            <li><a href="/#features">المزايا</a></li>
            <li><a href="/articles/">المقالات</a></li>
            <li><a href="/#faq">أسئلة شائعة</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>قانوني</h4>
          <ul class="footer-links">
            <li><a href="/privacy">سياسة الخصوصية</a></li>
            <li><a href="/terms">شروط الاستخدام</a></li>
            <li><a href="/contact">تواصل معنا</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p class="footer-copy">&copy; 2026 Sihtak. جميع الحقوق محفوظة.</p>
        <p class="footer-creator" style="font-size:13px;color:var(--text-d);margin-top:6px;"><span>صُنع بواسطة</span> <strong style="color:var(--text-m);">Adnan Alrefai</strong></p>
        <p class="footer-owner" style="font-size:13px;color:var(--text-d);margin-top:4px;"><span>منتج من</span> <a href="https://poctify.com" target="_blank" rel="noopener" style="color:var(--text-m);font-weight:600;text-decoration:none;">POCTIFY LTD</a></p>
        <p style="font-size:13px;color:var(--text-d);margin-top:4px;">تابعنا على <a href="https://instagram.com/sihtak_app" style="color:var(--teal);font-weight:600;" target="_blank" rel="noopener">@sihtak_app</a></p>
      </div>
    </div>
  </footer>
""".replace("{play}", PLAY),
    "en": """  <footer class="footer" role="contentinfo">
    <div class="footer-inner">
      <div class="footer-top">
        <div class="footer-brand-section">
          <div class="footer-logo-row">
            <img src="/icon.png" alt="" width="40" height="40">
            <span>Sihtak</span>
          </div>
          <p class="footer-tag">Your smart health companion, free with no ads.</p>
          <a href="{play}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">Download</a>
        </div>
        <div class="footer-col">
          <h4>App</h4>
          <ul class="footer-links">
            <li><a href="/#features">Features</a></li>
            <li><a href="/en/articles/">Articles</a></li>
            <li><a href="/#faq">FAQ</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <ul class="footer-links">
            <li><a href="/privacy">Privacy Policy</a></li>
            <li><a href="/terms">Terms of Service</a></li>
            <li><a href="/contact">Contact Us</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p class="footer-copy">&copy; 2026 Sihtak. All rights reserved.</p>
        <p class="footer-creator" style="font-size:13px;color:var(--text-d);margin-top:6px;"><span>Built by</span> <strong style="color:var(--text-m);">Adnan Alrefai</strong></p>
        <p class="footer-owner" style="font-size:13px;color:var(--text-d);margin-top:4px;"><span>A product of</span> <a href="https://poctify.com" target="_blank" rel="noopener" style="color:var(--text-m);font-weight:600;text-decoration:none;">POCTIFY LTD</a></p>
        <p style="font-size:13px;color:var(--text-d);margin-top:4px;">Follow us on <a href="https://instagram.com/sihtak_app" style="color:var(--teal);font-weight:600;" target="_blank" rel="noopener">@sihtak_app</a></p>
      </div>
    </div>
  </footer>
""".replace("{play}", PLAY),
}

MONTHS_EN = ["", "January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def e(s, quote=False):
    return html.escape(str(s), quote=quote)


def card_meta(lang, a):
    if lang == "ar":
        return f'{a["date_ar"]} · {a["read_min"]} دقائق قراءة'
    return f'{a["date_en"]} · {a["read_min"]} min read'


def card_html(lang, a):
    c = a["content"][lang]
    chip = a["chip_ar"] if lang == "ar" else a["chip_en"]
    href = f'{L[lang]["base"]}{a["slug"]}/'
    return (
        f'        <a class="art-card reveal" href="{href}">\n'
        f'          <div class="art-card-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{a["icon"]}</svg></div>\n'
        f'          <span class="art-chip">{e(chip)}</span>\n'
        f'          <h3>{e(c["title"])}</h3>\n'
        f'          <p>{e(c["desc"])}</p>\n'
        f'          <span class="art-card-meta">{card_meta(lang, a)}</span>\n'
        f'        </a>\n'
    )


def related_cards(lang, a, articles):
    i = next((k for k, x in enumerate(articles) if x["slug"] == a["slug"]), 0)
    rotated = articles[i + 1:] + articles[:i]
    others = rotated[:4]
    return "".join(card_html(lang, x) for x in others)


def body_html(lang, a):
    c = a["content"][lang]
    out = []
    # takeaways
    lis = "".join(f'          <li>{e(t)}</li>\n' for t in c["takeaways"])
    out.append(f'      <aside class="art-takeaways reveal">\n        <h2>{L[lang]["takeaways_h"]}</h2>\n        <ul>\n{lis}        </ul>\n      </aside>\n')
    # sections
    for s in c["sections"]:
        out.append('      <section class="reveal">\n')
        out.append(f'        <h2>{e(s["h2"])}</h2>\n')
        for p in s["paras"]:
            out.append(f'        <p>{e(p)}</p>\n')
        if s.get("list"):
            items = "".join(f'          <li>{e(li)}</li>\n' for li in s["list"])
            out.append(f'        <ul class="art-list">\n{items}        </ul>\n')
        out.append('      </section>\n')
    # app tie-in
    out.append(f'      <section class="art-tie reveal">\n        <p>{e(c["tie"])}</p>\n      </section>\n')
    # CTA
    out.append(
        '      <aside class="art-cta reveal">\n'
        '        <img src="/icon.png" alt="Sihtak app icon" width="56" height="56">\n'
        '        <div class="art-cta-text">\n'
        f'          <h3>{L[lang]["cta_h"]}</h3>\n'
        f'          <p>{L[lang]["cta_p"]}</p>\n'
        '        </div>\n'
        '        <div class="art-cta-btns">\n'
        f'          <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">{L[lang]["cta_b1"]}</a>\n'
        f'          <a href="{APPSTORE}" class="btn btn-ghost btn-sm" target="_blank" rel="noopener">{L[lang]["cta_b2"]}</a>\n'
        '        </div>\n'
        '      </aside>\n'
    )
    # FAQ
    faqs = []
    for f in c["faqs"]:
        faqs.append(
            '        <details class="art-faq-item">\n'
            f'          <summary>{e(f["q"])}</summary>\n'
            f'          <p>{e(f["a"])}</p>\n'
            '        </details>\n'
        )
    out.append(f'      <section class="art-faq reveal">\n        <h2>{L[lang]["faq_h"]}</h2>\n{"".join(faqs)}      </section>\n')
    # Sources (research pieces)
    src = a.get("sources") or []
    if src:
        items = "".join(
            f'          <li><a href="{s["url"]}" target="_blank" rel="noopener">{e(s["label"])}</a></li>\n'
            for s in src
        )
        out.append(f'      <section class="reveal">\n        <h2>{L[lang]["sources_h"]}</h2>\n        <ul class="art-list">\n{items}        </ul>\n      </section>\n')
    # disclaimer
    out.append(f'      <p class="art-disclaimer">{L[lang]["disclaimer"]}</p>\n')
    return "".join(out)


def ldjson(lang, a):
    c = a["content"][lang]
    url = f'https://www.sihtak.com{L[lang]["base"]}{a["slug"]}/'
    art = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": c["h1"], "description": c["desc"], "inLanguage": lang,
        "datePublished": a["date_iso"], "dateModified": a["date_iso"],
        "mainEntityOfPage": url, "image": OG_IMAGE,
        "author": {"@type": "Person", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": "Sihtak", "url": "https://www.sihtak.com",
                      "logo": {"@type": "ImageObject", "url": "https://www.sihtak.com/icon.png"}},
    }
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": f["q"],
                           "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in c["faqs"]]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": L[lang]["crumb_home"], "item": "https://www.sihtak.com/"},
        {"@type": "ListItem", "position": 2, "name": L[lang]["crumb_articles"], "item": L[lang]["hub"]},
        {"@type": "ListItem", "position": 3, "name": c["h1"], "item": url},
    ]}
    j = lambda d: json.dumps(d, ensure_ascii=False, separators=(", ", ": "))
    return (f'  <script type="application/ld+json">{j(art)}</script>\n'
            f'  <script type="application/ld+json">{j(faq)}</script>\n'
            f'  <script type="application/ld+json">{j(crumb)}</script>\n')


def page(lang, a, articles):
    c = a["content"][lang]
    o = L[lang]
    slug = a["slug"]
    url = f'https://www.sihtak.com{o["base"]}{slug}/'
    ar_url = f'https://www.sihtak.com/articles/{slug}/'
    en_url = f'https://www.sihtak.com/en/articles/{slug}/'
    other_href = (f'/en/articles/{slug}/' if lang == "ar" else f'/articles/{slug}/')
    other_label = ("EN" if lang == "ar" else "عربي")
    chip = a["chip_ar"] if lang == "ar" else a["chip_en"]
    if lang == "ar":
        byline = f'{o["byline"]} <bdi><strong>{AUTHOR}</strong></bdi> · {a["date_ar"]} · {a["read_min"]} {o["read_suffix"]}'
    else:
        byline = f'{o["byline"]} <bdi><strong>{AUTHOR}</strong></bdi> · {a["date_en"]} · {a["read_min"]} {o["read_suffix"]}'

    head = []
    head.append("<!DOCTYPE html>\n" + o["htmltag"] + "\n<head>\n")
    head.append('  <script async src="https://www.googletagmanager.com/gtag/js?id=G-JGTTBKMM4G"></script>\n')
    head.append('  <script>\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag(\'js\', new Date());\n    gtag(\'config\', \'G-JGTTBKMM4G\');\n  </script>\n')
    head.append('  <script src="/analytics.js" defer></script>\n')
    head.append('  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
    head.append(f'  <title>{e(c["title"])} | {o["site"]}</title>\n')
    head.append(f'  <meta name="description" content="{e(c["desc"], quote=True)}">\n')
    head.append(f'  <meta name="keywords" content="{e(c["keywords"], quote=True)}">\n')
    head.append(f'  <meta name="author" content="{AUTHOR}">\n')
    head.append('  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">\n')
    head.append(f'  <link rel="canonical" href="{url}">\n')
    head.append(f'  <link rel="alternate" hreflang="ar" href="{ar_url}">\n')
    head.append(f'  <link rel="alternate" hreflang="en" href="{en_url}">\n')
    head.append(f'  <link rel="alternate" hreflang="x-default" href="{ar_url}">\n')
    head.append(f'  <meta property="og:title" content="{e(c["title"], quote=True)} | {o["site"]}">\n')
    head.append(f'  <meta property="og:description" content="{e(c["desc"], quote=True)}">\n')
    head.append('  <meta property="og:type" content="article">\n')
    head.append(f'  <meta property="og:url" content="{url}">\n')
    head.append(f'  <meta property="og:image" content="{OG_IMAGE}">\n')
    head.append('  <meta property="og:site_name" content="Sihtak">\n')
    head.append(f'  <meta property="og:locale" content="{o["oglocale"]}">\n')
    head.append(f'  <meta property="og:locale:alternate" content="{o["oglocale_alt"]}">\n')
    head.append('  <meta name="twitter:card" content="summary_large_image">\n  <meta name="twitter:site" content="@sihtak_app">\n')
    head.append(f'  <meta name="twitter:image" content="{OG_IMAGE}">\n')
    head.append('  <link rel="manifest" href="/manifest.json">\n  <meta name="theme-color" content="#ffffff" id="meta-theme-color">\n')
    head.append('  <link rel="icon" type="image/png" href="/icon.png">\n  <link rel="apple-touch-icon" href="/icon.png">\n')
    head.append('  <link rel="stylesheet" href="/style.css">\n  <link rel="stylesheet" href="/articles/article.css">\n')
    head.append(ldjson(lang, a))
    head.append('  <link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n')
    head.append('  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">\n')
    head.append("  <script>(function(){var t=localStorage.getItem('sihtak-theme');if(t!=='dark'){document.documentElement.setAttribute('data-theme','light');}})();</script>\n")
    head.append("</head>\n<body>\n")

    nav = (
        '  <nav class="nav" role="navigation" aria-label="Main navigation">\n'
        '    <div class="nav-inner">\n'
        '      <a href="/" class="nav-brand" aria-label="Sihtak Home">\n'
        '        <img src="/icon.png" alt="" class="nav-logo" width="36" height="36">\n'
        f'        <span class="nav-name">{o["site"]}</span>\n'
        '      </a>\n'
        '      <div class="nav-actions">\n'
        f'        <a href="{o["nav_articles"]}" class="art-nav-link">{o["nav_articles_label"]}</a>\n'
        f'        <a href="{"/tools/" if lang == "ar" else "/en/tools/"}" class="art-nav-link">{"الأدوات" if lang == "ar" else "Tools"}</a>\n'
        f'        {THEME_ICONS}\n'
        f'        <a class="lang-btn" href="{other_href}" aria-label="Switch language">{other_label}</a>\n'
        f'        <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener"><span>{o["download"]}</span></a>\n'
        '      </div>\n'
        '    </div>\n'
        '  </nav>\n'
    )

    hero = (
        '  <main class="art-page">\n'
        '    <header class="art-hero">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <div class="art-hero-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{a["icon"]}</svg></div>\n'
        f'        <span class="art-chip">{e(chip)}</span>\n'
        f'        <h1>{e(c["h1"])}</h1>\n'
        f'        <p class="art-meta">{byline}</p>\n'
        '      </div>\n'
        '    </header>\n'
        '    <article class="art-body">\n'
    )

    related = (
        '    <section class="art-related">\n'
        f'      <h2 class="reveal">{o["related_h"]}</h2>\n'
        '      <div class="art-grid">\n'
        f'{related_cards(lang, a, articles)}'
        '      </div>\n'
        '    </section>\n'
        '  </main>\n'
    )

    return ("".join(head) + nav + hero + body_html(lang, a) +
            "    </article>\n" + related + FOOTER[lang] + SCRIPT_BLOCK)


def write_pages(articles):
    for a in articles:
        for lang in ("ar", "en"):
            d = os.path.join(BASE, ("articles" if lang == "ar" else os.path.join("en", "articles")), a["slug"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(page(lang, a, articles))
            print(f"  page  {lang}  {a['slug']}")


def insert_hub(lang, articles):
    path = os.path.join(BASE, ("articles" if lang == "ar" else os.path.join("en", "articles")), "index.html")
    with open(path, encoding="utf-8") as fh:
        htmltext = fh.read()
    new = [a for a in articles if f'{L[lang]["base"]}{a["slug"]}/"' not in htmltext]
    if not new:
        print(f"  hub   {lang}  (nothing new)")
        return
    cards = "".join(card_html(lang, a) for a in new)
    marker = '<div class="art-grid">\n'
    idx = htmltext.index(marker) + len(marker)
    htmltext = htmltext[:idx] + cards + htmltext[idx:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(htmltext)
    print(f"  hub   {lang}  +{len(new)} cards")


def insert_sitemap(articles):
    path = os.path.join(BASE, "sitemap.xml")
    with open(path, encoding="utf-8") as fh:
        xml = fh.read()
    blocks = []
    for a in articles:
        for base in ("/articles/", "/en/articles/"):
            loc = f"https://www.sihtak.com{base}{a['slug']}/"
            if loc in xml:
                continue
            blocks.append(
                "  <url>\n"
                f"    <loc>{loc}</loc>\n"
                f'    <xhtml:link rel="alternate" hreflang="ar" href="https://www.sihtak.com/articles/{a["slug"]}/"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="en" href="https://www.sihtak.com/en/articles/{a["slug"]}/"/>\n'
                f'    <xhtml:link rel="alternate" hreflang="x-default" href="https://www.sihtak.com/articles/{a["slug"]}/"/>\n'
                f"    <lastmod>{a['date_iso']}</lastmod>\n"
                "    <changefreq>monthly</changefreq>\n"
                "    <priority>0.8</priority>\n"
                "  </url>\n"
            )
    if not blocks:
        print("  sitemap (nothing new)")
        return
    xml = xml.replace("</urlset>", "".join(blocks) + "</urlset>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print(f"  sitemap +{len(blocks)} urls")


def insert_feed(articles):
    path = os.path.join(BASE, "articles", "feed.xml")
    with open(path, encoding="utf-8") as fh:
        xml = fh.read()
    items = []
    for a in articles:
        link = f"https://www.sihtak.com/articles/{a['slug']}/"
        if link in xml:
            continue
        c = a["content"]["ar"]
        d = datetime.date.fromisoformat(a["date_iso"])
        pub = d.strftime("%a, %d %b %Y") + " 08:00:00 GMT"
        items.append(
            "    <item>\n"
            f"      <title>{e(c['title'])}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid>{link}</guid>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f"      <description>{e(c['desc'])}</description>\n"
            "    </item>\n"
        )
    if not items:
        print("  feed    (nothing new)")
        return
    anchor = "    <language>ar</language>\n"
    idx = xml.index(anchor) + len(anchor)
    xml = xml[:idx] + "".join(items) + xml[idx:]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print(f"  feed    +{len(items)} items")


def main():
    with open(DATA, encoding="utf-8") as fh:
        articles = json.load(fh)
    print(f"Loaded {len(articles)} article(s) from articles.json")
    write_pages(articles)
    insert_hub("ar", articles)
    insert_hub("en", articles)
    insert_sitemap(articles)
    insert_feed(articles)
    print("Done.")


if __name__ == "__main__":
    main()
