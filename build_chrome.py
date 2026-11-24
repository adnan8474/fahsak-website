#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared chrome for every generated Sihtak page.

build_content.py (articles) and build_site.py (hubs, categories, sitemaps)
both import from here so the nav, footer, head and taxonomy can never drift
apart between the two builders.
"""
import os, json, html, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.sihtak.com"

AUTHOR = "Adnan Alrefai"
AUTHOR_URL = f"{SITE}/author/"
OG_IMAGE = f"{SITE}/og-image.png"
PLAY = "https://play.google.com/store/apps/details?id=com.sihhati.app"
APPSTORE = "https://apps.apple.com/us/app/sihtak-%D8%B5%D8%AD%D8%AA%D9%83/id6764330989"
GA_ID = "G-JGTTBKMM4G"

# Bump this whenever a shared .css or .js changes. staticwebapp.config.json
# caches those for seven days, so without a new query string a returning
# visitor keeps the old file for a week.
ASSET_V = "2026112401"

# --------------------------------------------------------------------------
# taxonomy
# --------------------------------------------------------------------------
with open(os.path.join(BASE, "content", "categories.json"), encoding="utf-8") as _fh:
    CATEGORIES = json.load(_fh)
CAT_BY_ID = {c["id"]: c for c in CATEGORIES}


# --------------------------------------------------------------------------
# per-article cover art
# --------------------------------------------------------------------------
def load_covers():
    """Slugs that have a cover, keyed to their alt text, from build_covers.py.

    Filtered against the files actually on disk rather than trusted from the
    manifest. Covers arrive in batches, and a slug listed but not yet rendered
    would put a 404 into og:image and the image sitemap, which is the one kind
    of broken link a crawler tells other people about.
    """
    path = os.path.join(BASE, "content", "covers.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        listed = json.load(fh)
    art = os.path.join(BASE, "images", "articles")
    return {slug: meta for slug, meta in listed.items()
            if os.path.exists(os.path.join(art, f"{slug}.webp"))}


COVER_HERO = "/images/articles/{}.webp"
COVER_SHARE = "/images/articles/{}-share-{}.jpg"


def headline(a, lang):
    """The h1. The six hand-written legacy pages only carry a title."""
    c = a["content"][lang]
    return c.get("h1") or c.get("title", "")


def cat_url(lang, cid):
    return f'/articles/c/{cid}/' if lang == "ar" else f'/en/articles/c/{cid}/'


def cat_name(lang, cid):
    c = CAT_BY_ID.get(cid)
    return c[lang]["name"] if c else ""


# --------------------------------------------------------------------------
# dates
# --------------------------------------------------------------------------
MONTHS_AR = ["", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
MONTHS_EN = ["", "January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def fmt_date(iso, lang):
    d = datetime.date.fromisoformat(iso)
    if lang == "ar":
        return f"{d.day} {MONTHS_AR[d.month]} {d.year}"
    return f"{d.day} {MONTHS_EN[d.month]} {d.year}"


def e(s, quote=False):
    return html.escape(str(s), quote=quote)


# --------------------------------------------------------------------------
# per-language strings
# --------------------------------------------------------------------------
L = {
    "ar": {
        "htmltag": '<html lang="ar" dir="rtl" data-theme="light">',
        "site": "صحتك",
        "nav_articles": "/articles/", "nav_articles_label": "المقالات",
        "nav_tools": "/tools/", "nav_tools_label": "الأدوات",
        "download": "حمّل الآن",
        "takeaways_h": "باختصار",
        "related_h": "مقالات ذات صلة",
        "more_in_h": "المزيد في",
        "faq_h": "أسئلة شائعة",
        "sources_h": "المصادر",
        "toc_h": "محتويات المقال",
        "byline": "بقلم",
        "updated": "آخر تحديث",
        "read_suffix": "دقائق قراءة",
        "disclaimer": "هذا المحتوى للتثقيف الصحي فقط ولا يغني عن استشارة الطبيب. إذا كانت لديك أعراض تقلقك فراجع طبيبك.",
        "cta_h": "جرّب صحتك مجاناً",
        "cta_p": "مساعد صحي ذكي يفهم تحاليلك وأدويتك ويتابع صحة عائلتك. مجاني بالكامل وبدون إعلانات.",
        "cta_b1": "حمّل من Google Play", "cta_b2": "حمّل من App Store",
        "base": "/articles/", "hub": f"{SITE}/articles/",
        "crumb_home": "الرئيسية", "crumb_articles": "المقالات",
        "oglocale": "ar_SA", "oglocale_alt": "en_US",
        "author_role": "مؤسس صحتك · ماجستير في الكيمياء الحيوية السريرية · عضو IBMS",
        "author_bio": ("عدنان الرفاعي مؤسس تطبيق صحتك، حاصل على ماجستير في الكيمياء الحيوية "
                       "السريرية، وعضو في معهد العلوم الطبية الحيوية البريطاني IBMS، "
                       "وعضو لجنة الصحة في المجلس العلمي السوري. يعمل منذ سنوات على أنظمة تربط أجهزة التحاليل الطبية بالسجلات "
                       "الصحية في المملكة المتحدة والشرق الأوسط. تُكتب هذه المقالات اعتماداً على "
                       "مصادر منشورة من منظمة الصحة العالمية والهيئات الصحية الوطنية، وهي للتثقيف "
                       "الصحي ولا تغني عن استشارة طبيبك."),
        "author_link": "المزيد عن الكاتب",
        "browse_h": "تصفح حسب الموضوع",
        # Printed as the h2 above a category's article grid. It stops the page
        # jumping h1 -> h3, but the reason it is worth a real sentence rather
        # than a hidden spacer is that the topic name lands in a heading a
        # second time, in the wording someone would actually search.
        "cat_list_h": "مقالات عن {}",
        "all_articles": "كل المقالات",
        "search_ph": "ابحث عن مرض أو تحليل أو دواء…",
        "search_none": "لا توجد نتائج مطابقة. جرّب كلمة أخرى.",
        "count_suffix": "مقالاً",
        "chip_all": "الكل",
        "filters_label": "تصفية حسب الموضوع",
        "sort_label": "ترتيب المقالات",
        "sort_new": "الأحدث",
        "sort_az": "أبجدياً",
        "clear_filter": "إزالة التصفية",
        # {n} = المعروض، {t} = الإجمالي. النص كامل في الصفحة قبل تشغيل جافاسكربت.
        "tpl_all": "{t} مقالاً",
        "tpl_some": "{n} من {t} مقالاً",
        # الشريط المولَّد في الصفحة الرئيسية. {t} = عدد المقالات الكلي.
        # الصفحة الرئيسية مهمتها التطبيق، فهذا الشريط يذكر المكتبة ويفتح بابها
        # فقط، ولا يعدّد المقالات ولا المواضيع.
        "lib_eyebrow": "مكتبة صحتك المجانية",
        "lib_h": "{t} مقالاً صحياً، مكتوبة لتُفهم من أول قراءة",
        "lib_sub": ("بلغة بسيطة ومصادر منشورة، مفتوحة للجميع بلا تسجيل "
                    "وبلا مقابل."),
        "lib_cta": "ادخل المكتبة",
    },
    "en": {
        "htmltag": '<html lang="en" dir="ltr" data-theme="light">',
        "site": "Sihtak",
        "nav_articles": "/en/articles/", "nav_articles_label": "Articles",
        "nav_tools": "/en/tools/", "nav_tools_label": "Tools",
        "download": "Download",
        "takeaways_h": "In short",
        "related_h": "Related articles",
        "more_in_h": "More in",
        "faq_h": "Frequently asked questions",
        "sources_h": "Sources",
        "toc_h": "What this article covers",
        "byline": "By",
        "updated": "Last updated",
        "read_suffix": "min read",
        "disclaimer": "This content is for health education only and is not a substitute for medical advice. If you have symptoms that worry you, see your doctor.",
        "cta_h": "Try Sihtak for free",
        "cta_p": "A smart health assistant that understands your labs and medications and looks after your family's health. Completely free, no ads.",
        "cta_b1": "Get it on Google Play", "cta_b2": "Download on the App Store",
        "base": "/en/articles/", "hub": f"{SITE}/en/articles/",
        "crumb_home": "Home", "crumb_articles": "Articles",
        "oglocale": "en_US", "oglocale_alt": "ar_SA",
        "author_role": "Founder of Sihtak · MSc Clinical Biochemistry · MIBMS",
        "author_bio": ("Adnan Alrefai is the founder of Sihtak and holds an MSc in Clinical "
                       "Biochemistry. He is a member of the UK Institute of Biomedical Science (MIBMS) "
                       "and of the Health Committee of the Syrian Scientific Council. He has spent years building systems that connect laboratory "
                       "analysers to health records across the UK and the Middle East. These "
                       "articles are written from published sources including the World "
                       "Health Organization and national health bodies, and are health education "
                       "rather than a substitute for your own doctor."),
        "author_link": "More about the author",
        "browse_h": "Browse by topic",
        "cat_list_h": "{} articles",
        "all_articles": "All articles",
        "search_ph": "Search a condition, test or medicine…",
        "search_none": "Nothing matched. Try another word.",
        "count_suffix": "articles",
        "chip_all": "All",
        "filters_label": "Filter by topic",
        "sort_label": "Sort articles",
        "sort_new": "Newest",
        "sort_az": "A-Z",
        "clear_filter": "Clear filters",
        # {n} = shown, {t} = total. Rendered in full server-side so the count
        # is correct before hub.js runs.
        "tpl_all": "{t} articles",
        "tpl_some": "{n} of {t} articles",
        # The generated band on the home page. {t} = the whole article set.
        # The home page sells the app, so this band mentions the library and
        # opens the door to it. It does not list articles or topics.
        "lib_eyebrow": "The free Sihtak library",
        "lib_h": "{t} health guides, written to be understood first time",
        "lib_sub": ("Plain language, published sources, open to everyone. "
                    "No sign-up and no charge."),
        "lib_cta": "Open the library",
    },
}

THEME_ICONS = (
    '<button class="theme-btn" onclick="toggleTheme()" aria-label="Toggle light/dark mode">'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon-sun"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon-moon" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    '</button>'
)

SCRIPT_BLOCK = """  <script>
    // Charts and callouts fade in via .reveal, which starts at opacity 0. If JS
    // ever fails to run, that would hide every visual on the page, so the fade
    // is opted into here rather than assumed. See the html:not(.js) rule.
    document.documentElement.classList.add('js');
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


