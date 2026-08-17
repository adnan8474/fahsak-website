"""Per-article cover art: one 3D render, four derivatives, two languages.

Reads a master render from covers-src/<slug>.jpg (16:9, roughly 2752x1536,
gitignored because it is large and regenerable) and writes into
images/articles/:

    <slug>.webp            1200x675  the in-page hero
    <slug>-share-ar.jpg    1200x630  og:image for the Arabic page
    <slug>-share-en.jpg    1200x630  og:image for the English page

There is deliberately no card-sized derivative. Article cards are text and an
icon, and putting 174 thumbnails on the hub would cost more than a megabyte
to load a page whose job is to be scanned. Add one when a card design needs
it, not before.

Two decisions worth keeping.

The share variants are JPEG, not WebP, while the on-site images are WebP.
On-site we control the browser and WebP is smaller; an og:image is fetched by
other people's crawlers, and LinkedIn in particular still renders WebP cards
badly. A share image that fails to draw costs more than the bytes it saves.

The titles are drawn by a real browser, never by PIL and never by the image
model. Arabic needs bidi ordering and contextual letter shaping, which
Pillow's basic text layout does not do and which an image generator gets
wrong in a way that looks like a typo to anyone who reads Arabic. The site's
own og-image.png is the cautionary example: its Arabic is scrambled.
"""

import io
import json
import os
import shutil
import sys
import tempfile

from PIL import Image, ImageFilter

from build_chrome import cat_name, headline, load_articles

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "covers-src")
OUT = os.path.join(BASE, "images", "articles")
MANIFEST = os.path.join(BASE, "content", "covers.json")

HERO = (1200, 675)
SHARE = (1200, 630)

# The share card is split: artwork on the trailing side, title on the leading
# side. Trailing means right in English and left in Arabic, so the reader's eye
# lands on the words first in either language.
ART_W = 660
TEXT_W = SHARE[0] - ART_W
FADE = 70          # px over which the artwork dissolves into the text panel
SCALE = 2          # render at 2x, downsample at the end, so the text is crisp

# What each render actually depicts. Written per cover rather than generated
# from the headline: a screen reader announcing the headline twice is noise,
# and Google Images ranks on what the picture shows.
ALTS = {
    "thyroid-tsh-guide": (
        "رسم ثلاثي الأبعاد للغدة الدرقية بجانب أنبوبي سحب دم لتحليل TSH",
        "3D illustration of the thyroid gland beside two blood collection tubes for a TSH test",
    ),
    "high-blood-pressure-guide": (
        "رسم ثلاثي الأبعاد لجهاز قياس ضغط الدم مع قلب ونبضة",
        "3D illustration of a blood pressure monitor cuff with a heart and pulse line",
    ),
    "mental-health-in-syria": (
        "رسم ثلاثي الأبعاد لرأس بشري مجرد تنبت منه أغصان، رمز التعافي النفسي",
        "3D illustration of an abstract human head with growing branches, a symbol of recovery",
    ),
    "vitamin-b12-deficiency-guide": (
        "رسم ثلاثي الأبعاد لكبسولة فيتامين ب12 مع خلايا دم حمراء",
        "3D illustration of a vitamin B12 capsule with red blood cells",
    ),
    "pcos-guide": (
        "رسم ثلاثي الأبعاد لحلقة الدورة الشهرية مع ميزان يمثل توازن الهرمونات",
        "3D illustration of a menstrual cycle ring with a scale representing hormone balance",
    ),
    "measles-vaccination-syria": (
        "رسم ثلاثي الأبعاد لقارورة لقاح ومحقنة ودرع حماية وبطاقة تطعيم",
        "3D illustration of a vaccine vial, syringe, protection shield and immunisation card",
    ),
}


# --------------------------------------------------------------------------
# titles
# --------------------------------------------------------------------------
def split_title(title):
    """Headline and subline, cut at the colon the way our titles are written.

    Almost every title here is "Keyword: the promise". On a share card that
    reads far better as a big keyword with the promise beneath it than as one
    long block set small enough to fit. Titles with no colon stay whole.

    Unlike serp_title this accepts a very short head. "Cholera" alone is a
    fine headline here because the promise is still on the card, one line
    down, where a search result would have thrown it away.
    """
    for sep in (":", "؟", "?", "،"):
        head, found, tail = title.partition(sep)
        if not found:
            continue
        head, tail = head.strip(), tail.strip()
        if len(head) >= 5 and tail:
            return (head + sep if sep in ("؟", "?") else head), tail
    return title, ""


