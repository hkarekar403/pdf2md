try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
import re
import statistics
from collections import Counter

# Fonts whose blocks are code listings, not prose. Their line breaks and
# indentation carry meaning, so they must not be reflowed into a paragraph.
_MONO_RE = re.compile(r"Courier|Mono|Consol|Typewriter", re.I)

# Table reconstruction. Columns are found by clustering span left-edges, so
# whitespace-aligned tables are recovered as well as ruled ones.
_TABLE_TOL = 6.0          # points of slack when snapping a span to a column
_TABLE_MIN_ROWS = 3
_LIST_LEAD = re.compile(r"^(\d+[.)]|[a-z][.)]|[-•▪•])$")
_TOC_TAIL = re.compile(r"(^|\s)[A-Za-z]?-?\d+([-.]\d+)*$")

_ocr_engine = None


def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine


def _ocr_page(page):
    engine = _get_ocr_engine()
    pix = page.get_pixmap(dpi=200)
    result, _ = engine(pix.tobytes("png"))
    if not result:
        return ""
    return "\n".join(item[1] for item in result if item[1].strip())


def _is_code_block(block):
    """True when a block is mostly monospace, i.e. a code listing."""
    mono = total = 0
    for line in block["lines"]:
        for span in line["spans"]:
            text = span["text"].strip()
            if not text:
                continue
            total += len(text)
            if _MONO_RE.search(span["font"]):
                mono += len(text)
    return total > 0 and mono / total >= 0.8


def _code_lines(block):
    """Render a code block, keeping line breaks and column indentation.

    PDFs carry no leading whitespace: indentation is the span's x offset, so
    columns are reconstructed from x positions and the monospace char width.
    """
    rows, widths = [], []
    for line in block["lines"]:
        spans = [s for s in line["spans"] if s["text"].strip()]
        if not spans:
            continue
        for s in spans:
            if _MONO_RE.search(s["font"]):
                w = (s["bbox"][2] - s["bbox"][0]) / len(s["text"])
                if w > 0:
                    widths.append(w)
        rows.append(spans)
    if not rows:
        return []

    char_w = statistics.median(widths) if widths else 6.0
    left = min(s["bbox"][0] for spans in rows for s in spans)
    out = []
    prev_bottom = None
    for spans in rows:
        top = min(s["bbox"][1] for s in spans)
        height = max(s["bbox"][3] for s in spans) - top
        # a vertical gap wider than half a line is a blank line in the source
        if prev_bottom is not None and height and top - prev_bottom > 0.6 * height:
            out.append("")
        prev_bottom = max(s["bbox"][3] for s in spans)
        text = ""
        for s in spans:
            col = int(round((s["bbox"][0] - left) / char_w))
            if col > len(text):
                text += " " * (col - len(text))
            text += s["text"].replace("\n", "")
        out.append(text.rstrip())
    return out


def _flush_code(md_lines, pending):
    if pending:
        body = "\n".join(pending).strip("\n")
        if body:
            md_lines.append(f"```\n{body}\n```")
        pending.clear()


def _text_lines(blocks):
    """Visual lines of non-code text on a page, top-down, spans left-to-right.

    Tables routinely span several blocks, so rows are rebuilt from y position
    across the whole page rather than trusting block boundaries.
    """
    rows = {}
    for b in blocks:
        if "lines" not in b or _is_code_block(b):
            continue
        for ln in b["lines"]:
            for s in ln["spans"]:
                if s["text"].strip():
                    rows.setdefault(round(s["bbox"][1] / 2.0), []).append(s)
    return [sorted(rows[k], key=lambda s: s["bbox"][0]) for k in sorted(rows)]


def _column_anchors(lines):
    xs = sorted({s["bbox"][0] for spans in lines for s in spans})
    anchors = []
    for x in xs:
        if not anchors or x - anchors[-1] > _TABLE_TOL:
            anchors.append(x)
    return anchors


def _anchor_hits(spans, anchors):
    hits = set()
    for s in spans:
        for i, a in enumerate(anchors):
            if abs(s["bbox"][0] - a) <= _TABLE_TOL:
                hits.add(i)
                break
    return hits