def footer(lang):
    """Footer carries a topic column: it is the site-wide internal link mesh
    that pushes authority from the homepage down into every category."""
    o = L[lang]
    # Every internal link here ends in a slash. The slashless forms are 301s
    # now, and a site-wide footer linking through a redirect on 396 pages is
    # 396 wasted crawls plus a duplicate URL Google has to reconcile.
    about_href = "/about/" if lang == "ar" else "/en/about/"
    top = [c for c in CATEGORIES[:6]]
    topic_links = "".join(
        f'            <li><a href="{cat_url(lang, c["id"])}">{e(c[lang]["short"])}</a></li>\n'
        for c in top
    )
    if lang == "ar":
        brand, tag = "صحتك", "مساعدك الصحي الذكي، مجاني وبدون إعلانات."
        h_app, h_topics, h_legal = "التطبيق", "المواضيع", "قانوني"
        l_features, l_articles, l_tools, l_faq = "المزايا", "المقالات", "الأدوات", "أسئلة شائعة"
        l_priv, l_terms, l_contact, l_about = "سياسة الخصوصية", "شروط الاستخدام", "تواصل معنا", "من نحن"
        copy = "&copy; 2026 Sihtak. جميع الحقوق محفوظة."
        made, product, follow = "صُنع بواسطة", "منتج من", "تابعنا على"
        all_lbl = "كل المواضيع"
    else:
        brand, tag = "Sihtak", "Your smart health companion, free with no ads."
        h_app, h_topics, h_legal = "App", "Topics", "Legal"
        l_features, l_articles, l_tools, l_faq = "Features", "Articles", "Tools", "FAQ"
        l_priv, l_terms, l_contact, l_about = "Privacy Policy", "Terms of Service", "Contact Us", "About"
        copy = "&copy; 2026 Sihtak. All rights reserved."
        made, product, follow = "Built by", "A product of", "Follow us on"
        all_lbl = "All topics"
    return f"""  <footer class="footer" role="contentinfo">
    <div class="footer-inner">
      <div class="footer-top">
        <div class="footer-brand-section">
          <div class="footer-logo-row">
            <img src="/images/app-icon-112.webp" alt="" width="40" height="40">
            <span>{brand}</span>
          </div>
          <p class="footer-tag">{tag}</p>
          <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">{o["download"]}</a>
        </div>
        <div class="footer-col">
          <h2 class="footer-col-h">{h_app}</h2>
          <ul class="footer-links">
            <li><a href="/#features">{l_features}</a></li>
            <li><a href="{o["nav_articles"]}">{l_articles}</a></li>
            <li><a href="{o["nav_tools"]}">{l_tools}</a></li>
            <li><a href="/#faq">{l_faq}</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h2 class="footer-col-h">{h_topics}</h2>
          <ul class="footer-links">
{topic_links}            <li><a href="{o["nav_articles"]}">{all_lbl}</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h2 class="footer-col-h">{h_legal}</h2>
          <ul class="footer-links">
            <li><a href="{about_href}">{l_about}</a></li>
            <li><a href="/privacy/">{l_priv}</a></li>
            <li><a href="/terms/">{l_terms}</a></li>
            <li><a href="/contact/">{l_contact}</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p class="footer-copy">{copy}</p>
        <p class="footer-creator" style="font-size:13px;color:var(--text-d);margin-top:6px;"><span>{made}</span> <strong style="color:var(--text-m);">{AUTHOR}</strong></p>
        <p class="footer-owner" style="font-size:13px;color:var(--text-d);margin-top:4px;"><span>{product}</span> <a href="https://poctify.com" target="_blank" rel="noopener" style="color:var(--text-m);font-weight:600;text-decoration:none;">POCTIFY LTD</a></p>
        <p style="font-size:13px;color:var(--text-d);margin-top:4px;">{follow} <a href="https://instagram.com/sihtak_app" style="color:var(--teal);font-weight:600;" target="_blank" rel="noopener">@sihtak_app</a></p>
      </div>
    </div>
  </footer>
"""


