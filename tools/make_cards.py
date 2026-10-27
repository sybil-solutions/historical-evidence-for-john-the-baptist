#!/usr/bin/env python3
"""Generate one card per source-note entry under collections/citations/.

Each of the dossier's 94 numbered entries gets a page carrying the citation as
the PDF printed it, the host it named, the exact destination read from the
PDF's own link annotation, the chapters of this archive that cite it, and a
link to the mirrored document when the repository holds one.

    python3 tools/make_cards.py       (run after make_references and make_links)
"""
import json
from pathlib import Path

REFS = Path("collections/references/refs.json")
LINKS = Path("collections/references/links.json")
OUT = Path("collections/citations")


def main() -> int:
    refs = json.loads(REFS.read_text())
    links = json.loads(LINKS.read_text()) if LINKS.exists() else {}
    (OUT / "_meta").mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("S*.md"):
        stale.unlink()

    for ref in refs:
        rid = ref["id"]
        doc = links.get(rid)
        rows = [("Register entry", str(ref["number"]))]
        if ref["domains"]:
            rows.append(("Host as printed", ", ".join(ref["domains"])))
        if ref.get("url"):
            rows.append(("Destination", f"[{ref['url']}]({ref['url']})"))
        if doc:
            rows.append(("Mirrored here", f"[{doc}](#/doc/{doc})"))
        cited = [f"{k} ({v}×)" for k, v in ref["cited_in"].items()]
        if cited:
            rows.append(("Cited in", ", ".join(cited)))
        rows.append(("Printed on", f"page {ref['pdf_page']}"))

        lines = [f"# {rid} — {ref['citation']}", ""]
        if ref["detail"]:
            lines += [f"*{ref['work']}* — {ref['detail']}", ""]
        lines += ["| Field | Value |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in rows]
        lines += [""]
        if doc:
            lines += [f"Read the [mirrored text](#/doc/{doc}).", ""]
        text = "\n".join(lines)

        (OUT / f"{rid}.md").write_text(
            f"<!-- Generated from the dossier's source notes. -->\n\n{text}\n", encoding="utf-8"
        )
        (OUT / "_meta" / f"{rid}.json").write_text(
            json.dumps(
                {
                    "slug": rid,
                    "title": f"{rid} — {ref['citation'][:110]}",
                    "source_name": "John_the_Baptist_Research_Dossier.pdf, source notes",
                    "source_url": ref.get("url", ""),
                    "license": "Generated card; citation text from the dossier.",
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    print(f"{len(refs)} reference cards -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
