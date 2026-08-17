#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sihtak health-tools generator.

Emits interactive calculator pages (BMI, HbA1c to average glucose, lab-unit
converter) plus a /tools/ hub, in Arabic (/tools/) and English (/en/tools/),
reusing the site chrome + article.css + tools.css. No network, no deploy.
Run:  python build_tools.py
"""
import os, json, html

from build_chrome import serp_title, serp_desc, ASSET_V

BASE = os.path.dirname(os.path.abspath(__file__))
AUTHOR = "Adnan Alrefai"
OG_IMAGE = "https://www.sihtak.com/og-image.png"
PLAY = "https://play.google.com/store/apps/details?id=com.sihhati.app"

L = {
    "ar": {"htmltag": '<html lang="ar" dir="rtl" data-theme="light">', "site": "صحتك",
           "articles_href": "/articles/", "articles_label": "المقالات",
           "tools_href": "/tools/", "tools_label": "الأدوات",
           "download": "حمّل الآن", "base": "/tools/", "hub": "https://www.sihtak.com/tools/",
           "crumb_home": "الرئيسية", "crumb_tools": "الأدوات",
           "oglocale": "ar_SA", "oglocale_alt": "en_US",
           "disclaimer": "هذه الأداة للتوعية والتقدير العام فقط، ولا تُشخّص ولا تغني عن استشارة الطبيب. النتائج تقديرية ويفسّرها طبيبك ضمن حالتك.",
           "howto_h": "كيف تعمل هذه الأداة؟", "faq_h": "أسئلة شائعة",
           "more_h": "أدوات أخرى", "cta_h": "احفظ نتائجك في تطبيق صحتك",
           "cta_p": "صوّر تحاليلك ليقرأها الماسح الذكي، وتابع أرقامك مع الوقت، واسأل المساعد الذكي عن معناها. مجاني وبدون إعلانات.",
           "cta_b1": "حمّل من Google Play", "cta_b2": "حمّل من App Store"},
    "en": {"htmltag": '<html lang="en" dir="ltr" data-theme="light">', "site": "Sihtak",
           "articles_href": "/en/articles/", "articles_label": "Articles",
           "tools_href": "/en/tools/", "tools_label": "Tools",
           "download": "Download", "base": "/en/tools/", "hub": "https://www.sihtak.com/en/tools/",
           "crumb_home": "Home", "crumb_tools": "Tools",
           "oglocale": "en_US", "oglocale_alt": "ar_SA",
           "disclaimer": "This tool is for general awareness and estimation only. It does not diagnose or replace a doctor. Results are estimates and your doctor interprets them for your situation.",
           "howto_h": "How does this tool work?", "faq_h": "Frequently asked questions",
           "more_h": "More tools", "cta_h": "Save your results in the Sihtak app",
           "cta_p": "Photograph your lab tests for the smart scanner to read, track your numbers over time, and ask the AI assistant what they mean. Free, no ads.",
           "cta_b1": "Get it on Google Play", "cta_b2": "Download on the App Store"},
}

THEME_ICONS = ('<button class="theme-btn" onclick="toggleTheme()" aria-label="Toggle light/dark mode">'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon-sun"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="theme-icon-moon" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    '</button>')

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
    "ar": """  <footer class="footer" role="contentinfo"><div class="footer-inner"><div class="footer-top">
        <div class="footer-brand-section"><div class="footer-logo-row"><img src="/icon.png" alt="" width="40" height="40"><span>صحتك</span></div>
          <p class="footer-tag">مساعدك الصحي الذكي، مجاني وبدون إعلانات.</p>
          <a href="__PLAY__" class="btn btn-primary btn-sm" target="_blank" rel="noopener">حمّل الآن</a></div>
        <div class="footer-col"><h4>استكشف</h4><ul class="footer-links"><li><a href="/#features">المزايا</a></li><li><a href="/articles/">المقالات</a></li><li><a href="/tools/">الأدوات</a></li></ul></div>
        <div class="footer-col"><h4>قانوني</h4><ul class="footer-links"><li><a href="/privacy/">سياسة الخصوصية</a></li><li><a href="/terms/">شروط الاستخدام</a></li><li><a href="/contact/">تواصل معنا</a></li></ul></div></div>
      <div class="footer-bottom"><p class="footer-copy">&copy; 2026 Sihtak. جميع الحقوق محفوظة.</p>
        <p class="footer-owner" style="font-size:13px;color:var(--text-d);margin-top:6px;"><span>منتج من</span> <a href="https://poctify.com" target="_blank" rel="noopener" style="color:var(--text-m);font-weight:600;text-decoration:none;">POCTIFY LTD</a></p>
        <p style="font-size:13px;color:var(--text-d);margin-top:4px;">تابعنا على <a href="https://instagram.com/sihtak_app" style="color:var(--teal);font-weight:600;" target="_blank" rel="noopener">@sihtak_app</a></p></div>
    </div></footer>
