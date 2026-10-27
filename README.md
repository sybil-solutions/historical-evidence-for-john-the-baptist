# Historical evidence for John the Baptist: a research dossier, its sources, and an archive

This repository holds three things:

1. **The dossier** — [John_the_Baptist_Research_Dossier.pdf](John_the_Baptist_Research_Dossier.pdf), a research report on the historical John: what evidence survives, a life reconstructed with its gaps left visible, the movement he led, why baptism was consequential, the relationship with Jesus, prophecy and Elijah, why he was killed, what became of his followers, the archaeology and the relic claims, his afterlives in Mandaeism, Islam and Christian worship, and why a man with so little surviving biography became so large a figure (research cutoff 27 October 2026).
2. **The sources it cites** — the ancient texts behind the report, mirrored in public-domain translations where one exists, with the exact destination of every one of the 94 numbered source notes taken from the PDF's own hyperlinks.
3. **A readable, searchable site** — [docs/index.html](docs/index.html), which turns the collections into a searchable archive with a reading pane, source cards, and cross-links between the dossier's passages and the documents behind them.

**Read it:** <https://sybil-solutions.github.io/historical-evidence-for-john-the-baptist/>

The companion archive on Jesus of Nazareth — the dossier, the 238 sources it cites, and the same searchable reader — is at
[sybil-solutions/all-historical-evidence-of-jesus-christ](https://sybil-solutions.github.io/all-historical-evidence-of-jesus-christ/).
John appears in both; the difference is which figure the evidence is organised around.

To run the same site locally, open `docs/index.html`, or serve it:

```sh
python3 -m http.server -d docs 8123   # then open http://127.0.0.1:8123/
```

## Who he was

A Jewish preacher and baptizer of the early first century, active in the Judean
wilderness and the Jordan valley, who called Israel to repentance, immersed
people in water as the visible side of that repentance, gathered disciples,
baptized Jesus, and was executed by Herod Antipas — Josephus says at Machaerus,
and the Gospels say over Herod's marriage to his brother's wife. The execution
falls before 36 CE, when Antipas was deposed; the usual dating of his activity is
the late 20s.

That is the reconstruction nearly every historian who works on the period
accepts. Everything past it is argued, and the argument is the subject of the
dossier:

- **No document written by John survives.** Nothing he wrote, nothing written in
  his lifetime by anyone, and no contemporary notice of him. His own words come
  only through authors who had other purposes.
- **Josephus is the non-Christian witness that matters.** *Antiquities* XVIII.5.2,
  written around 93 CE, describes a good man who called on Jews to practise
  virtue, baptize, and gather — and says Antipas killed him because the crowds
  might follow him into revolt. The passage makes sense without Christianity in
  it, which is why it carries weight. Origen, in *Against Celsus* I.47, already
  argues from it.
- **The Gospels agree on the frame and disagree on the portrait.** Mark's John is
  Elijah returned, preaching repentance and a mightier one to come; Matthew and
  Luke reuse Mark and add birth narratives and John's own moral teaching; the
  Fourth Gospel turns him into a witness who must decrease. They honour him and
  subordinate him, and the ways they do so differ enough to be read separately
  before being harmonised.
- **His baptism outlived him.** Acts 18-19 shows disciples of John in Ephesus
  decades later, and a baptism that had to be distinguished from Christian
  baptism. A movement that needed explaining is a movement that existed.
- **Other traditions kept him.** Mandaeans revere John as a priest and teacher in
  a religion of their own; Islam honours him as Yahya, son of Zakariyya, without
  the baptism of Jesus or the dance and the platter. These are related histories,
  not one biography.

### What the evidence establishes, and what it does not

| Claim | Best assessment |
|---|---|
| John existed and led a baptismal movement | Strong historical conclusion |
| Antipas ordered his execution | Strong historical conclusion |
| Jesus received John's baptism | Widely accepted historical conclusion |
| John belonged to Qumran | Unproved hypothesis |
| A traditional shrine marks the exact first-century event | Requires evidence beyond later commemoration |
| Radiocarbon dating has identified John's bones | False: age compatibility is not personal identification |
| DNA has established a genetic profile of John | Unsupported by the published relic study |
| A later book preserves John's own verbatim teachings | Must be argued passage by passage; no authenticated autograph exists |

## The collections

<!-- collections:start -->
| Collection | Documents | What it holds |
|---|---|---|
| [dossier](collections/dossier/) | 16 | The report itself, chaptered, plus the 94-entry source notes |
| [scripture](collections/scripture/) | 9 | The books the dossier cites, World English Bible, one file per book |
| [quran](collections/quran/) | 4 | Surahs 3, 6, 19 and 21 on Yahya, Palmer's public-domain translation |
| [gospels](collections/gospels/) | 2 | The Gospel of Thomas and the Protevangelium of James, public-domain translations |
| [witnesses](collections/witnesses/) | 2 | Josephus, Antiquities XVIII.5, and Origen, Against Celsus I.47 |
| [archaeology](collections/archaeology/) | 5 | Machaerus, Bethany beyond the Jordan, the Sozopol relics, the Suba cave, the Qumran question |
| [afterlives](collections/afterlives/) | 3 | The Mandaeans, Yahya in Islam, and Christian worship and art |
| [citations](collections/citations/) | 94 | One page per source note: the citation, the exact destination, and where it is cited |
| [references](collections/references/) | 94 | `refs.json` (exact link destinations from the PDF), `links.json` (mirrored entries), `links-report.md` (the verified match for each) |
<!-- collections:end -->

Also: [the source notes](collections/dossier/12-source-notes.md), one heading per
numbered entry, and [the link report](collections/references/links-report.md),
which records the verified match between each entry and the document that
carries it.

## How the reference layer works

The dossier prints a numbered source for each of its findings, and its PDF
carries a live hyperlink on 94 of those notes — often to a particular page
(Josephus on livius.org, Origen I.47 on New Advent, the AMS/DNA bone study on the
University of Copenhagen research portal). `tools/make_references.py` reads those
link annotations out of the PDF and attaches each one to the numbered entry whose
position on the page it belongs to, so the archive carries the exact destination
rather than a guess made from the printed hostname.

A reference is linked to a mirrored document only when two things hold: the
citation names the work, **and** the document actually contains the locator the
citation gives (a chapter heading, or the phrase the extract is built around).
Everything else keeps its own publisher link and is not copied.

## Build

Everything derived is reproducible:

```sh
./tools/build-all.sh
```

| Tool | Does |
|---|---|
| `tools/fetch_web.py` | eBible.org USFM archive → `collections/scripture/` (World English Bible, public domain) |
| `tools/fetch_quran.py` | Wikisource → `collections/quran/` (Palmer, 1880, public domain) |
| `tools/fetch_witness.py` | Extract Josephus XVIII.5 and Origen I.47 between printed markers, with an anchor check |
| `tools/make_references.py` | PDF → 94 source-note entries with their exact link destinations |
| `tools/make_dossier.py` | PDF → chaptered Markdown: paragraphs reflowed from line leading, tables rebuilt, headings restored from the table of contents |
| `tools/make_cards.py` | One card per source-note entry |
| `tools/make_links.py` | Verified reference → document mapping, with a report |
| `tools/build_catalog.py` | Filesystem + sidecars → `collections/catalog.json` |
| `tools/build_site.py` | Catalog → `docs/` (site shell, per-document JSON, search index) |
| `tools/verify_sources.py` | Asserts every mirrored source contains the text it claims |
| `tools/check_site.py` | Asserts no generated page points at something that does not exist |

## Sourcing and licensing

Mirrored texts are public domain: the World English Bible (public domain;
"World English Bible" is a trademark of eBible.org, and the wording here is
unaltered), Whiston's Josephus (1737), the Ante-Nicene Fathers translation of
Origen, E. H. Palmer's Qur'an (1880), and Mark M. Mattison's public-domain
translations of the Gospel of Thomas and the Protevangelium of James.

Copyrighted scholarship is **linked, never copied**. The archaeology and
afterlife entries are the archive's own prose, with links to the excavators, the
holding institutions and the publishers; no inscription text, relic photograph or
copyrighted translation is reproduced here. The entries state what each artifact
or study does and does not establish, and flag the disputed cases (the Suba cave,
the Sozopol relics, the Qumran affiliation) as disputed.

The dossier itself is the archive's own document.
