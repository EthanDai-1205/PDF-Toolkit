"""Tests for pdf_to_image module."""

import pytest
from pathlib import Path
import fitz
from pdf_toolkit.pdf_to_image import PDFToImageConverter


def create_test_pdf(path: Path, num_pages: int = 3):
    """Create a simple test PDF."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), f"Test page {i + 1}")
        page.draw_rect(fitz.Rect(100, 100, 200, 200))
    doc.save(path)
    doc.close()


def test_convert_all_pages(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 3)
    output_dir = tmp_path / "output"

    converter = PDFToImageConverter()
    results = converter.convert(
        input_pdf, output_dir, dpi=72, format="png", overwrite=True
    )

    assert len(results) == 3
    assert all((output_dir / f"input_page_{i+1}.png").exists() for i in range(3))

    # Check dimensions are reasonable
    # Default page is 595x842 points @ 72 DPI -> 595x842 pixels
    assert results[0]["width"] > 500
    assert results[0]["height"] > 800


def test_convert_specific_pages(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 5)
    output_dir = tmp_path / "output"

    converter = PDFToImageConverter()
    results = converter.convert(
        input_pdf, output_dir, page_ranges="1,3-5", dpi=72, format="png", overwrite=True
    )

    # Pages 1, 3, 4, 5 -> 4 pages
    assert len(results) == 4


def test_convert_jpeg(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 1)
    output_dir = tmp_path / "output"

    converter = PDFToImageConverter()
    results = converter.convert(
        input_pdf, output_dir, dpi=72, format="jpeg", quality=80, overwrite=True
    )

    assert len(results) == 1
    output_file = Path(results[0]["output_path"])
    assert output_file.suffix == ".jpg"
    assert output_file.exists()


def test_convert_single_page(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 5)
    output_image = tmp_path / "page2.png"

    converter = PDFToImageConverter()
    result = converter.convert_single_page(
        input_pdf, output_image, page_number=2, dpi=72, overwrite=True
    )

    assert output_image.exists()
    assert "width" in result
    assert "height" in result


def test_invalid_format(tmp_path):
    input_pdf = tmp_path / "input.pdf"
    create_test_pdf(input_pdf, 1)
    output_dir = tmp_path / "output"

    converter = PDFToImageConverter()
    with pytest.raises(ValueError, match="Format must be"):
        converter.convert(input_pdf, output_dir, format="bmp", overwrite=True)