def nav(lang, other_href):
    o = L[lang]
    other_label = "EN" if lang == "ar" else "عربي"
    return (
        '  <nav class="nav" role="navigation" aria-label="Main navigation">\n'
        '    <div class="nav-inner">\n'
        '      <a href="/" class="nav-brand" aria-label="Sihtak Home">\n'
        '        <img src="/images/app-icon-112.webp" alt="" class="nav-logo" width="36" height="36">\n'
        f'        <span class="nav-name">{o["site"]}</span>\n'
        '      </a>\n'
        '      <div class="nav-actions">\n'
        f'        <a href="{o["nav_articles"]}" class="art-nav-link">{o["nav_articles_label"]}</a>\n'
        f'        <a href="{o["nav_tools"]}" class="art-nav-link">{o["nav_tools_label"]}</a>\n'
        f'        {THEME_ICONS}\n'
        f'        <a class="lang-btn" href="{other_href}" aria-label="Switch language">{other_label}</a>\n'
        f'        <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener"><span>{o["download"]}</span></a>\n'
        '      </div>\n'
        '    </div>\n'
        '  </nav>\n'
    )


SERP_TITLE_MAX = 65
SERP_DESC_MAX = 165


def serp_title(title, suffix):
    """The <title> Google actually has room to show, brand suffix included.

    A result title is cut at roughly 600 pixels. Running past that is not a
    penalty, it just means the half we wrote to earn the click is the half that
    disappears. Almost every title here is "Keyword: a longer promise", so the
    first cut is at the colon: that keeps the keyword and drops the promise.
    Only if the keyword half is still too long do we fall back to a word
    boundary. The whole title stays on the page as the h1 and in og:title,
    where a social card gives it far more room.
    """
    budget = SERP_TITLE_MAX - len(suffix)
    if len(title) <= budget:
        return title
    for sep in (":", "؟", " - "):
        head_part = title.split(sep)[0].strip()
        if 18 <= len(head_part) <= budget:
            return head_part
    window = title[:budget]
    space = window.rfind(" ")
    return window[:space].rstrip(" ,،-:؛") if space > 18 else window


