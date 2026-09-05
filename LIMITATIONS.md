# What PDF2MD Preserves

PDF2MD reads a PDF's text, type sizes and page geometry to rebuild structure. It is very
good at words, code and tables, and it cannot see pictures at all. This page sets out where
the line falls, so you know what to check before trusting a conversion.

> A styled, shareable version of this page lives at [`docs/fidelity.html`](docs/fidelity.html).

**Measured on 1,191 pages across 2 technical manuals.**

## At a glance

| Preserved | Approximate | Not carried over |
| --- | --- | --- |
| Body text, essentially in full | Heading levels | Diagrams and charts |
| Code listings, with indentation | Tables split across pages | Images |
| Tables, including unruled ones | Nested list indentation | Links and cross-references |
| Bold emphasis | Multi-column reading order | Maths and equations |
| Reading order, single column | Running heads appear inline | Merged table cells |

## Is your document a good fit?

**Works well**

- Text-based PDFs exported from a word processor or typesetter
- Technical manuals, references, specifications
- Documents whose value is in the prose, code and tables
- Single-column layouts

**Expect to lose a lot**

- Anything where diagrams carry the meaning
- Slide decks, brochures, infographics
- Scanned paper, unless you switch OCR on
- Forms, invoices and receipts with boxed layouts
- Two-column academic papers

## What it preserves

Each of these was measured against the source PDF rather than eyeballed, by comparing every
word in the output with every word the PDF actually contains.

### Body text

Effectively everything. Across two manuals, 25 and 2 words respectively went missing out of
roughly 129,000 each — 99.98% and 99.998% of words retained.

### Code listings

Monospaced blocks become fenced code, keeping line breaks, blank lines and indentation.
PDFs store no leading spaces, so indentation is rebuilt from each character's position on
the page. 1,835 listings fenced, 0 flattened.

### Tables

Columns are found by geometry, so tables aligned with plain whitespace are recovered as
well as ruled ones. Cells that wrap over several lines are joined back together. 268 tables
rebuilt as Markdown.

### Speed, and privacy

A 553-page manual converts in about 1.6 seconds (~350 pages/second). Nothing leaves your
machine — there is no upload, no API call and no account, and OCR runs on-device too.

## What is approximate

These come out usable but imperfect. The content is there; the structure around it is a
best guess.

### Heading levels

Headings are inferred from type size relative to the page average, not from any real
structure in the file — PDFs rarely carry one. A document that sets everything in one size
gets no headings at all, and levels can be uneven between sections. One manual yielded
30 / 6 / 285 across H1–H3; the other 335 / 1043 / 806.

### Tables across a page break

A table continuing onto the next page is emitted as two separate tables. Because Markdown
requires a header row, the second piece promotes its first row of data into the header.

### Nested lists

List items survive as text and usually still render as a list, but indentation levels are
flattened — sub-points lettered `a.` and `b.` come out at the same level as the numbered
points above them.

### Multi-column pages

Text is read in the order the PDF stores it. On a two-column page that order may interleave
the columns, so the words are all present but the sentences can be shuffled. This is the one
failure that is easy to miss, because nothing looks obviously broken.

### Running heads and page numbers

Repeated page furniture is content as far as the converter is concerned, so chapter titles,
part numbers and stray page numbers appear inline throughout the output — 275 running-head
lines in a 553-page manual.

## What is not carried over

These are absent from the Markdown entirely. Nothing warns you, which makes this the
section worth reading twice.

### Diagrams and charts

The biggest single loss. Figures drawn as vector artwork — flowcharts, memory layouts,
architecture diagrams — leave no trace at all, not even a placeholder. Their captions and
any surrounding text remain, so a caption reading "Figure 4-1" may be followed by nothing.
**584 of 1,191 pages carried vector artwork — 49% of the corpus.**

### Images

Photographs and other embedded pictures are marked `*[image]*` in place. The marker tells
you something was there; the picture itself is not extracted or saved.

### Links and cross-references

Hyperlinks become plain text, and internal references such as "see Section 12" keep their
wording but lose any ability to navigate.

### Merged and spanning cells

Markdown tables have no way to express a cell spanning several rows or columns, so such
tables are approximated with the content redistributed into a plain grid.

### Equations, and scanned pages

Mathematical notation is not reconstructed. Pages that are pure images of text produce
nothing at all unless you tick **OCR scanned pages**, which reads them on-device at a cost
of a few seconds per page. OCR only runs on pages with no extractable text whatsoever — a
page mixing real text with a scanned figure is left alone.

## Checking your own conversion

Five minutes with the output will tell you most of what you need to know.

1. **Compare the length.** If the Markdown is far shorter than the PDF felt, the document is
   probably scanned. Re-run it with OCR enabled.
2. **Search for orphaned captions.** Look for "Figure" or "Diagram" in the output. Each one
   you find marks a picture that is now missing, and tells you how much the document relied
   on them.
3. **Count the headings.** No `#` headings at all means the source used a single type size,
   and you will need to add structure by hand.
4. **Spot-check a long table.** Find one that ran over a page break in the original and
   confirm both halves are present and correctly aligned.
5. **Read one paragraph from a busy page.** If a sentence stops making sense halfway
   through, the page was probably multi-column and the reading order interleaved.

## The measurements behind this

| Measure | Programmer's Guide | Reference Manual |
| --- | ---: | ---: |
| Pages | 553 | 638 |
| Conversion time | 1.6 s | 1.4 s |
| Words in source | 129,661 | 128,354 |
| Words missing from output | 25 | 2 |
| Code listings fenced | 790 | 1,045 |
| Tables rebuilt | 132 | 136 |
| Document set in monospace | 22.1% | 10.0% |
| Pages with vector artwork | 172 | 412 |

## How far to trust these numbers

Everything here was measured on two documents of a single kind: HPE TAL programming
manuals, typeset in 1993, single-column, heavy with code and reference tables. They are a
demanding test for text and tables and a very forgiving one for layout.

Nothing on this page has been verified against modern PDFs, two-column academic papers,
forms, invoices, presentation decks, right-to-left scripts or CJK text. The tool will still
convert them; the accuracy figures above simply do not extend that far, and the layout
limitations are likely to bite harder than they did here.