""".replace("__PLAY__", PLAY),
    "en": """  <footer class="footer" role="contentinfo"><div class="footer-inner"><div class="footer-top">
        <div class="footer-brand-section"><div class="footer-logo-row"><img src="/icon.png" alt="" width="40" height="40"><span>Sihtak</span></div>
          <p class="footer-tag">Your smart health companion, free with no ads.</p>
          <a href="__PLAY__" class="btn btn-primary btn-sm" target="_blank" rel="noopener">Download</a></div>
        <div class="footer-col"><h4>Explore</h4><ul class="footer-links"><li><a href="/#features">Features</a></li><li><a href="/en/articles/">Articles</a></li><li><a href="/en/tools/">Tools</a></li></ul></div>
        <div class="footer-col"><h4>Legal</h4><ul class="footer-links"><li><a href="/privacy/">Privacy Policy</a></li><li><a href="/terms/">Terms of Service</a></li><li><a href="/contact/">Contact Us</a></li></ul></div></div>
      <div class="footer-bottom"><p class="footer-copy">&copy; 2026 Sihtak. All rights reserved.</p>
        <p class="footer-owner" style="font-size:13px;color:var(--text-d);margin-top:6px;"><span>A product of</span> <a href="https://poctify.com" target="_blank" rel="noopener" style="color:var(--text-m);font-weight:600;text-decoration:none;">POCTIFY LTD</a></p>
        <p style="font-size:13px;color:var(--text-d);margin-top:4px;">Follow us on <a href="https://instagram.com/sihtak_app" style="color:var(--teal);font-weight:600;" target="_blank" rel="noopener">@sihtak_app</a></p></div>
    </div></footer>
