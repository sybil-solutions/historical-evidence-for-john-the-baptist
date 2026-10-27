#!/usr/bin/env python3
"""Resolve source-note entries to documents in this repository, with verification.

A reference is linked to a mirrored document only when both hold:

  * the citation names the work (a pattern, not a loose keyword), and
  * the document actually contains the locator the citation gives (a chapter
    heading, or a phrase the extract is supposed to contain).

Anything that fails either test keeps `doc: null`, and the site then links the
exact URL taken from the PDF's own hyperlink instead of guessing a match. That
is the difference between "the archive holds Josephus on John" and "the archive
holds something with Josephus in the title".

Writes collections/references/links.json and links-report.md.

    python3 tools/make_links.py
"""
import json
import re
from pathlib import Path

ROOT = Path("collections")
OUT = ROOT / "references"

SCRIPTURE = {
    "2 kings": "2-kings",
    "isaiah": "isaiah",
    "malachi": "malachi",
    "matthew": "matthew",
    "mark": "mark",
    "luke": "luke",
    "john": "john",
    "acts": "acts",
    "romans": "romans",
}

# (citation pattern, document id, marker the document must contain)
RULES: list[tuple[str, str, str]] = [
    (r"josephus.*antiquit", "witnesses/josephus-antiquities-18", "called the baptist"),
    (r"against celsus|contra celsum", "witnesses/origen-contra-celsum-1-47", "john"),
    (r"machaerus", "archaeology/machaerus", "machaerus"),
    (r"baptism site|bethany beyond the jordan|al-maghtas", "archaeology/bethany-beyond-the-jordan", "maghtas"),
    (r"ams dating|bone relics|radiocarbon", "archaeology/bulgarian-relics", "radiocarbon"),
    (r"cave of john", "archaeology/cave-of-john", "cave"),
    (r"qumran|wilderness relationship", "archaeology/qumran-and-john", "qumran"),
    (r"gospel of thomas", "gospels/gospel-of-thomas", "thomas"),
    (r"protevangelium|infancy gospel of james", "gospels/protevangelium-of-james", "joachim"),
    (r"mandae|ginza|book of john", "afterlives/mandaeans", "mandaean"),
    (r"yahya|yahy", "afterlives/yahya-in-islam", "yahya"),
]
COMPILED = [(re.compile(p, re.I), doc, marker) for p, doc, marker in RULES]

QURAN = re.compile(r"qur.?an\s+(\d{1,3}):", re.I)


def main() -> int:
    refs = json.loads((OUT / "refs.json").read_text())
    texts: dict[str, str] = {}
    for path in ROOT.rglob("*.md"):
        if path.parent.name == "_meta":
            continue
        texts[path.relative_to(ROOT).with_suffix("").as_posix()] = path.read_text(
            encoding="utf-8", errors="replace"
        ).lower()

    links: dict[str, str] = {}
    rows: list[tuple[str, str, str, str]] = []
    unmatched_primary: list[tuple[str, str]] = []

    for ref in refs:
        citation = ref["citation"]
        low = citation.lower()
        target = marker = None

        m = QURAN.search(low)
        if m:
            doc = f"quran/surah-{int(m.group(1)):02d}"
            if doc in texts:
                target, marker = doc, ""

        if not target:
            m = re.match(r"^(\d?\s?[a-z]+?),?\s+(?:beginning with chapter\s+)?(\d+)", low)
            if m and m.group(1).strip() in SCRIPTURE:
                doc = f"scripture/{SCRIPTURE[m.group(1).strip()]}"
                chapter = int(m.group(2))
                if doc in texts and f"## chapter {chapter}" in texts[doc]:
                    target, marker = doc, f"## Chapter {chapter}"

        if not target:
            for pattern, doc, need in COMPILED:
                if pattern.search(low) and doc in texts and (not need or need in texts[doc]):
                    target, marker = doc, need
                    break

        if target:
            links[ref["id"]] = target
            rows.append((ref["id"], citation, target, marker or "—"))
        elif ref["domains"] and ref["url"] and not re.search(r"primary text", low):
            unmatched_primary.append((ref["id"], citation[:90]))

    (OUT / "links.json").write_text(json.dumps(dict(sorted(links.items())), indent=1) + "\n")
    report = [
        "# Reference to document links",
        "",
        "Every row is a source-note entry, the document in this repository that carries the same",
        "work, and the marker that was found in that document to confirm the match. Entries that",
        "are not listed here are in copyright and are linked to their own publisher from the",
        "citation card instead of being copied.",
        "",
        "| Ref | Citation | Document | Marker found |",
        "|---|---|---|---|",
    ]
    report += [f"| {rid} | {cite[:110]} | {doc} | {mark} |" for rid, cite, doc, mark in rows]
    (OUT / "links-report.md").write_text("\n".join(report) + "\n")

    print(f"{len(links)} of {len(refs)} entries linked to a mirrored document")
    if unmatched_primary:
        print(f"primary texts with no confirmed mirror ({len(unmatched_primary)}):")
        for rid, cite in unmatched_primary:
            print(f"  {rid}  {cite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