# --------------------------------------------------------------------------
# imaging
# --------------------------------------------------------------------------
def _fade_row(width, fade, from_left):
    """A one-pixel-tall alpha ramp, cheaper than walking every pixel."""
    row = Image.new("L", (width, 1))
    row.putdata([min(255, round(255 * i / fade)) if i < fade else 255
                 for i in range(width)])
    return row if from_left else row.transpose(Image.FLIP_LEFT_RIGHT)


def share_base(master, art_on_right):
    """The 1200x630 backdrop: artwork one side, its own background the other.

    The text panel is not flat cream. It is a 50px strip lifted from the edge
    of the artwork, stretched across the panel and blurred, so the render's
    vignette and floor shadow carry on across the whole card. Butting the art
    against a flat swatch leaves a visible vertical seam, because the render's
    background is a gradient, not one colour.
    """
    w, h = SHARE[0] * SCALE, SHARE[1] * SCALE
    aw = ART_W * SCALE

    mw, mh = master.size
    crop_w = round(mh * ART_W / SHARE[1])
    x0 = (mw - crop_w) // 2
    art = master.crop((x0, 0, x0 + crop_w, mh)).resize((aw, h), Image.LANCZOS)

    edge = (x0, 0, x0 + 50, mh) if art_on_right else (x0 + crop_w - 50, 0, x0 + crop_w, mh)
    panel = (master.crop(edge).resize((w, h), Image.LANCZOS)
             .filter(ImageFilter.GaussianBlur(38 * SCALE)))

    mask = _fade_row(aw, FADE * SCALE, art_on_right).resize((aw, h))
    panel.paste(art, (TEXT_W * SCALE if art_on_right else 0, 0), mask)
    return panel


def hero(slug, master):
    """The in-page image: the whole 16:9 render, uncropped, about 15KB."""
    master.resize(HERO, Image.LANCZOS).save(
        os.path.join(OUT, f"{slug}.webp"), "WEBP", quality=82, method=6)


# --------------------------------------------------------------------------
# the browser half
# --------------------------------------------------------------------------
CARD_HTML = """<!DOCTYPE html>
<html dir="{dir}" lang="{lang}">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;800&family=Tajawal:wght@500;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {w}px; height: {h}px; overflow: hidden;
    background: url("{bg}") no-repeat center / cover;
    font-family: {font};
  }}
  .copy {{
    width: {tw}px; height: {h}px; float: {lead};
    padding: 52px 40px 52px 56px;
    display: flex; flex-direction: column; justify-content: center;
  }}
  .chip {{
    font-size: 15px; font-weight: 700; letter-spacing: 0.06em;
    color: #1F8A78; margin-bottom: 16px;
  }}
  h1 {{
    font-size: 58px; line-height: 1.24; font-weight: 800;
    color: #1E3A5F; letter-spacing: -0.01em;
  }}
  .sub {{
    margin-top: 14px; font-size: 20px; line-height: 1.45; font-weight: 500;
    color: rgba(30, 58, 95, 0.66);
  }}
  .mark {{
    margin-top: 30px; display: flex; align-items: center; gap: 10px;
    font-size: 16px; font-weight: 700; color: #1E3A5F;
  }}
  .mark img {{ width: 30px; height: 30px; border-radius: 8px; }}
</style>
</head>
<body>
  <div class="copy">
    <div class="chip">{chip}</div>
    <h1>{headline}</h1>
    {subline}
    <div class="mark"><img src="{icon}" alt=""><span>sihtak.com</span></div>
  </div>
</body>
</html>
"""


