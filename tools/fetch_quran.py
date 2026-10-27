#!/usr/bin/env python3
"""Mirror the Qur'an passages about John/Yaḥyā from Palmer's public-domain translation.

Edward Henry Palmer's translation (Sacred Books of the East, 1880) is public
domain. The four surahs the dossier cites are fetched once from Wikisource's
rendered page and cached, then written as Markdown with the translator's verse
numbers left where he printed them.

Output: collections/quran/surah-NN.md plus `_meta/` sidecars.

    python3 tools/fetch_quran.py [--refresh]
"""
import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SURAHS = {
    3: ("Imran", "The Chapter of Imrân's Family"),
    6: ("Anam", "The Chapter of Cattle"),
    19: ("Maryam", "The Chapter of Mary"),
    21: ("Anbiya", "The Chapter of the Prophets"),
}
CACHE = Path(".cache/quran")
OUT = Path("collections/quran")
UA = {"User-Agent": "john-the-baptist-archive/1.0 (+https://github.com/sybil-solutions)"}
PAGE = "The Qur'an (Palmer)/{}"


def fetch(slug: str, refresh: bool) -> str:
    target = CACHE / f"{slug}.html"
    if target.exists() and not refresh:
        return target.read_text(encoding="utf-8")
    url = "https://en.wikisource.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "parse",
            "page": PAGE.format(slug),
            "prop": "text",
            "format": "json",
            "formatversion": "2",
        }
    )
    body = ""
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as resp:
                payload = json.loads(resp.read().decode())
            body = payload["parse"]["text"]
            break
        except Exception as exc:  # noqa: BLE001 - transient network
            if attempt == 4:
                raise SystemExit(f"{slug}: {exc}")
            time.sleep(2 * (attempt + 1))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return body


def to_text(body: str, title: str = "") -> str:
    """Rendered article HTML -> plain paragraphs, keeping the printed verse numbers."""
    body = re.sub(r"(?is)<(script|style|sup)[^>]*>.*?</\1>", "", body)
    # Wikisource wraps each proofread page in a div; a page break is not a break
    # in the surah, but a <p> is.
    body = re.sub(r"(?i)</p>", "\n\n", body)
    body = re.sub(r"(?i)<br\s*/?>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    text = html.unescape(body)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    paragraphs = [" ".join(p.split()) for p in text.split("\n\n")]
    kept: list[str] = []
    for para in paragraphs:
        if not para or re.fullmatch(r"\[?\d{1,4}\]?", para):
            continue  # folio numbers and bare footnote markers
        if "\u2190" in para or "Wikisource" in para or "translated by Edward Henry Palmer" in para:
            continue  # header navigation the parser block carries
        if "\u2192" in para:
            para = para.split("\u2192")[0].strip()
        if para.lower() in {"the qur\u02bc\u00e2n", "the qur'\u00e2n"}:
            continue
        if kept and kept[-1] == para:
            continue
        if title and para.rstrip(".").strip() == title.rstrip(".").strip() and not kept:
            continue
        kept.append(para)
    return "\n\n".join(kept)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_meta").mkdir(exist_ok=True)
    for number, (slug, title) in SURAHS.items():
        text = to_text(fetch(slug, args.refresh), title)
        stem = f"surah-{number:02d}"
        url = f"https://en.wikisource.org/wiki/{PAGE.format(slug).replace(' ', '_').replace(chr(39), '%27')}"
        doc = f"# {title}\n\n{text.strip()}\n"
        (OUT / f"{stem}.md").write_text(
            f"<!-- Fetched from {url.replace('%27', chr(39))} on {date.today().isoformat()}. "
            "E. H. Palmer, The Qur'an (Sacred Books of the East, 1880), public domain. -->\n\n" + doc,
            encoding="utf-8",
        )
        (OUT / "_meta" / f"{stem}.json").write_text(
            json.dumps(
                {
                    "slug": stem,
                    "title": f"Qur'an, Surah {number} ({slug}), Palmer translation (1880)",
                    "source_name": "E. H. Palmer, Sacred Books of the East vols. 6 & 9 (1880), via Wikisource",
                    "source_url": url,
                    "license": "Public domain",
                    "fetched": date.today().isoformat(),
                    "chars": len(doc),
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        print(f"{stem:10s} {len(doc):7d} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
