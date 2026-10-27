#!/usr/bin/env python3
"""Mirror the biblical books the dossier cites, from the World English Bible.

The World English Bible is public domain. The text is taken from eBible.org's
USFM edition of the whole Bible (one archive, so the build is offline after the
first run) and reduced to paragraph text, with the USFM word-level markup,
footnotes and cross-references stripped.

Output: collections/scripture/<slug>.md, five verses to a paragraph, one
`## Chapter N` heading per chapter, plus `_meta/` sidecars.

    python3 tools/fetch_web.py            # download the archive if needed, then rebuild
    python3 tools/fetch_web.py --refresh  # re-download the archive
"""
import argparse
import json
import re
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

USFM_ZIP = "https://ebible.org/Scriptures/eng-web_usfm.zip"
CACHE = Path(".cache/web_usfm")
OUT = Path("collections/scripture")
UA = {"User-Agent": "john-the-baptist-archive/1.0 (+https://github.com/sybil-solutions)"}

# slug -> (USFM id, printed title, testament)
BOOKS = {
    "2-kings": ("2KI", "The Second Book of Kings", "Old Testament"),
    "isaiah": ("ISA", "The Book of Isaiah", "Old Testament"),
    "malachi": ("MAL", "The Book of Malachi", "Old Testament"),
    "matthew": ("MAT", "The Gospel According to Matthew", "New Testament"),
    "mark": ("MRK", "The Gospel According to Mark", "New Testament"),
    "luke": ("LUK", "The Good News According to Luke", "New Testament"),
    "john": ("JHN", "The Good News According to John", "New Testament"),
    "acts": ("ACT", "The Acts of the Apostles", "New Testament"),
    "romans": ("ROM", "The Letter of Paul to the Romans", "New Testament"),
}

# Inline markers whose content is kept.
KEEP = re.compile(r"\\(?:add|nd|qt|bk|wj|it|bd|em|sc|no|k|ord|pn|png|sig)\*?", re.I)
# Marker families removed with everything inside them.
DROP_INLINE = re.compile(r"\\(f|x)\s.*?\\\1\*", re.S)
WORD_MARKER = re.compile(r"\\\+?w\s+([^|]*?)(?:\|[^\\]*?)?\\\+?w\*", re.S)
MILESTONE = re.compile(r"\\[a-z]+\d?\*?")


def archive(refresh: bool) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / "eng-web_usfm.zip"
    if target.exists() and not refresh:
        return target
    req = urllib.request.Request(USFM_ZIP, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        target.write_bytes(resp.read())
    return target


def book_text(zip_path: Path, usfm_id: str) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        name = next(n for n in zf.namelist() if n.endswith(f"{usfm_id}eng-web.usfm"))
        raw = zf.read(name).decode("utf-8", "replace")
    return raw


def clean_inline(text: str) -> str:
    text = DROP_INLINE.sub("", text)
    text = WORD_MARKER.sub(lambda m: m.group(1), text)
    text = KEEP.sub("", text)
    text = MILESTONE.sub("", text)
    text = text.replace("\\~", "\u00a0").replace("\\-", "")
    text = text.replace("|", "")
    return " ".join(text.split())


CHAPTER = re.compile(r"^\\c\s+(\d+)\s*$")
VERSE = re.compile(r"^\\v\s+(\d+)\s*(.*)$")
SKIP = re.compile(r"^\\(?:id|ide|h|toc\d|mt\d?|is\d?|ip|rem|sts|restore)\b")


def parse(raw: str) -> dict[int, dict[int, str]]:
    chapters: dict[int, dict[int, str]] = {}
    chapter = None
    verse = None
    for line in raw.splitlines():
        line = line.rstrip()
        m = CHAPTER.match(line.strip())
        if m:
            chapter = int(m.group(1))
            chapters.setdefault(chapter, {})
            verse = None
            continue
        m = VERSE.match(line.strip())
        if m and chapter is not None:
            verse = int(m.group(1))
            chapters[chapter][verse] = m.group(2)
            continue
        if SKIP.match(line):
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("\\"):
            continue
        if verse is not None:
            chapters[chapter][verse] += " " + stripped
    return chapters


def to_markdown(title: str, chapters: dict[int, dict[int, str]]) -> str:
    out = [f"# {title}", ""]
    for number in sorted(chapters):
        out += [f"## Chapter {number}", ""]
        verses = chapters[number]
        para: list[str] = []
        for v in sorted(verses):
            text = clean_inline(verses[v])
            if not text:
                continue
            para.append(f"**{v}** {text}")
            if len(para) == 5:
                out += [" ".join(para), ""]
                para = []
        if para:
            out += [" ".join(para), ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    zip_path = archive(args.refresh)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_meta").mkdir(exist_ok=True)
    for slug, (usfm_id, title, testament) in BOOKS.items():
        chapters = parse(book_text(zip_path, usfm_id))
        doc = to_markdown(title, chapters)
        (OUT / f"{slug}.md").write_text(
            f"<!-- World English Bible, {title}. Public domain. "
            f"USFM edition from ebible.org, built {date.today().isoformat()}. -->\n\n{doc}",
            encoding="utf-8",
        )
        (OUT / "_meta" / f"{slug}.json").write_text(
            json.dumps(
                {
                    "slug": slug,
                    "title": title,
                    "source_name": "World English Bible",
                    "source_url": "https://ebible.org/web/",
                    "license": "Public domain (World English Bible)",
                    "testament": testament,
                    "chapters": len(chapters),
                    "fetched": date.today().isoformat(),
                },
                indent=2,
            )
            + "\n"
        )
        print(f"{slug:10s} {len(chapters):3d} chapters {len(doc):7d} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