def fit_script():
    """Shrink the headline until the column stops overflowing.

    Arabic headlines run about a third longer than their English twin, and a
    few titles are twice the length of the shortest, so one fixed size either
    clips the long ones or wastes the short ones.

    The column is centred, and a centred flex column overflows upward and
    downward without ever growing its scrollHeight, so the obvious test never
    fires. Measure against flex-start, then put the centring back.

    Fitting the column is not enough on its own. Six lines of 58px headline
    technically fits and still looks like a wall, so a headline is also capped
    at four lines: past that, smaller type reads as more composed, not less
    important.
    """
    return """() => {
      const copy = document.querySelector('.copy');
      const h1 = document.querySelector('h1');
      copy.style.justifyContent = 'flex-start';
      let chosen = 26;
      for (let px = 58; px >= 26; px -= 2) {
        h1.style.fontSize = px + 'px';
        const lines = Math.round(h1.offsetHeight / (px * 1.24));
        if (copy.scrollHeight <= copy.clientHeight && lines <= 4) { chosen = px; break; }
      }
      h1.style.fontSize = chosen + 'px';
      copy.style.justifyContent = 'center';
      return chosen;
    }"""


def render_share(page, slug, lang, chip, headline, subline, bg_path, icon_path):
    html = CARD_HTML.format(
        dir="rtl" if lang == "ar" else "ltr", lang=lang,
        w=SHARE[0], h=SHARE[1], tw=TEXT_W,
        lead="right" if lang == "ar" else "left",
        font="'Tajawal', sans-serif" if lang == "ar" else "'Inter', sans-serif",
        bg="file:///" + bg_path.replace("\\", "/"),
        icon="file:///" + icon_path.replace("\\", "/"),
        chip=chip, headline=headline,
        subline=f'<div class="sub">{subline}</div>' if subline else "",
    )
    tmp = os.path.join(tempfile.gettempdir(), f"cover-{slug}-{lang}.html")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(html)

    page.goto("file:///" + tmp.replace("\\", "/"))
    page.wait_for_load_state("networkidle")
    page.evaluate("() => document.fonts.ready")
    want = "700 40px Tajawal" if lang == "ar" else "800 40px Inter"
    if not page.evaluate(f"() => document.fonts.check('{want}')"):
        raise RuntimeError(f"{want} did not load; the card would render in a fallback face")
    size = page.evaluate(fit_script())

    shot = page.screenshot(clip={"x": 0, "y": 0, "width": SHARE[0], "height": SHARE[1]})
    img = Image.open(io.BytesIO(shot)).convert("RGB").resize(SHARE, Image.LANCZOS)
    img.save(os.path.join(OUT, f"{slug}-share-{lang}.jpg"), "JPEG",
             quality=88, optimize=True, progressive=True)
    return size


# --------------------------------------------------------------------------
def main():
    from playwright.sync_api import sync_playwright

    # PowerShell's console is cp1252 and every one of these slugs prints an
    # Arabic headline somewhere, so decode explicitly or the run dies on print.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.makedirs(OUT, exist_ok=True)
    by_slug = {a["slug"]: a for a in load_articles()}
    masters = sorted(f for f in os.listdir(SRC) if f.endswith(".jpg"))
    if not masters:
        sys.exit(f"no masters in {SRC}")

    work = tempfile.mkdtemp(prefix="covers-")
    icon = os.path.join(BASE, "icon.png")
    manifest = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": SHARE[0], "height": SHARE[1]},
                                    device_scale_factor=SCALE)
            for fname in masters:
                slug = fname[:-4]
                a = by_slug.get(slug)
                if not a:
                    print(f"  ?  {slug}: no article with that slug, skipped")
                    continue
                master = Image.open(os.path.join(SRC, fname)).convert("RGB")
                hero(slug, master)

                sizes = {}
                for lang in ("ar", "en"):
                    bg = os.path.join(work, f"{slug}-{lang}.png")
                    share_base(master, art_on_right=(lang == "en")).save(bg)
                    head, sub = split_title(headline(a, lang))
                    sizes[lang] = render_share(
                        page, slug, lang, cat_name(lang, a.get("category")) or "",
                        head, sub, bg, icon)

                alt_ar, alt_en = ALTS.get(slug, ("", ""))
                manifest[slug] = {"alt_ar": alt_ar, "alt_en": alt_en}
                kb = os.path.getsize(os.path.join(OUT, f"{slug}-share-ar.jpg")) // 1024
                print(f"  ok {slug}  headline ar {sizes['ar']}px / en {sizes['en']}px, share {kb}KB")
            browser.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)

    existing = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            existing = json.load(fh)
    existing.update(manifest)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"{len(manifest)} cover(s) built; manifest now lists {len(existing)}")
    print("Now run: python build_content.py && python build_site.py")


if __name__ == "__main__":
    main()
