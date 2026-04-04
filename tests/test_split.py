"""Tests for split module."""

from pathlib import Path
import fitz
from pdf_toolkit.split import PDFSplitter


def create_test_pdf(path: Path, num_pages: int = 5):
    """Create a simple test PDF."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), f"Test page {i + 1}")
    doc.save(path)
    doc.close()


def test_split_by_pages_single_page(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 5)
    output_dir = tmp_path / "output"

    splitter = PDFSplitter()
    results = splitter.split_by_pages(
        input_pdf, output_dir, pages_per_file=1, prefix="test", overwrite=True
    )

    assert len(results) == 5
    assert all((output_dir / f"test_page_{i+1}.pdf").exists() for i in range(5))

    # Check each output has one page
    for res in results:
        doc = fitz.open(res["output_path"])
        assert len(doc) == 1
        doc.close()


def test_split_by_pages_multiple_pages(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 5)
    output_dir = tmp_path / "output"

    splitter = PDFSplitter()
    results = splitter.split_by_pages(
        input_pdf, output_dir, pages_per_file=2, prefix="test", overwrite=True
    )

    # 5 pages with 2 per file -> 3 parts (2 + 2 + 1)
    assert len(results) == 3


def test_extract_pages(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 10)
    output = tmp_path / "extracted.pdf"

    splitter = PDFSplitter()
    result = splitter.extract_pages(input_pdf, output, "2-5,7", overwrite=True)

    assert result["pages_extracted"] == 5  # 2,3,4,5,7
    assert output.exists()

    doc = fitz.open(output)
    assert len(doc) == 5
    doc.close()


def test_split_by_ranges(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 10)
    output_dir = tmp_path / "output"

    splitter = PDFSplitter()
    results = splitter.split_by_ranges(
        input_pdf, output_dir, ["1-3", "5-7"], prefix="test", overwrite=True
    )

    assert len(results) == 2
    # Check first range
    doc1 = fitz.open(results[0]["output_path"])
    assert len(doc1) == 3
    doc1.close()
    # Check second range
    doc2 = fitz.open(results[1]["output_path"])
    assert len(doc2) == 3
    doc2.close()
