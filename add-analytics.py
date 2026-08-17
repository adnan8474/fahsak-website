# One-shot: add the Ops Central analytics tag to every page, just after the GA4 block.
# Idempotent. Run from the repo root: python add-analytics.py
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
TAG = '  <script src="/analytics.js" defer></script>\n'
SKIP_DIRS = {".git", "deck", "fahsak-com", "fahsak-co-uk", "screenshots", "images"}
GA_CONFIG = re.compile(r"gtag\('config', 'G-JGTTBKMM4G'\);")

pages = sorted(
    p for p in ROOT.rglob("index.html")
    if not (SKIP_DIRS & set(p.relative_to(ROOT).parts))
)

added, already, missed = [], [], []
for p in pages:
    text = p.read_text(encoding="utf-8")
    if 'src="/analytics.js"' in text:
        already.append(p)
        continue
    m = GA_CONFIG.search(text)
    if not m:
        missed.append(p)
        continue
    close = text.find("</script>", m.end())
    if close == -1:
        missed.append(p)
        continue
    cut = text.find("\n", close) + 1
    p.write_text(text[:cut] + TAG + text[cut:], encoding="utf-8")
    added.append(p)

for label, group in (("added", added), ("already had it", already), ("NO ANCHOR", missed)):
    if group:
        print(f"{label}: {len(group)}")
        for p in group:
            print("   ", p.relative_to(ROOT).as_posix())

raise SystemExit(1 if missed else 0)