def _line_height(spans):
    return max((s["size"] for s in spans), default=10.0) * 1.2


def _table_runs(lines, anchors):
    """Maximal runs of vertically adjacent lines sharing >=2 column anchors."""
    hits = [_anchor_hits(sp, anchors) for sp in lines]
    tops = [min(s["bbox"][1] for s in sp) for sp in lines]
    runs, i = [], 0
    while i < len(lines):
        j, shared = i, hits[i]
        while j + 1 < len(lines):
            nxt = shared & hits[j + 1]
            gap = tops[j + 1] - tops[j]
            size = max(s["size"] for s in lines[j + 1])
            if len(nxt) >= 2 and gap <= 2.2 * _line_height(lines[j]):
                shared, j = nxt, j + 1
            elif hits[j + 1] and hits[j + 1] <= shared and gap <= 1.35 * size:
                # a wrapped cell: too few columns to stand as a row, but tight
                # against the line above and aligned to columns already in use
                j += 1
            else:
                break
        if j - i + 1 >= _TABLE_MIN_ROWS and len(shared) >= 2:
            runs.append((i, j, sorted(shared)))
            i = j + 1
        else:
            i += 1
    return runs


def _build_rows(lines, run, anchors):
    """Group a run's lines into logical rows, merging wrapped cells.

    A wrapped cell continues on the next line at single line spacing, while a
    new row is set off by extra leading. Returns (rows, spans left of the
    table's first column, which belong to the surrounding text).
    """
    i, j, cols = run
    xs = [anchors[c] for c in cols]
    rows, outside = [], []
    # A cell that wraps continues at the font's own leading (~1.2x the point
    # size); a new row is set further down. Measured across these manuals,
    # continuations sit at 1.20 and new rows at 1.50-1.67, so 1.35 separates
    # them without depending on any one table's spacing.
    prev_top = None
    for spans in lines[i:j + 1]:
        top = min(s["bbox"][1] for s in spans)
        size = max(s["size"] for s in spans)
        new_row = prev_top is None or (top - prev_top) > 1.35 * size
        prev_top = top
        cells = [""] * len(xs)
        for s in spans:
            if s["bbox"][0] < xs[0] - _TABLE_TOL:
                outside.append(s["text"].strip())
                continue
            k = max(n for n, x in enumerate(xs) if s["bbox"][0] >= x - _TABLE_TOL)
            cells[k] += (" " if cells[k] else "") + s["text"].strip()
        if new_row or not rows:
            rows.append(cells)
        else:
            for n, v in enumerate(cells):
                if v:
                    rows[-1][n] += (" " if rows[-1][n] else "") + v
    return rows, outside


def _looks_tabular(rows):
    """Reject runs that are really lists or contents entries, not tables."""
    if len(rows) < _TABLE_MIN_ROWS:
        return False
    first = [r[0].strip() for r in rows if r[0].strip()]
    if first and sum(bool(_LIST_LEAD.match(c)) for c in first) / len(first) >= 0.6:
        return False
    last = [r[-1].strip() for r in rows if r[-1].strip()]
    if last and sum(bool(_TOC_TAIL.search(c)) for c in last) / len(last) >= 0.7:
        return False
    # every row but the header needs real content in at least two columns
    filled = sum(1 for r in rows[1:] if sum(1 for c in r if c.strip()) >= 2)
    return filled >= len(rows[1:]) * 0.6


def _conserved(lines, run, rows, outside):
    """Every non-space character in the region must survive into the output.

    Silently dropping a wrapped cell turns a visibly mangled table into a
    well-formed one that lies, so a region that fails this is left as prose.
    """
    src = "".join(s["text"] for spans in lines[run[0]:run[1] + 1] for s in spans)
    out = " ".join(c for r in rows for c in r) + " " + " ".join(outside)
    return Counter(re.findall(r"\S", src)) == Counter(re.findall(r"\S", out))


