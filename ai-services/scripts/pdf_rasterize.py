#!/usr/bin/env python3
"""
Rasterize page(s) of a PDF to PNG using PyMuPDF.

Used by the /api/icr/filter and /api/icr/rasterize-pdf endpoints to accept
PDFs (the blue-ink filter and jsQR both only operate on raster pixels).
Renders at 300 DPI so downstream OCR/QR-detection sees enough detail.

Default mode rasterizes page 1 only, writing exactly to <output_path>.
Stdout format (single JSON line):
  {"success": true, "output_path": "...", "page_size": [w, h]}

With --all-pages, rasterizes every page instead. <output_path> is treated
as a naming template — each page is written next to it with "_pN" inserted
before the extension (e.g. "out.png" -> "out_p1.png", "out_p2.png", ...).
Stdout format (single JSON line):
  {"success": true, "pages": [{"output_path": "...", "page_number": 1, "page_size": [w, h]}, ...]}
"""

import json
import sys
from pathlib import Path


def rasterize_page(page, matrix, output_path: Path):
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(output_path)
    return pix


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "success": False,
            "error": "Usage: python pdf_rasterize.py <input_pdf> <output_png> [--all-pages]",
        }))
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    all_pages = "--all-pages" in sys.argv[3:]

    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        print(json.dumps({
            "success": False,
            "error": f"PyMuPDF is not installed in the venv: {e}",
        }))
        sys.exit(1)

    if not input_path.exists():
        print(json.dumps({
            "success": False,
            "error": f"Input PDF not found: {input_path}",
        }))
        sys.exit(1)

    try:
        doc = fitz.open(input_path)
        if doc.page_count == 0:
            doc.close()
            print(json.dumps({
                "success": False,
                "error": "PDF has no pages.",
            }))
            sys.exit(1)

        # 300 DPI for OCR/QR-quality detail. fitz uses 72 DPI as the base;
        # 300/72 ≈ 4.1667 zoom.
        matrix = fitz.Matrix(300 / 72, 300 / 72)

        if not all_pages:
            page = doc.load_page(0)
            pix = rasterize_page(page, matrix, output_path)
            page_w, page_h = page.rect.width, page.rect.height
            doc.close()
            print(json.dumps({
                "success": True,
                "output_path": str(output_path),
                "page_size": [page_w, page_h],
                "raster_size": [pix.width, pix.height],
            }))
            return

        stem = output_path.stem
        suffix = output_path.suffix
        pages_result = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            page_output_path = output_path.with_name(f"{stem}_p{i + 1}{suffix}")
            pix = rasterize_page(page, matrix, page_output_path)
            pages_result.append({
                "output_path": str(page_output_path),
                "page_number": i + 1,
                "page_size": [page.rect.width, page.rect.height],
                "raster_size": [pix.width, pix.height],
            })
        doc.close()

        print(json.dumps({
            "success": True,
            "pages": pages_result,
        }))
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"PDF rasterization failed: {e}",
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
