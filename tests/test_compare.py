"""Tests for compare module."""

from pathlib import Path
import fitz
from pdf_toolkit.compare import PDFComparator


def create_test_pdf(path: Path, text: str = "Test", num_pages: int = 1):
    """Create a simple test PDF."""
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), text)
    doc.save(path)
    doc.close()


def test_identical_pdfs(tmp_path):
    pdf1 = tmp_path / "pdf1.pdf"
    pdf2 = tmp_path / "pdf2.pdf"
    create_test_pdf(pdf1, "Hello World", 2)
    create_test_pdf(pdf2, "Hello World", 2)

    comparator = PDFComparator(threshold=1.0)
    result = comparator.compare(pdf1, pdf2)

    assert result["pdf1_pages"] == 2
    assert result["pdf2_pages"] == 2
    assert not result["different_page_count"]
    assert result["pages_with_differences"] == 0
    assert result["identical"]


def test_different_page_counts(tmp_path):
    pdf1 = tmp_path / "pdf1.pdf"
    pdf2 = tmp_path / "pdf2.pdf"
    create_test_pdf(pdf1, "Test", 2)
    create_test_pdf(pdf2, "Test", 3)

    comparator = PDFComparator()
    result = comparator.compare(pdf1, pdf2)

    assert result["different_page_count"]
    assert result["pages_with_differences"] == 1  # Extra page in pdf2
    assert not result["identical"]


def test_different_content(tmp_path):
    pdf1 = tmp_path / "pdf1.pdf"
    pdf2 = tmp_path / "pdf2.pdf"
    create_test_pdf(pdf1, "Hello World", 1)
    create_test_pdf(pdf2, "Hello World Different", 1)

    diff_dir = tmp_path / "diffs"

    comparator = PDFComparator(threshold=0.0)  # Any difference counts
    result = comparator.compare(pdf1, pdf2, output_diff_dir=diff_dir)

    assert not result["identical"]
    assert result["pages_with_differences"] == 1
    # Check that diff image was created
    assert (diff_dir / "diff_page_1.png").exists()


def test_compare_with_output_dir(tmp_path):
    pdf1 = tmp_path / "pdf1.pdf"
    pdf2 = tmp_path / "pdf2.pdf"
    create_test_pdf(pdf1, "Page 1 content", 2)
    # Create pdf2 with extra content
    doc2 = fitz.open()
    for i in range(2):
        page = doc2.new_page()
        if i == 0:
            page.insert_text((50, 50), "Page 1 content")
        else:
            page.insert_text((50, 50), "Page 2 content")
            page.insert_text((100, 100), "Extra content")
    doc2.save(pdf2)
    doc2.close()

    diff_dir = tmp_path / "diffs"
    comparator = PDFComparator(threshold=0.0)  # Any difference counts
    result = comparator.compare(pdf1, pdf2, output_diff_dir=diff_dir)

    assert not result["identical"]
    assert result["pages_with_differences"] == 1
    assert result["pages"][1]["has_differences"]
    assert (diff_dir / "diff_page_2.png").exists()
