try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
import re
import statistics

# Fonts whose blocks are code listings, not prose. Their line breaks and
# indentation carry meaning, so they must not be reflowed into a paragraph.
_MONO_RE = re.compile(r"Courier|Mono|Consol|Typewriter", re.I)

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
        for b in blocks:
            if "lines" not in b:
                _flush_code(md_lines, pending_code)
                md_lines.append("*[image]*")
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
                    if not text:
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
