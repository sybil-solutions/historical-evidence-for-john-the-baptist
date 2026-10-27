#!/usr/bin/env python3
"""Convert the dossier PDF into sectioned Markdown for the site reader.

The PDF's own table of contents supplies every chapter heading, its subheadings
and their printed page numbers, so headings land where the typesetting put them
instead of being guessed from font sizes. Page furniture (running head, footer,
folio) is stripped, stray bullet glyphs are folded into list items, and the
inline citation markers `[12]` are rewritten to the register ids `[S12]` that
the citation cards and the site use.

    python3 tools/make_dossier.py [--pdf John_the_Baptist_Research_Dossier.pdf]

Writes one Markdown file per chapter under collections/dossier/, plus
`12-source-notes.md` holding every numbered entry with its exact link, and
`_meta/` sidecars with title and page range.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

import fitz

RUNNING_HEAD = {"JOHN THE BAPTIST", "HISTORY / EVIDENCE / LEGACY", "27 OCTOBER 2026"}

# (slug, printed title, printed page the chapter opens on)
CHAPTERS = [
    ("00-executive-findings", "Executive findings", 3),
    ("00-scope-and-method", "Scope and method", 4),
    ("01-what-evidence-survives", "1. What evidence actually survives?", 5),
    ("02-a-life-reconstructed", "2. A life reconstructed, with its gaps left visible", 8),
    ("03-what-kind-of-movement", "3. What kind of movement did John lead?", 11),
    ("04-why-baptism-mattered", "4. Why baptism was so consequential", 14),
    ("05-john-and-jesus", "5. John and Jesus: the decisive relationship", 17),
    ("06-prophecy-and-elijah", "6. Prophecy, Elijah and the meaning of \u201cForerunner\u201d", 21),
    ("07-why-he-was-killed", "7. Why was he killed?", 23),
    ("08-his-followers", "8. What became of his followers?", 26),
    ("09-archaeology-and-relics", "9. Archaeology, relics and claims of proof", 27),
    ("10-afterlives", "10. The afterlives of John", 31),
    ("11-significance", "11. Why John had such extraordinary significance", 39),
    ("appendix-a-reading-map", "Appendix A. Primary-source reading map", 43),
    ("appendix-b-scholarship", "Appendix B. How scholarship disagrees", 47),
]
NOTES = ("12-source-notes", "Source notes", 50)


def page_lines(pdf: Path) -> list[list[dict]]:
    """Rendered lines per page, with the geometry needed to rebuild paragraphs."""
    doc = fitz.open(pdf)
    pages = []
    for page in doc:
        lines = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                text = "".join(span["text"] for span in line["spans"]).rstrip()
                if text.strip():
                    lines.append({"text": text, "y": line["bbox"][1], "x": line["bbox"][0]})
        lines.sort(key=lambda l: (round(l["y"], 1), l["x"]))
        pages.append(lines)
    return pages


LEFT_MARGIN = 52.0      # prose starts here; table cells start right of it
ROW_GAP = 20.0          # leading inside a row is 12.5pt; a row gap is over 20


def is_table_line(line: dict) -> bool:
    return line["x"] > LEFT_MARGIN


def render_table(lines: list[dict]) -> str:
    """Rebuild a typeset table as a Markdown table.

    Cells wrap, so a row is a run of lines whose leading stays under ROW_GAP of
    the previous line, and each line joins the column whose left edge is
    nearest to it. The header row repeats at the top of each page and is
    emitted once.
    """
    edges: list[float] = []
    for line in lines:
        for edge in edges:
            if abs(edge - line["x"]) < 6:
                break
        else:
            edges.append(line["x"])
    edges.sort()
    rows: list[list[list[str]]] = []
    prev_y = None
    for line in sorted(lines, key=lambda l: (l["y"], l["x"])):
        if prev_y is None or line["y"] - prev_y > ROW_GAP:
            rows.append([[] for _ in edges])
        col = min(range(len(edges)), key=lambda i: abs(edges[i] - line["x"]))
        rows[-1][col].append(line["text"].strip())
        prev_y = line["y"]

    header = None
    body: list[list[str]] = []
    for row in rows:
        cells = [" ".join(c).replace("|", "\\|").strip() for c in row]
        if not any(cells):
            continue
        if header is None:
            header = cells
            continue
        if cells == header:
            continue
        body.append(cells)
    if header is None:
        return ""
    if len(header) == 1 or not body:
        return "  \n".join(" ".join([c for c in row if c]) for row in ([header] + body))
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(row) + " |" for row in body]
    return "\n".join(out)


def page_text(lines: list[dict]) -> str:
    """One page as Markdown: prose reflowed into paragraphs, tables rebuilt.

    A paragraph gap is visible in the typesetting as extra leading (16.0pt
    against roughly 25pt between paragraphs), so blocks are cut on the gap and
    the lines inside a block are rejoined, undoing the PDF's hard wrap. A
    standalone bullet glyph becomes the item's marker. Lines indented past the
    left margin belong to a table and are routed through render_table().
    """
    out: list[str] = []
    block: list[dict] = []
    table: list[dict] = []
    prev_y = None

    def flush_block() -> None:
        nonlocal block
        if not block:
            return
        texts = [l["text"].strip() for l in block]
        out.append(" ".join(texts))
        block = []

    def flush_table() -> None:
        nonlocal table
        if table:
            rendered = render_table(table)
            if rendered:
                out.append(rendered)
        table = []

    for line in lines:
        s = line["text"].strip()
        if s in RUNNING_HEAD or re.fullmatch(r"\d{1,3}", s):
            prev_y = None
            flush_block()
            flush_table()
            continue
        if is_table_line(line):
            flush_block()
            table.append(line)
            prev_y = line["y"]
            continue
        flush_table()
        if s in {"\u2022", "-", "\u2013"}:
            prev_y = None
            flush_block()
            block = [dict(line, text="\u2022")]
            continue
        if prev_y is not None and line["y"] - prev_y > 19.5:
            flush_block()
        block.append(line)
        prev_y = line["y"]
    flush_block()
    flush_table()
    return "\n\n".join(out)


def toc(pdf: Path) -> list[tuple[int, str, int]]:
    return [(lvl, title, page) for lvl, title, page in fitz.open(pdf).get_toc()]


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def find_heading(text: str, heading: str) -> int | None:
    want = "".join(ch for ch in heading.lower() if ch.isalnum())
    flat, index = [], []
    for i, ch in enumerate(text):
        if ch.isalnum():
            flat.append(ch.lower())
            index.append(i)
    pos = "".join(flat).find(want)
    return None if pos < 0 else index[pos]


def heading_end(text: str, start: int, heading: str) -> int:
    need = sum(ch.isalnum() for ch in heading)
    seen = 0
    for i in range(start, len(text)):
        if text[i].isalnum():
            seen += 1
            if seen >= need:
                return i + 1
    return start + len(heading)


def mark_heading(text: str, heading: str, level: int) -> tuple[str, bool]:
    pos = find_heading(text, heading)
    if pos is None:
        return text, False
    stop = heading_end(text, pos, heading)
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", stop)
    line_end = len(text) if line_end < 0 else line_end
    return text[:line_start] + f"{'#' * level} {heading}" + text[line_end:], True


def tidy(text: str) -> str:
    # A bullet glyph typeset on its own line belongs to the item below it.
    text = re.sub(r"(?m)^\u2022\s*\n\s*", "- ", text)
    text = re.sub(r"(?m)^\u2022\s+", "- ", text)
    # Inline citation markers become register ids.
    text = re.sub(r"\[(\d{1,3})\]", lambda m: f"[S{int(m.group(1)):02d}]", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="John_the_Baptist_Research_Dossier.pdf")
    ap.add_argument("--outdir", default="collections/dossier")
    args = ap.parse_args()
    pdf = Path(args.pdf)
    outdir = Path(args.outdir)
    (outdir / "_meta").mkdir(parents=True, exist_ok=True)

    pages = page_lines(pdf)
    headings = toc(pdf)
    subheads: dict[int, list[str]] = {}
    for level, title, page in headings:
        if level == 2:
            subheads.setdefault(page, []).append(title)

    plan = CHAPTERS + [NOTES]
    plan.sort(key=lambda c: c[2])
    bounds = {}
    for i, (slug, title, page) in enumerate(plan):
        end = plan[i + 1][2] if i + 1 < len(plan) else len(pages) + 1
        bounds[slug] = (page, end)

    written = []
    for slug, title, page in plan:
        start, end = bounds[slug]
        chunks = []
        for pno in range(start, end):
            if pno - 1 >= len(pages):
                break
            chunks.append(page_text(pages[pno - 1]))
        body = "\n\n".join(chunks)
        # The chapter title is printed at the top of its first page: replace it
        # with the document's own H1.
        body, found = mark_heading(body, title, 1)
        if not found:
            body = f"# {title}\n\n" + body
        for pno in range(start, end):
            for sub in subheads.get(pno, []):
                body, _ = mark_heading(body, sub, 2)
        body = tidy(body)

        if slug == NOTES[0]:
            body = source_notes(body)

        path = outdir / f"{slug}.md"
        path.write_text(
            f"<!-- Converted from {pdf.name}, printed pages {start}-{min(end, len(pages) + 1) - 1}. -->\n\n"
            + body
            + "\n",
            encoding="utf-8",
        )
        (outdir / "_meta" / f"{slug}.json").write_text(
            json.dumps(
                {
                    "slug": slug,
                    "title": title,
                    "source_name": pdf.name,
                    "source_url": "",
                    "license": "Original research dossier in this repository.",
                    "pages": f"{start}-{min(end, len(pages) + 1) - 1}",
                    "converted": date.today().isoformat(),
                    "chars": len(body),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        written.append((slug, len(body)))

    for slug, chars in written:
        print(f"{slug:30s} {chars:6d} chars")
    print(f"{len(written)} documents -> {outdir}")
    return 0


def source_notes(body: str) -> str:
    """Rebuild the printed note list from the extracted register.

    The PDF prints each entry as a wrapped title plus the host it came from.
    collections/references/refs.json already carries that text and the exact
    URL the title linked to, so the document is assembled from it instead of
    re-parsing the page: one heading per entry, the host as printed, and the
    destination.
    """
    refs_path = Path("collections/references/refs.json")
    if not refs_path.exists():
        return body
    refs = json.loads(refs_path.read_text())
    out = [
        "# Source notes",
        "",
        "Sources are numbered by first appearance and repeated citations share the same number. "
        "Each entry below carries the exact page the dossier's own hyperlink opened, read from the "
        "PDF's link annotations rather than guessed from the printed host. Biblical book-and-verse "
        "references stay in the text. Accessed 27 October 2026.",
        "",
    ]
    for ref in refs:
        citation = ref["citation"]
        out.append(f"## {ref['id']}. {citation}")
        out.append("")
        hosts = ", ".join(ref["domains"])
        if ref["url"]:
            label = hosts or "original"
            out.append(f"{label} · [open]({ref['url']})")
        elif hosts:
            out.append(hosts)
        out.append("")
    return "\n".join(out).strip()


if __name__ == "__main__":
    raise SystemExit(main())
