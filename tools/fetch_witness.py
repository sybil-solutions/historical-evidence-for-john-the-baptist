#!/usr/bin/env python3
"""Mirror the two ancient witnesses the dossier quotes in full.

Both are public domain and both are excerpted to the unit the argument needs:

  * Josephus, Antiquities XVIII.5 (Whiston, 1737) — the whole chapter, because
    §1 (the defeat of Antipas's army and how people read it), §2 (John), and
    §3-4 (the Herodian family, Vitellius) are one continuous narrative.
  * Origen, Against Celsus I.47 (Ante-Nicene Fathers, 1885) — the chapter in
    which Origen argues from Josephus that John's existence is not a Christian
    invention.

Each page is sliced between two printed markers so the extract cannot drift
into a neighbouring chapter without the check failing.

    python3 tools/fetch_witness.py [--refresh]
"""
import argparse
import html
import json
import re
import time
import urllib.request
from datetime import date
from pathlib import Path

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126 Safari/537.36"
}
CACHE = Path(".cache/witnesses")

SOURCES = [
    {
        "slug": "josephus-antiquities-18",
        "url": "https://www.ccel.org/ccel/josephus/works/files/ant-18.htm",
        "start": "CHAPTER 5.",
        "end": "CHAPTER 6.",
        "title": "Flavius Josephus, Antiquities of the Jews, Book XVIII, chapter 5",
        "source_name": "William Whiston translation (1737), via Christian Classics Ethereal Library",
        "license": "Public domain",
        "note": (
            "The chapter is reproduced whole. Section 1 reports the destruction of Antipas's army "
            "by Aretas and the popular reading of it as revenge for John; section 2 is the account "
            "of John, his baptism, his influence and his execution; sections 3-4 turn to the "
            "Herodian family and to Vitellius. Whiston's bracketed numerals are his own footnote "
            "markers and are left where he printed them."
        ),
        "anchor": "Now some of the Jews thought",
    },
    {
        "slug": "origen-contra-celsum-1-47",
        "url": "https://www.newadvent.org/fathers/04161.htm",
        "start": "Chapter 47",
        "end": "Chapter 48",
        "title": "Origen, Against Celsus, Book I, chapter 47",
        "source_name": "Ante-Nicene Fathers, volume 4 (1885), via New Advent",
        "license": "Public domain",
        "note": (
            "Origen answers Celsus by pointing to Josephus: the Baptist's existence and his rite "
            "are reported by a writer who did not believe in Jesus, and who lived soon enough "
            "after the events to be a witness rather than a legend."
        ),
        "anchor": "josephus bears witness to john",
    },
]


def fetch(url: str, refresh: bool, slug: str) -> str:
    target = CACHE / f"{slug}.html"
    if target.exists() and not refresh:
        return target.read_text(encoding="utf-8", errors="replace")
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read().decode("utf-8", "replace")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(raw, encoding="utf-8")
            return raw
        except Exception as exc:  # noqa: BLE001 - transient network
            if attempt == 4:
                raise SystemExit(f"{url}: {exc}")
            time.sleep(2 * (attempt + 1))
    return ""


def plain(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", raw)
    text = re.sub(r"(?i)</p>|</div>|<br\s*/?>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\u00a0", " ")
    lines = [" ".join(l.split()) for l in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def slice_between(text: str, start: str, end: str) -> str:
    i = text.find(start)
    j = text.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or j < 0:
        raise SystemExit(f"markers not found: {start!r} .. {end!r}")
    body = text[i + len(start) : j]
    body = re.sub(r"\n{2,}", "\n\n", body)
    return body.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    out = Path("collections/witnesses")
    (out / "_meta").mkdir(parents=True, exist_ok=True)

    for spec in SOURCES:
        raw = fetch(spec["url"], args.refresh, spec["slug"])
        body = slice_between(plain(raw), spec["start"], spec["end"])
        low = body.lower()
        if spec["anchor"].lower() not in low:
            raise SystemExit(f"{spec['slug']}: extract does not contain {spec['anchor']!r}")
        doc = (
            f"# {spec['title']}\n\n"
            f"> {spec['note']}\n\n"
            f"*{spec['source_name']}. Public domain. [Original page]({spec['url']}).*\n\n"
            f"{body}\n"
        )
        (out / f"{spec['slug']}.md").write_text(
            f"<!-- Mirrored from {spec['url']} on {date.today().isoformat()}. {spec['source_name']}. -->\n\n"
            + doc,
            encoding="utf-8",
        )
        (out / "_meta" / f"{spec['slug']}.json").write_text(
            json.dumps(
                {
                    "slug": spec["slug"],
                    "title": spec["title"],
                    "source_name": spec["source_name"],
                    "source_url": spec["url"],
                    "license": spec["license"],
                    "fetched": date.today().isoformat(),
                    "chars": len(doc),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        print(f"{spec['slug']:32s} {len(doc):7d} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
