"""The site-wide og:image, drawn by a browser so the Arabic is real Arabic.

Writes og-image.png, 1200x630, the fallback social card for every page that
has no cover of its own. Run it when the branding, the tagline or the app
screenshots change; it is not part of the per-build chain.

Two things drive the design.

The Arabic is shaped and ordered by Chromium, not composited by hand. The card
this replaced was built without a text shaper, so its brand read "كتحص"
instead of "صحتك" and its tagline was scrambled the same way. To an Arabic
reader that is not a stylistic quibble, it is gibberish, and it fronted three
hundred and fifty seven pages.

The card is dark while the article share cards are cream, on purpose. This one
sells the app and the article cards sell the writing, and a dark card with the
teal glowing off it is the one that stops a thumb in a WhatsApp or LinkedIn
feed. The phones are the real App Store screenshots in a drawn bezel, never a
redrawn interface, and they sit in a real perspective scene rather than flat
rotations, so the card reads as a product shot instead of a slide.
"""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "og-image.png")

W, H = 1200, 630
SCALE = 2       # render at 2x and downsample, so the type stays crisp

# Arabic leads because the site does: / is Arabic and English lives at /en/.
# That is also why the words sit on the right and the phones on the left: in
# an RTL layout the right edge is where reading starts, and giving every line
# one shared right margin is what stops a bilingual card looking assembled.
EYEBROW = "SIHTAK"
BRAND_AR = "صحتك"
H1_AR = "مساعدك الصحي الذكي"
H2_EN = "Your AI health companion"
LEAD_AR = "يقرأ تحاليلك ويشرحها بلغة تفهمها."
FEATURES = ["محادثة صوتية", "قارئ التحاليل", "تداخل الأدوية"]
FOOT = "مجاني · بلا إعلانات · عربي وإنجليزي"

