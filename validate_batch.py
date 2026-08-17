"""Check authored article batches before they reach content/articles.json.

Run against one file or the whole content/batches/ directory. Errors block a
merge; warnings are quality nudges that do not. The point is that a bad article
is caught here rather than on a live page, and that no writer has to be trusted
to have counted their own sections.

    python validate_batch.py                     # everything in content/batches
    python validate_batch.py content/batches/x.json
    python validate_batch.py --offline x.json    # skip the PubMed check
"""
import json
import os
import re
import sys

import build_visuals
import cite

CATS = {c["id"] for c in json.load(open("content/categories.json", encoding="utf-8"))}
LANGS = ("ar", "en")
REQ_LANG = ("title", "desc", "keywords", "h1", "takeaways", "sections", "tie", "faqs")
VIZ_TYPES = set(build_visuals.RENDERERS)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ARABIC_RE = re.compile(r"[؀-ۿ]")


def words(block):
    """Body prose only.

    Headings, takeaways and FAQ text are deliberately excluded. Counting them
    let an article of roughly 1,000 words of real explanation pass a 1,300 word
    bar on page furniture alone, which is exactly the thin page this bar exists
    to catch.
    """
    n = 0
    for s in block.get("sections", []):
        n += sum(len(p.split()) for p in s.get("paras", []))
    return n


def check_visual(v, where, err, warn):
    t = v.get("type")
    if t not in VIZ_TYPES:
        err.append(f"{where}: unknown visual type {t!r}")
        return
    # the renderer is the real contract, so exercise it rather than re-describe it
    for lang in LANGS:
        if build_visuals.render(lang, v) == "":
            err.append(f"{where}: visual {t!r} failed to render in {lang}")
            return
    if t == "range-scale":
        zones = v.get("zones") or []
        if len(zones) < 2:
            err.append(f"{where}: range-scale needs at least 2 zones")
        tops = [float(z["to"]) for z in zones if z.get("to") is not None]
        if tops != sorted(tops):
            err.append(f"{where}: range-scale zones are not in ascending order")
        if tops and abs(tops[-1] - float(v["max"])) > 1e-6:
            warn.append(f"{where}: last zone ends at {tops[-1]}, max is {v['max']}")
    if t in ("bar", "stats", "timeline", "steps") and len(v.get("items") or []) < 2:
        warn.append(f"{where}: {t} has fewer than 2 items")
    if t == "table":
        head = v.get("head") or v.get("columns") or []
        for r in v.get("rows") or []:
            if len(r) != len(head):
                err.append(f"{where}: table row has {len(r)} cells, header has {len(head)}")
                break