def _render_table(rows):
    def cell(c):
        return c.replace("|", "\\|").strip() or " "

    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(cell(c) for c in rows[0]) + " |",
           "|" + "---|" * width]
    for r in rows[1:]:
        out.append("| " + " | ".join(cell(c) for c in r) + " |")
    return "\n".join(out)


def _detect_tables(blocks):
    """Tables on a page as (markdown, ids of the spans it consumed).

    Spans are tracked by identity rather than by region, so a block that only
    partly overlaps a table is neither dropped nor emitted twice.
    """
    lines = _text_lines(blocks)
    if len(lines) < _TABLE_MIN_ROWS:
        return []
    anchors = _column_anchors(lines)
    found = []
    for run in _table_runs(lines, anchors):
        rows, outside = _build_rows(lines, run, anchors)
        if not _looks_tabular(rows) or not _conserved(lines, run, rows, outside):
            continue
        used = {id(s) for sp in lines[run[0]:run[1] + 1] for s in sp}
        md = _render_table(rows)
        if outside:
            md = " ".join(outside) + "\n\n" + md
        found.append((md, used))
    return found


def convert_pdf_to_md(pdf_path, enable_ocr=False):
    doc = pymupdf.open(pdf_path)
    md_lines = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        page_font_sizes = []
        page_has_text = False
        page_has_image = False
        for b in blocks:
            if "lines" in b:
                for line in b["lines"]:
                    for span in line["spans"]:
                        page_font_sizes.append(span["size"])
                        if span["text"].strip():
                            page_has_text = True
            else:
                page_has_image = True
        avg_font = (
            sum(page_font_sizes) / len(page_font_sizes) if page_font_sizes else 12
        )

        if enable_ocr and page_has_image and not page_has_text:
            ocr_text = _ocr_page(page)
            if ocr_text:
                md_lines.append(f"<!-- OCR: page {page_num + 1} -->\n\n{ocr_text}")
            else:
                md_lines.append(f"*[image, page {page_num + 1} — OCR found no text]*")
            continue

        pending_code = []
        tables = _detect_tables(blocks)
        emitted = set()
        for b in blocks:
            if "lines" not in b:
                _flush_code(md_lines, pending_code)
                md_lines.append("*[image]*")
                continue
            # emit any table this block's spans belong to, then drop those
            # spans so the prose path cannot repeat them
            block_ids = {id(s) for ln in b["lines"] for s in ln["spans"]}
            skip = set()
            for n, (table_md, used) in enumerate(tables):
                if block_ids & used:
                    _flush_code(md_lines, pending_code)
                    if n not in emitted:
                        emitted.add(n)
                        md_lines.append(table_md)
                    skip |= used
            if block_ids and block_ids <= skip:
                continue
            if _is_code_block(b):
                # consecutive listings merge into one fence
                pending_code.extend(_code_lines(b))
                continue
            _flush_code(md_lines, pending_code)
            block_text = ""
            max_font = 0
            is_bold = False
            for line in b["lines"]:
                line_text = ""
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or id(span) in skip:
                        continue
                    font_size = span["size"]
                    flags = span["flags"]
                    if font_size > max_font:
                        max_font = font_size
                    if flags & 2**4:
                        is_bold = True
                    # keep the span's own spacing: stripping here would glue
                    # adjacent spans together ("The " + "TAL" -> "TheTAL")
                    line_text += span["text"]
                block_text += line_text.strip() + " "
            block_text = block_text.strip()
            if not block_text:
                continue
            ratio = max_font / avg_font if avg_font else 1
            if ratio >= 1.6:
                md_lines.append(f"# {block_text}")
            elif ratio >= 1.3:
                md_lines.append(f"## {block_text}")
            elif ratio >= 1.1:
                md_lines.append(f"### {block_text}")
            else:
                if is_bold and len(block_text) < 120:
                    md_lines.append(f"**{block_text}**")
                else:
                    md_lines.append(block_text)
        _flush_code(md_lines, pending_code)
    doc.close()
    md = "\n\n".join(md_lines)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md