HTML = """<!DOCTYPE html>
<html dir="ltr" lang="en">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&family=Tajawal:wght@500;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {w}px; height: {h}px; overflow: hidden; position: relative;
    font-family: 'Inter', sans-serif; color: #fff;
    background: #06141d;
  }}
  [lang="ar"] {{ font-family: 'Tajawal', sans-serif; }}

  /* Depth first: a teal core behind the phones, a cooler wash top-left, and a
     dark floor. Three stacked radials read as lit space; one flat fill reads
     as a slide. */
  .field {{
    position: absolute; inset: 0;
    background:
      radial-gradient(58% 78% at 68% 46%, rgba(0, 212, 170, .40) 0%, rgba(0, 212, 170, 0) 62%),
      radial-gradient(48% 60% at 6% 2%, rgba(56, 189, 248, .20) 0%, rgba(56, 189, 248, 0) 70%),
      radial-gradient(90% 120% at 50% 118%, rgba(2, 10, 16, .95) 0%, rgba(2, 10, 16, 0) 62%),
      linear-gradient(155deg, #0a2230 0%, #071a26 45%, #05121a 100%);
  }}
  /* A single soft light streak across the upper left, so the flat area behind
     the type is not dead. */
  .sheen {{
    position: absolute; inset: -30% -10% auto -30%; height: 130%;
    background: linear-gradient(103deg, rgba(255,255,255,0) 38%, rgba(255,255,255,.055) 47%, rgba(255,255,255,0) 56%);
  }}

  /* ---- the phones ---- */
  .stage {{
    position: absolute; right: 520px; top: -46px; width: 800px; height: 760px;
    perspective: 1700px;
  }}
  .fan {{
    position: absolute; inset: 0; transform-style: preserve-3d;
    transform: rotateY(19deg) rotateX(7deg) rotateZ(3deg);
  }}
  .device {{
    position: absolute; border-radius: 30px; padding: 7px;
    background: linear-gradient(148deg, #55636f 0%, #18202a 26%, #0b1016 62%, #2b3540 100%);
    box-shadow: 0 60px 90px -38px rgba(0, 0, 0, .92), 0 8px 26px -10px rgba(0, 0, 0, .6);
  }}
  .device img {{ display: block; width: 100%; border-radius: 24px; }}
  /* bezel rim light plus screen glare, in one pseudo-element each */
  .device::before {{
    content: ''; position: absolute; inset: 0; border-radius: 30px;
    border: 1px solid rgba(255, 255, 255, .16); pointer-events: none;
  }}
  .device::after {{
    content: ''; position: absolute; inset: 7px; border-radius: 24px;
    background: linear-gradient(112deg, rgba(255,255,255,.26) 0%, rgba(255,255,255,.05) 24%, rgba(255,255,255,0) 46%);
    pointer-events: none;
  }}
  .d1 {{ width: 214px; right: 8px;   top: 208px; transform: translateZ(-110px); }}
  .d3 {{ width: 214px; right: 386px; top: 152px; transform: translateZ(-60px); }}
  .d2 {{ width: 258px; right: 176px; top: 96px;  transform: translateZ(60px); }}
  /* the teal bloom the front phone throws onto the field */
  .glow {{
    position: absolute; right: 150px; top: 150px; width: 420px; height: 560px;
    background: radial-gradient(50% 50% at 50% 50%, rgba(0, 212, 170, .34) 0%, rgba(0, 212, 170, 0) 70%);
    filter: blur(26px);
  }}

  /* ---- the words ---- */
  .copy {{
    position: absolute; right: 0; top: 0; width: 560px; height: {h}px;
    padding: 56px 62px 52px 34px;
    display: flex; flex-direction: column; justify-content: center;
    align-items: flex-end; text-align: right;
  }}
  /* The back phone tucks under the copy column. A scrim rather than a hard
     edge keeps the type legible over it without boxing the text in a panel. */
  .copy::before {{
    content: ''; position: absolute; inset: 0; z-index: -1;
    background: linear-gradient(to left, rgba(5,18,26,.95) 0%, rgba(5,18,26,.88) 52%, rgba(5,18,26,0) 100%);
  }}
  .copy > * {{ max-width: 100%; }}
  .lockup {{ display: flex; align-items: center; gap: 13px; margin-bottom: 26px; }}
  .lockup img {{ width: 46px; height: 46px; border-radius: 13px;
                 box-shadow: 0 10px 22px -8px rgba(0, 0, 0, .8); }}
  .wordmark {{ font-size: 21px; font-weight: 800; letter-spacing: .17em; }}
  .wordmark em {{ font-style: normal; color: #00D4AA; }}
  .wordmark span {{ font-size: 19px; font-weight: 700; color: rgba(255,255,255,.6);
                    letter-spacing: 0; margin-inline-start: 4px; }}

  /* One line, always. A three-word promise broken across two lines with a
     single word stranded on the second reads as a mistake, so the size is
     fitted to the column instead of fixed. */
  h1 {{ font-size: 50px; font-weight: 800; line-height: 1.3; letter-spacing: -.01em;
        white-space: nowrap; }}
  .en {{ margin-top: 10px; font-size: 25px; font-weight: 600; line-height: 1.3;
         color: #00D4AA; }}
  .lead {{ margin-top: 18px; font-size: 18.5px; font-weight: 500; line-height: 1.75;
           color: rgba(255, 255, 255, .74); }}

  .feat {{ margin-top: 26px; display: flex; flex-wrap: wrap; gap: 8px;
           justify-content: flex-end; }}
  .feat div {{
    padding: 8px 16px; border-radius: 999px; font-size: 15px; font-weight: 500;
    background: rgba(255, 255, 255, .09); border: 1px solid rgba(255, 255, 255, .17);
    backdrop-filter: blur(6px); white-space: nowrap;
  }}

  .foot {{ margin-top: 30px; display: flex; align-items: baseline; gap: 12px; }}
  .url {{ font-size: 21px; font-weight: 800; color: #fff; letter-spacing: -.01em; }}
  .terms {{ font-size: 14.5px; font-weight: 500; color: rgba(255, 255, 255, .6); }}
</style>
</head>
<body>
  <div class="field"></div>
  <div class="sheen"></div>

  <div class="stage">
    <div class="glow"></div>
    <div class="fan">
      <!-- the dashboard goes where it is fully visible: it is the most
           colourful screen and the one that says "app" at a glance, while the
           chat screen is mostly white and survives being the back one -->
      <div class="device d1"><img src="{chat}" alt=""></div>
      <div class="device d3"><img src="{dash}" alt=""></div>
      <div class="device d2"><img src="{voice}" alt=""></div>
    </div>
  </div>

  <div class="copy" dir="rtl">
    <div class="lockup">
      <img src="{icon}" alt="">
      <div class="wordmark"><em>{eyebrow}</em> <span lang="ar" dir="rtl">{brand_ar}</span></div>
    </div>
    <h1 lang="ar" dir="rtl">{h1_ar}</h1>
    <div class="en">{h2_en}</div>
    <div class="lead" lang="ar" dir="rtl">{lead_ar}</div>
    <div class="feat" dir="rtl">{feats}</div>
    <div class="foot">
      <span class="url">sihtak.com</span>
      <span class="terms" lang="ar" dir="rtl">{foot}</span>
    </div>
  </div>
</body>
</html>
"""