""".replace("__PLAY__", PLAY),
}


def e(s, quote=False):
    return html.escape(str(s), quote=quote)


def head(lang, slug, title, desc, keywords, extra_ld):
    o = L[lang]
    url = f'https://www.sihtak.com{o["base"]}{slug + "/" if slug else ""}'
    ar_url = f'https://www.sihtak.com/tools/{slug + "/" if slug else ""}'
    en_url = f'https://www.sihtak.com/en/tools/{slug + "/" if slug else ""}'
    j = lambda d: json.dumps(d, ensure_ascii=False, separators=(", ", ": "))
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": o["crumb_home"], "item": "https://www.sihtak.com/"},
        {"@type": "ListItem", "position": 2, "name": o["crumb_tools"], "item": o["hub"]}]}
    if slug:
        crumb["itemListElement"].append({"@type": "ListItem", "position": 3, "name": title, "item": url})
    parts = ["<!DOCTYPE html>\n" + o["htmltag"] + "\n<head>\n",
        '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-JGTTBKMM4G"></script>\n',
        "  <script>\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('js', new Date());\n    gtag('config', 'G-JGTTBKMM4G');\n  </script>\n",
        '  <script src="/analytics.js" defer></script>\n',
        '  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n',
        f'  <title>{e(serp_title(title, " | " + o["site"]))} | {o["site"]}</title>\n',
        f'  <meta name="description" content="{e(serp_desc(desc), True)}">\n',
        f'  <meta name="keywords" content="{e(keywords, True)}">\n',
        f'  <meta name="author" content="{AUTHOR}">\n',
        '  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">\n',
        f'  <link rel="canonical" href="{url}">\n',
        f'  <link rel="alternate" hreflang="ar" href="{ar_url}">\n',
        f'  <link rel="alternate" hreflang="en" href="{en_url}">\n',
        f'  <link rel="alternate" hreflang="x-default" href="{ar_url}">\n',
        f'  <meta property="og:title" content="{e(title, True)} | {o["site"]}">\n',
        f'  <meta property="og:description" content="{e(desc, True)}">\n',
        '  <meta property="og:type" content="website">\n',
        f'  <meta property="og:url" content="{url}">\n',
        f'  <meta property="og:image" content="{OG_IMAGE}">\n  <meta property="og:site_name" content="Sihtak">\n',
        f'  <meta property="og:locale" content="{o["oglocale"]}">\n  <meta property="og:locale:alternate" content="{o["oglocale_alt"]}">\n',
        '  <meta name="twitter:card" content="summary_large_image">\n  <meta name="twitter:site" content="@sihtak_app">\n',
        f'  <meta name="twitter:image" content="{OG_IMAGE}">\n',
        '  <link rel="manifest" href="/manifest.json">\n  <meta name="theme-color" content="#ffffff" id="meta-theme-color">\n',
        '  <link rel="icon" type="image/png" href="/icon.png">\n  <link rel="apple-touch-icon" href="/icon.png">\n',
        f'  <link rel="stylesheet" href="/style.css?v={ASSET_V}">\n  <link rel="stylesheet" href="/articles/article.css?v={ASSET_V}">\n  <link rel="stylesheet" href="/tools/tools.css?v={ASSET_V}">\n',
        f'  <script type="application/ld+json">{j(crumb)}</script>\n']
    for ld in extra_ld:
        parts.append(f'  <script type="application/ld+json">{j(ld)}</script>\n')
    parts += ['  <link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n',
        '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">\n',
        "  <script>(function(){var t=localStorage.getItem('sihtak-theme');if(t!=='dark'){document.documentElement.setAttribute('data-theme','light');}})();</script>\n",
        "</head>\n<body>\n"]
    return "".join(parts)


def nav(lang, slug):
    o = L[lang]
    other_href = (f'/en/tools/{slug + "/" if slug else ""}' if lang == "ar" else f'/tools/{slug + "/" if slug else ""}')
    other_label = ("EN" if lang == "ar" else "عربي")
    return ('  <nav class="nav" role="navigation" aria-label="Main navigation">\n    <div class="nav-inner">\n'
        '      <a href="/" class="nav-brand" aria-label="Sihtak Home">\n        <img src="/icon.png" alt="" class="nav-logo" width="36" height="36">\n'
        f'        <span class="nav-name">{o["site"]}</span>\n      </a>\n      <div class="nav-actions">\n'
        f'        <a href="{o["articles_href"]}" class="art-nav-link">{o["articles_label"]}</a>\n'
        f'        <a href="{o["tools_href"]}" class="art-nav-link">{o["tools_label"]}</a>\n'
        f'        {THEME_ICONS}\n        <a class="lang-btn" href="{other_href}" aria-label="Switch language">{other_label}</a>\n'
        f'        <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener"><span>{o["download"]}</span></a>\n'
        '      </div>\n    </div>\n  </nav>\n')


def hero(lang, tool):
    chip = tool["chip_ar"] if lang == "ar" else tool["chip_en"]
    c = tool[lang]
    return ('  <main class="art-page">\n    <header class="art-hero">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <div class="art-hero-icon"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{tool["icon"]}</svg></div>\n'
        f'        <span class="art-chip">{e(chip)}</span>\n        <h1>{e(c["h1"])}</h1>\n      </div>\n    </header>\n')


def tool_card(lang, tool):
    return {"bmi": bmi_body, "a1c-converter": a1c_body, "lab-unit-converter": labunit_body}[tool["slug"]](lang)


def bmi_body(lang):
    if lang == "ar":
        return ('<div class="tool-card">\n  <div class="tool-fields">\n'
            '    <div class="tool-field"><label for="bmi-weight">الوزن (كيلوغرام)</label><input class="tool-input" id="bmi-weight" type="number" inputmode="decimal" min="1" max="500" placeholder="مثال: 70"></div>\n'
            '    <div class="tool-field"><label for="bmi-height">الطول (سنتيمتر)</label><input class="tool-input" id="bmi-height" type="number" inputmode="decimal" min="50" max="260" placeholder="مثال: 170"></div>\n'
            '  </div>\n  <button class="tool-btn" id="bmi-calc" type="button">احسب مؤشر كتلة الجسم</button>\n'
            '  <div class="tool-result" id="bmi-result"><div class="tool-big">--</div><div class="tool-unit">مؤشر كتلة الجسم</div><div><span class="tool-cat tool-teal"></span></div></div>\n'
            '  <div class="tool-scale">\n    <div class="seg"><span class="dot blue"></span> أقل من 18.5: نقص في الوزن</div>\n    <div class="seg"><span class="dot teal"></span> 18.5 إلى 24.9: وزن طبيعي</div>\n    <div class="seg"><span class="dot amber"></span> 25 إلى 29.9: زيادة في الوزن</div>\n    <div class="seg"><span class="dot rose"></span> 30 فأكثر: سمنة</div>\n  </div>\n</div>\n')
    return ('<div class="tool-card">\n  <div class="tool-fields">\n'
        '    <div class="tool-field"><label for="bmi-weight">Weight (kg)</label><input class="tool-input" id="bmi-weight" type="number" inputmode="decimal" min="1" max="500" placeholder="e.g. 70"></div>\n'
        '    <div class="tool-field"><label for="bmi-height">Height (cm)</label><input class="tool-input" id="bmi-height" type="number" inputmode="decimal" min="50" max="260" placeholder="e.g. 170"></div>\n'
        '  </div>\n  <button class="tool-btn" id="bmi-calc" type="button">Calculate BMI</button>\n'
        '  <div class="tool-result" id="bmi-result"><div class="tool-big">--</div><div class="tool-unit">Body Mass Index</div><div><span class="tool-cat tool-teal"></span></div></div>\n'
        '  <div class="tool-scale">\n    <div class="seg"><span class="dot blue"></span> Below 18.5: underweight</div>\n    <div class="seg"><span class="dot teal"></span> 18.5 to 24.9: normal weight</div>\n    <div class="seg"><span class="dot amber"></span> 25 to 29.9: overweight</div>\n    <div class="seg"><span class="dot rose"></span> 30 and above: obesity</div>\n  </div>\n</div>\n')


def a1c_body(lang):
    if lang == "ar":
        return ('<div class="tool-card">\n  <div class="tool-fields">\n'
            '    <div class="tool-field"><label for="a1c-value">نسبة السكر التراكمي HbA1c (%)</label><input class="tool-input" id="a1c-value" type="number" inputmode="decimal" step="0.1" min="3" max="20" placeholder="مثال: 7.0"></div>\n'
            '  </div>\n  <button class="tool-btn" id="a1c-calc" type="button">احسب متوسط السكر التقديري</button>\n'
            '  <div class="tool-result" id="a1c-result"><div class="tool-unit">متوسط السكر التقديري (eAG)</div><div class="tool-big">--</div>\n'
            '    <div class="tool-lines"><div class="row"><span>ملغم/دل</span><strong class="tool-val">--</strong></div><div class="row"><span>ملي مول/لتر</span><strong class="tool-val">--</strong></div></div>\n'
            '    <div class="tool-sub"></div></div>\n</div>\n')
    return ('<div class="tool-card">\n  <div class="tool-fields">\n'
        '    <div class="tool-field"><label for="a1c-value">HbA1c (%)</label><input class="tool-input" id="a1c-value" type="number" inputmode="decimal" step="0.1" min="3" max="20" placeholder="e.g. 7.0"></div>\n'
        '  </div>\n  <button class="tool-btn" id="a1c-calc" type="button">Estimate average glucose</button>\n'
        '  <div class="tool-result" id="a1c-result"><div class="tool-unit">Estimated average glucose (eAG)</div><div class="tool-big">--</div>\n'
        '    <div class="tool-lines"><div class="row"><span>mg/dL</span><strong class="tool-val">--</strong></div><div class="row"><span>mmol/L</span><strong class="tool-val">--</strong></div></div>\n'
        '    <div class="tool-sub"></div></div>\n</div>\n')


def labunit_body(lang):
    if lang == "ar":
        opts = [("glucose", "سكر الدم (الغلوكوز)"), ("cholesterol", "الكوليسترول (كلي/LDL/HDL)"),
                ("triglycerides", "الدهون الثلاثية"), ("creatinine", "الكرياتينين"), ("urea", "اليوريا (BUN)")]
        options = "".join(f'<option value="{v}">{e(t)}</option>' for v, t in opts)
        return ('<div class="tool-card">\n  <div class="tool-fields">\n'
            f'    <div class="tool-field"><label for="lu-analyte">التحليل</label><select class="tool-select" id="lu-analyte">{options}</select></div>\n'
            '    <div class="tool-field"><label for="lu-value">القيمة</label><input class="tool-input" id="lu-value" type="number" inputmode="decimal" step="any" min="0" placeholder="مثال: 100"></div>\n'
            '  </div>\n  <div class="tool-field" style="margin-top:14px"><label>اتجاه التحويل</label>\n'
            '    <div class="tool-radios"><label><input type="radio" name="lu-dir" value="toSI" checked> تقليدي إلى دولي</label><label><input type="radio" name="lu-dir" value="toConv"> دولي إلى تقليدي</label></div>\n  </div>\n'
            '  <button class="tool-btn" id="lu-calc" type="button">حوّل الوحدة</button>\n'
            '  <div class="tool-result" id="lu-result"><div class="tool-big">--</div><div class="tool-unit"></div><div class="tool-sub"></div></div>\n</div>\n')
    opts = [("glucose", "Glucose"), ("cholesterol", "Cholesterol (total/LDL/HDL)"),
            ("triglycerides", "Triglycerides"), ("creatinine", "Creatinine"), ("urea", "Urea (BUN)")]
    options = "".join(f'<option value="{v}">{e(t)}</option>' for v, t in opts)
    return ('<div class="tool-card">\n  <div class="tool-fields">\n'
        f'    <div class="tool-field"><label for="lu-analyte">Analyte</label><select class="tool-select" id="lu-analyte">{options}</select></div>\n'
        '    <div class="tool-field"><label for="lu-value">Value</label><input class="tool-input" id="lu-value" type="number" inputmode="decimal" step="any" min="0" placeholder="e.g. 100"></div>\n'
        '  </div>\n  <div class="tool-field" style="margin-top:14px"><label>Direction</label>\n'
        '    <div class="tool-radios"><label><input type="radio" name="lu-dir" value="toSI" checked> Conventional to SI</label><label><input type="radio" name="lu-dir" value="toConv"> SI to Conventional</label></div>\n  </div>\n'
        '  <button class="tool-btn" id="lu-calc" type="button">Convert unit</button>\n'
        '  <div class="tool-result" id="lu-result"><div class="tool-big">--</div><div class="tool-unit"></div><div class="tool-sub"></div></div>\n</div>\n')


def other_tool_cards(lang, tools, slug):
    o = L[lang]
    out = []
    for tinfo in tools:
        if tinfo["slug"] == slug:
            continue
        c = tinfo[lang]
        out.append(f'        <a class="art-card reveal" href="{o["base"]}{tinfo["slug"]}/">\n'
            f'          <div class="art-card-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{tinfo["icon"]}</svg></div>\n'
            f'          <span class="art-chip">{e(tinfo["chip_ar"] if lang=="ar" else tinfo["chip_en"])}</span>\n'
            f'          <h3>{e(c["title"])}</h3>\n          <p>{e(c["desc"])}</p>\n        </a>\n')
    return "".join(out)


def tool_page(lang, tool, tools):
    o = L[lang]
    c = tool[lang]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in c["faqs"]]}
    parts = [head(lang, tool["slug"], c["title"], c["desc"], c["keywords"], [faq_ld]), nav(lang, tool["slug"]), hero(lang, tool)]
    parts.append('    <div class="tool-wrap">\n')
    parts.append(f'      <p class="tool-intro reveal">{e(c["intro"])}</p>\n')
    parts.append("      " + tool_card(lang, tool).replace("\n", "\n      ").rstrip() + "\n")
    parts.append(f'      <p class="tool-note">{o["disclaimer"]}</p>\n')
    parts.append('    </div>\n')
    parts.append('    <article class="art-body">\n')
    parts.append(f'      <section class="reveal"><h2>{o["howto_h"]}</h2>\n')
    for p in c["howto"]:
        parts.append(f'        <p>{e(p)}</p>\n')
    parts.append('      </section>\n')
    parts.append(f'      <section class="art-faq reveal"><h2>{o["faq_h"]}</h2>\n')
    for f in c["faqs"]:
        parts.append(f'        <details class="art-faq-item"><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>\n')
    parts.append('      </section>\n')
    parts.append('      <aside class="art-cta reveal"><img src="/icon.png" alt="Sihtak app icon" width="56" height="56"><div class="art-cta-text">'
        f'<h3>{o["cta_h"]}</h3><p>{o["cta_p"]}</p></div><div class="art-cta-btns">'
        f'<a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">{o["cta_b1"]}</a>'
        f'<a href="https://apps.apple.com/us/app/sihtak-%D8%B5%D8%AD%D8%AA%D9%83/id6764330989" class="btn btn-ghost btn-sm" target="_blank" rel="noopener">{o["cta_b2"]}</a></div></aside>\n')
    parts.append('    </article>\n')
    parts.append(f'    <section class="art-related"><h2 class="reveal">{o["more_h"]}</h2>\n      <div class="art-grid">\n{other_tool_cards(lang, tools, tool["slug"])}      </div>\n    </section>\n  </main>\n')
    parts.append(FOOTER[lang])
    parts.append(f'  <script src="/tools/js/{tool["js"]}"></script>\n')
    parts.append(SCRIPT_BLOCK)
    return "".join(parts)


def hub_page(lang, tools):
    o = L[lang]
    title = "أدوات صحية مجانية" if lang == "ar" else "Free Health Tools"
    desc = ("أدوات صحية مجانية من صحتك: حاسبة كتلة الجسم، محول السكر التراكمي إلى متوسط السكر، ومحول وحدات التحاليل الطبية."
            if lang == "ar" else
            "Free health tools from Sihtak: BMI calculator, HbA1c to average glucose converter, and a medical lab unit converter.")
    kw = ("حاسبة كتلة الجسم, حساب BMI, محول السكر التراكمي, محول وحدات التحاليل, أدوات صحية, صحتك"
          if lang == "ar" else "BMI calculator, HbA1c converter, lab unit converter, health tools, Sihtak")
    sub = ("حاسبات صحية بسيطة ومجانية تعمل مباشرة في متصفحك، دون تسجيل. للتوعية والتقدير العام، ولا تغني عن الطبيب."
           if lang == "ar" else
           "Simple, free health calculators that run right in your browser, no sign-up. For awareness and general estimation, not a substitute for a doctor.")
    # The grid used to start at h3 straight after the h1, which left a hole in
    # the outline and wasted the one heading on this page that could carry the
    # words people type. "Free health calculators" is what the page is.
    grid_h = "الحاسبات الصحية المجانية" if lang == "ar" else "Free health calculators"
    cards = []
    for t in tools:
        c = t[lang]
        cards.append(f'        <a class="art-card reveal" href="{o["base"]}{t["slug"]}/">\n'
            f'          <div class="art-card-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{t["icon"]}</svg></div>\n'
            f'          <span class="art-chip">{e(t["chip_ar"] if lang=="ar" else t["chip_en"])}</span>\n'
            f'          <h3>{e(c["title"])}</h3>\n          <p>{e(c["desc"])}</p>\n        </a>\n')
    hub_icon = '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>'
    coll = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": o["hub"], "inLanguage": lang,
            "publisher": {"@type": "Organization", "name": "Sihtak", "url": "https://www.sihtak.com"}}
    parts = [head(lang, "", title, desc, kw, [coll]), nav(lang, ""),
        '  <main class="art-page">\n    <header class="art-hero art-hero--hub">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <div class="art-hero-icon" style="margin-inline:auto"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{hub_icon}</svg></div>\n'
        f'        <h1>{e(title)}</h1>\n        <p class="art-hub-sub">{e(sub)}</p>\n      </div>\n    </header>\n'
        f'    <section class="art-related art-related--hub">\n      <h2 class="cat-list-h">{e(grid_h)}</h2>\n      <div class="art-grid">\n{"".join(cards)}      </div>\n    </section>\n  </main>\n',
        FOOTER[lang], SCRIPT_BLOCK]
    return "".join(parts)


def load_tools():
    with open(os.path.join(BASE, "content", "tools.json"), encoding="utf-8") as fh:
        return json.load(fh)


def main():
    tools = load_tools()
    for lang in ("ar", "en"):
        hubdir = os.path.join(BASE, "tools" if lang == "ar" else os.path.join("en", "tools"))
        os.makedirs(hubdir, exist_ok=True)
        with open(os.path.join(hubdir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(hub_page(lang, tools))
        print(f"  hub  {lang}")
        for t in tools:
            d = os.path.join(hubdir, t["slug"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(tool_page(lang, t, tools))
            print(f"  tool {lang} {t['slug']}")
    print("Done.")


if __name__ == "__main__":
    main()
