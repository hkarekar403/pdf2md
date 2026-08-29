try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
import re

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

        for b in blocks:
            if "lines" not in b:
                md_lines.append("*[image]*")
                continue
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
                    line_text += text
                block_text += line_text + " "
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
    doc.close()
    md = "\n\n".join(md_lines)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md