def check_article(a, seen, err, warn):
    slug = a.get("slug", "<no slug>")
    w = f"[{slug}]"

    if not SLUG_RE.match(a.get("slug", "")):
        err.append(f"{w}: slug is not clean kebab-case")
    if slug in seen:
        err.append(f"{w}: duplicate slug")
    seen.add(slug)

    if a.get("category") not in CATS:
        err.append(f"{w}: category {a.get('category')!r} is not one of {sorted(CATS)}")
    for k in ("chip_ar", "chip_en", "date_iso"):
        if not a.get(k):
            err.append(f"{w}: missing {k}")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(a.get("date_iso", ""))):
        err.append(f"{w}: date_iso must be YYYY-MM-DD")

    src = a.get("sources") or []
    if len(src) < 3:
        err.append(f"{w}: only {len(src)} sources, need at least 3")
    for s in src:
        if not s.get("label"):
            err.append(f"{w}: a source has no label")
        u = s.get("url")
        if u and not u.startswith("https://"):
            err.append(f"{w}: source url is not https: {u}")

    content = a.get("content") or {}
    for lang in LANGS:
        c = content.get(lang)
        if not c:
            err.append(f"{w}: missing {lang} content")
            continue
        wl = f"{w}.{lang}"
        for k in REQ_LANG:
            if not c.get(k):
                err.append(f"{wl}: missing {k}")
        if not c.get("sections"):
            continue

        n = len(c["sections"])
        if n < 6:
            err.append(f"{wl}: {n} sections, need at least 6")
        elif n > 12:
            warn.append(f"{wl}: {n} sections is long")
        if len(c.get("faqs", [])) < 5:
            err.append(f"{wl}: {len(c.get('faqs', []))} FAQs, need at least 5")
        if not 3 <= len(c.get("takeaways", [])) <= 6:
            warn.append(f"{wl}: {len(c.get('takeaways', []))} takeaways (want 3 to 5)")

        # Arabic says the same thing in fewer words than English: it drops the
        # copula, attaches pronouns and prepositions, and needs no articles of
        # its own, so an equally rich Arabic article scores roughly 15% lower.
        wc = words(c)
        floor, target = (950, 1300) if lang == "ar" else (1100, 1500)
        if wc < floor:
            err.append(f"{wl}: only ~{wc} words of body prose, too thin to rank")
        elif wc < target:
            warn.append(f"{wl}: ~{wc} words of body prose, thinner than target")

        # length caps that protect the layout rather than the prose
        if len(c["title"]) > 65:
            warn.append(f"{wl}: title is {len(c['title'])} chars, will truncate in search")
        if not 110 <= len(c["desc"]) <= 175:
            warn.append(f"{wl}: desc is {len(c['desc'])} chars (want 150 to 160)")

        # Adnan's house style, and the tell he reacts to most
        for field, text in (("title", c["title"]), ("desc", c["desc"]), ("h1", c["h1"])):
            if "—" in text or "–" in text:
                err.append(f"{wl}: em-dash or en-dash in {field}")
        for i, s in enumerate(c["sections"]):
            if not s.get("paras"):
                err.append(f"{wl}: section {i} has no paragraphs")
            for p in s.get("paras", []):
                if "—" in p or "–" in p:
                    err.append(f"{wl}: em-dash in section {i}")
                    break

        if lang == "ar" and not ARABIC_RE.search(c["h1"]):
            err.append(f"{wl}: Arabic h1 contains no Arabic script")
        if lang == "en" and ARABIC_RE.search(c["h1"]):
            err.append(f"{wl}: English h1 contains Arabic script")

        seen_types, count = set(), 0
        for i, s in enumerate(c["sections"]):
            vs = ([s["visual"]] if s.get("visual") else []) + list(s.get("visuals") or [])
            for v in vs:
                count += 1
                seen_types.add(v.get("type"))
                check_visual(v, f"{wl} section {i}", err, warn)
        if count < 3:
            err.append(f"{wl}: {count} visuals, need at least 3")
        if len(seen_types) < 2 and count:
            warn.append(f"{wl}: all visuals are the same type")

    # the two languages must describe the same article
    if content.get("ar") and content.get("en"):
        na, ne = len(content["ar"].get("sections", [])), len(content["en"].get("sections", []))
        if na != ne:
            err.append(f"{w}: {na} Arabic sections vs {ne} English")
        fa, fe = len(content["ar"].get("faqs", [])), len(content["en"].get("faqs", []))
        if fa != fe:
            warn.append(f"{w}: {fa} Arabic FAQs vs {fe} English")


def check_citations(targets, err, warn):
    """Prove every cited paper is the paper at that PubMed ID.

    Models recall PubMed IDs that look right and belong to an unrelated paper,
    so this is the one check that cannot be done by reading the file. If the
    network is down we warn rather than fail: a writer should not be blocked by
    NCBI being unreachable, but nothing merges without a clean run.
    """
    try:
        problems, _, n_pmid, n_other = cite.audit(targets, links=True)
    except Exception as exc:  # noqa: BLE001 - NCBI outages are not the writer's fault
        warn.append(f"citation check could not run ({exc}), rerun before merging")
        return
    for slug, kind, ref, label, real in problems:
        err.append(f"[{slug}]: {kind} {ref}\n         cited as : {label}"
                   + (f"\n         actually : {real}" if real else ""))
    if not problems and (n_pmid or n_other):
        print(f"  ok    {n_pmid} PubMed citations and {n_other} links verified")


def main(argv):
    offline = "--offline" in argv
    argv = [a for a in argv if a != "--offline"]
    targets = argv[1:]
    if not targets:
        d = "content/batches"
        targets = ([os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".json")]
                   if os.path.isdir(d) else [])
    if not targets:
        print("nothing to validate")
        return 0

    existing = {a["slug"] for a in json.load(open("content/articles.json", encoding="utf-8"))}
    seen, err, warn, total = set(), [], [], 0

    for path in targets:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as exc:
            err.append(f"{os.path.basename(path)}: not valid JSON: {exc}")
            continue
        if isinstance(data, dict):
            data = [data]
        for a in data:
            total += 1
            before = len(err)
            check_article(a, seen, err, warn)
            if a.get("slug") in existing:
                warn.append(f"[{a['slug']}]: already in articles.json, will replace it")
            if len(err) > before:
                err[before] = f"{os.path.basename(path)} " + err[before]

    if not offline:
        check_citations(targets, err, warn)

    for m in warn:
        print(f"  warn  {m}")
    for m in err:
        print(f"  FAIL  {m}")
    print(f"\n{total} article(s), {len(err)} error(s), {len(warn)} warning(s)")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
