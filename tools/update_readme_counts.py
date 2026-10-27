#!/usr/bin/env python3
"""Rewrite the collection table in README.md from collections/catalog.json.

The table lives between the markers `<!-- collections:start -->` and
`<!-- collections:end -->`, so it cannot drift from the actual contents.

    python3 tools/update_readme_counts.py
"""
import json, re
from pathlib import Path

BLURB = {
    "dossier": "The report itself, chaptered, plus the 94-entry source notes",
    "scripture": "The books the dossier cites, World English Bible, one file per book",
    "quran": "Surahs 3, 6, 19 and 21 on Yahya, Palmer's public-domain translation",
    "gospels": "The Gospel of Thomas and the Protevangelium of James, public-domain translations",
    "witnesses": "Josephus, Antiquities XVIII.5, and Origen, Against Celsus I.47",
    "archaeology": "Machaerus, Bethany beyond the Jordan, the Sozopol relics, the Suba cave, the Qumran question",
    "afterlives": "The Mandaeans, Yahya in Islam, and Christian worship and art",
    "citations": "One page per source note: the citation, the exact destination, and where it is cited",
}


def main() -> int:
    cat = json.loads(Path("collections/catalog.json").read_text())
    counts = {c["id"]: c["docs"] for c in cat["collections"]}
    rows = ["| Collection | Documents | What it holds |", "|---|---|---|"]
    for cid, n in counts.items():
        if not n:
            continue
        rows.append(f"| [{cid}](collections/{cid}/) | {n} | {BLURB.get(cid, cat['collections'][[c['id'] for c in cat['collections']].index(cid)]['blurb'])} |")
    rows.append(f"| [references](collections/references/) | {len(cat['references'])} | `refs.json` (exact link destinations from the PDF), `links.json` (mirrored entries), `links-report.md` (the verified match for each) |")
    block = "\n".join(rows)

    readme = Path("README.md")
    text = readme.read_text()
    pat = re.compile(r"<!-- collections:start -->.*?<!-- collections:end -->", re.S)
    if not pat.search(text):
        print("markers not found in README.md")
        return 1
    readme.write_text(pat.sub(f"<!-- collections:start -->\n{block}\n<!-- collections:end -->", text))
    print(f"{len(counts)} collections written to README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