def url(path):
    return "file:///" + path.replace("\\", "/")


def main():
    from PIL import Image
    from playwright.sync_api import sync_playwright

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    html = HTML.format(
        w=W, h=H,
        icon=url(os.path.join(BASE, "icon.png")),
        dash=url(os.path.join(BASE, "screenshots", "dashboard.png")),
        chat=url(os.path.join(BASE, "screenshots", "ai-chat.png")),
        voice=url(os.path.join(BASE, "screenshots", "voice-chat.png")),
        eyebrow=EYEBROW, brand_ar=BRAND_AR, h1_ar=H1_AR, h2_en=H2_EN,
        lead_ar=LEAD_AR, foot=FOOT,
        feats="".join(f'<div lang="ar">{f}</div>' for f in FEATURES),
    )

    with tempfile.TemporaryDirectory() as work:
        page_path = os.path.join(work, "og.html")
        with open(page_path, "w", encoding="utf-8") as fh:
            fh.write(html)

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": W, "height": H},
                                    device_scale_factor=SCALE)
            page.goto(url(page_path))
            page.wait_for_load_state("networkidle")
            page.evaluate("() => document.fonts.ready")

            # A fallback face would silently undo the whole point of rendering
            # this in a browser, so fail loudly rather than ship a second
            # broken card.
            for want in ("800 40px Inter", "800 40px Tajawal"):
                if not page.evaluate(f"() => document.fonts.check('{want}')"):
                    raise RuntimeError(f"{want} did not load")

            # Fit the promise to one line. The column is fixed and the string
            # is not, so the size follows the words rather than the other way
            # round.
            page.evaluate("""() => {
              const h1 = document.querySelector('h1');
              const room = document.querySelector('.copy').clientWidth
                         - parseFloat(getComputedStyle(document.querySelector('.copy')).paddingLeft)
                         - parseFloat(getComputedStyle(document.querySelector('.copy')).paddingRight);
              for (let px = 52; px >= 32; px -= 1) {
                h1.style.fontSize = px + 'px';
                if (h1.scrollWidth <= room) break;
              }
            }""")

            # The card this replaces clipped its last feature chip. The copy
            # column is a centred flex column, and those overflow in both
            # directions without ever growing scrollHeight, so measure against
            # flex-start the way build_covers.py does.
            over = page.evaluate("""() => {
              const c = document.querySelector('.copy');
              c.style.justifyContent = 'flex-start';
              const spill = c.scrollHeight - c.clientHeight;
              c.style.justifyContent = 'center';
              return spill;
            }""")
            if over > 0:
                raise RuntimeError(f"copy column overflows by {over}px; the card would clip")

            shot = page.screenshot(clip={"x": 0, "y": 0, "width": W, "height": H})
            browser.close()

    img = Image.open(io.BytesIO(shot)).convert("RGB").resize((W, H), Image.LANCZOS)
    img.save(OUT, "PNG", optimize=True)
    print(f"og-image.png  {W}x{H}  {os.path.getsize(OUT) // 1024}KB")


if __name__ == "__main__":
    main()
