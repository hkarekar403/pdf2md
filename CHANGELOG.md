# Changelog

All notable changes to this project are documented here. This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-09-03

The theme of this release is **fidelity**: the converter now keeps the parts of a document
that carry its meaning, rather than reducing everything to a stream of words. Two structural
features and two correctness fixes, all measured against 1,191 pages of real technical
manuals.

### Added

- **Code listings are preserved as fenced blocks.** Blocks set in a monospace face are
  emitted as fenced code with their line breaks, blank lines and indentation intact.
  Previously a multi-line listing was reflowed into a single paragraph — correct for prose,
  destructive for code. PDFs store no leading whitespace, so indentation is rebuilt from
  each span's horizontal position and the median character width. Consecutive listings merge
  into one fence instead of fragmenting. In one test manual this is 22% of the document:
  1,120 multi-line listings, roughly 6,700 lines that were previously flattened.

- **Tables are rebuilt as Markdown tables.** Columns are recovered geometrically by
  clustering span left-edges, so whitespace-aligned tables are found as well as ruled ones.
  PyMuPDF's own `find_tables()` is not used: on these manuals it finds none of the real
  tables and returns 114 false ones, because it looks for ruled cells while the vector rules
  on the page belong to figures and memory-layout diagrams. Cells that wrap across several
  lines are joined back together, and rows are assembled across block boundaries.

- **Two guards keep a bad table from being worse than no table.** Runs that are really
  numbered lists or contents entries are rejected on shape and left as prose. Every non-space
  character in a candidate region must reappear in the emitted cells, or the region is left
  as prose — a flattened table is visibly degraded and a reader knows to check the source,
  whereas a well-formed table that quietly dropped a cell is not.

- **`LIMITATIONS.md` and `docs/fidelity.html`** — a user-facing one-pager describing what
  the tool preserves, what it approximates and what it drops entirely, with the measurements
  behind each claim.

### Fixed

- **Words are no longer glued together.** Each span's text was stripped before being
  concatenated, which discarded the space *between* spans, so `"The "` + `"TAL Programmer's
  Guide"` became `"TheTAL Programmer'sGuide"`. Stripping at line granularity instead fixes
  it. This affected 1,523 and 4,431 words per manual — up to 3.4% of all words in a
  document.

- **Text is no longer dropped or duplicated around tables.** Spans consumed by a table are
  tracked by identity rather than by bounding box, so a block that only partly overlaps a
  table is neither dropped nor emitted twice.

### Measured

| | Programmer's Guide | Reference Manual |
| --- | ---: | ---: |
| Pages | 553 | 638 |
| Conversion time | 1.6 s | 1.4 s |
| Words missing from output (was) | 25 (1,523) | 2 (4,431) |
| Code listings fenced | 790 | 1,045 |
| Tables rebuilt | 132 | 136 |

Word retention is 99.98% and 99.998%. No candidate table region failed the conservation
check. Conversion speed is unchanged.

### Known limitations

Vector diagrams, images, links and equations are still not carried over, and tables split
across a page break are emitted as fragments. See [LIMITATIONS.md](LIMITATIONS.md) for the
full picture and for how to check a conversion yourself.

## [1.0.0] — 2026-08-29

Initial release.

### Added

- Drag-and-drop PDF upload with batch conversion and real-time progress
- Heading detection from relative type size, plus bold emphasis
- Warm Editorial and Pro Dark themes, remembered across launches
- Optional on-device OCR (RapidOCR) for pages with no text layer
- Visible `*[image]*` markers where images cannot be represented
- Native save dialog, with browser download fallback outside the desktop shell
- Exit confirmation guarding an in-progress queue
- PyInstaller packaging for a standalone executable, with app icon and favicon
- Animated PDF-to-Markdown explainer on the startup splash

[1.1.0]: https://github.com/hkarekar403/pdf2md/releases/tag/v1.1.0
[1.0.0]: https://github.com/hkarekar403/pdf2md/releases/tag/v1.0.0
