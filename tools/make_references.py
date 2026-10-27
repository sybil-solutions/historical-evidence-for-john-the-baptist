#!/usr/bin/env python3
"""Extract the dossier's 94 source notes with their exact link destinations.

The PDF's source notes are numbered by first appearance. Each entry prints a
bibliographic line and then the host it came from, and the title line carries a
live hyperlink to a particular page (Josephus XVIII on livius.org, Origen
Against Celsus 1.47 on New Advent, the AMS/DNA bone study on the University of
Copenhagen research portal). This tool reads those link annotations out of the
PDF and attaches each one to the numbered entry whose vertical band on the page
holds it, so every entry carries the exact destination rather than a guess made
from the printed hostname.

Output: collections/references/refs.json
  id, number, citation, work, detail, domains (as printed), urls (from the PDF,
  in printed order), pdf_page, cited_in (dossier documents that cite the entry)

    python3 tools/make_references.py
"""
import json
import re
from collections import OrderedDict
from datetime import date
from pathlib import Path

import fitz

PDF = Path("John_the_Baptist_Research_Dossier.pdf")
OUT = Path("collections/references/refs.json")
DOSSIER = Path("collections/dossier")

# Pages of the printed source notes, 1-based.
NOTES_PAGES = range(50, 58)
FURNITURE = re.compile(
    r"^(JOHN THE BAPTIST|HISTORY / EVIDENCE / LEGACY|27 OCTOBER 2026|\d{1,3})$"
)
HOST = re.compile(r"^[a-z0-9][a-z0-9.\-]*\.(com|org|net|edu|it|uk|il|tr|de|va|gov|int)$")
ENTRY = re.compile(r"^(\d{1,3})\.\s+(.*)$")


def page_lines(page) -> list[str]:
    """Text lines in reading order, one string per rendered line."""
    lines = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                lines.append(text)
    return lines


def entry_tops(page) -> list[tuple[int, float]]:
    """(entry number, y of its first line) for every 'N.' at the left margin."""
    tops: list[tuple[int, float]] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            m = ENTRY.match(text)
            if m and line["bbox"][0] < 60:
                tops.append((int(m.group(1)), line["bbox"][1]))
    return tops


def parse(doc) -> tuple[list[dict], dict[int, float], dict[int, int]]:
    """Entries, their page and top coordinate, and the page each starts on."""
    entries: list[dict] = []
    where: dict[int, tuple[int, float]] = {}
    for pno in NOTES_PAGES:
        page = doc[pno - 1]
        tops = entry_tops(page)
        for num, y in tops:
            where[num] = (pno, y)
        for line in page_lines(page):
            if FURNITURE.match(line):
                continue
            m = ENTRY.match(line)
            if m:
                entries.append(
                    {"number": int(m.group(1)), "lines": [m.group(2)], "page": pno}
                )
            elif entries and not HOST.match(line):
                entries[-1]["lines"].append(line)
            elif entries and HOST.match(line):
                entries[-1].setdefault("domains", []).append(line)
    return entries, where


def attach_urls(doc, entries: list[dict], where: dict[int, tuple[int, float]]) -> None:
    by_page: dict[int, list[int]] = {}
    for num, (pno, _) in where.items():
        by_page.setdefault(pno, []).append(num)
    for pno, nums in by_page.items():
        nums.sort(key=lambda n: where[n][1])
        bounds = [(n, where[n][1]) for n in nums]
        for link in doc[pno - 1].get_links():
            uri = link.get("uri")
            if not uri:
                continue
            top = link["from"].y0
            owner = None
            for idx, (num, y) in enumerate(bounds):
                nxt = bounds[idx + 1][1] if idx + 1 < len(bounds) else 10_000
                if y - 3 <= top < nxt - 3:
                    owner = num
            if owner is None:
                continue
            for entry in entries:
                if entry["number"] == owner:
                    urls = entry.setdefault("urls", [])
                    if uri not in urls:
                        urls.append(uri)
                    break


def cited_in(dossier: Path) -> dict[str, dict[str, int]]:
    """Which dossier documents cite each S-id, and how often."""
    counts: dict[str, dict[str, int]] = {}
    if not dossier.is_dir():
        return counts
    for path in sorted(dossier.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\[S(\d{2})\]", text):
            rid = f"S{m.group(1)}"
            bucket = counts.setdefault(rid, {})
            bucket[path.stem] = bucket.get(path.stem, 0) + 1
    return counts


def main() -> int:
    doc = fitz.open(PDF)
    entries, where = parse(doc)
    entries.sort(key=lambda e: e["number"])
    if [e["number"] for e in entries] != list(range(1, len(entries) + 1)):
        raise SystemExit(f"source notes are not a clean 1..N run: {[e['number'] for e in entries]}")
    attach_urls(doc, entries, where)

    cites = cited_in(DOSSIER)
    refs = []
    missing = []
    for entry in entries:
        text = " ".join(entry["lines"]).strip()
        text = re.sub(r"\s+", " ", text)
        work, _, detail = text.partition(", ")
        urls = entry.get("urls", [])
        rid = f"S{entry['number']:02d}"
        if not urls:
            missing.append(rid)
        refs.append(
            {
                "id": rid,
                "number": entry["number"],
                "citation": text,
                "work": work.strip(),
                "detail": detail.strip(),
                "domains": entry.get("domains", []),
                "urls": urls,
                "url": urls[0] if urls else "",
                "pdf_page": entry["page"],
                "cited_in": cites.get(rid, {}),
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(refs, indent=1, ensure_ascii=False) + "\n")
    with_url = sum(1 for r in refs if r["url"])
    cited = sum(1 for r in refs if r["cited_in"])
    print(f"{len(refs)} source notes -> {OUT}")
    print(f"{with_url} carry an exact URL from the PDF, {cited} are cited by the dossier")
    if missing:
        print(f"no embedded link ({len(missing)}): {' '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