def serp_desc(desc):
    """Trim a meta description to something Google will show whole.

    A snippet that stops mid-clause reads like a bug, and over the limit Google
    cuts it there regardless, so we choose the cut ourselves and prefer to land
    on a full stop. og:description keeps the untrimmed text: a social card has
    room for it.
    """
    if len(desc) <= SERP_DESC_MAX:
        return desc
    window = desc[:SERP_DESC_MAX]
    stop = max(window.rfind(". "), window.rfind("؟ "), window.rfind("! "))
    if stop >= 90:
        return window[: stop + 1].strip()
    space = window.rfind(" ")
    return window[:space].rstrip(" ,،-:؛") if space >= 90 else window


def head(lang, *, title, desc, url, ar_url, en_url, keywords="", og_type="article",
         og_image=None, og_image_alt="", extra_ld="",
         css=(f"/style.css?v={ASSET_V}", f"/articles/article.css?v={ASSET_V}"),
         robots="index, follow, max-image-preview:large, max-snippet:-1"):
    o = L[lang]
    img = og_image or OG_IMAGE
    img_alt = (f'  <meta property="og:image:alt" content="{e(og_image_alt, True)}">\n'
               f'  <meta name="twitter:image:alt" content="{e(og_image_alt, True)}">\n'
               if og_image_alt else "")
    brand = " | " + o["site"]
    css_links = "".join(f'  <link rel="stylesheet" href="{c}">\n' for c in css)
    kw = f'  <meta name="keywords" content="{e(keywords, True)}">\n' if keywords else ""
    return (
        "<!DOCTYPE html>\n" + o["htmltag"] + "\n<head>\n"
        f'  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>\n'
        "  <script>\n    window.dataLayer = window.dataLayer || [];\n"
        "    function gtag(){dataLayer.push(arguments);}\n    gtag('js', new Date());\n"
        f"    gtag('config', '{GA_ID}');\n  </script>\n"
        '  <script src="/analytics.js" defer></script>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <title>{e(serp_title(title, brand))}{brand}</title>\n'
        f'  <meta name="description" content="{e(serp_desc(desc), True)}">\n'
        + kw +
        f'  <meta name="author" content="{AUTHOR}">\n'
        f'  <meta name="robots" content="{robots}">\n'
        f'  <link rel="canonical" href="{url}">\n'
        f'  <link rel="alternate" hreflang="ar" href="{ar_url}">\n'
        f'  <link rel="alternate" hreflang="en" href="{en_url}">\n'
        f'  <link rel="alternate" hreflang="x-default" href="{ar_url}">\n'
        # The untrimmed title, and no brand suffix: og:site_name already prints
        # "Sihtak" beside the card, and a social card has room the SERP has not.
        f'  <meta property="og:title" content="{e(title, True)}">\n'
        f'  <meta property="og:description" content="{e(desc, True)}">\n'
        f'  <meta property="og:type" content="{og_type}">\n'
        f'  <meta property="og:url" content="{url}">\n'
        f'  <meta property="og:image" content="{img}">\n'
        '  <meta property="og:image:width" content="1200">\n'
        '  <meta property="og:image:height" content="630">\n'
        + img_alt +
        '  <meta property="og:site_name" content="Sihtak">\n'
        f'  <meta property="og:locale" content="{o["oglocale"]}">\n'
        f'  <meta property="og:locale:alternate" content="{o["oglocale_alt"]}">\n'
        '  <meta name="twitter:card" content="summary_large_image">\n'
        '  <meta name="twitter:site" content="@sihtak_app">\n'
        f'  <meta name="twitter:image" content="{img}">\n'
        '  <link rel="manifest" href="/manifest.json">\n'
        '  <meta name="theme-color" content="#ffffff" id="meta-theme-color">\n'
        '  <link rel="icon" type="image/png" href="/icon.png">\n'
        '  <link rel="apple-touch-icon" href="/icon.png">\n'
        '  <link rel="alternate" type="application/rss+xml" title="Sihtak" href="/articles/feed.xml">\n'
        + css_links
        + extra_ld
        + '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">\n'
        "  <script>(function(){var t=localStorage.getItem('sihtak-theme');if(t!=='dark'){document.documentElement.setAttribute('data-theme','light');}})();</script>\n"
        "</head>\n<body>\n"
    )


