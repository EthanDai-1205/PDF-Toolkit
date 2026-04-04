"""Tests for merge module."""

import pytest
from pathlib import Path
import fitz
from pdf_toolkit.merge import PDFMerger


def create_test_pdf(path: Path, num_pages: int = 1):
    """Create a simple test PDF."""
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), "Test page")
    doc.save(path)
    doc.close()


def test_merge_multiple_pdfs(tmp_path):
    # Create two test PDFs
    pdf1 = tmp_path / "test1.pdf"
    pdf2 = tmp_path / "test2.pdf"
    create_test_pdf(pdf1, 2)
    create_test_pdf(pdf2, 3)

    output = tmp_path / "merged.pdf"

    merger = PDFMerger()
    result = merger.merge([pdf1, pdf2], output, overwrite=True)

    assert result["total_pages"] == 5
    assert result["input_files"] == 2
    assert output.exists()

    # Verify page count
    doc = fitz.open(output)
    assert len(doc) == 5
    doc.close()


def test_merge_with_page_ranges(tmp_path):
    pdf1 = tmp_path / "test1.pdf"
    pdf2 = tmp_path / "test2.pdf"
    create_test_pdf(pdf1, 5)
    create_test_pdf(pdf2, 5)

    output = tmp_path / "merged.pdf"

    merger = PDFMerger()
    # Take first 2 from first, last 2 from second
    result = merger.merge(
        [pdf1, pdf2], output, page_ranges={0: "1-2", 1: "4-5"}, overwrite=True
    )

    assert result["total_pages"] == 4
    assert output.exists()


def test_merge_output_exists_no_overwrite(tmp_path):
    pdf1 = tmp_path / "test1.pdf"
    output = tmp_path / "output.pdf"
    create_test_pdf(pdf1, 1)
    create_test_pdf(output, 1)

    merger = PDFMerger()
    with pytest.raises(ValueError, match="already exists"):
        merger.merge([pdf1], output, overwrite=False)
