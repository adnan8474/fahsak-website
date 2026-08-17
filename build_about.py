#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the Sihtak About page (/about/ and /en/about/), reusing chrome from
build_tools.py. No network, no deploy.  Run:  python build_about.py"""
import os, json
import build_tools as bt
from build_chrome import serp_title, serp_desc

BASE = bt.BASE
PLAY = bt.PLAY
APPSTORE = "https://apps.apple.com/us/app/sihtak-%D8%B5%D8%AD%D8%AA%D9%83/id6764330989"
e = bt.e

CONTENT = {
    "ar": {
        "title": "عن صحتك: من نحن ولماذا بنينا التطبيق",
        "desc": "صحتك منصة صحية عربية مجانية: مساعد ذكي، وماسح تحاليل، ومتتبع أدوية، ومقالات وأدوات صحية موثوقة بلغة يفهمها الجميع.",
        "keywords": "عن صحتك, من نحن, تطبيق صحتك, منصة صحية عربية, مساعد صحي ذكي, POCTIFY",
        "chip": "من نحن",
        "h1": "عن صحتك",
        "intro": "صحتك منصة صحية عربية تجعل المعرفة الطبية الموثوقة في متناول الجميع، عبر تطبيق ذكي ومقالات وأدوات مجانية بلغة بسيطة.",
        "sections": [
            {"h2": "مهمتنا", "paras": [
                "نؤمن أن كل شخص يستحق أن يفهم صحته بلغته. لذلك بنينا صحتك لتكون رفيقاً صحياً ذكياً يبسّط تحاليلك وأدويتك ومعلوماتك الصحية، ويضعها بين يديك في مكان واحد، مجاناً وبدون إعلانات.",
                "المعلومة الصحية الجيدة لا يجب أن تكون معقدة ولا حكراً على أحد. هدفنا أن نحوّل الأرقام والمصطلحات إلى كلمات مطمئنة تفهمها، وأن نساعدك على اتخاذ خطوات أفضل لصحتك ولصحة من تحب."]},
            {"h2": "ماذا نقدم؟", "paras": ["صحتك ليست مجرد تطبيق، بل منظومة تدعم رحلتك الصحية من عدة جوانب:"], "list": [
                "مساعد صحي ذكي يجيب أسئلتك بالعربية ويشرح نتائجك بلغة بسيطة.",
                "ماسح تحاليل يقرأ صورة تقريرك، يحفظ نتائجك، ويتابع تغيّرها مع الوقت.",
                "متتبّع أدوية بتذكيرات وتنبيهات للتعارضات المحتملة.",
                "ملف صحة العائلة لمتابعة صحة من تحب في مكان واحد.",
                "مكتبة مقالات صحية موثوقة بالعربية، وأدوات وحاسبات مجانية تعمل مباشرة في متصفحك."]},
            {"h2": "قيمنا", "paras": ["ما نبنيه تحكمه مبادئ واضحة لا نساوم عليها:"], "list": [
                "مجاني بالكامل وبدون إعلانات.",
                "خصوصيتك أولاً، فصحتك أمانة نحملها بمسؤولية.",
                "لغة بسيطة يفهمها الجميع، بعيداً عن التعقيد والتخويف.",
                "أداة تدعم علاقتك بطبيبك ولا تحل محله أبداً."]},
            {"h2": "من يقف خلف صحتك", "paras": [
                "صحتك من إنتاج شركة POCTIFY LTD، وقد بُني بشغف ليخدم المستخدم العربي أينما كان. نطوّره باستمرار بناءً على ملاحظات مستخدمينا، لأن ثقتكم هي ما يدفعنا.",
                "لديك اقتراح أو ملاحظة؟ يسعدنا أن نسمع منك عبر صفحة التواصل. تذكّر أن محتوى صحتك للتثقيف الصحي فقط، ولا يغني عن استشارة الطبيب."]},
        ],
        "cta_h": "ابدأ مع صحتك مجاناً",
        "cta_p": "مساعد صحي ذكي يفهم تحاليلك وأدويتك ويتابع صحة عائلتك. مجاني بالكامل وبدون إعلانات.",
    },
    "en": {
        "title": "About Sihtak: who we are and why we built the app",
        "desc": "Sihtak is a free Arabic health platform: a smart assistant, a lab scanner, a medication tracker, and trusted health articles and tools in plain language everyone understands.",
        "keywords": "about Sihtak, who we are, Sihtak app, Arabic health platform, smart health assistant, POCTIFY",
        "chip": "Who we are",
        "h1": "About Sihtak",
        "intro": "Sihtak is an Arabic health platform that puts trustworthy medical knowledge within everyone's reach, through a smart app and free articles and tools in plain language.",
        "sections": [
            {"h2": "Our mission", "paras": [
                "We believe everyone deserves to understand their health in their own language. So we built Sihtak to be a smart health companion that simplifies your lab tests, medications, and health information, and puts them in your hands in one place, free and with no ads.",
                "Good health information should not be complicated or reserved for a few. Our goal is to turn numbers and jargon into reassuring words you understand, and to help you take better steps for your health and the health of those you love."]},
            {"h2": "What we offer", "paras": ["Sihtak is not just an app, but a system that supports your health journey from several sides:"], "list": [
                "A smart health assistant that answers your questions in Arabic and explains your results in simple language.",
                "A lab scanner that reads a photo of your report, saves your results, and tracks how they change over time.",
                "A medication tracker with reminders and alerts for possible interactions.",
                "A family health profile to follow the health of those you love in one place.",
                "A library of trusted Arabic health articles, and free tools and calculators that run right in your browser."]},
            {"h2": "Our values", "paras": ["What we build is guided by clear principles we do not compromise on:"], "list": [
                "Completely free and with no ads.",
                "Your privacy first, because your health is a trust we carry responsibly.",
                "Plain language everyone understands, away from complexity and fear.",
                "A tool that supports your relationship with your doctor and never replaces it."]},
            {"h2": "Who is behind Sihtak", "paras": [
                "Sihtak is produced by POCTIFY LTD, and it was built with passion to serve Arabic-speaking users wherever they are. We keep improving it based on our users' feedback, because your trust is what drives us.",
                "Have a suggestion or feedback? We would love to hear from you through the contact page. Remember that Sihtak content is for health education only and does not replace consulting a doctor."]},
        ],
        "cta_h": "Get started with Sihtak for free",
        "cta_p": "A smart health assistant that understands your labs and medications and looks after your family's health. Completely free, no ads.",
    },
}


def head(lang, c):
    site = bt.L[lang]["site"]
    base = "/about/" if lang == "ar" else "/en/about/"
    url = "https://www.sihtak.com" + base
    ar_url, en_url = "https://www.sihtak.com/about/", "https://www.sihtak.com/en/about/"
    o = bt.L[lang]
    j = lambda d: json.dumps(d, ensure_ascii=False, separators=(", ", ": "))
    about_ld = {"@context": "https://schema.org", "@type": "AboutPage", "name": c["title"], "description": c["desc"],
                "url": url, "inLanguage": lang,
                "publisher": {"@type": "Organization", "name": "Sihtak", "url": "https://www.sihtak.com",
                              "logo": {"@type": "ImageObject", "url": "https://www.sihtak.com/icon.png"},
                              "parentOrganization": {"@type": "Organization", "name": "POCTIFY LTD", "url": "https://poctify.com"}}}
    p = ["<!DOCTYPE html>\n" + o["htmltag"] + "\n<head>\n",
        '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-JGTTBKMM4G"></script>\n',
        "  <script>\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag('js', new Date());\n    gtag('config', 'G-JGTTBKMM4G');\n  </script>\n",
        '  <script src="/analytics.js" defer></script>\n',
        '  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n',
        f'  <title>{e(serp_title(c["title"], " | " + site))} | {site}</title>\n',
        f'  <meta name="description" content="{e(serp_desc(c["desc"]), True)}">\n',
        f'  <meta name="keywords" content="{e(c["keywords"], True)}">\n',
        f'  <meta name="author" content="{bt.AUTHOR}">\n',
        '  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">\n',
        f'  <link rel="canonical" href="{url}">\n',
        f'  <link rel="alternate" hreflang="ar" href="{ar_url}">\n  <link rel="alternate" hreflang="en" href="{en_url}">\n  <link rel="alternate" hreflang="x-default" href="{ar_url}">\n',
        f'  <meta property="og:title" content="{e(c["title"], True)} | {site}">\n',
        f'  <meta property="og:description" content="{e(c["desc"], True)}">\n  <meta property="og:type" content="website">\n',
        f'  <meta property="og:url" content="{url}">\n  <meta property="og:image" content="{bt.OG_IMAGE}">\n  <meta property="og:site_name" content="Sihtak">\n',
        f'  <meta property="og:locale" content="{o["oglocale"]}">\n  <meta property="og:locale:alternate" content="{o["oglocale_alt"]}">\n',
        '  <meta name="twitter:card" content="summary_large_image">\n  <meta name="twitter:site" content="@sihtak_app">\n',
        f'  <meta name="twitter:image" content="{bt.OG_IMAGE}">\n',
        '  <link rel="manifest" href="/manifest.json">\n  <meta name="theme-color" content="#ffffff" id="meta-theme-color">\n',
        '  <link rel="icon" type="image/png" href="/icon.png">\n  <link rel="apple-touch-icon" href="/icon.png">\n',
        f'  <link rel="stylesheet" href="/style.css?v={bt.ASSET_V}">\n  <link rel="stylesheet" href="/articles/article.css?v={bt.ASSET_V}">\n',
        f'  <script type="application/ld+json">{j(about_ld)}</script>\n',
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n',
        '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">\n',
        "  <script>(function(){var t=localStorage.getItem('sihtak-theme');if(t!=='dark'){document.documentElement.setAttribute('data-theme','light');}})();</script>\n",
        "</head>\n<body>\n"]
    return "".join(p)


def nav(lang):
    o = bt.L[lang]
    other = "/en/about/" if lang == "ar" else "/about/"
    other_label = "EN" if lang == "ar" else "عربي"
    return ('  <nav class="nav" role="navigation" aria-label="Main navigation">\n    <div class="nav-inner">\n'
        '      <a href="/" class="nav-brand" aria-label="Sihtak Home">\n        <img src="/icon.png" alt="" class="nav-logo" width="36" height="36">\n'
        f'        <span class="nav-name">{o["site"]}</span>\n      </a>\n      <div class="nav-actions">\n'
        f'        <a href="{o["articles_href"]}" class="art-nav-link">{o["articles_label"]}</a>\n'
        f'        <a href="{o["tools_href"]}" class="art-nav-link">{o["tools_label"]}</a>\n'
        f'        {bt.THEME_ICONS}\n        <a class="lang-btn" href="{other}" aria-label="Switch language">{other_label}</a>\n'
        f'        <a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener"><span>{o["download"]}</span></a>\n'
        '      </div>\n    </div>\n  </nav>\n')


def page(lang):
    c = CONTENT[lang]
    parts = [head(lang, c), nav(lang),
        '  <main class="art-page">\n    <header class="art-hero">\n'
        '      <img src="/images/dna-helix.svg" alt="" class="hero-deco" aria-hidden="true" width="200" height="600">\n'
        '      <div class="art-hero-inner reveal">\n'
        f'        <span class="art-chip">{e(c["chip"])}</span>\n        <h1>{e(c["h1"])}</h1>\n'
        f'        <p class="art-hub-sub" style="margin-inline-start:0">{e(c["intro"])}</p>\n      </div>\n    </header>\n'
        '    <article class="art-body">\n']
    for s in c["sections"]:
        parts.append('      <section class="reveal">\n')
        parts.append(f'        <h2>{e(s["h2"])}</h2>\n')
        for para in s["paras"]:
            parts.append(f'        <p>{e(para)}</p>\n')
        if s.get("list"):
            parts.append('        <ul class="art-list">\n' + "".join(f'          <li>{e(li)}</li>\n' for li in s["list"]) + '        </ul>\n')
        parts.append('      </section>\n')
    parts.append('      <aside class="art-cta reveal"><img src="/icon.png" alt="Sihtak app icon" width="56" height="56"><div class="art-cta-text">'
        f'<h3>{e(c["cta_h"])}</h3><p>{e(c["cta_p"])}</p></div><div class="art-cta-btns">'
        f'<a href="{PLAY}" class="btn btn-primary btn-sm" target="_blank" rel="noopener">{"حمّل من Google Play" if lang=="ar" else "Get it on Google Play"}</a>'
        f'<a href="{APPSTORE}" class="btn btn-ghost btn-sm" target="_blank" rel="noopener">{"حمّل من App Store" if lang=="ar" else "Download on the App Store"}</a></div></aside>\n')
    parts.append('    </article>\n  </main>\n')
    parts.append(bt.FOOTER[lang])
    parts.append(bt.SCRIPT_BLOCK)
    return "".join(parts)


def main():
    for lang in ("ar", "en"):
        d = os.path.join(BASE, "about" if lang == "ar" else os.path.join("en", "about"))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page(lang))
        print("  about", lang)
    print("Done.")


if __name__ == "__main__":
    main()