def jd(d):
    return json.dumps(d, ensure_ascii=False, separators=(", ", ": "))


ORG_LD = {
    "@type": "Organization", "@id": f"{SITE}/#org", "name": "Sihtak",
    "alternateName": "صحتك", "url": SITE,
    "logo": {"@type": "ImageObject", "url": f"{SITE}/icon.png"},
    "sameAs": ["https://instagram.com/sihtak_app"],
    "parentOrganization": {"@type": "Organization", "name": "POCTIFY LTD",
                           "url": "https://poctify.com"},
}

PERSON_LD = {
    "@type": "Person", "@id": f"{SITE}/#adnan", "name": AUTHOR, "url": AUTHOR_URL,
    "jobTitle": "Founder, Sihtak",
    "hasCredential": {"@type": "EducationalOccupationalCredential",
                      "credentialCategory": "degree", "name": "MSc Clinical Biochemistry"},
    "knowsAbout": ["clinical biochemistry", "point-of-care testing", "laboratory information systems",
                   "health informatics", "HL7", "medical laboratory diagnostics"],
    "memberOf": [{"@type": "Organization", "name": "Institute of Biomedical Science", "url": "https://www.ibms.org"},
                 {"@type": "Organization", "name": "Syrian Scientific Council", "alternateName": "المجلس العلمي السوري"}],
    "worksFor": {"@id": f"{SITE}/#org"},
    "sameAs": ["https://www.adnanalrefai.net/", "https://www.wikidata.org/wiki/Q140467467",
               "https://orcid.org/0009-0004-1559-075X", "https://www.linkedin.com/in/adnan-alrefai-69a53842"],
}


