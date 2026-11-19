"""Home page images: cinematic photographs and real app screenshots.

Not part of the per-build chain. Run it when the photographs or the app
screenshots change:

    python build_home_assets.py                      # defaults below
    python build_home_assets.py --screens <folder>   # a new capture set

Photographs come from the store-preview pipeline (GPT-6 renders, no text in
the art). Screenshots are the real app captured from its web build: drop a new
set into a folder laid out as <folder>/ar/*.png and <folder>/en/*.png with the
names in SCREENS and rerun. The page never references the PNGs; it uses the
AVIF and WebP written here, at fixed sizes so width/height in the HTML stay
true and nothing shifts while loading.
"""
import argparse
import os

from PIL import Image, ImageEnhance

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "images", "home")
HOME = os.path.expanduser("~")
ART = os.path.join(HOME, "OneDrive", "HQ", "09_Ventures", "Sihtak",
                   "Store-Previews-2026-11-19", "_pipeline", "art")
EXTRA_ART = os.path.join(HOME, ".claude", "tmp", "sihtak-cine", "gen")
SCREENS_SRC = os.path.join(HOME, "shots-sihtak", "raw")

# name -> (source file, focal x 0..1, focal y 0..1). Wide crops are 16:9 for
# full-bleed bands, tall crops 4:5 for cards and phones.
PHOTOS = {
    "hero": ("feature.png", 0.5, 0.55),
    "lounge": ("chat.png", 0.5, 0.45),
    "meal": ("family.png", 0.5, 0.5),
    "courtyard": ("free.png", 0.5, 0.5),
    "report": ("labs.png", 0.5, 0.5),
    "pills": ("meds.png", 0.5, 0.55),
    "door": ("privacy.png", 0.5, 0.5),
    "balcony": ("start.png", 0.5, 0.5),
}
SCREENS = ["first", "meds", "lab", "chat", "family", "home", "labs"]


def crop_to(im, ratio, fx, fy):
    w, h = im.size
    if w / h > ratio:
        nw = int(h * ratio)
        x = int(min(max(fx * w - nw / 2, 0), w - nw))
        return im.crop((x, 0, x + nw, h))
    nh = int(w / ratio)
    y = int(min(max(fy * h - nh / 2, 0), h - nh))
    return im.crop((0, y, w, y + nh))


def save_pair(im, path_noext, q_avif=50, q_webp=74):
    im.save(path_noext + ".avif", quality=q_avif, speed=6)
    im.save(path_noext + ".webp", quality=q_webp, method=6)


def photos():
    d = os.path.join(OUT, "photo")
    os.makedirs(d, exist_ok=True)
    for name, (src, fx, fy) in PHOTOS.items():
        p = os.path.join(EXTRA_ART, src)
        if not os.path.exists(p):
            p = os.path.join(ART, src)
        im = Image.open(p).convert("RGB")
        # A touch less saturation and brightness: the page lays text and glows
        # over these, and the renders come out a little sweet.
        im = ImageEnhance.Color(im).enhance(0.9)
        wide = crop_to(im, 16 / 9, fx, fy)
        for w in (1600, 900):
            save_pair(wide.resize((w, int(w * 9 / 16)), Image.LANCZOS),
                      os.path.join(d, f"{name}-{w}"))
        tall = crop_to(im, 4 / 5, fx, fy)
        save_pair(tall.resize((640, 800), Image.LANCZOS), os.path.join(d, f"{name}-tall"))
        print("  photo", name)


def screens(src):
    for lang in ("ar", "en"):
        d = os.path.join(OUT, "screens", lang)
        os.makedirs(d, exist_ok=True)
        for name in SCREENS:
            p = os.path.join(src, lang, name + ".png")
            if not os.path.exists(p):
                print("  missing", p)
                continue
            im = Image.open(p).convert("RGB")
            # 440x956 phone viewport at 3x. 600 wide covers a 300px phone at 2x.
            im = im.resize((600, int(600 * im.height / im.width)), Image.LANCZOS)
            save_pair(im, os.path.join(d, name), q_avif=60, q_webp=80)
        print("  screens", lang)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--screens", default=SCREENS_SRC)
    ap.add_argument("--only", choices=("photos", "screens"))
    a = ap.parse_args()
    if a.only != "screens":
        photos()
    if a.only != "photos":
        screens(a.screens)
