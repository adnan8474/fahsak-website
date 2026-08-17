"""Merge validated articles from content/batches into content/articles.json.

Matching is by slug, so re-merging a corrected batch file replaces that article
in place and leaves its position, and therefore its URL and its neighbours in
the hub listings, alone.

    python merge_batches.py            # dry run, prints what would change
    python merge_batches.py --write
"""
import json
import os
import subprocess
import sys

DATA = "content/articles.json"
BATCH = "content/batches"


def main(argv):
    write = "--write" in argv

    # Never merge unvalidated work: the citation check in particular cannot be
    # eyeballed, and a bad PubMed ID is invisible once it is on a live page.
    if subprocess.call([sys.executable, "validate_batch.py"]) != 0:
        print("\nvalidation failed, nothing merged")
        return 1

    live = json.load(open(DATA, encoding="utf-8"))
    by_slug = {a["slug"]: i for i, a in enumerate(live)}

    added, replaced = [], []
    for f in sorted(os.listdir(BATCH)):
        if not f.endswith(".json"):
            continue
        data = json.load(open(os.path.join(BATCH, f), encoding="utf-8"))
        for a in (data if isinstance(data, list) else [data]):
            if a["slug"] in by_slug:
                live[by_slug[a["slug"]]] = a
                replaced.append(a["slug"])
            else:
                by_slug[a["slug"]] = len(live)
                live.append(a)
                added.append(a["slug"])

    print(f"\n{len(added)} new, {len(replaced)} replaced, {len(live)} total")
    if replaced:
        print("  replacing: " + ", ".join(sorted(replaced)))
    if not write:
        print("\ndry run, pass --write to apply")
        return 0

    with open(DATA, "w", encoding="utf-8") as fh:
        json.dump(live, fh, ensure_ascii=False, indent=1)
    print(f"wrote {DATA}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