def card(lang, a, reveal=True, searchable=False):
    """One article card, used by hubs, category pages and related sections.

    The library grid on the hub sets reveal=False, because fading in 174 cards
    one by one looks like a fault rather than a flourish, and a card that is
    filtered out and back in would have to be re-animated. It sets
    searchable=True to carry the keywords the client-side filter needs; only
    the hub pays those bytes, since nothing else filters in place.
    """
    c = a["content"][lang]
    cid = a.get("category")
    chip = cat_name(lang, cid) or a.get(f"chip_{lang}", "")
    href = f'{L[lang]["base"]}{a["slug"]}/'
    meta = (f'{fmt_date(a["date_iso"], lang)} · {a["read_min"]} '
            f'{"دقائق قراءة" if lang == "ar" else "min read"}')
    icon = a.get("icon") or (CAT_BY_ID.get(cid, {}).get("icon", ""))
    cls = "art-card reveal" if reveal else "art-card"
    kw = f' data-k="{e(c.get("keywords", ""), True)}"' if searchable else ""
    return (
        f'        <a class="{cls}" href="{href}" data-cat="{e(cid or "", True)}"{kw}>\n'
        f'          <div class="art-card-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{icon}</svg></div>\n'
        f'          <span class="art-chip">{e(chip)}</span>\n'
        f'          <h3>{e(c["title"])}</h3>\n'
        f'          <p>{e(c["desc"])}</p>\n'
        f'          <span class="art-card-meta">{meta}</span>\n'
        f'        </a>\n'
    )


def load_articles():
    """All articles, newest first, from the authored file plus the metadata-only
    records for the six pages that predate the content engine."""
    out = []
    for name in ("articles.json", "legacy.json"):
        p = os.path.join(BASE, "content", name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                for a in json.load(fh):
                    a.setdefault("_legacy", name == "legacy.json")
                    out.append(a)
    seen, uniq = set(), []
    for a in out:
        if a["slug"] in seen:
            continue
        seen.add(a["slug"])
        uniq.append(a)
    uniq.sort(key=lambda x: (x["date_iso"], x["slug"]), reverse=True)
    return uniq
