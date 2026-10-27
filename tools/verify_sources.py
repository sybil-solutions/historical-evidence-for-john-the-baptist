#!/usr/bin/env python3
"""Check that every mirrored document actually contains the text it claims to.

A fetch can silently return a page shell, a login screen, or a different work.
This tool holds, per document, strings that must appear in the text, and a
minimum size. Run it after any fetch; it exits non-zero on failure.

    python3 tools/verify_sources.py
"""
import sys
from pathlib import Path

# document -> (required substrings, minimum characters)
CHECKS: dict[str, tuple[list[str], int]] = {
    # Scripture: the World English Bible
    "scripture/2-kings": (["chapter 1", "elijah"], 100_000),
    "scripture/isaiah": (["chapter 40", "voice of one who calls out"], 100_000),
    "scripture/malachi": (["chapter 3", "messenger"], 8_000),
    "scripture/matthew": (["chapter 3", "baptize"], 100_000),
    "scripture/mark": (["chapter 1", "baptize"], 70_000),
    "scripture/luke": (["chapter 3", "baptize"], 110_000),
    "scripture/john": (["chapter 1", "baptize"], 90_000),
    "scripture/acts": (["chapter 19", "baptism"], 110_000),
    "scripture/romans": (["chapter 6", "baptism"], 45_000),
    # Qur'an, Palmer
    "quran/surah-03": (["imrân", "john"], 20_000),
    "quran/surah-06": (["john", "cattle"], 10_000),
    "quran/surah-19": (["mary", "john"], 8_000),
    "quran/surah-21": (["john", "prophets"], 8_000),
    # Ancient witnesses
    "witnesses/josephus-antiquities-18": (["called the baptist", "aretas", "macherus"], 8_000),
    "witnesses/origen-contra-celsum-1-47": (["josephus", "john", "celsus"], 1_500),
    # Non-canonical gospels
    "gospels/gospel-of-thomas": (["thomas", "saying"], 20_000),
    "gospels/protevangelium-of-james": (["joachim", "mary"], 25_000),
    # The archive's own entries
    "archaeology/machaerus": (["herodian", "josephus"], 1_200),
    "archaeology/bethany-beyond-the-jordan": (["maghtas", "unesco"], 1_200),
    "archaeology/bulgarian-relics": (["radiocarbon", "dna"], 1_200),
    "archaeology/cave-of-john": (["suba", "strange"], 1_200),
    "archaeology/qumran-and-john": (["qumran", "isaiah 40:3"], 1_200),
    "afterlives/mandaeans": (["mandaean", "maṣbuta"], 1_500),
    "afterlives/yahya-in-islam": (["yahya", "qur'an"], 1_500),
    "afterlives/christian-art-and-liturgy": (["john", "louvre"], 1_500),
}


def main() -> int:
    failures = []
    for doc, (needs, minimum) in sorted(CHECKS.items()):
        path = Path("collections") / f"{doc}.md"
        if not path.exists():
            failures.append((doc, "missing file"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if len(text) < minimum:
            failures.append((doc, f"too short: {len(text)} < {minimum}"))
            continue
        absent = [n for n in needs if n not in text]
        if absent:
            failures.append((doc, f"missing: {', '.join(absent)}"))
    for doc, why in failures:
        print(f"FAIL {doc}: {why}")
    print(f"{len(CHECKS) - len(failures)}/{len(CHECKS)} documents verified")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
